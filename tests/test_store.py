"""Unit tests for result archiving/retrieval (spec §4, Result Management).

Uses tmp_path so nothing touches the real results/ directory.
"""
import pytest

from src.testing.results import Statistics, TestResult
from src.testing.store import ResultStore, ResultStoreError


def _result(ammeter: str = "greenlee", mean: float = 3.0) -> TestResult:
    stats = Statistics(count=3, mean=mean, median=mean, std_dev=0.5, minimum=mean - 1, maximum=mean + 1)
    return TestResult(
        ammeter=ammeter,
        samples=[mean - 1, mean, mean + 1],
        statistics=stats,
        failures=0,
        started_at="2026-07-25T00:00:00+00:00",
        duration_seconds=0.3,
    )


@pytest.mark.unit
def test_save_returns_unique_run_ids(tmp_path):
    store = ResultStore(str(tmp_path))
    ids = {store.save(_result()) for _ in range(5)}
    assert len(ids) == 5  # no collisions even when saved back-to-back


@pytest.mark.unit
def test_save_then_load_round_trips(tmp_path):
    store = ResultStore(str(tmp_path))
    run_id = store.save(_result(mean=4.2), metadata={"note": "hello"})

    envelope = store.load(run_id)
    assert envelope["run_id"] == run_id
    assert envelope["metadata"] == {"note": "hello"}
    assert envelope["result"]["ammeter"] == "greenlee"
    assert envelope["result"]["statistics"]["mean"] == 4.2


@pytest.mark.unit
def test_list_runs_is_chronological(tmp_path):
    store = ResultStore(str(tmp_path))
    first = store.save(_result())
    second = store.save(_result())
    assert store.list_runs() == sorted([first, second])


@pytest.mark.unit
def test_list_runs_empty_when_nothing_saved(tmp_path):
    assert ResultStore(str(tmp_path / "nope")).list_runs() == []


@pytest.mark.unit
def test_load_unknown_run_raises(tmp_path):
    with pytest.raises(ResultStoreError):
        ResultStore(str(tmp_path)).load("does-not-exist")


@pytest.mark.unit
def test_compare_reports_per_stat_deltas(tmp_path):
    store = ResultStore(str(tmp_path))
    a = store.save(_result(mean=2.0))
    b = store.save(_result(mean=5.0))

    diff = store.compare(a, b)
    assert diff["mean"] == {"a": 2.0, "b": 5.0, "delta": 3.0}
    assert set(diff) == {"count", "mean", "median", "std_dev", "minimum", "maximum"}
