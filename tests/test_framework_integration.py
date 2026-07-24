"""Framework tests: a config-driven run against a real emulator, plus error handling."""
import socket

import pytest

from src.testing.assertions import assert_in_range, assert_stats
from src.testing.settings import AmmeterConfig, ConfigError, FrameworkConfig, SamplingConfig
from src.testing.test_framework import AmmeterTestFramework


def _fast_config(name: str, port: int, command: bytes) -> FrameworkConfig:
    # Small count at a high rate so the run finishes in well under a second.
    return FrameworkConfig(
        sampling=SamplingConfig(
            measurements_count=5, sampling_frequency_hz=50.0, measurement_timeout_seconds=1.0
        ),
        ammeters={name: AmmeterConfig(name=name, port=port, command=command)},
    )


def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("localhost", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.mark.integration
def test_run_test_samples_and_reports_statistics(running_emulator):
    spec, emulator = running_emulator
    framework = AmmeterTestFramework(config=_fast_config(spec.name, emulator.port, spec.command))

    result = framework.run_test(spec.name)

    assert result.failures == 0
    assert result.ammeter == spec.name
    assert_stats(result.statistics, expected_count=5)
    for sample in result.samples:
        assert_in_range(sample, spec.expected_min, spec.expected_max)
    assert result.duration_seconds >= 0.0


@pytest.mark.integration
def test_run_all_returns_a_result_per_reachable_ammeter(running_emulator):
    spec, emulator = running_emulator
    framework = AmmeterTestFramework(config=_fast_config(spec.name, emulator.port, spec.command))

    results = framework.run_all()

    assert set(results) == {spec.name}
    assert results[spec.name].statistics.count == 5


@pytest.mark.integration
def test_run_all_skips_unreachable_ammeter():
    # Nothing is listening on this port, so every measurement is refused -> the ammeter is
    # skipped, not raised, and run_all returns empty rather than crashing.
    config = FrameworkConfig(
        sampling=SamplingConfig(
            measurements_count=2, sampling_frequency_hz=50.0, measurement_timeout_seconds=0.5
        ),
        ammeters={"dead": AmmeterConfig(name="dead", port=_free_port(), command=b"NOPE")},
    )
    framework = AmmeterTestFramework(config=config)

    assert framework.run_all() == {}


@pytest.mark.unit
def test_run_test_unknown_ammeter_raises():
    config = FrameworkConfig(
        sampling=SamplingConfig(measurements_count=5, sampling_frequency_hz=50.0),
        ammeters={},
    )
    framework = AmmeterTestFramework(config=config)
    with pytest.raises(ConfigError):
        framework.run_test("missing")
