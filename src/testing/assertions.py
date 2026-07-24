"""The assertion oracle — the only sanctioned way to assert in this repo's tests.

See .claude/skills/test-assertion-oracle. Two exception types keep findings honest:

- ``MeasurementFinding`` — the emulator/framework violated its declared contract.
  This is a real finding about the system under test (subclasses ``AssertionError``
  so pytest reports it as a failure).
- ``AuthoringError`` — the *test* asked for something the contract never
  declared (bad bounds, too few samples). Fix the test; never triage it as a bug.
"""
import math
from typing import Optional, Sequence


class MeasurementFinding(AssertionError):
    """The system under test violated its declared contract — a real finding."""


class AuthoringError(Exception):
    """The test itself is invalid — not a finding about the system under test."""


def assert_current(value: object) -> float:
    """A measured current must be a finite, non-negative float. Returns it for chaining."""
    # bool is a subclass of int/float-ish; reject it explicitly to avoid True == 1.0 slipping through
    if isinstance(value, bool) or not isinstance(value, float):
        raise MeasurementFinding(
            f"expected a float current, got {type(value).__name__}: {value!r}"
        )
    if not math.isfinite(value):
        raise MeasurementFinding(f"current is not finite: {value!r}")
    if value < 0:
        raise MeasurementFinding(f"current magnitude must be non-negative, got {value}")
    return value


def assert_in_range(value: object, lo: float, hi: float) -> float:
    """Assert a current is a valid float within the ammeter's declared output band."""
    if lo > hi:
        raise AuthoringError(f"invalid range: lo={lo} > hi={hi}")
    current = assert_current(value)
    if not (lo <= current <= hi):
        raise MeasurementFinding(f"current {current} outside declared band [{lo}, {hi}]")
    return current


def assert_no_reply(response: Optional[bytes]) -> None:
    """The emulator must not reply to a command it does not recognise (the negative contract)."""
    if response is not None:
        raise MeasurementFinding(
            f"expected no reply to an unmatched command, got {response!r}"
        )


def assert_varies(samples: Sequence[float]) -> None:
    """Metamorphic check: a random measurement source must produce spread, not a stuck value."""
    if len(samples) < 2:
        raise AuthoringError("assert_varies needs at least 2 samples")
    if len(set(samples)) == 1:
        raise MeasurementFinding(
            f"expected varying measurements, all {len(samples)} samples were {samples[0]}"
        )
