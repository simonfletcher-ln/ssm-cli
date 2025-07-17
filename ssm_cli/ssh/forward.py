import select
import threading
import logging
logger = logging.getLogger(__name__)

class ForwardThread(threading.Thread):
    def __init__(self, sock, chanid, channels, chan=None, chunk_size=1024):
        threading.Thread.__init__(self)
        
        logger.debug(f"setting up forward thread chan={chanid}")
        self.sock = sock
        self.chanid = chanid
        self.channels = channels
        self.chunk_size = chunk_size
        self.chan = chan

    def run(self):
        logger.info(f"starting forward thread chan={self.chanid}")

        if self.chan is None:
            self.chan = self.channels.get_channel(self.chanid)
        
        while True:
            logger.debug(f"waiting for data")

            r, _, _ = select.select([self.chan, self.sock], [], [])
            logger.debug(f"got data {r}")
            if self.sock in r:
                data = self.sock.recv(self.chunk_size)
                if len(data) == 0:
                    break
                logger.debug(f"got data from sock {data}")
                self.chan.send(data)

            if self.chan in r:
                data = self.chan.recv(self.chunk_size)
                if len(data) == 0:
                    break
                logger.debug(f"got data from chan {data}")
                self.sock.send(data)

        logger.info(f"closing forward thread chan={self.chanid}")
        self.chan.close()