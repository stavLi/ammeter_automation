import logging
import socket
import threading
import time
import random
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

NotImplementedErrorMsg = "Subclasses must implement this property."

# How often accept() wakes up to check the stop flag (seconds). Also the ceiling
# on how long stop()/teardown waits for the accept loop to notice.
_ACCEPT_POLL_INTERVAL = 0.5


class AmmeterEmulatorBase(ABC):
    """Base TCP emulator for an ammeter.

    Enhancements over the original starter (all backward compatible — existing
    ``Emulator(port).start_server()`` callers behave as before):

    - ``host`` is configurable (defaults to ``localhost``) so the emulator can bind
      ``0.0.0.0`` inside a container / docker-compose network.
    - Binding ``port=0`` lets the OS assign a free ephemeral port; after ``bind`` the
      real port is available on ``self.port``. This is what lets
      tests run each emulator on its own throwaway port instead of the fixed
      5001-5003 (which cause "address already in use" flakiness between runs).
    - ``wait_until_ready()`` blocks until the socket is actually listening, so tests
      never sleep-and-hope.
    - ``stop()`` cleanly shuts the accept loop down, so test fixtures don't leak
      threads/sockets.
    - ``SO_REUSEADDR`` avoids the TIME_WAIT bind failure the README warns about.
    """

    def __init__(self, port: int, host: str = "localhost"):
        self.port = port
        self.host = host
        self._ready = threading.Event()
        self._stop = threading.Event()
        random.seed(time.time())  # Seed the random number generator for each instance

    def wait_until_ready(self, timeout: float = 5.0) -> None:
        """Block until the server is listening. Raises TimeoutError if it never starts."""
        if not self._ready.wait(timeout):
            raise TimeoutError(
                f"{self.__class__.__name__} did not start listening within {timeout}s"
            )

    def stop(self) -> None:
        """Signal the accept loop to exit (it stops within _ACCEPT_POLL_INTERVAL)."""
        self._stop.set()

    def start_server(self):
        """
        Starts the server to listen for client requests.
        Runs until stop() is called, handling one client request at a time.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            self.port = s.getsockname()[1]  # resolve the real port when bound to 0
            s.listen()
            s.settimeout(_ACCEPT_POLL_INTERVAL)  # wake periodically to check _stop
            self._ready.set()
            logger.info("%s is running on %s:%s", self.__class__.__name__, self.host, self.port)
            while not self._stop.is_set():
                try:
                    conn, addr = s.accept()
                except socket.timeout:
                    continue
                with conn:
                    logger.debug("connected by %s", addr)
                    data = conn.recv(1024)
                    if data == self.get_current_command:
                        # Call the specific measure_current() method defined in subclasses
                        current = self.measure_current()
                        conn.sendall(str(current).encode('utf-8'))

    @property
    @abstractmethod
    def get_current_command(self) -> bytes:
        """
        This property must be implemented by each subclass to provide the specific
        command to get the current measurement.
        """
        raise NotImplementedError(NotImplementedErrorMsg)

    @abstractmethod
    def measure_current(self) -> float:
        """
        This method must be implemented by each subclass to provide the specific
        logic for current measurement.
        """
        raise NotImplementedError(NotImplementedErrorMsg)
