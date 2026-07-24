# Security & robustness findings

A running log of weaknesses found in the system under test (the emulators / client),
in the spirit of the role's "identify vulnerabilities early" responsibility. Each entry
records the declared-vs-actual gap, evidence, impact, and status. Fixes land in their own
PRs so the finding → fix → regression flow stays visible.

---

## FIND-001 — Silent/slow client can wedge the emulator (DoS)

- **Severity:** Medium (availability / denial-of-service).
- **Component:** `Ammeters/base_ammeter.py`, the accept loop.
- **Declared behavior:** the emulator serves measurement requests to clients.
- **Actual behavior:** the accept loop is single-threaded and calls `conn.recv(1024)` with
  **no per-connection timeout**. A client that connects and sends nothing (or dribbles bytes
  slowly) blocks the server on `recv` indefinitely, so **no other client can be served** — a
  classic slowloris-style DoS.
- **Evidence:** the `empty-send` case in `tests/test_security_negative.py` only recovers because
  the *test* client disconnects after its own 1s timeout, which makes the server's `recv` return
  EOF. A malicious client that keeps the socket open would not disconnect, and the server would
  stay blocked.
- **Recommended fix:** set a per-connection `settimeout` on the accepted socket so a silent
  client is dropped after a bound; optionally handle connections concurrently (thread per
  connection or non-blocking I/O) so one slow client can't affect others.
- **Status:** **Documented; fix deferred to a dedicated follow-up PR.** Tracked in code by the
  skipped test `test_silent_client_does_not_wedge_server` (flips from skipped to a real
  regression test when the fix lands).
