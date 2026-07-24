"""Human-readable formatting of test results for the CLI entry point."""
from typing import Dict

from .results import TestResult


def format_report(results: Dict[str, TestResult]) -> str:
    """Render a run's results as an aligned statistics table."""
    if not results:
        return "No results — no ammeter produced any data."

    header = (
        f"{'ammeter':<10} {'count':>5} {'mean':>12} {'median':>12} "
        f"{'std_dev':>12} {'min':>12} {'max':>12} {'fails':>5} {'dur(s)':>7}"
    )
    lines = [header, "-" * len(header)]
    for name, result in results.items():
        s = result.statistics
        lines.append(
            f"{name:<10} {s.count:>5} {s.mean:>12.4f} {s.median:>12.4f} "
            f"{s.std_dev:>12.4f} {s.minimum:>12.4f} {s.maximum:>12.4f} "
            f"{result.failures:>5} {result.duration_seconds:>7.2f}"
        )
    return "\n".join(lines)
