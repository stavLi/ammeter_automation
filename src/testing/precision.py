"""Cross-ammeter precision assessment (spec §5, Accuracy Assessment — bonus).

**An honesty note on "accuracy" vs "precision".** The spec asks to compare ammeter types and
identify the most reliable one. True *accuracy* — closeness to the real current — is **not
computable here**: the three emulators read different current ranges and there is no
ground-truth reference to compare against. What we *can* quantify is *precision* — how
*consistent* each ammeter's readings are — via the coefficient of variation (std / mean).
Because it is scale-free, it is comparable across ammeters that read different ranges, and a
lower value means more consistent (more reliable) measurement. We report precision and label
it as such, rather than overclaiming accuracy we cannot measure.
"""
from dataclasses import dataclass
from typing import Dict, List

from .results import Statistics


@dataclass(frozen=True)
class PrecisionAssessment:
    ammeter: str
    mean: float
    std_dev: float
    coefficient_of_variation: float


def assess_precision(stats_by_ammeter: Dict[str, Statistics]) -> List[PrecisionAssessment]:
    """Rank ammeters by measurement consistency, most consistent (lowest CV) first."""
    assessments = [
        PrecisionAssessment(
            ammeter=name,
            mean=stats.mean,
            std_dev=stats.std_dev,
            coefficient_of_variation=stats.coefficient_of_variation,
        )
        for name, stats in stats_by_ammeter.items()
    ]
    return sorted(assessments, key=lambda a: a.coefficient_of_variation)
