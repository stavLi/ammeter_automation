"""Unit tests for campaign archiving/retrieval (spec §4, Result Management).

One campaign (one framework invocation, one or more ammeters) is archived as one run.
Uses tmp_path so nothing touches the real results/ directory.
"""
import pytest

from src.testing.results import Statistics, TestResult
from src.testing.store import ResultStore, ResultStoreError


def _result(ammeter: str, mean: float = 3.0) -> TestResult:
    stats = Statistics(count=3, mean=mean, median=mean, std_dev=0.5, minimum=mean - 1, maximum=mean + 1)
    return TestResult(
        ammeter=ammeter,
        samples=[mean - 1, mean, mean + 1],
        statistics=stats,
        failures=0,
        started_at="2026-07-25T00:00:00+00:00",
        duration_seconds=0.3,
    )


def _campaign(**means: float):
    """A campaign dict {ammeter: TestResult}; kwargs are ammeter=mean."""
    return {name: _result(name, mean) for name, mean in means.items()}


@pytest.mark.unit
def test_save_returns_unique_run_ids(tmp_path):
    store = ResultStore(str(tmp_path))
    ids = {store.save(_campaign(greenlee=1.0)) for _ in range(5)}
    assert len(ids) == 5  # no collisions even when saved back-to-back


@pytest.mark.unit
def test_save_then_load_round_trips(tmp_path):
    store = ResultStore(str(tmp_path))
    run_id = store.save(_campaign(greenlee=4.2, entes=70.0), metadata={"note": "hello"})

    envelope = store.load(run_id)
    assert envelope["run_id"] == run_id
    assert envelope["metadata"] == {"note": "hello"}
    # Both ammeters of the campaign live under one run.
    assert set(envelope["results"]) == {"greenlee", "entes"}
    assert envelope["results"]["greenlee"]["statistics"]["mean"] == 4.2
    assert envelope["results"]["entes"]["statistics"]["mean"] == 70.0


@pytest.mark.unit
def test_list_runs_is_chronological(tmp_path):
    store = ResultStore(str(tmp_path))
    first = store.save(_campaign(greenlee=1.0))
    second = store.save(_campaign(greenlee=2.0))
    assert store.list_runs() == sorted([first, second])


@pytest.mark.unit
def test_list_runs_empty_when_nothing_saved(tmp_path):
    assert ResultStore(str(tmp_path / "nope")).list_runs() == []


@pytest.mark.unit
def test_load_unknown_run_raises(tmp_path):
    with pytest.raises(ResultStoreError):
        ResultStore(str(tmp_path)).load("does-not-exist")


@pytest.mark.unit
def test_compare_reports_per_ammeter_stat_deltas(tmp_path):
    store = ResultStore(str(tmp_path))
    a = store.save(_campaign(greenlee=2.0, entes=50.0))
    b = store.save(_campaign(greenlee=5.0, entes=50.0))

    diff = store.compare(a, b)
    assert diff["greenlee"]["mean"] == {"a": 2.0, "b": 5.0, "delta": 3.0}
    assert diff["entes"]["mean"]["delta"] == 0.0
    assert set(diff["greenlee"]) == {"count", "mean", "median", "std_dev", "minimum", "maximum"}


@pytest.mark.unit
def test_compare_only_covers_ammeters_in_both_runs(tmp_path):
    store = ResultStore(str(tmp_path))
    a = store.save(_campaign(greenlee=2.0, entes=50.0))
    b = store.save(_campaign(greenlee=5.0))  # circutor/entes absent

    diff = store.compare(a, b)
    assert set(diff) == {"greenlee"}  # only the ammeter present in both is comparable
