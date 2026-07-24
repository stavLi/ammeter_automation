"""Happy-path integration tests: real emulator, real socket, declared-contract assertions."""
from typing import List, Optional

import pytest

from Ammeters.client import request_current_from_ammeter
from src.testing.assertions import assert_in_range, assert_varies


@pytest.mark.integration
def test_measurement_is_within_declared_range(running_emulator):
    spec, emulator = running_emulator
    current = request_current_from_ammeter(emulator.port, spec.command, timeout=2.0)
    assert current is not None, f"{spec.name} did not reply to its declared command"
    # Assert the declared band, never the (random) observed value.
    assert_in_range(current, spec.expected_min, spec.expected_max)


@pytest.mark.integration
def test_measurements_vary_across_samples(running_emulator):
    spec, emulator = running_emulator
    samples: List[Optional[float]] = [
        request_current_from_ammeter(emulator.port, spec.command, timeout=2.0)
        for _ in range(8)
    ]
    assert all(s is not None for s in samples), f"{spec.name} dropped a reply"
    # Metamorphic: a random source must produce spread, not a stuck value.
    assert_varies([s for s in samples if s is not None])
