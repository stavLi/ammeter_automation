"""Archiving and retrieval of measurement runs (spec §4, Result Management).

A run is persisted as a single self-contained JSON file under ``results/`` — no database,
no ORM, no extra dependency (stdlib ``json`` only, honoring the "minimize dependencies"
constraint). Each file is an envelope:

    {
      "run_id":   "<UTC timestamp>-<short hash>",   # unique per run
      "saved_at": "<ISO-8601 UTC>",
      "metadata": { ... },                          # caller-supplied (sampling config, etc.)
      "result":   { ... }                            # TestResult.to_dict()
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

    def save(self, result: TestResult, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Archive one run and return its unique run_id."""
        self.root.mkdir(parents=True, exist_ok=True)
        run_id = _new_run_id()
        envelope = {
            "run_id": run_id,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
            "result": result.to_dict(),
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

    def compare(self, run_id_a: str, run_id_b: str) -> Dict[str, Dict[str, float]]:
        """Per-statistic comparison of two runs: {metric: {a, b, delta}} (delta = b - a)."""
        stats_a = self.load(run_id_a)["result"]["statistics"]
        stats_b = self.load(run_id_b)["result"]["statistics"]
        return {
            field: {"a": stats_a[field], "b": stats_b[field], "delta": stats_b[field] - stats_a[field]}
            for field in _STAT_FIELDS
        }

    def _path(self, run_id: str) -> Path:
        return self.root / f"{run_id}.json"
