"""The unified, config-driven entry point for running measurement tests.

`run_test(name)` runs one ammeter through the sampling engine and returns a `TestResult`
with statistics; `run_all()` does every configured ammeter, degrading gracefully if one is
unreachable. The framework is agnostic to ammeter type — adding a new device is a config
entry, not a code change.
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Optional

from Ammeters.client import request_current_from_ammeter

from .analysis import compute_statistics
from .results import TestResult
from .sampling import run_sampling
from .settings import FrameworkConfig, load_settings

logger = logging.getLogger(__name__)


class AmmeterTestFramework:
    def __init__(
        self,
        config_path: str = "config/config.yaml",
        host: str = "localhost",
        config: Optional[FrameworkConfig] = None,
    ):
        # `config` lets callers (and tests) inject a ready-made config instead of a file.
        self.config: FrameworkConfig = config if config is not None else load_settings(config_path)
        self.host = host

    def run_test(self, ammeter_type: str) -> TestResult:
        ammeter = self.config.ammeter(ammeter_type)  # raises ConfigError if unknown
        sampling = self.config.sampling

        def measure() -> Optional[float]:
            return request_current_from_ammeter(
                ammeter.port,
                ammeter.command,
                host=self.host,
                timeout=sampling.measurement_timeout_seconds,
            )

        started_at = datetime.now(timezone.utc).isoformat()
        outcome = run_sampling(measure, sampling.measurements_count, sampling.interval_seconds)
        # compute_statistics raises AnalysisError if every measurement failed — a caller of a
        # single run_test should know its target produced no data.
        stats = compute_statistics(outcome.samples)
        return TestResult(
            ammeter=ammeter.name,
            samples=outcome.samples,
            statistics=stats,
            failures=outcome.failures,
            started_at=started_at,
            duration_seconds=outcome.duration_seconds,
        )

    def run_all(self) -> Dict[str, TestResult]:
        """Run every configured ammeter. One unreachable ammeter is logged and skipped,
        not allowed to abort the others."""
        results: Dict[str, TestResult] = {}
        for name in self.config.ammeters:
            try:
                results[name] = self.run_test(name)
            except Exception as exc:  # noqa: BLE001 - one bad ammeter must not stop the rest
                logger.warning("skipping ammeter %s: %s", name, exc)
        return results
