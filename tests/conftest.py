import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from frankensettings.cli import main, parse_excludes

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"
FAKE_HOME = "/home/tester"


@pytest.fixture(autouse=True)
def fake_home(monkeypatch):
    monkeypatch.setenv("HOME", FAKE_HOME)
    return FAKE_HOME


@pytest.fixture
def run_cli(capsys):
    """Run the CLI in-process and return (exit_code, stdout, stderr)."""

    def run(*argv):
        code = main([str(arg) for arg in argv])
        captured = capsys.readouterr()
        return code, captured.out, captured.err

    return run


@dataclass(frozen=True)
class Case:
    name: str
    path: Path

    def text(self, filename):
        return (self.path / filename).read_text(encoding="utf-8")

    def load(self, filename):
        return json.loads(self.text(filename))

    def has(self, filename):
        return (self.path / filename).exists()

    @property
    def args(self):
        return self.load("args.json") if self.has("args.json") else {}

    def excludes(self):
        return parse_excludes(self.args.get("exclude"), self.args.get("no_exclude", False))

    def flags(self):
        flags = []
        for item in self.args.get("exclude") or []:
            flags += ["-e", item]
        if self.args.get("no_exclude"):
            flags.append("--no-exclude")
        return flags

    def apply_env(self, monkeypatch):
        for name, value in self.args.get("env", {}).items():
            monkeypatch.setenv(name, value)


def cases(area, required):
    """Discover fixtures/<area>/*; an incomplete case fails collection so it can never be skipped silently."""
    found = []
    for path in sorted((FIXTURES / area).iterdir()):
        missing = [name for name in required if not (path / name).exists()]
        assert not missing, f"fixture {path} lacks {missing}"
        found.append(pytest.param(Case(path.name, path), id=path.name))
    assert found, f"no fixtures under {area}"
    return found


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path
