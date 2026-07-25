"""Tests for the read-only results CLI: --list / --show / --compare (spec §4).

Covers the formatters and the run_query dispatcher. Uses tmp_path so nothing touches the
real results/ directory, and never starts an emulator (these are archive-only queries).
"""
from argparse import Namespace

import pytest

from main import run_query
from src.testing.report import format_comparison, format_run, format_run_list
from src.testing.results import Statistics, TestResult
from src.testing.store import ResultStore


def _result(name: str, mean: float) -> TestResult:
    stats = Statistics(count=3, mean=mean, median=mean, std_dev=0.5, minimum=mean - 1, maximum=mean + 1)
    return TestResult(
        ammeter=name, samples=[mean], statistics=stats, failures=0,
        started_at="2026-07-25T00:00:00+00:00", duration_seconds=0.3,
    )


def _args(results_dir, *, list=False, show=None, compare=None) -> Namespace:
    return Namespace(results_dir=str(results_dir), list=list, show=show, compare=compare)


# --- formatters ---------------------------------------------------------------

@pytest.mark.unit
def test_format_run_list_empty():
    assert "No archived runs" in format_run_list([])


@pytest.mark.unit
def test_format_run_list_lists_ids():
    assert format_run_list(["a", "b"]) == "a\nb"


@pytest.mark.unit
def test_format_run_shows_id_metadata_and_stats():
    envelope = {
        "run_id": "RID", "saved_at": "2026-07-25T00:00:00+00:00",
        "metadata": {"sampling": {"measurements_count": 30, "sampling_frequency_hz": 10.0,
                                  "measurement_timeout_seconds": 2.0}, "failed": ["circutor"]},
        "results": {"greenlee": _result("greenlee", 0.5).to_dict()},
    }
    text = format_run(envelope)
    assert "RID" in text
    assert "count=30" in text            # sampling metadata
    assert "circutor" in text            # failed ammeter surfaced
    assert "0.5000" in text              # formatted statistic


@pytest.mark.unit
def test_format_comparison_shows_deltas():
    diff = {"greenlee": {m: {"a": 1.0, "b": 3.0, "delta": 2.0}
                         for m in ("count", "mean", "median", "std_dev", "minimum", "maximum")}}
    text = format_comparison("A", "B", diff)
    assert "greenlee" in text
    assert "+2.0000" in text             # signed delta


@pytest.mark.unit
def test_format_comparison_no_common_ammeters():
    assert "No ammeters in common" in format_comparison("A", "B", {})


# --- run_query dispatcher -----------------------------------------------------

@pytest.mark.unit
def test_run_query_list(tmp_path, capsys):
    store = ResultStore(str(tmp_path))
    rid = store.save({"greenlee": _result("greenlee", 0.5)})

    handled = run_query(_args(tmp_path, list=True))
    assert handled is True
    assert rid in capsys.readouterr().out


@pytest.mark.unit
def test_run_query_compare(tmp_path, capsys):
    store = ResultStore(str(tmp_path))
    a = store.save({"greenlee": _result("greenlee", 2.0)})
    b = store.save({"greenlee": _result("greenlee", 5.0)})

    run_query(_args(tmp_path, compare=[a, b]))
    assert "+3.0000" in capsys.readouterr().out   # mean delta 5-2


@pytest.mark.unit
def test_run_query_returns_false_without_a_query_flag(tmp_path):
    assert run_query(_args(tmp_path)) is False


@pytest.mark.unit
def test_run_query_unknown_run_exits(tmp_path):
    with pytest.raises(SystemExit):
        run_query(_args(tmp_path, show="does-not-exist"))
