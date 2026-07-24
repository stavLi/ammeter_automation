"""Shared fixtures.

The `running_emulator` fixture starts each ammeter emulator on an OS-assigned
ephemeral port (bind to 0), in a daemon thread, and waits until it is actually
listening — no fixed 5001-5003 ports (which flake with "address already in use"
between runs) and no sleep-and-hope. It is parametrized across all registered
ammeters, so a test that requests it runs once per ammeter automatically.
"""
import threading
from typing import Iterator, Tuple

import pytest

from Ammeters.base_ammeter import AmmeterEmulatorBase
from src.testing.registry import AMMETERS, AmmeterSpec


@pytest.fixture(params=AMMETERS, ids=[spec.name for spec in AMMETERS])
def running_emulator(request: pytest.FixtureRequest) -> Iterator[Tuple[AmmeterSpec, AmmeterEmulatorBase]]:
    spec: AmmeterSpec = request.param
    emulator = spec.emulator_cls(0)  # port 0 -> ephemeral
    thread = threading.Thread(target=emulator.start_server, daemon=True)
    thread.start()
    emulator.wait_until_ready()
    try:
        yield spec, emulator
    finally:
        emulator.stop()
        thread.join(timeout=2.0)
