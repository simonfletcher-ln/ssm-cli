import threading
import paramiko
import select

from ssm_cli.ssh.channels import Channels

import logging
logger = logging.getLogger(__name__)


class ShellThread(threading.Thread):
    daemon = True

    def __init__(self, chan: paramiko.Channel, channels: Channels):
        threading.Thread.__init__(self)

        logger.debug(f"setting up shell thread chan={chan.get_id()}")
        self.chan = chan
        self.channels = channels

    def run(self):
        logger.info(f"starting shell thread chan={self.chan.get_id()}")

        # Even though a channel object is passed in here, we STILL have to do this bit to avoid
        # it being the first channel accepted when doing forwarding.
        chan = self.channels.get_channel(self.chan.get_id())
        
        self.chan.send(f"\r\nShell Requested for fake SSH Ctl+C or EOF (Ctl+D) to quit\r\n")
        
        while True:
            r, _, _ = select.select([self.chan], [], [])
            if self.chan in r:
                data = self.chan.recv(1024)
                if len(data) == 0 or data in [b'\x03', b'\x04']: # Ctl+C or Ctl+D
                    break
                self.chan.send(f"echo {data}\r\n")
        
        self.chan.close()