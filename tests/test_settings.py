"""Unit tests for config parsing and validation."""
import pytest

from src.testing.settings import ConfigError, SamplingConfig, load_settings


@pytest.mark.unit
def test_valid_sampling_config_derives_interval():
    s = SamplingConfig(measurements_count=30, sampling_frequency_hz=10.0, total_duration_seconds=3.0)
    assert s.interval_seconds == pytest.approx(0.1)


@pytest.mark.unit
@pytest.mark.parametrize("kwargs", [
    {"measurements_count": 0, "sampling_frequency_hz": 10.0},
    {"measurements_count": 10, "sampling_frequency_hz": 0.0},
    {"measurements_count": 10, "sampling_frequency_hz": 10.0, "measurement_timeout_seconds": 0.0},
])
def test_invalid_sampling_config_raises(kwargs):
    with pytest.raises(ConfigError):
        SamplingConfig(**kwargs)


@pytest.mark.unit
def test_contradictory_duration_raises():
    # 30 samples at 10 Hz is 3s, not 99s.
    with pytest.raises(ConfigError):
        SamplingConfig(measurements_count=30, sampling_frequency_hz=10.0, total_duration_seconds=99.0)


@pytest.mark.unit
def test_load_settings_from_real_config():
    cfg = load_settings("config/config.yaml")
    assert set(cfg.ammeters) == {"greenlee", "entes", "circutor"}
    assert cfg.sampling.measurements_count == 30
    assert cfg.ammeter("greenlee").command == b"MEASURE_GREENLEE -get_measurement"


@pytest.mark.unit
def test_unknown_ammeter_raises():
    cfg = load_settings("config/config.yaml")
    with pytest.raises(ConfigError):
        cfg.ammeter("nonexistent")


@pytest.mark.unit
def test_missing_required_key_raises_config_error(tmp_path):
    bad = tmp_path / "bad.yaml"
    # sampling is missing measurements_count -> friendly ConfigError, not a raw KeyError.
    bad.write_text("testing:\n  sampling:\n    sampling_frequency_hz: 10.0\n")
    with pytest.raises(ConfigError):
        load_settings(str(bad))
