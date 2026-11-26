"""Every functional requirement in spec.md maps to real tests listed in test-plan.md (SC-002)."""
import re

from conftest import ROOT

FEATURE = ROOT / "specs" / "001-frankensettings-v1"
TOKEN = re.compile(r"(\w+\.py)::(\w+)")


def _requirements():
    return re.findall(r"\*\*(FR-\d{3})\*\*", (FEATURE / "spec.md").read_text())


def _rows():
    rows = {}
    for line in (FEATURE / "test-plan.md").read_text().splitlines():
        match = re.match(r"\| (FR-\d{3}) \| (.*) \|$", line)
        if match:
            rows[match.group(1)] = match.group(2)
    return rows


def test_every_requirement_has_a_row():
    requirements = _requirements()
    assert len(requirements) >= 40
    rows = _rows()
    assert [fr for fr in requirements if fr not in rows] == []
    assert [fr for fr in rows if fr not in requirements] == []


def test_every_row_names_existing_tests():
    for fr, cell in _rows().items():
        tokens = TOKEN.findall(cell)
        assert tokens or "enforced by" in cell, fr
        for filename, function in tokens:
            source = (ROOT / "tests" / filename).read_text()
            assert re.search(rf"^(?:async )?def {function}\(", source, re.M), f"{fr}: {filename}::{function}"
