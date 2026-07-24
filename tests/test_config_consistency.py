"""Guard against drift between config/config.yaml and the code registry.

The framework reads ports/commands from config; tests spin emulators from the registry.
If they disagree, integration tests would pass in-process but the framework would talk to
the wrong port/command in a real deployment. This test keeps the two in lockstep.
"""
import pytest

from src.testing.registry import AMMETERS
from src.testing.settings import load_settings


@pytest.mark.unit
def test_config_ports_and_commands_match_registry():
    cfg = load_settings("config/config.yaml")
    assert set(cfg.ammeters) == {spec.name for spec in AMMETERS}
    for spec in AMMETERS:
        configured = cfg.ammeter(spec.name)
        assert configured.port == spec.default_port, f"{spec.name}: port drift"
        assert configured.command == spec.command, f"{spec.name}: command drift"
