# Design decisions

Deliverable #4 — the *why* behind the framework: the bug fixes made, the libraries installed,
and the design choices (including where we deliberately stopped, to avoid over-engineering a
three-emulator exercise). Usage lives in the [README](../README.md); this document is rationale.

## Framing: the emulator as an API under test

Each emulator is a request/response service over a socket — one exact command in, one
measurement reply out. We treat it exactly like a REST/gRPC endpoint: connection setup,
timeouts, malformed-input handling, and failure modes are all first-class concerns. The
framework and tests are written with that lens rather than as one-off socket scripts, which is
what makes the negative/security tests and the error-simulation work fit naturally.

## Bug fixes made

The spec asks that any fixes to the provided code be documented. There were two functional bugs
plus a set of backward-compatible robustness enhancements to the base emulator.

| Fix | Problem | Change |
|---|---|---|
| **Command-mismatch (the core bug)** | `main.py` / the client sent a *truncated* command, and the protocol is exact-match, so the emulator never replied — `main.py` returned no data. | Send the full command bytes from the registry; the client returns the measured current as a `float` (or `None` on empty reply). |
| **Crash on corrupt reply** | The client did `float(reply)`, so a non-numeric/garbage reply raised `ValueError` and aborted the *whole* ammeter's run (only swallowed by `run_all`'s broad skip). Surfaced by the error-simulation work. | The client now treats an unparseable reply as one failed measurement (`None`), consistent with how the sampling loop counts timeouts. |

**Base-emulator enhancements (backward compatible — existing callers behave as before):**
readiness/stop events (`wait_until_ready()` / `stop()`) so tests never sleep-and-hope;
`bind(port=0)` for an OS-assigned ephemeral port so tests don't collide on the fixed 5001–5003;
`SO_REUSEADDR` to avoid TIME_WAIT bind failures; an accept loop that wakes periodically to check
the stop flag; an overridable `_handle_connection` seam (used by the fault emulator); and
`print` → `logging` throughout.

**Removed unused starter scaffolding: `src/utils/logger.py`.** The starter shipped a
half-implemented `TestLogger` class that nothing imported and that never actually logged to a file
(`_setup_logger` built a log-file path but attached no handler, while creating a `results/logs/`
directory as a construction side effect). Logging is already handled the idiomatic way — `main.py`
calls `logging.basicConfig(...)` and every module uses `logging.getLogger(__name__)` — so keeping
a second, broken logging mechanism would only invite confusion. It was deleted rather than wired
in. (The other provided `src/utils/` files — `config.py`, `Utils.py` — are in active use and kept.)

## Libraries installed

Kept minimal per the brief; statistics use the stdlib, not numpy/scipy.

| Library | Scope | Why |
|---|---|---|
| `pyyaml` | runtime | Parse `config/config.yaml` (the config-driven approach). |
| `matplotlib` | runtime | Visualization bonus. The only heavy-ish dep (pulls numpy); **imported lazily** in `viz.py` with the headless `Agg` backend, so the core run, the read-only CLI, and the test suite never load it. |
| `pytest` | dev | Test runner. |
| `pyright` | dev | Static type-checking (config in `pyrightconfig.json`). |

Everything else is the standard library: `statistics`, `socket`, `json`, `dataclasses`,
`argparse`, `logging`, `uuid`, `datetime`, `pathlib`.

## Key design decisions

- **Config-driven, with a registry as the single source of truth.** Ports, commands, and
  expected ranges live in one place (`registry.py` / `config.yaml`); adding or retargeting an
  ammeter is a one-line change, and a consistency test keeps config and code from drifting.
- **Typed, validated config.** `settings.py` parses YAML into dataclasses and validates it up
  front (e.g. sampling `count`/`frequency`/`duration` must be mutually consistent), so a
  contradictory config fails loudly with a clear message instead of a silently-wrong run.
- **One campaign = one run = one file.** A run is one framework invocation; all its ammeters are
  archived together under a single `run_id`. This keeps comparison simple — historical
  comparison is campaign-vs-campaign, and cross-ammeter precision is a lookup *within* one
  campaign — instead of reconstructing "which results belong together" by matching timestamps.
- **Result store is stdlib JSON, not a database.** `unique run_id + metadata + retrieval +
  comparison` is fully served by one JSON file per run plus `load`/`list_runs`/`compare`. No
  SQLite/ORM/pandas — that would be over-engineering for this scale.
- **Sampling paces on a monotonic clock at absolute target times**, so a slow measurement
  doesn't accumulate into drift; the clock and sleep are injectable so pacing is unit-tested
  without real waiting.
- **Assertions go through a small closed "oracle"** (`assertions.py`): tests assert the
  *declared contract* and ranges/relations, never an observed random value, and use metamorphic
  checks for non-deterministic output — so tests stay meaningful and don't flake.
- **Precision, not accuracy.** With different current ranges and no ground-truth reference,
  accuracy is not computable; we report the coefficient of variation (consistency) and label it
  honestly rather than inventing an accuracy figure.
- **Error simulation lives in the test tier**, not a `main.py` demo flag — error handling is a
  framework property best proven by asserting it against a real misbehaving socket in CI, while
  keeping normal runs clean. (Full rationale in the README.)

## Beyond the brief — and its value

These go past a minimal take-home; each earns its place against a stated evaluation criterion or
constraint (not "because of the role").

| Extra | Value |
|---|---|
| **CI (GitHub Actions)** | Every push runs type-check + full suite across Python 3.9/3.11/3.12, so "it's green" is verifiable without a local setup and regressions surface immediately. |
| **Docker / compose** | One command runs emulators + suite in a fixed environment on any OS — directly serves the *cross-platform* constraint and lets a reviewer run everything without matching our Python setup. |
| **Static typing (pyright)** | Catches interface mistakes before runtime and makes the framework safer to extend. |
| **Ephemeral-port emulator fixture** | Tests spin up throwaway emulators on OS-assigned ports and wait on readiness — no sleeps, no fixed-port clashes; fast and deterministic. |
| **Security-minded negative tests** | Malformed/oversized/garbage commands are fired at a live emulator to prove it neither replies nor crashes — error handling is demonstrated, not assumed. |

## Deliberately out of scope (right-sizing)

To keep the exercise proportionate: **no database/ORM** for results (flat JSON is enough), **no
numpy/pandas** for statistics (stdlib `statistics`), **no interactive/HTML plotting** (static
PNGs), and **no concurrency rework** of the single-connection emulator. That last one is a real
known limitation, documented rather than hidden — see **FIND-001** in
[`findings.md`](findings.md) (a silent/slow client can wedge the single-threaded emulator; fix
deferred, tracked by a skipped regression test).
