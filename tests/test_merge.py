import copy

import pytest

from conftest import cases
from frankensettings import KeyConflictError, deep_merge
from frankensettings.fileio import format_json

MERGE_CASES = cases("merge", ["template.json", "target.json", "expected.json"])


@pytest.mark.parametrize("case", MERGE_CASES)
def test_merge_fixtures(case, monkeypatch):
    case.apply_env(monkeypatch)
    result = deep_merge(case.load("target.json"), case.load("template.json"), case.excludes())
    assert format_json(result) == case.text("expected.json")


@pytest.mark.parametrize("case", MERGE_CASES)
def test_merge_does_not_mutate_inputs(case, monkeypatch):
    case.apply_env(monkeypatch)
    template, target = case.load("template.json"), case.load("target.json")
    frozen = copy.deepcopy((template, target))
    result = deep_merge(target, template, case.excludes())
    assert (template, target) == frozen
    result["__probe__"] = 1
    assert "__probe__" not in target


@pytest.mark.parametrize("case", MERGE_CASES)
def test_merge_is_idempotent(case, monkeypatch):
    case.apply_env(monkeypatch)
    template = case.load("template.json")
    once = deep_merge(case.load("target.json"), template, case.excludes())
    twice = deep_merge(once, template, case.excludes())
    assert format_json(twice) == format_json(once)


def test_merge_accepts_any_collection_of_excludes():
    template, target = {"a": 1}, {"a": 0}
    for excludes in ({"a"}, ["a"], ("a",), frozenset({"a"})):
        assert deep_merge(target, template, excludes) == {"a": 0}


@pytest.mark.parametrize(
    "template,message",
    [
        ({"a": {"k": 1, "=!k": 2}}, "key 'a.k': both 'k' and '=!k' present"),
        ({"=k": 1, "=!k": 2}, "key 'k': both '=k' and '=!k' present"),
        ({"=!k": 1, "k": 2}, "key 'k': both '=!k' and 'k' present"),
        ({"a": {"=!": 1}}, "key 'a.=!': empty name after replace prefix"),
        ({"=": 1}, "key '=': empty name after replace prefix"),
    ],
)
def test_ambiguous_replace_keys(template, message):
    with pytest.raises(KeyConflictError) as info:
        deep_merge({}, template, set())
    assert str(info.value) == message
    assert info.value.source == "template"


def test_replace_values_are_not_checked_for_conflicts():
    template = {"=!k": {"x": 1, "=!x": 2}}
    assert deep_merge({}, template, set()) == {"k": {"x": 1, "=!x": 2}}
