"""Security-minded negative tests: fire malformed traffic at a real emulator and
prove it (a) stays silent and (b) stays alive. Adapted from the negative-testing
section of the ammeter-test-conventions skill."""
import pytest

from Ammeters.client import request_current_from_ammeter
from src.testing.assertions import assert_in_range, assert_no_reply
from tests.support import probe

# Hostile / malformed inputs an untrusted client might send. `4096` is deliberately
# larger than the server's 1024-byte recv buffer to exercise the oversized case.
MALFORMED_PAYLOADS = [
    pytest.param(b"MEASURE_GREENLEE", id="truncated-command"),
    pytest.param(b"\xff\xfe\x00\x01garbage", id="garbage-non-utf8"),
    pytest.param(b"", id="empty-send"),
    pytest.param(b"A" * 4096, id="oversized-payload"),
]


@pytest.mark.integration
@pytest.mark.parametrize("payload", MALFORMED_PAYLOADS)
def test_emulator_ignores_malformed_command(running_emulator, payload):
    spec, emulator = running_emulator
    reply = probe(emulator.host, emulator.port, payload, timeout=1.0)
    # The negative contract: an unrecognised command gets no reply.
    assert_no_reply(reply)


@pytest.mark.integration
@pytest.mark.parametrize("payload", MALFORMED_PAYLOADS)
def test_emulator_survives_abuse_and_still_serves(running_emulator, payload):
    spec, emulator = running_emulator
    # Abuse the emulator, then confirm a legitimate request still succeeds — one bad
    # client must not wedge the server.
    probe(emulator.host, emulator.port, payload, timeout=1.0)
    current = request_current_from_ammeter(emulator.port, spec.command, timeout=2.0)
    assert current is not None, f"{spec.name} stopped serving after malformed input"
    assert_in_range(current, spec.expected_min, spec.expected_max)


@pytest.mark.integration
@pytest.mark.skip(
    reason="FIND-001 (docs/findings.md): silent/slow client wedges the single-threaded "
    "emulator; fix deferred to a follow-up PR. Un-skip and implement when the recv-timeout "
    "hardening lands."
)
def test_silent_client_does_not_wedge_server():
    # A client that holds a connection open without sending must not block other clients.
    # Requires the per-connection recv-timeout (and/or concurrent handling) fix.
    raise NotImplementedError
