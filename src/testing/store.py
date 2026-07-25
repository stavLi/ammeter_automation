"""Archiving and retrieval of measurement runs (spec §4, Result Management).

**One campaign = one run = one file.** A "run" is a single framework invocation
(``python main.py``), which may sample one or several ammeters. All of it is archived as a
single JSON envelope under one ``run_id``.

We deliberately store the whole campaign together rather than one file per ammeter. Grouping
the ammeters that were measured *in the same run* under a single ``run_id`` keeps comparison
logic simple: historical comparison is campaign-vs-campaign, and cross-ammeter accuracy
(spec §5) is a lookup *within* one campaign — neither has to reconstruct "which results
belong together" by matching timestamps across separate files.

No database, no ORM, no extra dependency — stdlib ``json`` only (honors the "minimize
dependencies" constraint). The envelope:

    {
      "run_id":   "<UTC timestamp>-<short hash>",   # unique per run
      "saved_at": "<ISO-8601 UTC>",
      "metadata": { "sampling": {...}, "ammeters": {...}, "failed": [...] },
      "results":  { "<ammeter>": TestResult.to_dict(), ... }
    }

``ResultStore`` gives the three things §4 asks for: unique identification (``run_id``),
metadata storage (the ``metadata`` block), and easy retrieval/comparison of historical
results (``load`` / ``list_runs`` / ``compare``).
"""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .results import TestResult

# Statistic fields compared field-by-field by compare(); mirrors results.Statistics.
_STAT_FIELDS = ("count", "mean", "median", "std_dev", "minimum", "maximum")


class ResultStoreError(Exception):
    """A requested run could not be found or read."""


def _new_run_id() -> str:
    # Timestamp for human-sortable filenames; short hash to stay unique within one second.
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{uuid.uuid4().hex[:8]}"


class ResultStore:
    def __init__(self, root: str = "results"):
        self.root = Path(root)

    def save(self, results: Dict[str, TestResult], metadata: Optional[Dict[str, Any]] = None) -> str:
        """Archive one campaign (all its ammeters) and return its unique run_id."""
        self.root.mkdir(parents=True, exist_ok=True)
        run_id = _new_run_id()
        envelope = {
            "run_id": run_id,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
            "results": {name: result.to_dict() for name, result in results.items()},
        }
        # A run_id collision would silently overwrite a prior run — refuse instead.
        path = self._path(run_id)
        if path.exists():
            raise ResultStoreError(f"run_id {run_id} already exists")
        path.write_text(json.dumps(envelope, indent=2))
        return run_id

    def load(self, run_id: str) -> Dict[str, Any]:
        """Return the stored envelope for a run_id."""
        path = self._path(run_id)
        if not path.exists():
            raise ResultStoreError(f"no such run: {run_id}")
        return json.loads(path.read_text())

    def list_runs(self) -> List[str]:
        """Every stored run_id, oldest first (run_ids sort chronologically)."""
        if not self.root.exists():
            return []
        return sorted(p.stem for p in self.root.glob("*.json"))

    def compare(self, run_id_a: str, run_id_b: str) -> Dict[str, Dict[str, Dict[str, float]]]:
        """Per-ammeter, per-statistic comparison of two campaigns.

        Returns {ammeter: {metric: {a, b, delta}}} (delta = b - a) for every ammeter present
        in *both* runs.
        """
        results_a = self.load(run_id_a)["results"]
        results_b = self.load(run_id_b)["results"]
        common = sorted(set(results_a) & set(results_b))
        return {
            ammeter: self._stat_deltas(
                results_a[ammeter]["statistics"], results_b[ammeter]["statistics"]
            )
            for ammeter in common
        }

    @staticmethod
    def _stat_deltas(
        stats_a: Dict[str, float], stats_b: Dict[str, float]
    ) -> Dict[str, Dict[str, float]]:
        return {
            field: {"a": stats_a[field], "b": stats_b[field], "delta": stats_b[field] - stats_a[field]}
            for field in _STAT_FIELDS
        }

    def _path(self, run_id: str) -> Path:
        return self.root / f"{run_id}.json"
