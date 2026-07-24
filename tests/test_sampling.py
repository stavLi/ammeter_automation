"""Unit tests for the sampling engine, using an injected clock so pacing is deterministic
and no real time passes."""
import pytest

from src.testing.sampling import run_sampling

_NO_WAIT = {"sleep": lambda _s: None, "monotonic": lambda: 0.0}


@pytest.mark.unit
def test_collects_all_successful_samples():
    outcome = run_sampling(lambda: 1.5, count=10, interval_seconds=0.1, **_NO_WAIT)
    assert outcome.samples == [1.5] * 10
    assert outcome.failures == 0


@pytest.mark.unit
def test_none_replies_counted_as_failures():
    seq = [1.0, None, 2.0]
    outcome = run_sampling(lambda: seq.pop(0), count=3, interval_seconds=0.0, **_NO_WAIT)
    assert outcome.samples == [1.0, 2.0]
    assert outcome.failures == 1


@pytest.mark.unit
def test_socket_errors_counted_as_failures():
    def boom():
        raise ConnectionRefusedError("no server")
    outcome = run_sampling(boom, count=3, interval_seconds=0.0, **_NO_WAIT)
    assert outcome.samples == []
    assert outcome.failures == 3


@pytest.mark.unit
def test_pacing_compensates_for_measurement_time_without_drift():
    # Controllable clock: sleep and each measurement advance it; assert the engine waits to
    # the absolute target time (interval minus the time the measurement itself consumed).
    clock = {"t": 0.0}
    waits = []

    def monotonic():
        return clock["t"]

    def sleep(seconds):
        waits.append(seconds)
        clock["t"] += seconds

    def measure():
        clock["t"] += 0.001  # each measurement takes 1 ms
        return 1.0

    outcome = run_sampling(measure, count=3, interval_seconds=0.1, sleep=sleep, monotonic=monotonic)

    assert len(outcome.samples) == 3
    # First sample fires immediately (target 0); the next two wait interval-minus-measure-time.
    assert waits == pytest.approx([0.099, 0.099])
    assert outcome.duration_seconds == pytest.approx(0.201)
