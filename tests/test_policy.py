"""Cheap policy gates over the test suite (see .claude/skills/test-review-checklist).

Fast static scans that fail the build on a convention violation — no sleep-based
waits, no inline emulator port literals. These run in CI on every push.
"""
import re
from pathlib import Path

import pytest

_TESTS_DIR = Path(__file__).parent
_THIS_FILE = Path(__file__).name


def _test_files():
    # Scan every test module except this policy file itself.
    return [p for p in sorted(_TESTS_DIR.glob("test_*.py")) if p.name != _THIS_FILE]


@pytest.mark.unit
@pytest.mark.parametrize("path", _test_files(), ids=lambda p: p.name)
def test_no_sleep_based_waits(path: Path):
    assert "time.sleep(" not in path.read_text(), (
        f"{path.name} uses time.sleep; wait via readiness/timeouts instead"
    )


@pytest.mark.unit
@pytest.mark.parametrize("path", _test_files(), ids=lambda p: p.name)
def test_no_inline_emulator_ports(path: Path):
    hits = re.findall(r"\b50\d\d\b", path.read_text())
    assert not hits, (
        f"{path.name} hardcodes emulator port(s) {hits}; read ports from the registry/fixtures"
    )
