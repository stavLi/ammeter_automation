"""Fixed-rate sampling of a measurement source.

Paces samples against a monotonic clock at absolute target times (``start + i*interval``),
so the time each measurement itself takes does not accumulate into drift — if one call
overruns the interval, the next simply doesn't wait. `sleep` and `monotonic` are injectable
so the pacing logic can be unit-tested deterministically without real waiting.
"""
import time
from dataclasses import dataclass
from typing import Callable, List, Optional

MeasureFn = Callable[[], Optional[float]]


@dataclass(frozen=True)
class SamplingOutcome:
    samples: List[float]     # successful measurements (float)
    failures: int            # measurements that returned no value or errored
    duration_seconds: float  # measured span from the first to the last sample attempt


def run_sampling(
    measure: MeasureFn,
    count: int,
    interval_seconds: float,
    *,
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> SamplingOutcome:
    start = monotonic()
    samples: List[float] = []
    failures = 0

    for i in range(count):
        wait = (start + i * interval_seconds) - monotonic()
        if wait > 0:
            sleep(wait)
        try:
            value = measure()
        except OSError:
            # Connection refused / timeout / reset: a slow or unreachable ammeter fails
            # this one sample rather than aborting the whole run.
            value = None
        if value is None:
            failures += 1
        else:
            samples.append(value)

    return SamplingOutcome(samples=samples, failures=failures, duration_seconds=monotonic() - start)
