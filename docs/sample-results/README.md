# Sample test results (Deliverable #3)

These three JSON files are one **sample measurement campaign** — a single `python main.py`
run, which samples each ammeter once (greenlee / entes / circutor). They are committed here
as the exercise's "sample test results" deliverable.

Live runs are archived to `results/` (git-ignored); these copies are kept under version
control so a reviewer can see the archive format without running anything.

## What each file is

One archived run (see `src/testing/store.py`). The envelope:

| Field | Meaning |
|---|---|
| `run_id` | Unique per run: `<UTC timestamp>-<short hash>` |
| `saved_at` | When it was archived (ISO-8601 UTC) |
| `metadata` | Provenance — the sampling config and ammeter identity that produced it |
| `result` | The measurement: raw `samples`, computed `statistics`, `failures`, timing |

## Reproduce

```sh
python main.py                        # archives one run per ammeter to results/
python main.py --ammeter entes        # a single ammeter
python main.py --no-save              # run without archiving
python main.py --results-dir /tmp/x   # archive somewhere else
```

Retrieval and comparison of historical runs are available programmatically via
`ResultStore.load` / `list_runs` / `compare` (`src/testing/store.py`).
