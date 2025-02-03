import select
import threading

import logging
logger = logging.getLogger(__name__)

class ForwardThread(threading.Thread):
    def __init__(self, sock, chanid, channels, chunk_size=1024):
        threading.Thread.__init__(self)
        
        logger.debug(f"setting up forward thread chan={chanid}")
        self.sock = sock
        self.chanid = chanid
        self.channels = channels
        self.chunk_size = chunk_size

    def run(self):
        logger.info(f"starting forward thread chan={self.chanid}")

        chan = self.channels.get_channel(self.chanid)
        while True:
            r, _, _ = select.select([chan, self.sock], [], [])
            if self.sock in r:
                data = self.sock.recv(self.chunk_size)
                if len(data) == 0:
                    break
                chan.send(data)

            if chan in r:
                data = chan.recv(self.chunk_size)
                if len(data) == 0:
                    break
                self.sock.send(data)
    