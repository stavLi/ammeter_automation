# Sample test results (Deliverable #3)

This JSON file is one **sample measurement campaign** — a single `python main.py` run, which
samples every ammeter (greenlee / entes / circutor) and archives them together under one
`run_id`. It is committed here as the exercise's "sample test results" deliverable.

Live runs are archived to `results/` (git-ignored); this copy is kept under version control so
a reviewer can see the archive format without running anything.

The three `sample_*.png` files are the plots generated for this same run (histograms,
time-series, and the precision bar chart) — see the [main README](../../README.md#visualization-bonus)
where they're embedded.

## Envelope shape

One archived campaign = one run (see `src/testing/store.py`):

| Field | Meaning |
|---|---|
| `run_id` | Unique per run: `<UTC timestamp>-<short hash>` |
| `saved_at` | When it was archived (ISO-8601 UTC) |
| `metadata.sampling` | The sampling config used (shared across the campaign) |
| `metadata.ammeters` | Identity of each measured ammeter (port + command) |
| `metadata.failed` | Requested ammeters that returned no data (e.g. unreachable) |
| `results.<ammeter>` | Per-ammeter measurement: raw `samples`, `statistics`, `failures`, timing |

Storing the whole campaign under one `run_id` (rather than one file per ammeter) keeps
comparison simple: historical comparison is campaign-vs-campaign, and cross-ammeter accuracy
(spec §5) is a lookup *within* one campaign — no reconstructing which results belong together.

## Reproduce

```sh
python main.py                        # archives one run (all ammeters) to results/
python main.py --ammeter entes        # a one-ammeter campaign
python main.py --no-save              # run without archiving
python main.py --results-dir /tmp/x   # archive somewhere else
```

Retrieve and compare historical runs from the CLI (no emulators needed):

```sh
python main.py --list                       # list archived run IDs
python main.py --show <run_id>              # print one archived run
python main.py --compare <run_a> <run_b>    # per-ammeter, per-stat deltas
```

The same operations are available programmatically via `ResultStore.load` / `list_runs` /
`compare` (`src/testing/store.py`).
