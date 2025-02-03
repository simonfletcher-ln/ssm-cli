import threading
import paramiko

import logging
logger = logging.getLogger(__name__)

class Channels:
    """
    This class was needed because of the multitheading and not always getting the channel we accept in the right order
    """
    def __init__(self, transport: paramiko.Transport, timeout=10):
        self.transport = transport
        self.timeout = timeout
        self._channels = {}
        self._channels_lock = threading.Lock()

    def get_channel(self, chanid: int):
        logger.debug(f"getting channel {chanid}")
        with self._channels_lock:
            if chanid in self._channels:
                chan = self._channels[chanid]
                del self._channels[chanid]
                logger.debug(f"got channel from buffer")
                return chan

            for attempt in range(3):
                chan = self.transport.accept(self.timeout)
                if chan is None: # Timeout
                    logger.error(f"no channel available")
                    return None
 
                if chan.get_id() != chanid:
                    self._channels[chan.get_id()] = chan
                    logger.error(f"channel ID mismatch, attempt {attempt}, trying again")
                    continue
                logger.debug("got channel from transport")
                return chan