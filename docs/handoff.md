# Working handoff & progress log

A living tracker of where this project stands, what's been decided, and what's next —
so any working session (human or agent) can pick up without re-deriving context. Update
it as part of each PR. For the deep conventions see `CLAUDE.md` and `.claude/skills/`.

_Last updated: 2026-07-24._

## At a glance
- **Repo:** https://github.com/stavLi/ammeter_automation
- **Exercise:** Cloud Automation Developer take-home (Ness / NESS FORCE). Received 2026-07-22,
  **due 2026-07-29**. Build a pytest-based test-automation framework over three ammeter
  socket emulators. Spec: `Exam/ammeter-test-specification.md`.
- **Current phase:** foundation + tooling done; **starting the core measurement framework**.

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

## Exam requirements → status
| Requirement | Status |
|---|---|
| Make `main.py` return data; document fixes | ✅ done (PR #1; `base_ammeter` enhancements documented in PR #3) |
| **1. Unified measurement API** | ⏳ **next** (task #2) |
| **2. Measurement sampling** (count/duration/frequency) | ⏳ task #3 |
| **3. Result analysis** (mean/median/std/min/max) | ⏳ task #3 |
| **4. Result management** (run IDs, metadata, retrieval) | ⏳ task #4 |
| Bonus: visualization, accuracy assessment, error simulation | ⏳ task #5 |
| Deliverables: framework, README (usage), sample results, design doc | ⏳ task #6 (README still describes the emulators) |
| Constraint: minimize deps | ⚠️ `requirements.txt` lists numpy/scipy/matplotlib/seaborn/pandas — trim to what we actually use |

## Open findings
- **FIND-001** (`docs/findings.md`): silent/slow client can wedge the single-threaded
  emulator (DoS). Fix deferred; tracked by skipped `test_silent_client_does_not_wedge_server`.

## Environment notes
- Python via `.venv` (git-ignored). Runtime: `requirements.txt`; dev: `requirements-dev.txt`.
- Type-check: `.venv/bin/pyright`. Tests: `.venv/bin/pytest`.
- Docker verified locally via **Colima** (`colima start` / `colima stop`).
- Optional: `pyright-lsp` plugin enabled locally for live diagnostics (not committed).

## Next up
Core measurement framework (tasks #2–#4), TDD on top of the existing registry + oracle +
fixtures. Then bonuses (task #5) and docs/sample-results (task #6).
