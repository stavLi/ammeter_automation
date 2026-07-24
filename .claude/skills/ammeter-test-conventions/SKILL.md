---
name: ammeter-test-conventions
description: Domain rules and pytest patterns for the ammeter test framework in this repo. Use when writing or reviewing framework code (src/) or tests that talk to the Greenlee/ENTES/CIRCUTOR socket emulators — covers treating the emulator as an API/service under test, the exact-match command protocol, measurement ranges, sampling/timing, statistical expectations, socket-error handling, negative and security-minded testing (malformed/oversized/garbage payloads, timeouts, connection abuse), and how tests fake the emulators.
---

# Ammeter test conventions

Conventions for building and testing the current-measurement framework in this repo. The
emulators (`Ammeters/`) are fixed infrastructure; everything here is about the code that
drives and tests them.

Treat each emulator as a **service/API under test** (request/response contract over a socket,
like a REST/gRPC endpoint). The same rigor applies: happy-path *and* negative/malformed cases,
explicit timeouts, and graceful handling of failure modes.

## The measurement protocol (get this right first)

Each emulator is a TCP server that replies **only when the received bytes equal its command
exactly** (`if data == self.get_current_command`). There is no parsing, no prefix match, no
trailing-newline tolerance.

| Ammeter  | Port | Exact command bytes                          | Formula        | Output range (A) |
|----------|------|----------------------------------------------|----------------|------------------|
| Greenlee | 5001 | `MEASURE_GREENLEE -get_measurement`          | I = V / R      | ~0.01 – 100      |
| ENTES    | 5002 | `MEASURE_ENTES -get_data`                    | I = B · K      | ~5 – 200         |
| CIRCUTOR | 5003 | `MEASURE_CIRCUTOR -get_measurement -current` | I = Σ(V·Δt)    | ~0.001 – 0.1     |

Ranges derive from the emulators' input distributions (Greenlee: V∈[1,10], R∈[0.1,100];
ENTES: B∈[0.01,0.1], K∈[500,2000]; CIRCUTOR: 10× V∈[0.1,1.0], Δt∈[0.001,0.01]). Use them for
sanity assertions, **not** exact-value assertions — measurements are random.

Rules:
- Never hard-code truncated commands. Wrong bytes → the server never replies and the client
  blocks. Always set a **socket timeout** on the client so a mismatch fails fast instead of hanging.
- Treat the per-ammeter `(port, command)` pair as configuration (from `config/config.yaml`),
  not literals scattered through the code.

## Sampling & timing

- Sampling is defined by three knobs: measurement **count**, total **duration**, and
  **frequency** (Hz). Any two determine the third — validate the config rather than trusting it
  (reject `NULL`/missing/contradictory combinations).
- Pace samples against a monotonic clock (`time.monotonic()`), not `time.time()`. Account for
  the time each measurement itself takes so total duration doesn't drift.
- A slow/again-unreachable ammeter must not stall the whole run — bound each measurement by the
  socket timeout and record failures as data points, not crashes.

## Statistics

Report mean, median, std dev, min, max over the collected samples. Prefer the stdlib
`statistics` module for correctness and to honor the brief's "minimize dependencies"; reach for
`numpy`/`scipy` only where they add real value (e.g. richer analysis or performance). Guard
against empty/one-sample sets (std dev of <2 samples is undefined).

## Error handling

- Connection refused / timeout / unexpected reply are expected operational states, not bugs —
  catch them, log them, and surface them in results.
- A single ammeter failing should degrade gracefully (that ammeter's run is marked failed), not
  abort the others.

## pytest patterns for this repo

Assertions in tests follow the **[test-assertion-oracle](../test-assertion-oracle/SKILL.md)**
skill (declared-not-observed, named helpers, no sleep waits); review new test modules against the
**[test-review-checklist](../test-review-checklist/SKILL.md)** before pushing.

**Two tiers, marked:**
- `unit` — fast, may mock the socket/client; tests pure logic (stats, config validation, command
  building). No network.
- `integration` — talks to a **real** emulator over a real socket (ephemeral port); mocks are a
  smell here. This tier is the one that actually proves the contract.

CI runs both; keep the split explicit with `@pytest.mark.unit` / `@pytest.mark.integration`.

Test layout lives under `tests/`. Core patterns:

- **Ephemeral-port emulator fixture.** Start the real emulator on port `0` (OS-assigned) in a
  daemon thread, yield the bound port, tear down. This avoids the fixed 5001–5003 ports (which
  cause "address already in use" flakiness) and keeps tests parallel-safe.

  ```python
  @pytest.fixture
  def running_emulator():
      # start GreenleeAmmeter(port=0) in a thread, discover the real port, yield it
      ...
  ```

- **Parametrize across ammeters.** One test body, three `pytest.mark.parametrize` cases
  `(emulator_cls, command, expected_range)` — proves the unified API really is unified.
- **Protocol tests.** Assert: correct command → `float` in range; wrong/truncated command →
  client returns `None`/times out (with a short timeout so the test is fast).
- **Determinism.** For logic that shouldn't depend on RNG, seed `random` or `monkeypatch`
  `generate_random_float`; don't assert exact floats on live measurements.
- **Timing tests.** Assert sample **count** exactly and total **duration** within a tolerance
  band (timing is never exact); never assert on wall-clock equality.
- **No real external network.** Everything is localhost sockets; keep timeouts short (≤1s in
  tests) so a hang fails loudly.

## Negative & security-minded testing

The role (NESS FORCE, a security division) values finding weaknesses early. Beyond happy-path
tests, probe how the server/client behave under hostile or malformed input — treat it like
testing an untrusted API:

- **Malformed / unknown commands** → server must not reply (and must not crash); client must
  time out cleanly rather than hang.
- **Oversized payloads** (larger than the `recv` buffer) and **empty / partial sends** → no
  crash, no unbounded resource use.
- **Garbage / non-UTF-8 bytes** → handled as a rejected request, not an unhandled exception.
- **Connection abuse** — connect-and-drop, many rapid connections, slow senders → the emulator
  keeps serving other clients; one bad client can't wedge the server.
- **Timeout discipline** — every client socket sets a timeout; assert the *failure* path
  (timeout/`None`) as explicitly as the success path.

Frame these as regression tests for known weaknesses, and note in results/docs what each one
guards against.

## Definition of done for framework code

Green `pytest`, clean `pyright`, and the feature is exercised against the live emulators (not
just mocks) at least once before it's called complete.
