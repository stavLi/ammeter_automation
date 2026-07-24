---
name: test-assertion-oracle
description: Use when writing or reviewing assertions in tests for the ammeter framework — measurements, statistics, or client/emulator responses. Covers asserting against the declared contract (never the observed random value), a small closed set of named assertion helpers (the "oracle"), metamorphic/statistical checks for non-deterministic output, no-sleep bounded waits, and the finding-vs-authoring-error exception split.
---

# Test assertion oracle

How assertions are allowed to work in this repo. Adapted (deliberately scaled down) from a
larger HTTP-API regression blueprint: the ideas that survive for a small, non-deterministic
socket API are *declared-not-observed*, a *closed assertion vocabulary*, *metamorphic checks*,
and *no sleep waits*. The rest of that blueprint (cassettes, tenancy, coverage set-math) does
not apply here — see CLAUDE.md's "out of scope" note.

## When to use this
Before writing any `assert` against a measurement, a statistics summary, or an emulator/client
response. Also when reviewing whether an existing assertion is trustworthy or just a snapshot.

## The gotchas that bite (read first)
- **Snapshotting a random measurement.** Measurements are random (`V/R`, `B·K`, `Σ V·Δt`).
  `assert current == 0.176...` passes once and fails on the next run. Assert the *declared*
  property — type, sign, plausible range, or a *relation* — never the observed number.
- **Exact-value asserts on nondeterministic output = flaky green→red.** Use ranges, tolerances,
  or metamorphic relations.
- **`time.sleep()` to "wait for the server".** Hides races and slows the suite. Bind the emulator
  to port `0`, read the OS-assigned port, and connect with a socket **timeout that raises**. A
  wait that can never complete must fail loudly, never pass silently.
- **Asserting a field/stat the framework never produces** (e.g. a `p95` key that isn't emitted)
  is a *test* bug, not an emulator bug. Raise a `TestAuthoringError`, don't file it as a finding.
- **std dev / variance of < 2 samples is undefined.** Guard the small-N case in both the code
  and its assertion.

## The rules

**1. Assert against the declared contract, from a closed set of trusted sources only:**
- the **exact command bytes** the emulator declares (`get_current_command`),
- the **physics + input ranges** → a plausible output range (Greenlee ~0.01–100 A, ENTES ~5–200 A,
  CIRCUTOR ~0.001–0.1 A),
- the **declared return type** (`float`, finite, non-negative for a current magnitude),
- **config-declared** ports/commands (never inline literals).
Never encode an observed value. If the emulator returns something the contract doesn't sanction,
assert the *intended* value and mark the test an expected-failure with a note — so it flips green
when fixed.

**2. The oracle is the only legal way to assert.** A small, self-tested helper module
(`src/testing/assertions.py`, built with the test suite) exposes named primitives; tests call
those, not bare `assert` on raw values. Suggested vocabulary:

| Helper | Asserts |
|---|---|
| `assert_current(x)` | finite, non-negative `float` |
| `assert_in_range(x, lo, hi)` | within the ammeter's declared output band |
| `assert_stats(summary, n)` | `count == n`, `min <= mean <= max`, `median` in `[min,max]`, `std >= 0` (and defined only for `n >= 2`) |
| `assert_no_reply(resp)` | `None`/timeout for an unmatched command (the negative contract) |
| `assert_varies(samples)` | a random source actually produces spread (metamorphic: not all-equal) |
| `assert_repeatable(seeded_a, seeded_b)` | same seed → same sequence (metamorphic) |

**3. No sleep-based waiting.** Readiness and completion go through bounded, raising waits
(socket timeouts; `time.monotonic()` pacing for sampling). Never `sleep()` and hope.

**4. Two exception types, never conflated:**
- `MeasurementFinding` — the emulator/framework violated its declared contract → a real finding.
- `TestAuthoringError` — the test asked for something never declared (unknown field, wrong
  range) → fix the test. Never triage this as an emulator bug.

## A worked example

```python
import pytest
from src.testing.assertions import assert_in_range, assert_stats

@pytest.mark.parametrize("ammeter, lo, hi", [
    ("greenlee", 0.01, 100.0),
    ("entes",    5.0,  200.0),
    ("circutor", 0.001, 0.1),
])
def test_sampled_measurements_obey_declared_contract(framework, ammeter, lo, hi):
    result = framework.run_test(ammeter)          # config-driven; port/command from config
    for current in result.samples:
        assert_in_range(current, lo, hi)          # declared band, not an observed value
    assert_stats(result.stats, n=len(result.samples))  # relations, not exact numbers
```
