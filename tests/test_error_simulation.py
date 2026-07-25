"""Error-simulation tests (spec bonus: error simulation).

Design note — why this lives in the test tier (not a `main.py --simulate-errors` flag):
error handling is a *property of the framework*, and the honest way to demonstrate it is to
drive the real client / sampling loop / framework against a real misbehaving socket and
assert graceful degradation — which then runs in CI on every push. A manual demo flag would
prove less (a reviewer has to remember to run it), add surface to `main.py`, and pollute the
"fixed" emulator infrastructure. So faults are injected by a dedicated emulator here, while
normal runs stay clean.

These are integration tests: each starts a FaultInjectingEmulator on an ephemeral port and
talks to it over a real socket.
"""
import threading
from contextlib import contextmanager
from typing import Iterator

import pytest

from Ammeters.client import request_current_from_ammeter
from src.testing.fault_emulator import FaultInjectingEmulator, FaultMode
from src.testing.sampling import run_sampling
from src.testing.settings import AmmeterConfig, FrameworkConfig, SamplingConfig
from src.testing.test_framework import AmmeterTestFramework

_CMD = FaultInjectingEmulator.COMMAND


@contextmanager
def running_fault_emulator(mode: FaultMode, **kwargs) -> Iterator[FaultInjectingEmulator]:
    emulator = FaultInjectingEmulator(0, mode=mode, **kwargs)  # port 0 -> ephemeral
    thread = threading.Thread(target=emulator.start_server, daemon=True)
    thread.start()
    emulator.wait_until_ready()
    try:
        yield emulator
    finally:
        emulator.stop()
        thread.join(timeout=2.0)


def _measure(port: int, timeout: float = 1.0):
    return lambda: request_current_from_ammeter(port, _CMD, timeout=timeout)


@pytest.mark.integration
def test_garbage_reply_is_a_failed_reading_not_a_crash():
    # A non-numeric reply must be treated as "no measurement" (None), not raise.
    with running_fault_emulator(FaultMode.GARBAGE) as emu:
        assert request_current_from_ammeter(emu.port, _CMD, timeout=1.0) is None


@pytest.mark.integration
def test_dropped_connection_is_a_failed_reading():
    with running_fault_emulator(FaultMode.DROP) as emu:
        assert request_current_from_ammeter(emu.port, _CMD, timeout=1.0) is None


@pytest.mark.integration
def test_hang_raises_a_timeout_for_the_caller():
    # A hung ammeter surfaces as a socket timeout (OSError) the sampling loop can count.
    with running_fault_emulator(FaultMode.HANG) as emu:
        with pytest.raises(OSError):
            request_current_from_ammeter(emu.port, _CMD, timeout=0.3)


@pytest.mark.integration
def test_sampling_counts_garbage_as_failures():
    with running_fault_emulator(FaultMode.GARBAGE) as emu:
        outcome = run_sampling(_measure(emu.port), count=5, interval_seconds=0.0)
    assert outcome.samples == []
    assert outcome.failures == 5  # every reading failed, but the run completed


@pytest.mark.integration
def test_sampling_counts_hang_timeouts_as_failures():
    with running_fault_emulator(FaultMode.HANG) as emu:
        outcome = run_sampling(_measure(emu.port, timeout=0.2), count=3, interval_seconds=0.0)
    assert outcome.samples == []
    assert outcome.failures == 3


@pytest.mark.integration
def test_flaky_ammeter_yields_a_mix_but_never_crashes():
    # Seeded so the OK/fault split is deterministic; assert the metamorphic invariant
    # (every attempt is accounted for) and that both outcomes actually occurred.
    with running_fault_emulator(FaultMode.FLAKY, seed=1) as emu:
        outcome = run_sampling(_measure(emu.port), count=20, interval_seconds=0.0)
    assert len(outcome.samples) + outcome.failures == 20
    assert outcome.samples, "expected some successful readings"
    assert outcome.failures, "expected some failed readings"


@pytest.mark.integration
def test_framework_degrades_gracefully_when_an_ammeter_only_errors():
    # run_all must skip a fully-failing ammeter, not abort the campaign.
    with running_fault_emulator(FaultMode.GARBAGE) as emu:
        config = FrameworkConfig(
            sampling=SamplingConfig(
                measurements_count=3, sampling_frequency_hz=50.0, measurement_timeout_seconds=0.5
            ),
            ammeters={"faulty": AmmeterConfig(name="faulty", port=emu.port, command=_CMD)},
        )
        results = AmmeterTestFramework(config=config).run_all()
    assert results == {}  # the all-failing ammeter is skipped, no exception escapes
