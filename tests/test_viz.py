"""Unit tests for plot generation (spec bonus: visualization).

Assert the *contract* — which files are written and that they are valid non-empty PNGs —
not pixel content. Uses tmp_path and the headless Agg backend (via viz.py's lazy import).
"""
import pytest

from src.testing.results import Statistics, TestResult
from src.testing.viz import generate_plots

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _result(name: str, samples) -> TestResult:
    ordered = sorted(samples)
    stats = Statistics(
        count=len(samples), mean=sum(samples) / len(samples), median=ordered[len(samples) // 2],
        std_dev=0.5, minimum=ordered[0], maximum=ordered[-1],
    )
    return TestResult(
        ammeter=name, samples=list(samples), statistics=stats, failures=0,
        started_at="2026-07-25T00:00:00+00:00", duration_seconds=0.3,
    )


@pytest.mark.unit
def test_generate_plots_writes_three_valid_pngs(tmp_path):
    results = {
        "greenlee": _result("greenlee", [0.1, 0.2, 0.15, 0.3, 0.12]),
        "entes": _result("entes", [50.0, 60.0, 55.0, 70.0, 52.0]),
    }
    paths = generate_plots(results, tmp_path, "RID")

    assert [p.name for p in paths] == [
        "RID_histograms.png", "RID_timeseries.png", "RID_precision.png",
    ]
    for p in paths:
        data = p.read_bytes()
        assert data[:8] == _PNG_MAGIC  # a real PNG
        assert len(data) > 0


@pytest.mark.unit
def test_generate_plots_empty_results_writes_nothing(tmp_path):
    assert generate_plots({}, tmp_path, "RID") == []
    assert list(tmp_path.iterdir()) == []


@pytest.mark.unit
def test_generate_plots_single_ammeter(tmp_path):
    paths = generate_plots({"circutor": _result("circutor", [0.02, 0.03, 0.025])}, tmp_path, "R")
    assert len(paths) == 3
    assert all(p.exists() for p in paths)
