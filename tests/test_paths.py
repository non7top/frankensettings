import pytest

from frankensettings import collapse_env, expand_env

EXPAND = [
    ("~", "/home/tester"),
    ("~/x", "/home/tester/x"),
    ("~/", "/home/tester/"),
    ("~bob/x", "~bob/x"),
    ("a~/b", "a~/b"),
    ("~x", "~x"),
    ("$HOME/x", "/home/tester/x"),
    ("${HOME}/x", "/home/tester/x"),
    ("pre-$HOME", "pre-/home/tester"),
    ("$FS_UNSET_VARIABLE/x", "$FS_UNSET_VARIABLE/x"),
    ("${FS_UNSET_VARIABLE}", "${FS_UNSET_VARIABLE}"),
    ("plain", "plain"),
    ("", ""),
    (1, 1),
    (1.5, 1.5),
    (True, True),
    (None, None),
]


@pytest.mark.parametrize("value,expected", EXPAND)
def test_expand_table(value, expected):
    assert expand_env(value) == expected


def test_expand_recurses_but_not_into_keys():
    value = {"~/key": ["~/a", {"k": "$HOME"}, 3]}
    assert expand_env(value) == {"~/key": ["/home/tester/a", {"k": "/home/tester"}, 3]}


def test_expand_with_env_variable_after_tilde(monkeypatch):
    monkeypatch.setenv("FS_SUB", "sub")
    assert expand_env("~/$FS_SUB/x") == "/home/tester/sub/x"


@pytest.mark.parametrize("home", ["", "/"])
def test_expand_without_usable_home_leaves_tilde(monkeypatch, home):
    monkeypatch.setenv("HOME", home)
    assert expand_env("~/x") == "~/x"
    assert expand_env("~") == "~"


def test_expand_with_home_unset(monkeypatch):
    monkeypatch.delenv("HOME")
    assert expand_env("~/x") == "~/x"
    assert expand_env("$HOME/x") == "$HOME/x"


def test_expand_trailing_slash_home(monkeypatch):
    monkeypatch.setenv("HOME", "/home/tester/")
    assert expand_env("~/x") == "/home/tester/x"


COLLAPSE = [
    ("/home/tester", "~"),
    ("/home/tester/x", "~/x"),
    ("/home/tester/", "~/"),
    ("/home/tester2/x", "/home/tester2/x"),
    ("/home/testerx", "/home/testerx"),
    ("x/home/tester/y", "x/home/tester/y"),
    ("/home", "/home"),
    ("~/x", "~/x"),
    ("", ""),
    (1, 1),
    (None, None),
    (True, True),
]


@pytest.mark.parametrize("value,expected", COLLAPSE)
def test_collapse_table(value, expected):
    assert collapse_env(value) == expected


def test_collapse_recurses_but_not_into_keys():
    value = {"/home/tester/k": ["/home/tester/a", {"k": "/home/tester"}, 3]}
    assert collapse_env(value) == {"/home/tester/k": ["~/a", {"k": "~"}, 3]}


@pytest.mark.parametrize("home", ["", "/"])
def test_collapse_without_usable_home_is_identity(monkeypatch, home):
    monkeypatch.setenv("HOME", home)
    assert collapse_env("/home/tester/x") == "/home/tester/x"


def test_collapse_with_home_unset(monkeypatch):
    monkeypatch.delenv("HOME")
    assert collapse_env(["/home/tester/x"]) == ["/home/tester/x"]


def test_collapse_trailing_slash_home(monkeypatch):
    monkeypatch.setenv("HOME", "/home/tester/")
    assert collapse_env("/home/tester/x") == "~/x"
