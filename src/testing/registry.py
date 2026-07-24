"""Single source of truth for the ammeters under test.

Keeping the (name, emulator class, default port, expected range) in one place means
tests and `main.py` never hardcode ports or command literals — the command is read
from each emulator class itself, so it cannot drift from what the server matches on.
"""
from dataclasses import dataclass
from typing import List, Type

from Ammeters.base_ammeter import AmmeterEmulatorBase
from Ammeters.Greenlee_Ammeter import GreenleeAmmeter
from Ammeters.Entes_Ammeter import EntesAmmeter
from Ammeters.Circutor_Ammeter import CircutorAmmeter


@dataclass(frozen=True)
class AmmeterSpec:
    name: str
    emulator_cls: Type[AmmeterEmulatorBase]
    default_port: int
    # Plausible output band derived from the emulator's input ranges + formula.
    # Used for range/sanity assertions, never for exact-value checks.
    expected_min: float
    expected_max: float

    @property
    def command(self) -> bytes:
        """The exact command bytes this emulator matches on (read from the class)."""
        return self.emulator_cls(self.default_port).get_current_command


# Ports mirror how main.py wires the emulators. Ranges come from each emulator's
# input distributions (see .claude/skills/ammeter-test-conventions).
AMMETERS: List[AmmeterSpec] = [
    AmmeterSpec("greenlee", GreenleeAmmeter, 5001, 0.01, 100.0),
    AmmeterSpec("entes", EntesAmmeter, 5002, 5.0, 200.0),
    AmmeterSpec("circutor", CircutorAmmeter, 5003, 0.001, 0.1),
]
