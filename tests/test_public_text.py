"""Public repos must not carry real home paths, emails or addresses (Constitution II and FR-065)."""
import re

from conftest import ROOT

SCAN = [
    "README.md", "CHANGELOG.md", "pyproject.toml", "Makefile", "docs", "specs",
    "tests", "frankensettings", ".github", "scripts",
]
SKIP_SUFFIXES = {".pyc"}
PLACEHOLDER_NAMES = {"tester", "tester2", "testerx", "alice", "alice2", "bob", "user", "username"}
DOCUMENTATION_IPV4 = ("192.0.2.", "198.51.100.", "203.0.113.", "127.0.0.1", "0.0.0.0")

HOME_PATH = re.compile(r"(?<![\w.])/(?:home|Users)/([A-Za-z0-9_.-]+)")
EMAIL = re.compile(r"[\w.+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b")
IPV4 = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")
CHECKOUT_DIR = re.compile(r"~/(?:scm|src|code|git|projects)/")


def _files():
    for entry in SCAN:
        path = ROOT / entry
        if path.is_file():
            yield path
        else:
            for found in sorted(path.rglob("*")):
                if found.is_file() and found.suffix not in SKIP_SUFFIXES and "__pycache__" not in found.parts:
                    yield found


def test_no_private_text():
    problems = []
    for path in _files():
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(ROOT)
        for match in HOME_PATH.finditer(text):
            if match.group(1) not in PLACEHOLDER_NAMES:
                problems.append(f"{rel}: home path {match.group(0)}")
        for match in EMAIL.finditer(text):
            problems.append(f"{rel}: email {match.group(0)}")
        for match in IPV4.finditer(text):
            if not match.group(0).startswith(DOCUMENTATION_IPV4):
                problems.append(f"{rel}: address {match.group(0)}")
        for match in CHECKOUT_DIR.finditer(text):
            problems.append(f"{rel}: checkout path {match.group(0)}")
    assert problems == []


def test_scanner_catches_what_it_should():
    # Built at runtime so this file does not trip its own scan.
    assert HOME_PATH.search("cd /home" + "/realperson/project")
    assert HOME_PATH.search("/Users" + "/realperson/x")
    assert not HOME_PATH.search("/home/")
    assert EMAIL.search("write to someone" + "@example.org")
    assert not EMAIL.search("pypa/gh-action-pypi-publish@v1.14.3")
    assert not EMAIL.search("actions/checkout@v7")
    assert IPV4.search("host 10.1." + "2.3 down")
    assert not IPV4.search("version 1.2.3")
    assert CHECKOUT_DIR.search("see ~/" + "scm/project")
