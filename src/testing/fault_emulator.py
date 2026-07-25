"""A fault-injecting ammeter emulator (spec bonus: error simulation).

Real emulators always answer a matched command with a valid measurement. To prove the
framework *handles* faults, we need something that misbehaves on purpose. This emulator
reuses the base's readiness/stop/ephemeral-port machinery (via the ``_handle_connection``
seam) and, on a matched command, injects one of:

    HANG     — block past the client's timeout without replying   (client sees a timeout)
    GARBAGE  — reply with non-numeric bytes                        (client can't parse it)
    DROP     — close the connection without replying               (client sees an empty read)
    FLAKY    — randomly reply correctly or inject ``flaky_fault``  (intermittent failures)

It lives in the test framework (not the Ammeters/ package of real devices) and is used by the
error-simulation tests, not wired into normal runs — see the design note in those tests.
"""
import enum
import socket
from random import Random
from typing import Optional

from Ammeters.base_ammeter import AmmeterEmulatorBase


class FaultMode(enum.Enum):
    HANG = "hang"
    GARBAGE = "garbage"
    DROP = "drop"
    FLAKY = "flaky"


class FaultInjectingEmulator(AmmeterEmulatorBase):
    COMMAND = b"MEASURE_FAULT -get_measurement"

    def __init__(
        self,
        port: int,
        host: str = "localhost",
        *,
        mode: FaultMode,
        hang_seconds: float = 30.0,
        ok_value: float = 1.23,
        flaky_fault: FaultMode = FaultMode.GARBAGE,
        seed: Optional[int] = None,
    ):
        super().__init__(port, host)
        self.mode = mode
        self.hang_seconds = hang_seconds
        self.ok_value = ok_value
        self.flaky_fault = flaky_fault
        self._rng = Random(seed)

    @property
    def get_current_command(self) -> bytes:
        return self.COMMAND

    def measure_current(self) -> float:
        return self.ok_value

    def _handle_connection(self, conn: socket.socket) -> None:
        data = conn.recv(1024)
        if data != self.get_current_command:
            return  # unknown command: no reply, exactly like the base emulator
        self._inject(conn, self.mode)

    def _inject(self, conn: socket.socket, mode: FaultMode) -> None:
        if mode is FaultMode.FLAKY:
            if self._rng.random() < 0.5:
                conn.sendall(str(self.measure_current()).encode("utf-8"))
                return
            mode = self.flaky_fault

        if mode is FaultMode.HANG:
            # Block without replying so the client hits its timeout. Wait on the stop event
            # (not time.sleep) so test teardown can interrupt it immediately.
            self._stop.wait(self.hang_seconds)
        elif mode is FaultMode.GARBAGE:
            conn.sendall(b"NOT_A_NUMBER")
        elif mode is FaultMode.DROP:
            return  # send nothing; the `with conn` in the accept loop closes the socket
