"""Low-level test helpers (not assertions — those live in src/testing/assertions.py)."""
import socket
from typing import Optional


def probe(host: str, port: int, payload: bytes, timeout: float = 1.0) -> Optional[bytes]:
    """Send raw bytes to an emulator and return its reply, or None if it doesn't reply.

    Used by negative/security tests to fire malformed traffic at a real emulator and
    confirm it stays silent (and alive). Returns None on both an empty reply and a
    timeout, so a non-responsive emulator reads as "no reply", never a hang.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        s.connect((host, port))
        s.sendall(payload)
        try:
            data = s.recv(1024)
        except (socket.timeout, ConnectionError):
            # Timeout (server stayed silent) or reset (server closed on unread
            # bytes, e.g. an oversized payload) both mean "no measurement reply".
            return None
        return data or None
