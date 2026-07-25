"""Result data model for a measurement run.

Kept as plain dataclasses with a `to_dict` so results are easy to report, archive, and
compare later (result-management / persistence is a separate task and builds on this shape).
"""
from dataclasses import asdict, dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class Statistics:
    count: int
    mean: float
    median: float
    std_dev: float
    minimum: float
    maximum: float

    @property
    def coefficient_of_variation(self) -> float:
        """Relative standard deviation (std / mean) — a scale-free measure of consistency,
        so it can be compared across ammeters that read different current ranges. Lower is
        more consistent. Undefined (inf) if the mean is non-positive."""
        return self.std_dev / self.mean if self.mean > 0 else float("inf")


@dataclass(frozen=True)
class TestResult:
    # Tell pytest not to collect this as a test class (its name starts with "Test").
    __test__ = False

    ammeter: str
    samples: List[float]
    statistics: Statistics
    failures: int            # measurements that errored/timed out and were skipped
    started_at: str          # ISO-8601 timestamp
    duration_seconds: float  # measured wall-clock span of the sampling run

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
