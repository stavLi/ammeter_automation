"""Visualization of measurement data (spec bonus: advanced visualization).

Produces three PNGs per run, paired with the run's ID:
  * ``<run_id>_histograms.png`` — each ammeter's sample distribution
  * ``<run_id>_timeseries.png`` — each ammeter's readings over the sampling window
  * ``<run_id>_precision.png``  — coefficient of variation per ammeter (the precision ranking)

matplotlib (and numpy behind it) is the one heavy-ish dependency in the project, so it is
imported **lazily inside these functions** with the headless ``Agg`` backend — the core run,
the read-only CLI queries, and the test suite never import it unless plots are requested.
"""
from pathlib import Path
from typing import Dict, List

from .precision import assess_precision
from .results import TestResult


def generate_plots(results: Dict[str, TestResult], out_dir: Path, run_id: str) -> List[Path]:
    """Write the three plots for a campaign and return the paths written (empty if no data)."""
    if not results:
        return []

    # Lazy, headless import: no display needed, safe in CI/containers.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_dir.mkdir(parents=True, exist_ok=True)
    names = list(results)

    paths = [
        _plot_per_ammeter(
            plt, results, names, out_dir / f"{run_id}_histograms.png",
            title="Measurement distribution",
            draw=lambda ax, samples: ax.hist(samples, bins=12, color="#4c78a8", edgecolor="white"),
            ylabel="count",
        ),
        _plot_per_ammeter(
            plt, results, names, out_dir / f"{run_id}_timeseries.png",
            title="Measurements over the sampling window",
            draw=lambda ax, samples: ax.plot(range(1, len(samples) + 1), samples, marker=".",
                                             color="#4c78a8"),
            ylabel="current (A)",
        ),
        _plot_precision(plt, results, out_dir / f"{run_id}_precision.png"),
    ]
    return paths


def _plot_per_ammeter(plt, results, names, path: Path, *, title: str, draw, ylabel: str) -> Path:
    """One stacked subplot per ammeter (separate axes, since the current ranges differ widely)."""
    fig, axes = plt.subplots(len(names), 1, figsize=(7, 2.4 * len(names)), squeeze=False)
    for ax, name in zip(axes[:, 0], names):
        draw(ax, results[name].samples)
        ax.set_title(f"{name} (n={results[name].statistics.count})", fontsize=10, loc="left")
        ax.set_ylabel(ylabel, fontsize=8)
        ax.tick_params(labelsize=8)
    fig.suptitle(title, fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def _plot_precision(plt, results, path: Path) -> Path:
    """Coefficient of variation per ammeter — lower bars are more consistent."""
    ranked = assess_precision({name: r.statistics for name, r in results.items()})
    labels = [a.ammeter for a in ranked]
    cvs = [a.coefficient_of_variation for a in ranked]

    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.bar(labels, cvs, color="#54a24b")
    ax.set_title("Precision — coefficient of variation (lower = more consistent)", fontsize=11)
    ax.set_ylabel("CV = std / mean", fontsize=9)
    ax.tick_params(labelsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path
