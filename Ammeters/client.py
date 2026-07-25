import logging
from socket import socket, AF_INET, SOCK_STREAM
from typing import Optional

logger = logging.getLogger(__name__)


def request_current_from_ammeter(
    port: int,
    command: bytes,
    host: str = 'localhost',
    timeout: float = 5.0,
) -> Optional[float]:
    """Send a measurement command to an ammeter emulator and return the current.

    Returns the measured current as a float, or None if the emulator sent no data back
    (e.g. the command did not match) or replied with something that is not a valid
    measurement (a corrupt/garbage reply). A malformed *reply* is a failed measurement, not
    a fatal error — so one bad reading is counted as a single failure rather than aborting
    the whole run. Connection/timeout failures still raise socket.error so callers (the
    sampling loop) can count them too.
    """
    with socket(AF_INET, SOCK_STREAM) as s:
        s.settimeout(timeout)
        s.connect((host, port))
        s.sendall(command)
        data = s.recv(1024)
        if not data:
            logger.debug("no data received from %s:%s", host, port)
            return None
        try:
            # UnicodeDecodeError is a subclass of ValueError, so a non-UTF-8 reply is
            # covered here too.
            current = float(data.decode('utf-8'))
        except ValueError:
            logger.debug("unparseable reply from %s:%s: %r", host, port, data[:64])
            return None
        logger.debug("received current from %s:%s: %s A", host, port, current)
        return current

