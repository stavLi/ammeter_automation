"""Entry point: start the ammeter emulators and run the measurement framework.

    python main.py                 # run every configured ammeter, print a stats report
    python main.py --ammeter entes # run a single ammeter
    python main.py --verbose       # also show per-measurement debug logging

Set AMMETER_SERVE_FOREVER=1 to keep the emulators serving instead of running a campaign
(used by the docker-compose `emulators` service); AMMETER_BIND_HOST overrides the bind host.
"""
import argparse
import logging
import os
import threading
from typing import Dict, List, Optional

from Ammeters.base_ammeter import AmmeterEmulatorBase
from src.testing.registry import AMMETERS
from src.testing.report import format_report
from src.testing.results import TestResult
from src.testing.test_framework import AmmeterTestFramework


def start_emulators(host: str = "localhost") -> List[AmmeterEmulatorBase]:
    """Start every registered emulator in its own daemon thread and wait until each is
    actually listening (no sleep-and-hope)."""
    emulators: List[AmmeterEmulatorBase] = []
    for spec in AMMETERS:
        emulator = spec.emulator_cls(spec.default_port, host=host)
        threading.Thread(target=emulator.start_server, daemon=True).start()
        emulator.wait_until_ready()
        emulators.append(emulator)
    return emulators


def run_campaign(framework: AmmeterTestFramework, ammeter: Optional[str] = None) -> Dict[str, TestResult]:
    """Run one named ammeter, or every configured ammeter when none is given."""
    if ammeter:
        return {ammeter: framework.run_test(ammeter)}
    return framework.run_all()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run measurement tests against the ammeter emulators."
    )
    parser.add_argument("--ammeter", help="run a single ammeter by name (default: all configured)")
    parser.add_argument("--config", default="config/config.yaml", help="path to the config file")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="show per-measurement debug logging"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    # Bind host is configurable so the emulators can listen on 0.0.0.0 inside a container.
    bind_host = os.environ.get("AMMETER_BIND_HOST", "localhost")
    print("Starting ammeter emulators...")
    start_emulators(bind_host)

    if os.environ.get("AMMETER_SERVE_FOREVER"):
        # Long-lived emulator service (used by the docker-compose `emulators` service).
        print("Emulators are serving. Press Ctrl+C to stop.")
        threading.Event().wait()
    else:
        print("Running measurements...\n")
        framework = AmmeterTestFramework(config_path=args.config)
        print(format_report(run_campaign(framework, args.ammeter)))
