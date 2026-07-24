# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project purpose

This repo is a take-home for a **Cloud Automation Developer** role (Ness Technologies /
NESS FORCE — a security-focused division). The stated skills are Python + **pytest/Playwright**,
**API/backend testing (REST, gRPC)**, **Docker/Kubernetes**, **CI/CD integration**, and early
**vulnerability detection**. The ammeter emulators are a *proxy*: the point isn't hardware, it's
to show clean, reusable, CI-integrated **test-automation infrastructure** with an API-testing and
security mindset.

Concretely: build a framework on top of three provided ammeter emulators (Greenlee, ENTES,
CIRCUTOR) — a unified measurement API, configurable sampling, statistical analysis, result
archiving, robust error handling, and (bonus) visualization + cross-ammeter accuracy comparison.
The emulators are fixed infrastructure; the deliverable is the automation around them. Full brief
in `Exam/ammeter-test-specification.md`.

### What this repo is meant to demonstrate for the role

| Role competency | Where it shows up here |
|---|---|
| Python + pytest automation | `src/` framework + `tests/` suite driven by pytest |
| API / service testing (REST/gRPC discipline) | The emulator command protocol is treated as an **API under test** — request/response, contract, timeouts, negative cases |
| CI/CD integration | GitHub Actions runs pyright + pytest on every push/PR (`.github/workflows/`, added in the `feat/ci-docker-security` branch) |
| Docker / K8s | Containerized emulators + tests (`Dockerfile`/`docker-compose.yml`, same follow-up branch) |
| Early vulnerability detection | Security-minded negative tests: malformed/oversized/garbage payloads, timeouts, resource/abuse handling |
| Reusable automation infrastructure | Config-driven framework, extensible to new "devices" without code changes |

## Commands

All Python runs through the project virtualenv (`.venv`), which is git-ignored.

```bash
# One-time setup
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt          # runtime deps
.venv/bin/pip install -r requirements-dev.txt       # dev tools (pytest, pyright)

# Run the emulators + a sample measurement round
.venv/bin/python main.py

# Type-check
.venv/bin/pyright                                   # config in pyrightconfig.json

# Tests
.venv/bin/pytest                                    # whole suite
.venv/bin/pytest tests/test_client.py               # single file
.venv/bin/pytest tests/test_client.py::test_name    # single test
.venv/bin/pytest -k "sampling"                       # by keyword
```

## Architecture

**Emulators are TCP socket servers, one per ammeter, each on its own thread and port.**
`main.py` starts all three as daemon threads, then the client requests a measurement from each.

Treat each emulator as a **service/API under test**: it exposes a request/response contract
(an exact command → a measurement reply) over a network socket, with the same concerns as a
REST/gRPC endpoint — connection setup, timeouts, malformed-input handling, and failure modes.
Framework and tests should be written with that lens, not as one-off socket scripts.

- `Ammeters/base_ammeter.py` — `AmmeterEmulatorBase` (ABC). `start_server()` binds a socket,
  accepts one connection at a time, and replies **only if the received bytes match
  `get_current_command` exactly**. Subclasses implement `get_current_command` (the exact
  command bytes) and `measure_current()` (the physics).
- `Ammeters/{Greenlee,Entes,Circutor}_Ammeter.py` — the three concrete emulators.
- `Ammeters/client.py` — `request_current_from_ammeter(port, command)` opens a socket, sends
  the command, and **returns the measured current as a float** (or `None` on empty reply).

**Ports and commands (as wired in `main.py` — these are the source of truth, the README's
port numbers are out of date):**

| Ammeter  | Port | Exact command bytes                          | Physics                     |
|----------|------|----------------------------------------------|-----------------------------|
| Greenlee | 5001 | `MEASURE_GREENLEE -get_measurement`          | Ohm's law: I = V / R        |
| ENTES    | 5002 | `MEASURE_ENTES -get_data`                    | Hall effect: I = B · K      |
| CIRCUTOR | 5003 | `MEASURE_CIRCUTOR -get_measurement -current` | Rogowski coil: I = ∫V dt    |

**The framework being built** (`src/`) sits on top of the client:
- `src/testing/test_framework.py` — `AmmeterTestFramework`, config-driven, the unified entry point.
- `src/utils/` — `config.py` (loads `config/config.yaml`), `logger.py`, `Utils.py`.
- `config/config.yaml` — drives ports/commands, sampling params, analysis, result management.

### Gotchas that will bite

- **Exact-match protocol.** Truncated or approximate commands get *no reply* (the socket just
  blocks/times out) — the server does `if data == self.get_current_command`. Always send the
  full command bytes from the table above.
- **Emulators bind fixed ports.** If a previous run didn't release them, a rerun fails to bind;
  increase the startup sleep in `main.py` or wait for the OS to free the port.
- **Starter stubs.** `src/testing/test_framework.py`, `src/utils/logger.py`, and
  `config/config.yaml` ship as incomplete stubs — they are the framework to build out, not
  working code. Some contain deliberate bugs to find and fix (document any fix).

## Domain + testing conventions

Detailed guidance lives in committed skills under `.claude/skills/` — consult them before
writing framework code or tests:
- **`ammeter-test-conventions`** — API-under-test framing, protocol handling, sampling/timing,
  statistics, socket-error handling, negative/security testing, unit vs integration tiers.
- **`test-assertion-oracle`** — how assertions are allowed to work: assert the declared contract
  (not observed random values), a closed set of named helpers, metamorphic checks, no sleep waits.
- **`test-review-checklist`** — the rubric (+ cheap policy checks) every test module passes
  before a push.

### Patterns deliberately left out of scope

These skills are right-sized down from a larger HTTP-API regression blueprint. The following
patterns from that blueprint were **considered and intentionally excluded** as over-engineering
for a 3-emulator take-home (documented so the exclusion reads as judgment, not omission):
recorded-traffic "cassettes" (no external HTTP to record), multi-tenant isolation (no tenancy),
a computed obligation-coverage merge gate + exercised-operation recorder (only three operations),
async job-polling chains (measurements are synchronous), and the failure-triage/ticket-epic and
generator/reviewer *agent-fleet* machinery (an ongoing-suite concern, not a take-home). The ideas
that *do* survive — declared-not-observed assertions, a closed oracle vocabulary, metamorphic
checks for random output, no-sleep waits, real-services integration, and a review checklist — are
kept in the skills above.

## How we work in this repo (agentic workflow)

- **Branch per task.** Every bug/feature gets its own branch off `origin/main`
  (`fix/…`, `feat/…`, `chore/…`). Never commit framework work directly to `main`.
- **Pushes require explicit human approval; the agent never merges to `main`.** Commit and
  self-review locally; do **not** `git push` until the user says so. Merges into `main` happen
  via GitHub PR (merge commit, branch kept) so the branch-and-merge history stays visible to
  reviewers.
- **Re-validate; never trust a self-reported "done."** A change counts only when the checks
  actually pass — re-run `pytest`/`pyright` and read the output rather than asserting green.
- **Checkpoint-based.** Work in small verified steps; pause for review at each checkpoint
  rather than landing everything at once.
- **Verify before claiming done.** Run the emulators / `pytest` / `pyright` and report real
  output; never assume green.
- **Tools used** (Claude Code built-ins, not committed): `/code-review` on the working diff
  before requesting a push, `simplify` for cleanup, `dataviz` for measurement plots. Static
  type-checking via the committed `pyrightconfig.json` (and the `pyright-lsp` plugin locally).
- **Don't assume — ask.** When a real decision comes up, ask rather than guess.
