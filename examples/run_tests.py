"""Example: drive the framework programmatically (an alternative to `python main.py`).

Run from the repo root:  python examples/run_tests.py
"""
from main import start_emulators
from src.testing.report import format_report
from src.testing.test_framework import AmmeterTestFramework


def main() -> None:
    # Spin up the emulators locally, then run every configured ammeter.
    start_emulators()
    framework = AmmeterTestFramework()
    results = framework.run_all()

    print(format_report(results))

    # Results are ordinary objects — access statistics programmatically:
    greenlee = results["greenlee"]
    print(
        f"\ngreenlee mean current: {greenlee.statistics.mean:.4f} A "
        f"over {greenlee.statistics.count} samples"
    )


if __name__ == "__main__":
    main()
