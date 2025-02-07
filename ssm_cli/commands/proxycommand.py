import socket
import time

from ssm_cli.ssh.server import SshServer
from ssm_cli.instances import Instances
from ssm_cli.config import config
from ssm_cli.commands.base import BaseCommand

import logging
logger = logging.getLogger(__name__)

class ProxyCommandCommand(BaseCommand):
    HELP="SSH ProxyCommand feature"
    def add_arguments(parser):
        parser.add_argument("group", type=str, help="group to run against")

    def run(args, session):
        logger.info("running proxycommand action")


        instances = Instances(session)
        instance = instances.select_instance(args.group, config.actions.proxycommand.selector)

        if instance is None:
            logger.error("failed to select host")
            raise RuntimeError("failed to select host")

        logger.info(f"connecting to {repr(instance)}")
        
        server = SshServer(direct_tcpip_callback(instance, session))
        server.start()

def direct_tcpip_callback(instance, session):
    def callback(host, remote_port) -> socket.socket:
        logger.debug(f"connect to {host}:{remote_port}")
        internal_port = get_next_free_port(remote_port + 3000, 20)
        logger.debug(f"got internal port {internal_port}")
        try:
            instance.start_port_forwarding_session_to_remote_host(session, host, remote_port, internal_port)
        except Exception as e:
            logger.error(f"failed to open port forward: {e}")
            return None
        
        logger.debug(f"connecting to session manager plugin on 127.0.0.1:{internal_port}")
        # Even though we wait for the process to say its connected, we STILL need to wait for it
        for attempt in range(10):
            try:
                sock = socket.create_connection(('127.0.0.1', internal_port))
                logger.info(f"connected to 127.0.0.1:{internal_port}")
            except Exception as e:
                logger.warning(f"connection attempt {attempt} failed: {e}")
                time.sleep(0.1)
        
        return sock

    return callback

def get_next_free_port(port: int, tries: int) -> int:
    max_port = port + tries
    while port < max_port:
        logger.debug(f"attempting port {port}")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(('127.0.0.1', port))
        if result != 0:
            return port
        port += 1