# Working handoff & progress log

A living tracker of where this project stands, what's been decided, and what's next —
so any working session (human or agent) can pick up without re-deriving context. Update
it as part of each PR. For the deep conventions see `CLAUDE.md` and `.claude/skills/`.

_Last updated: 2026-07-25._

## At a glance
- **Repo:** https://github.com/stavLi/ammeter_automation
- **Exercise:** Cloud Automation Developer take-home (Ness / NESS FORCE). Received 2026-07-22,
  **due 2026-07-29**. Build a pytest-based test-automation framework over three ammeter
  socket emulators. Spec: `Exam/ammeter-test-specification.md`.
- **Current phase:** framework is now runnable (`python main.py` prints a stats report) with
  usage docs (PR #6); next is result management (task #4).

## How we work (short version — full rules in CLAUDE.md)
- Branch per task off `origin/main` (`fix/…`, `feat/…`, `chore/…`).
- **Never push without explicit approval;** the human merges PRs on GitHub (merge commit, keep branch).
- Checkpoint-based; ask on real decisions; re-validate (`pytest`/`pyright`) before claiming done.
- Self-review with the `test-review-checklist` skill / `simplify` before requesting a push.

## PR history (merged to main)
| PR | Branch | What |
|----|--------|------|
| #1 | `fix/preexisting-bugs` | Fixed the command-mismatch bug so `main.py` returns measurements; client returns a float. |
| #2 | `chore/agentic-setup` | `CLAUDE.md`, three committed skills, pyright config + dev deps. |
| #3 | `feat/ci-docker-security` | Test harness, registry, assertion oracle, security-negative tests, CI matrix, Docker + compose. |
| #4 | `chore/ci-tidy` | CI trigger dedup + bump actions to Node 24. |
| #7 | `feat/result-management` | JSON result archive (run IDs, metadata) — later reshaped to one-run-per-campaign (#8). |
| #8 | `refactor/campaign-run-model` | One campaign = one run = one file (simpler comparison). |
| #9 | `feat/results-cli` | `--list`/`--show`/`--compare` read-only archive CLI. |

## Exam requirements → status
| Requirement | Status |
|---|---|
| Make `main.py` return data; document fixes | ✅ done (PR #1; `base_ammeter` enhancements documented in PR #3) |
| **1. Unified measurement API** | ✅ done (PR #5 — config-driven `AmmeterTestFramework`) |
| **2. Measurement sampling** (count/duration/frequency) | ✅ done (PR #5 — `sampling.py`, monotonic pacing) |
| **3. Result analysis** (mean/median/std/min/max) | ✅ done (PR #5 — `analysis.py`, stdlib `statistics`) |
| **4. Result management** (run IDs, metadata, retrieval/compare) | ✅ done (`store.py` — one campaign = one run = one JSON file; save-by-default; `--list`/`--show`/`--compare` CLI; sample under `docs/sample-results/`) |
| Bonus: **accuracy/precision assessment** | ✅ done — honest *precision* ranking (coefficient of variation) in `precision.py`; accuracy not computable (no ground truth). Viz + error-sim still task #5 |
| Bonus: **visualization** | ✅ done — `viz.py` writes 3 PNGs/run (histogram, time-series, precision bar); matplotlib lazy-imported; sample embedded in README |
| Bonus: **error simulation** | ✅ done — `fault_emulator.py` (HANG/GARBAGE/DROP/FLAKY) + integration tests; fixed a client `ValueError` crash on corrupt replies. Tests-only by design (rationale in README) |
| Deliverables: framework, README (usage), sample results, design doc | ✅ done — framework runnable; README overhauled; `docs/design-decisions.md` (bug fixes + libraries + rationale); sample results + plots under `docs/sample-results/` |
| Constraint: minimize deps | ✅ `requirements.txt` trimmed to `pyyaml` (stats use stdlib); matplotlib added later with the viz bonus |

## Open findings
- **FIND-001** (`docs/findings.md`): silent/slow client can wedge the single-threaded
  emulator (DoS). Fix deferred; tracked by skipped `test_silent_client_does_not_wedge_server`.

## Environment notes
- Python via `.venv` (git-ignored). Runtime: `requirements.txt`; dev: `requirements-dev.txt`.
- Type-check: `.venv/bin/pyright`. Tests: `.venv/bin/pytest`.
- Docker verified locally via **Colima** (`colima start` / `colima stop`).
- Optional: `pyright-lsp` plugin enabled locally for live diagnostics (not committed).

## Next up
All spec requirements and bonuses are implemented and documented. Remaining is optional polish
and the actual submission (email the repo link). FIND-001 (emulator DoS) is the one deferred
robustness fix if time allows.
