"""Unit tests for statistical analysis."""
import pytest

from src.testing.analysis import AnalysisError, compute_statistics


@pytest.mark.unit
def test_compute_statistics_known_values():
    stats = compute_statistics([1.0, 2.0, 3.0, 4.0, 5.0])
    assert stats.count == 5
    assert stats.mean == pytest.approx(3.0)
    assert stats.median == pytest.approx(3.0)
    assert stats.minimum == 1.0
    assert stats.maximum == 5.0
    assert stats.std_dev == pytest.approx(1.5811388, rel=1e-5)  # sample stdev of 1..5


@pytest.mark.unit
def test_single_sample_has_zero_std_dev():
    stats = compute_statistics([4.2])
    assert stats.count == 1
    assert stats.mean == pytest.approx(4.2)
    assert stats.std_dev == 0.0


@pytest.mark.unit
def test_empty_sample_set_raises():
    with pytest.raises(AnalysisError):
        compute_statistics([])
