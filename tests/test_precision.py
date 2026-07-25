"""Unit tests for cross-ammeter precision assessment (spec §5 bonus).

Precision = consistency via coefficient of variation (std/mean). These assert the ranking
and the CV contract, not any observed random value.
"""
import pytest

from src.testing.precision import assess_precision
from src.testing.report import format_precision
from src.testing.results import Statistics


def _stats(mean: float, std: float) -> Statistics:
    return Statistics(count=30, mean=mean, median=mean, std_dev=std, minimum=mean - std, maximum=mean + std)


@pytest.mark.unit
def test_coefficient_of_variation_is_std_over_mean():
    assert _stats(mean=4.0, std=1.0).coefficient_of_variation == pytest.approx(0.25)


@pytest.mark.unit
def test_cv_is_infinite_when_mean_non_positive():
    assert _stats(mean=0.0, std=1.0).coefficient_of_variation == float("inf")


@pytest.mark.unit
def test_assess_ranks_most_consistent_first():
    # entes has the lowest relative spread (CV 0.05) despite the largest absolute std.
    stats = {
        "greenlee": _stats(mean=1.0, std=0.5),    # CV 0.50
        "entes": _stats(mean=100.0, std=5.0),     # CV 0.05
        "circutor": _stats(mean=0.02, std=0.004), # CV 0.20
    }
    ranked = assess_precision(stats)
    assert [a.ammeter for a in ranked] == ["entes", "circutor", "greenlee"]
    assert ranked[0].coefficient_of_variation == pytest.approx(0.05)


@pytest.mark.unit
def test_non_positive_mean_sorts_last():
    ranked = assess_precision({"good": _stats(2.0, 0.2), "dead": _stats(0.0, 0.1)})
    assert ranked[-1].ammeter == "dead"


@pytest.mark.unit
def test_format_precision_names_the_most_consistent():
    text = format_precision(assess_precision({
        "greenlee": _stats(1.0, 0.5),
        "entes": _stats(100.0, 5.0),
    }))
    assert "most consistent: entes" in text


@pytest.mark.unit
def test_format_precision_single_ammeter_has_no_winner_line():
    text = format_precision(assess_precision({"greenlee": _stats(1.0, 0.5)}))
    assert "most consistent" not in text  # nothing to compare against
    assert "greenlee" in text


@pytest.mark.unit
def test_format_precision_empty_is_blank():
    assert format_precision([]) == ""
