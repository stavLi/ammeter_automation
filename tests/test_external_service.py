"""Smoke test against a *live* emulator service reachable over the network.

Skipped unless AMMETER_HOST is set. The docker-compose `tests` service sets it to the
`emulators` service hostname, so this exercises real cross-container socket networking
(the in-process integration tests can't cover that). Locally it simply skips.
"""
import os

import pytest

from Ammeters.client import request_current_from_ammeter
from src.testing.assertions import assert_in_range
from src.testing.registry import AMMETERS

EXTERNAL_HOST = os.environ.get("AMMETER_HOST")


@pytest.mark.integration
@pytest.mark.skipif(
    not EXTERNAL_HOST,
    reason="set AMMETER_HOST to run against a live emulator service (e.g. via docker-compose)",
)
@pytest.mark.parametrize("spec", AMMETERS, ids=[spec.name for spec in AMMETERS])
def test_live_service_returns_measurement(spec):
    assert EXTERNAL_HOST is not None  # guaranteed by skipif; narrows type for the call below
    current = request_current_from_ammeter(
        spec.default_port, spec.command, host=EXTERNAL_HOST, timeout=5.0
    )
    assert current is not None, f"{spec.name} service did not reply"
    assert_in_range(current, spec.expected_min, spec.expected_max)
