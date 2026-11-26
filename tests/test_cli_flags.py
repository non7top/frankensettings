import json

import pytest

from frankensettings.cli import parse_excludes

from conftest import write_json


@pytest.fixture
def pair(tmp_path):
    template = write_json(tmp_path / "template.json", {"a": 1, "c": 2})
    target = write_json(tmp_path / "target.json", {})
    return template, target


@pytest.mark.parametrize(
    "order",
    [
        ["-q", "T", "G"],
        ["T", "G", "-q"],
        ["T", "-q", "G"],
        ["diff", "-q", "T", "G"],
        ["diff", "T", "G", "-q"],
        ["diff", "T", "-q", "G"],
        ["-q", "diff", "T", "G"],
        ["--quiet", "diff", "T", "G"],
    ],
)
def test_global_flags_any_position(pair, run_cli, order):
    template, target = pair
    argv = [{"T": template, "G": target}.get(word, word) for word in order]
    assert run_cli(*argv) == (1, "", "")


def test_default_subcommand_is_diff(pair, run_cli):
    template, target = pair
    code, out, _ = run_cli(template, target)
    assert code == 1
    assert "(merged)" in out
    assert target.read_text() == "{}\n"


@pytest.mark.parametrize(
    "flags",
    [["-e", "foo"], ["--exclude", "foo"], ["--exclude=foo"], ["-efoo"], ["-e", "foo", "-e", "bar"], ["-e", "a,b"]],
)
def test_default_diff_with_exclude_value(pair, run_cli, flags):
    template, target = pair
    for argv in ([*flags, template, target], [template, target, *flags], [template, *flags, target]):
        code, out, err = run_cli(*argv)
        assert (code, err) == (1, "")
        assert "(merged)" in out


def test_exclude_value_is_not_mistaken_for_the_command(pair, run_cli):
    template, target = pair
    assert run_cli("-e", "push", template, target)[0] == 1
    assert target.read_text() == "{}\n"


@pytest.mark.parametrize("flag", ["--diff", "--dry-run"])
def test_pull_diff_after_subcommand(pair, run_cli, flag):
    template, target = pair
    write_json(target, {"a": 2})
    assert run_cli("pull", flag, template, target)[0] == 1
    assert run_cli("pull", template, flag, target)[0] == 1
    assert run_cli("pull", template, target, flag)[0] == 1
    assert run_cli(flag, "pull", template, target)[0] == 1
    assert '"a": 1' in template.read_text()


def test_exclusion_flags_change_what_push_does(tmp_path, run_cli):
    template = write_json(tmp_path / "template.json", {"trustedWorkspaces": ["x"], "other": ["y"]})
    for flags, expected in (
        ([], ["/w"]),
        (["--no-exclude"], ["/w", "x"]),
        (["-e", ""], ["/w", "x"]),
        (["-e", "other"], ["/w", "x"]),
        (["-e", "trustedWorkspaces,other"], ["/w"]),
    ):
        target = write_json(tmp_path / "target.json", {"trustedWorkspaces": ["/w"]})
        assert run_cli(*flags, "push", "-q", template, target)[0] == 0
        assert json.loads(target.read_text())["trustedWorkspaces"] == expected


@pytest.mark.parametrize(
    "raw,no_exclude,expected",
    [
        (None, False, {"trustedWorkspaces"}),
        (None, True, set()),
        ([""], False, set()),
        (["[]"], False, set()),
        (["a"], False, {"a"}),
        (["a,b"], False, {"a", "b"}),
        (["a", "b,c"], False, {"a", "b", "c"}),
        ([" a , b "], False, {"a", "b"}),
        (["a,,b", ""], False, {"a", "b"}),
        (["a", "[]"], False, {"a"}),
        (["a"], True, set()),
    ],
)
def test_exclude_parsing(raw, no_exclude, expected):
    assert parse_excludes(raw, no_exclude) == expected


def test_unknown_option_and_missing_positional(pair, run_cli):
    template, target = pair
    assert run_cli("--nope", template, target)[0] == 2
    assert run_cli("push", template)[0] == 2
