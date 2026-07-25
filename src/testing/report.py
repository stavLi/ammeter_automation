"""Human-readable formatting of results for the CLI entry point.

`format_report` renders a just-run campaign; `format_run_list` / `format_run` /
`format_comparison` render archived runs for the retrieval/compare CLI (spec §4). All of
them share one aligned-table core so live and archived output look identical.
"""
from typing import Any, Dict, List

from .precision import PrecisionAssessment, assess_precision
from .results import Statistics, TestResult

_STAT_ORDER = ("count", "mean", "median", "std_dev", "minimum", "maximum")


def _stats_table(results: Dict[str, Dict[str, Any]]) -> str:
    """Aligned statistics table from result dicts (TestResult.to_dict() shape)."""
    if not results:
        return "No results — no ammeter produced any data."

    header = (
        f"{'ammeter':<10} {'count':>5} {'mean':>12} {'median':>12} "
        f"{'std_dev':>12} {'min':>12} {'max':>12} {'fails':>5} {'dur(s)':>7}"
    )
    lines = [header, "-" * len(header)]
    for name, result in results.items():
        s = result["statistics"]
        lines.append(
            f"{name:<10} {s['count']:>5} {s['mean']:>12.4f} {s['median']:>12.4f} "
            f"{s['std_dev']:>12.4f} {s['minimum']:>12.4f} {s['maximum']:>12.4f} "
            f"{result['failures']:>5} {result['duration_seconds']:>7.2f}"
        )
    return "\n".join(lines)


def format_report(results: Dict[str, TestResult]) -> str:
    """Render a just-run campaign's results as an aligned statistics table."""
    return _stats_table({name: r.to_dict() for name, r in results.items()})


def format_precision(assessments: List[PrecisionAssessment]) -> str:
    """Render the cross-ammeter precision ranking (most consistent first).

    Precision = consistency, measured by coefficient of variation (std/mean); see
    precision.py for why this is precision, not accuracy.
    """
    if not assessments:
        return ""

    lines = [
        "Precision (coefficient of variation = std/mean; lower = more consistent):",
        f"  {'ammeter':<10} {'mean':>12} {'std_dev':>12} {'CV':>10}",
    ]
    for a in assessments:
        cv = "inf" if a.coefficient_of_variation == float("inf") else f"{a.coefficient_of_variation:.4f}"
        lines.append(f"  {a.ammeter:<10} {a.mean:>12.4f} {a.std_dev:>12.4f} {cv:>10}")
    if len(assessments) > 1:
        lines.append(f"  -> most consistent: {assessments[0].ammeter}")
    return "\n".join(lines)


def _precision_from_result_dicts(results: Dict[str, Dict[str, Any]]) -> List[PrecisionAssessment]:
    # Rebuild Statistics from the stored dict so archived runs can be assessed too.
    return assess_precision({name: Statistics(**r["statistics"]) for name, r in results.items()})


def format_run_list(run_ids: List[str]) -> str:
    """List archived run IDs, oldest first (the ID embeds the UTC timestamp)."""
    if not run_ids:
        return "No archived runs."
    return "\n".join(run_ids)


def format_run(envelope: Dict[str, Any]) -> str:
    """Render one archived run: its ID, metadata summary, and statistics table."""
    meta = envelope.get("metadata", {})
    sampling = meta.get("sampling", {})
    failed = meta.get("failed", [])
    lines = [
        f"Run {envelope['run_id']}  (saved {envelope.get('saved_at', '?')})",
    ]
    if sampling:
        lines.append(
            f"sampling: count={sampling.get('measurements_count')} "
            f"freq={sampling.get('sampling_frequency_hz')}Hz "
            f"timeout={sampling.get('measurement_timeout_seconds')}s"
        )
    if failed:
        lines.append(f"failed (no data): {', '.join(failed)}")
    results = envelope.get("results", {})
    lines.append("")
    lines.append(_stats_table(results))
    if results:
        lines.append("")
        lines.append(format_precision(_precision_from_result_dicts(results)))
    return "\n".join(lines)


def format_comparison(
    run_id_a: str, run_id_b: str, diff: Dict[str, Dict[str, Dict[str, float]]]
) -> str:
    """Render a campaign-vs-campaign comparison: per ammeter, each stat's A / B / delta."""
    if not diff:
        return f"No ammeters in common between {run_id_a} and {run_id_b}."

    lines = [f"Comparing runs:", f"  A = {run_id_a}", f"  B = {run_id_b}", ""]
    for ammeter, stats in diff.items():
        lines.append(ammeter)
        lines.append(f"  {'metric':<10} {'A':>14} {'B':>14} {'delta (B-A)':>14}")
        for metric in _STAT_ORDER:
            cell = stats[metric]
            lines.append(
                f"  {metric:<10} {cell['a']:>14.4f} {cell['b']:>14.4f} {cell['delta']:>+14.4f}"
            )
        lines.append("")
    return "\n".join(lines).rstrip()
