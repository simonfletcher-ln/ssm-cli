import threading
import paramiko

from ssm_cli.ssh.channels import Channels

import logging
logger = logging.getLogger(__name__)


class ShellThread(threading.Thread):
    daemon = True

    def __init__(self, chan: paramiko.Channel, channels: Channels, chunk_size=1024):
        threading.Thread.__init__(self)

        logger.debug(f"setting up shell thread chan={chan.get_id()}")
        self.chan = chan
        self.channels = channels
        self.chunk_size = chunk_size

    def run(self):
        logger.info(f"starting shell thread chan={self.chan.get_id()}")

        # Even though a channel object is passed in here, we STILL have to do this bit to avoid
        # it being the first channel accepted when doing forwarding.
        chan = self.channels.get_channel(self.chan.get_id())
        
        self.chan.send(f"\r\nShell Requested for fake SSH Ctl+C or EOF (Ctl+D) to quit\r\n")
        buffer = b""
        while True:
            if self.chan.closed:
                break

            if self.chan.recv_ready():
                data = self.chan.recv(self.chunk_size)
                if len(data) == 0 or data in [b'\x03', b'\x04']:
                    break
                self.chan.send(f"echo {data}\r\n")
                if data == b"\r" or data == b"\n":
                    logger.debug(f"got line: {buffer}")
                    buffer = b""
                else:
                    buffer += data
        
        self.chan.close()