import copy

import pytest

from conftest import cases
from frankensettings import KeyConflictError, deep_merge, pull_merge
from frankensettings.fileio import format_json

PULL_CASES = cases("pull", ["template.json", "target.json", "expected.json"])


@pytest.mark.parametrize("case", PULL_CASES)
def test_pull_fixtures(case, monkeypatch):
    case.apply_env(monkeypatch)
    result = pull_merge(case.load("template.json"), case.load("target.json"), case.excludes())
    assert format_json(result) == case.text("expected.json")


@pytest.mark.parametrize("case", PULL_CASES)
def test_pull_does_not_mutate_inputs(case, monkeypatch):
    case.apply_env(monkeypatch)
    template, target = case.load("template.json"), case.load("target.json")
    frozen = copy.deepcopy((template, target))
    result = pull_merge(template, target, case.excludes())
    assert (template, target) == frozen
    result["__probe__"] = 1
    assert "__probe__" not in template


@pytest.mark.parametrize("case", PULL_CASES)
def test_pull_leak_scan(case, monkeypatch):
    """Private values in the target are spelled with PRIVATE or the fake home; neither may reach the template."""
    case.apply_env(monkeypatch)
    result = format_json(pull_merge(case.load("template.json"), case.load("target.json"), case.excludes()))
    assert "PRIVATE" not in result
    if not case.args.get("allow_home_literals"):
        assert "/home/tester" not in result
    assert "PRIVATE" not in case.text("expected.json")


def test_pull_fixtures_cover_enough_private_values():
    markers = sum(param.values[0].text("target.json").count("PRIVATE") for param in PULL_CASES)
    assert markers >= 25


def test_round_trip_no_leak():
    template = {"theme": "dark", "bin": "~/bin", "trustedWorkspaces": []}
    target = {"model": "local", "trustedWorkspaces": ["/workspaces/PRIVATE"]}
    live = deep_merge(target, template, {"trustedWorkspaces"})
    assert live["bin"] == "/home/tester/bin"
    pulled = pull_merge(template, live, {"trustedWorkspaces"})
    assert pulled == {"theme": "dark", "bin": "~/bin", "trustedWorkspaces": [], "model": "local"}
    assert "PRIVATE" not in format_json(pulled)


def test_pull_rejects_target_keys_that_look_like_replace_markers():
    with pytest.raises(KeyConflictError) as info:
        pull_merge({}, {"=x": 1}, set())
    assert info.value.source == "target"
    assert str(info.value) == "key '=x' starts with '=' and cannot be stored in a template"


def test_pull_rejects_ambiguous_template():
    with pytest.raises(KeyConflictError) as info:
        pull_merge({"k": 1, "=k": 2}, {}, set())
    assert info.value.source == "template"
