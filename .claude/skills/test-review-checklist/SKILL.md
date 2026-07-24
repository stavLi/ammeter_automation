---
name: test-review-checklist
description: Use when reviewing a new or changed test module in this repo (self-review before requesting a push, or during /code-review). A fixed rubric plus cheap automatable policy checks that catch hollow, flaky, or dishonest tests — over-mocking, sleep waits, inline ports/commands, exact-value asserts on random output, missing negative cases.
---

# Test review checklist

The rubric every test module is checked against before it can be pushed — by me during
self-review and by `/code-review`. Adapted from a larger regression-suite reviewer checklist,
trimmed to what matters for this socket-API framework. Keep the shape even as specifics change.

## When to use this
Reviewing any change under `tests/` (or framework code that ships with tests) before requesting
a push. Run it as a pass/fail gate: every item must pass or be explicitly justified.

## The gotchas that bite (read first)
- **Isolation theater / hollow negatives.** A "malformed command" test that connects to a port
  where nothing is listening proves nothing. Send the malformed/garbage command to a **real
  running emulator** and assert it doesn't reply and doesn't crash.
- **Over-mocking = testing your mock.** If an "integration" test patches the socket, it never
  exercises the emulator. Integration-tier tests must talk to a real server on an ephemeral port.
- **A green test that called no oracle** is probably asserting nothing meaningful. Every test
  goes through at least one `assertions.py` helper.
- **Exact-value asserts on random measurements** pass in review and fail in CI. Ranges/relations only.

## The checklist (all must pass)
1. **Fields exist.** Every asserted key/field is actually produced by the framework — no
   hallucinated stats (`p95`, `variance`) that the code never emits.
2. **No exact-value asserts on random output.** Measurements/stats are checked by range or
   relation via the oracle, never `== <number>`.
3. **No sleep waits.** No `time.sleep()` for readiness/completion; timeouts and `monotonic()`
   pacing only, and waits raise on timeout.
4. **No inline ports/commands.** `500x` port numbers and `MEASURE_*` command literals come from
   config/fixtures, not typed into the test.
5. **Every test uses ≥1 oracle helper** from `src/testing/assertions.py`.
6. **Right tier, real services.** Integration tests hit a real emulator over a real socket
   (ephemeral port, per-test setup/teardown); mocks appear only in deliberately-marked unit tests.
7. **Negative/security case per emulator.** At least one malformed / oversized / garbage-byte
   command test per ammeter, asserting no-reply/handled and no crash.
8. **Finding vs authoring error.** Contract violations raise `MeasurementFinding`; invalid tests
   raise `AuthoringError`. The two are not conflated.
9. **No dead duplicates.** A test that supersedes an older one deletes it in the same change.

## Cheap policy checks (automatable, belong in CI)
Fast string/AST scans over `tests/` — fail the build on a hit:
- `time.sleep(` present in a test file.
- A bare port literal (`\b50\d\d\b`) or a `MEASURE_` byte literal in a test file.
- A test file that never imports from `src.testing.assertions`.

## A worked example (a review pass)

```
module: tests/test_measurement_contract.py
1 fields exist ............ PASS
2 no exact asserts ........ PASS (uses assert_in_range)
3 no sleep waits .......... FAIL  -> line 41 sleeps 2s to wait for server; replace with
                                    ephemeral-port fixture + connect timeout
4 no inline ports ......... FAIL  -> line 12 hardcodes 5001; read from config
5 uses an oracle .......... PASS
6 real services .......... PASS (ephemeral-port emulator fixture)
7 negative case .......... MISSING -> add a garbage-command case
8 exception split ........ PASS
9 no dead duplicates ..... PASS
VERDICT: CHANGES REQUESTED (3, 4, 7)
```
