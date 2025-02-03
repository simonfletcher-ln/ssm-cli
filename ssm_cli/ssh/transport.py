import sys

import logging
logger = logging.getLogger(__name__)

class StdIoSocket:
    _closed = True

    def send(self, bytes):
        n = sys.stdout.buffer.write(bytes)
        sys.stdout.flush()
        return n
    def recv(self, length):
        return sys.stdin.buffer.read(length)
    
    # ignore close for now, we can probably handle it
    def close(self):
        logger.debug("Ignoring close")

    # timeout should be used, for now we are ignoring it
    def settimeout(self, timeout):
        logger.debug("Ignoring settimeout")
