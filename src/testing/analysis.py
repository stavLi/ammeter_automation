"""Statistical analysis of measurement samples.

Uses the standard-library ``statistics`` module (not numpy/scipy) to honor the brief's
"minimize external dependencies" — mean/median/std-dev/min/max need nothing heavier.
"""
import statistics
from typing import Sequence

from .results import Statistics


class AnalysisError(ValueError):
    """Statistics were requested for an empty sample set."""


def compute_statistics(samples: Sequence[float]) -> Statistics:
    """Compute summary statistics over the collected measurements.

    Standard deviation is the *sample* std dev (Bessel-corrected) and is only defined for
    two or more samples; with a single sample it is reported as 0.0.
    """
    if not samples:
        raise AnalysisError("cannot compute statistics over an empty sample set")

    # Sample std dev needs n >= 2; a single measurement has no spread.
    std_dev = statistics.stdev(samples) if len(samples) >= 2 else 0.0

    return Statistics(
        count=len(samples),
        mean=statistics.mean(samples),
        median=statistics.median(samples),
        std_dev=std_dev,
        minimum=min(samples),
        maximum=max(samples),
    )
