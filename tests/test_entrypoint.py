"""Tests for the runnable entry point: report formatting and run_campaign."""
import pytest

from main import run_campaign
from src.testing.report import format_report
from src.testing.results import Statistics, TestResult
from src.testing.settings import AmmeterConfig, FrameworkConfig, SamplingConfig
from src.testing.test_framework import AmmeterTestFramework


def _sample_result(name: str, mean: float) -> TestResult:
    stats = Statistics(
        count=5, mean=mean, median=mean, std_dev=0.1, minimum=mean - 0.1, maximum=mean + 0.1
    )
    return TestResult(
        ammeter=name,
        samples=[mean] * 5,
        statistics=stats,
        failures=0,
        started_at="2026-01-01T00:00:00+00:00",
        duration_seconds=1.23,
    )


@pytest.mark.unit
def test_format_report_empty_is_explained():
    assert "No results" in format_report({})


@pytest.mark.unit
def test_format_report_shows_ammeter_and_stats():
    text = format_report({"greenlee": _sample_result("greenlee", 0.5)})
    assert "ammeter" in text          # header present
    assert "greenlee" in text         # row present
    assert "0.5000" in text           # formatted statistic


@pytest.mark.integration
def test_run_campaign_single_ammeter(running_emulator):
    spec, emulator = running_emulator
    config = FrameworkConfig(
        sampling=SamplingConfig(measurements_count=3, sampling_frequency_hz=50.0),
        ammeters={spec.name: AmmeterConfig(name=spec.name, port=emulator.port, command=spec.command)},
    )
    results = run_campaign(AmmeterTestFramework(config=config), ammeter=spec.name)
    assert set(results) == {spec.name}
    assert results[spec.name].statistics.count == 3
