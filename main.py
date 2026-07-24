import os
import threading
from typing import List

from Ammeters.base_ammeter import AmmeterEmulatorBase
from Ammeters.client import request_current_from_ammeter
from src.testing.registry import AMMETERS


def start_emulators(host: str = "localhost") -> List[AmmeterEmulatorBase]:
    """Start every registered emulator in its own daemon thread and wait until each
    is actually listening (no sleep-and-hope)."""
    emulators: List[AmmeterEmulatorBase] = []
    for spec in AMMETERS:
        emulator = spec.emulator_cls(spec.default_port, host=host)
        threading.Thread(target=emulator.start_server, daemon=True).start()
        emulator.wait_until_ready()
        emulators.append(emulator)
    return emulators


def sample_once(host: str = "localhost") -> None:
    """Request one measurement from each emulator.

    Each emulator matches the FULL command exactly (see each Ammeter's
    `get_current_command`); the command bytes come from the registry so they can't
    drift from what the server expects. The original starter sent truncated commands
    (e.g. b'MEASURE_GREENLEE'), which never matched, so the servers never replied.
    """
    for spec in AMMETERS:
        request_current_from_ammeter(spec.default_port, spec.command, host=host)


if __name__ == "__main__":
    # Bind host is configurable so the emulators can listen on 0.0.0.0 inside a
    # container / docker-compose network (defaults to localhost for local runs).
    bind_host = os.environ.get("AMMETER_BIND_HOST", "localhost")
    start_emulators(bind_host)

    if os.environ.get("AMMETER_SERVE_FOREVER"):
        # Long-lived emulator service (used by the docker-compose `emulators` service).
        print("Emulators are serving. Press Ctrl+C to stop.")
        threading.Event().wait()
    else:
        # Local demo: request one measurement from each emulator, then exit.
        sample_once("localhost")
