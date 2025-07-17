import json
import os
import subprocess
import threading
import boto3
import paramiko
import time

from ssm_cli.ssh.transport import StdIoSocket
from ssm_cli.ssh.shell import ShellThread
from ssm_cli.ssh.forward import ForwardThread
from ssm_cli.ssh.channels import Channels
from ssm_cli.xdg import get_ssh_hostkey
from ssm_cli.instances import Instance

import logging
logger = logging.getLogger(__name__)

class SshServer(paramiko.ServerInterface):
    """
    Creates ssh server using StdIoSocket
    """
    event: threading.Event
    direct_tcpip_callback: callable
    instance: Instance
    session: boto3.Session
    needs_pty: bool = False
    
    def __init__(self, instance: Instance, session, direct_tcpip_callback: callable):
        logger.debug("creating server")
        self.event = threading.Event()
        self.instance = instance
        self.session = session
        self.direct_tcpip_callback = direct_tcpip_callback
    
    def start(self):
        logger.info("starting server")

        sock = StdIoSocket()
        self.transport = paramiko.Transport(sock)
        self.channels = Channels(self.transport)

        key_path = get_ssh_hostkey()
        host_key = paramiko.RSAKey(filename=key_path)
        logger.info("Loaded existing host key")
        
        self.transport.add_server_key(host_key)
        self.transport.start_server(server=self)

        self.event.wait()

    # Auth handlers, just allow anything. The only use of this code is ProxyCommand and auth is not needed
    def get_allowed_auths(self, username):
        logger.info(f"allowing all auths: username={username}")
        return "password,publickey,none"
    def check_auth_none(self, username):
        logger.info(f"accepting auth none: username={username}")
        return paramiko.AUTH_SUCCESSFUL
    def check_auth_password(self, username, password):
        logger.info(f"accepting auth password: username={username}")
        return paramiko.AUTH_SUCCESSFUL
    def check_auth_publickey(self, username, key):
        logger.info(f"accepting auth public key: username={username}")
        return paramiko.AUTH_SUCCESSFUL
    
    # Allow sessions
    def check_channel_request(self, kind, chanid):
        logger.info(f"received channel request: kind={kind} chanid={chanid}")
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        logger.error(f"we only accept session")
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY
    
    # Just accept the PTY request
    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        logger.debug(f"pty request: {term} {width}x{height}")
        self.needs_pty = True
        return True
    
    # Start a echo shell if requested
    def check_channel_shell_request(self, channel):
        logger.info(f"shell request: {channel.get_id()}")
        return self.start_shell(channel)

    # The real meat and potatos here!
    def check_channel_direct_tcpip_request(self, chanid, origin, destination):
        logger.info(f"direct TCP/IP request: chan={chanid} origin={origin} destination={destination}")
        host = destination[0]
        remote_port = destination[1]

        sock = self.direct_tcpip_callback(host, remote_port)
        
        if not sock:
            logger.error("failed to connect to session manager plugin")
            return paramiko.OPEN_FAILED_CONNECT_FAILED
        
        # Start thread to open the channel and forward data
        t = ForwardThread(sock, chanid, self.channels)
        t.start()
        
        logger.debug("started forwarding thread")
        return paramiko.OPEN_SUCCEEDED
    
    def get_banner(self):
        return ("SSM CLI - ProxyCommand SSH server\r\n", "en-US")

    def check_channel_exec_request(self, channel, command):
        logger.info(f"exec request: {command}")

        return self.start_shell(channel, command)

    def start_shell(self, channel, command=None):
        logger.info(f"starting shell: {channel.get_id()}")

        client = self.session.client('ssm')

        # We dont use the command here because we need to turn off echo and other bits
        parameters = dict(
            Target=self.instance.id,
        )
        if command is not None:
            logger.info(f"command provided, using AWS-StartInteractiveCommand and a sh wrapper")
            parameters['DocumentName'] = 'AWS-StartInteractiveCommand'
            parameters['Parameters'] = {'command': ['sh --noprofile --norc -to pipefail']}
        
        logger.info("calling out to ssm:StartSession")
        response = client.start_session(**parameters)

        logger.info(f"starting session: {response['SessionId']}")

        ready = threading.Event()
        def thread():
            logger.debug("starting proc thread")
            proc = subprocess.Popen(
                [
                    "session-manager-plugin",
                    json.dumps({
                        "SessionId": response["SessionId"],
                        "TokenValue": response["TokenValue"],
                        "StreamUrl": response["StreamUrl"]
                    }),
                    self.session.region_name,
                    "StartSession",
                    self.session.profile_name,
                    json.dumps(parameters),
                    f"https://ssm.{self.session.region_name}.amazonaws.com"
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )

            # Session manager puts a bunch of crap in the stdout, we need to read it all to get to the shell
            proc.stdout.readline()
            if not proc.stdout.readline().startswith(b"Starting session with SessionId"):
                raise RuntimeError("Failed to start session")
            
            # turn off echo and read loop instead of cat because EOF stops cat
            if command is not None:
                logger.info(f"command provided, starting shell forwarder")
                proc.stdin.write(f"stty -echo; while IFS= read line; do echo \"$line\"; done | {command.decode()}\n".encode())
                proc.stdin.flush()

                # we turn echo off, but we need to hide this line form the user
                if not proc.stdout.readline().find(b"stty -echo; "):
                    raise RuntimeError("Failed to start shell")
            
            time.sleep(0.1)
            ready.set()
            
            def forward_proc_to_chan():
                logger.debug("started")
                while True:
                    char = proc.stdout.read(1)
                    if not char:
                        break
                    channel.send(char)
                proc.stdout.close()
                logger.debug("finished")

            def forward_chan_to_proc():
                logger.debug("started")
                while True:
                    data = channel.recv(1024)
                    if not data:
                        break
                    proc.stdin.write(data)
                    proc.stdin.flush()
                logger.debug("sending EOF to session manager plugin")
                proc.stdin.write(b'\x04')  # Send the EOF character (Ctrl+D)
                proc.stdin.flush()
                logger.debug("finished")

            threading.Thread(target=forward_proc_to_chan).start()
            threading.Thread(target=forward_chan_to_proc).start()

            proc.wait()
            channel.close()            
            logger.debug("finished proc thread")

        threading.Thread(target=thread).start()

        ready.wait()
        logger.debug("proc thread is ready, letting ssh client know")
        return True