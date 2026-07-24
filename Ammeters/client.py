from socket import socket, AF_INET, SOCK_STREAM
from typing import Optional


def request_current_from_ammeter(
    port: int,
    command: bytes,
    host: str = 'localhost',
    timeout: float = 5.0,
) -> Optional[float]:
    """Send a measurement command to an ammeter emulator and return the current.

    Returns the measured current as a float, or None if the emulator sent no
    data back (e.g. the command did not match the one the emulator expects).
    Raises socket.error on connection/timeout failures so callers can handle them.
    """
    with socket(AF_INET, SOCK_STREAM) as s:
        s.settimeout(timeout)
        s.connect((host, port))
        s.sendall(command)
        data = s.recv(1024)
        if not data:
            print(f"No data received from {host}:{port}.")
            return None
        current = float(data.decode('utf-8'))
        print(f"Received current measurement from {host}:{port}: {current} A")
        return current

