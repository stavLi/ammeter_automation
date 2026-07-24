"""Typed, validated view over config/config.yaml.

Parsing the raw YAML into dataclasses (and validating it up front) keeps the framework
honest: contradictory or missing sampling parameters fail loudly here with a clear message,
rather than producing a silently-wrong run later.
"""
from dataclasses import dataclass, field
from typing import Dict, List

from ..utils.config import load_config

# How far total_duration_seconds may disagree with count / frequency before it's a config error.
_DURATION_TOLERANCE = 0.05


class ConfigError(ValueError):
    """The configuration is missing or self-contradictory."""


@dataclass(frozen=True)
class SamplingConfig:
    measurements_count: int
    sampling_frequency_hz: float
    measurement_timeout_seconds: float = 2.0
    total_duration_seconds: float = 0.0  # 0 -> derive from count / frequency

    def __post_init__(self) -> None:
        if self.measurements_count <= 0:
            raise ConfigError(f"measurements_count must be > 0, got {self.measurements_count}")
        if self.sampling_frequency_hz <= 0:
            raise ConfigError(f"sampling_frequency_hz must be > 0, got {self.sampling_frequency_hz}")
        if self.measurement_timeout_seconds <= 0:
            raise ConfigError(
                f"measurement_timeout_seconds must be > 0, got {self.measurement_timeout_seconds}"
            )
        # If total_duration is given, it must agree with count / frequency (any two of the
        # three knobs determine the third).
        if self.total_duration_seconds:
            expected = self.measurements_count / self.sampling_frequency_hz
            if abs(self.total_duration_seconds - expected) > _DURATION_TOLERANCE * expected:
                raise ConfigError(
                    f"total_duration_seconds={self.total_duration_seconds} contradicts "
                    f"measurements_count/sampling_frequency_hz={expected:.3f}"
                )

    @property
    def interval_seconds(self) -> float:
        """Target time between the start of consecutive measurements."""
        return 1.0 / self.sampling_frequency_hz


@dataclass(frozen=True)
class AmmeterConfig:
    name: str
    port: int
    command: bytes


@dataclass(frozen=True)
class FrameworkConfig:
    sampling: SamplingConfig
    ammeters: Dict[str, AmmeterConfig]
    metrics: List[str] = field(default_factory=list)

    def ammeter(self, name: str) -> AmmeterConfig:
        try:
            return self.ammeters[name]
        except KeyError:
            known = ", ".join(sorted(self.ammeters)) or "(none configured)"
            raise ConfigError(f"unknown ammeter {name!r}; configured: {known}")


def load_settings(config_path: str = "config/config.yaml") -> FrameworkConfig:
    raw = load_config(config_path)
    if not isinstance(raw, dict):
        raise ConfigError(f"config at {config_path} is empty or not a mapping")

    sampling_raw = raw.get("testing", {}).get("sampling", {})
    if not sampling_raw:
        raise ConfigError("missing testing.sampling section")
    try:
        sampling = SamplingConfig(
            measurements_count=sampling_raw["measurements_count"],
            sampling_frequency_hz=sampling_raw["sampling_frequency_hz"],
            measurement_timeout_seconds=sampling_raw.get("measurement_timeout_seconds", 2.0),
            total_duration_seconds=sampling_raw.get("total_duration_seconds", 0.0) or 0.0,
        )
    except KeyError as missing:
        raise ConfigError(f"missing sampling key: {missing}")

    ammeters_raw = raw.get("ammeters") or {}
    if not ammeters_raw:
        raise ConfigError("no ammeters configured")
    try:
        ammeters = {
            name: AmmeterConfig(name=name, port=spec["port"], command=spec["command"].encode("utf-8"))
            for name, spec in ammeters_raw.items()
        }
    except KeyError as missing:
        raise ConfigError(f"ammeter config missing key: {missing}")

    metrics = list(raw.get("analysis", {}).get("metrics", []) or [])
    return FrameworkConfig(sampling=sampling, ammeters=ammeters, metrics=metrics)
