import hashlib
import json
import os
import runpy
import shutil
import stat
import sys

import pytest

from conftest import ROOT, cases, write_json
import frankensettings
from frankensettings import cli
from frankensettings.fileio import format_json

MERGE_CASES = cases("merge", ["template.json", "target.json", "expected.json"])
PULL_CASES = cases("pull", ["template.json", "target.json", "expected.json"])
MISSING_CASES = cases("missing", ["template.json", "target.json", "expected.txt"])
INVALID_CASES = cases("invalid", ["args.json", "expected_error.txt"])


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def workspace(tmp_path, template=None, target=None):
    paths = tmp_path / "template.json", tmp_path / "target.json"
    for path, data in zip(paths, (template, target)):
        if data is not None:
            write_json(path, data)
    return paths


def materialize(case, tmp_path):
    for name in ("template.json", "target.json"):
        if case.has(name):
            shutil.copy(case.path / name, tmp_path / name)
    return tmp_path / "template.json", tmp_path / "target.json"


@pytest.mark.parametrize("command", ["diff", "push", "apply", "pull", "missing"])
def test_subcommands_exist(tmp_path, run_cli, command):
    template, target = workspace(tmp_path, {"a": 1}, {"b": 2})
    code, out, err = run_cli(command, template, target)
    assert err == ""
    assert code == (1 if command == "diff" else 0)
    assert out != ""


def test_apply_is_push(tmp_path, run_cli):
    one, two = tmp_path / "one", tmp_path / "two"
    for folder in (one, two):
        folder.mkdir()
        workspace(folder, {"a": [1], "b": "~/x"}, {"a": [0], "c": 1})
    assert run_cli("push", one / "template.json", one / "target.json")[0] == 0
    assert run_cli("apply", two / "template.json", two / "target.json")[0] == 0
    assert (one / "target.json").read_text() == (two / "target.json").read_text()


def test_exit_codes(tmp_path, run_cli):
    template, target = workspace(tmp_path, {"a": 1}, {})
    assert run_cli("diff", template, target)[0] == 1
    assert run_cli("push", template, target)[0] == 0
    assert run_cli("diff", template, target)[0] == 0
    assert run_cli("pull", "--diff", template, target)[0] == 0
    write_json(target, {"a": 2})
    assert run_cli("pull", "--diff", template, target)[0] == 1
    assert run_cli("pull", template, target)[0] == 0
    assert run_cli("pull", "--diff", template, target)[0] == 0
    assert run_cli("missing", template, target)[0] == 0
    assert run_cli("--version")[0] == 0
    assert run_cli("--bogus")[0] == 2


def test_diff_labels(tmp_path, run_cli):
    template, target = workspace(tmp_path, {"a": 1}, {"b": 2})
    _, out, _ = run_cli("diff", template, target)
    assert f"--- {target}\n+++ {target} (merged)\n" in out
    assert '+  "a": 1' in out
    _, out, _ = run_cli("push", template, target)
    assert f"--- {target}\n+++ {target} (updated)\n" in out
    write_json(target, {"a": 5, "z": 1})
    _, out, _ = run_cli("pull", template, target)
    assert f"--- {template}\n+++ {template} (pulled)\n" in out


def test_quiet_suppresses_output_only(tmp_path, run_cli):
    template, target = workspace(tmp_path, {"a": 1}, {})
    assert run_cli("-q", "diff", template, target) == (1, "", "")
    assert run_cli("push", "-q", template, target) == (0, "", "")
    assert '"a": 1' in target.read_text()
    write_json(target, {"a": 1, "m": 2})
    assert run_cli("pull", template, target, "--quiet") == (0, "", "")
    assert "m" in template.read_text()


@pytest.mark.parametrize("case", INVALID_CASES)
def test_invalid_fixtures(case, tmp_path, run_cli):
    args = case.args
    template, target = tmp_path / "template.json", tmp_path / "target.json"
    if not args.get("omit_template"):
        shutil.copy(case.path / "template.raw", template)
    if not args.get("omit_target"):
        shutil.copy(case.path / "target.raw", target)
    if args.get("target_dir"):
        target.unlink()
        target.mkdir()
    if args.get("same_path"):
        target = template
    before = {p.name: digest(p) for p in tmp_path.iterdir() if p.is_file()}
    code, out, err = run_cli(args["command"], template, target)
    expected = case.text("expected_error.txt").replace("{template}", str(template)).replace("{target}", str(target))
    assert (code, out) == (2, "")
    assert err == "fsettings: " + expected
    assert err.count("\n") == 1
    assert {p.name: digest(p) for p in tmp_path.iterdir() if p.is_file()} == before
    assert sorted(p.name for p in tmp_path.iterdir() if p.name.startswith(".")) == []


@pytest.mark.parametrize("argv", [[], ["only-one"], ["a", "b", "c"], ["push", "a"], ["push", "a", "b", "c"]])
def test_usage_errors_exit_2(run_cli, argv):
    code, out, err = run_cli(*argv)
    assert (code, out) == (2, "")
    assert "usage: fsettings" in err
    assert "expected TEMPLATE and TARGET" in err


def test_option_misuse_exits_2(tmp_path, run_cli):
    template, target = workspace(tmp_path, {}, {})
    for argv in (["push", "--diff", template, target], ["--dry-run", template, target], ["--bogus", template, target]):
        code, out, err = run_cli(*argv)
        assert (code, out) == (2, "")
        assert err.startswith("usage: fsettings")


def test_help_and_version(run_cli):
    code, out, err = run_cli("-h")
    assert (code, err) == (0, "")
    assert "Exit codes:" in out
    for command in cli.COMMANDS:
        assert command in out
    assert run_cli("--version") == (0, f"fsettings {frankensettings.__version__}\n", "")


def test_unchanged_result_not_written(tmp_path, run_cli):
    template, target = workspace(tmp_path, {"a": 1}, {"a": 1, "b": 2})
    before = os.stat(target)
    assert run_cli("push", template, target) == (0, "", "")
    after = os.stat(target)
    assert (before.st_ino, before.st_mtime_ns) == (after.st_ino, after.st_mtime_ns)


def test_diff_ignores_formatting(tmp_path, run_cli):
    template, target = workspace(tmp_path, {"a": 1})
    target.write_text('{"a":1,"b":[1,2]}')
    assert run_cli("diff", template, target) == (0, "", "")
    assert run_cli("push", template, target) == (0, "", "")
    assert target.read_text() == '{"a":1,"b":[1,2]}'


def test_missing_target_is_empty_for_diff_and_push(tmp_path, run_cli):
    template = tmp_path / "template.json"
    write_json(template, {"a": 1})
    target = tmp_path / "new" / "dir" / "target.json"
    code, out, _ = run_cli("diff", template, target)
    assert code == 1
    assert '+  "a": 1' in out
    assert not target.exists()
    assert run_cli("push", "-q", template, target) == (0, "", "")
    assert target.read_text() == format_json({"a": 1})


def test_empty_template_and_target_change_nothing(tmp_path, run_cli):
    template = tmp_path / "template.json"
    write_json(template, {})
    target = tmp_path / "target.json"
    assert run_cli("push", template, target) == (0, "", "")
    assert not target.exists()


@pytest.mark.parametrize("flag", ["--diff", "--dry-run"])
@pytest.mark.parametrize("position", ["before", "after"])
def test_pull_dry_run_does_not_write(tmp_path, run_cli, flag, position):
    template, target = workspace(tmp_path, {"a": 1}, {"a": 2})
    before = digest(template)
    argv = [flag, "pull", template, target] if position == "before" else ["pull", template, target, flag]
    code, out, _ = run_cli(*argv)
    assert code == 1
    assert '-  "a": 1' in out
    assert digest(template) == before


def test_pull_creates_missing_template(tmp_path, run_cli):
    target = tmp_path / "target.json"
    write_json(target, {"a": "/home/tester/x", "trustedWorkspaces": ["/w/PRIVATE"]})
    template = tmp_path / "repo" / "template.json"
    code, out, _ = run_cli("pull", template, target)
    assert code == 0
    assert template.read_text() == format_json({"a": "~/x", "trustedWorkspaces": []})
    assert f"--- {template}\n" in out


def test_pull_nothing_to_do_exit_zero(tmp_path, run_cli):
    template, target = workspace(tmp_path, {"a": 1}, {"a": 1})
    assert run_cli("pull", template, target) == (0, "", "")


def test_missing_exit_zero(tmp_path, run_cli):
    template, target = workspace(tmp_path, {"a": 1}, {"b": 1, "trustedWorkspaces": []})
    code, out, err = run_cli("missing", template, target)
    assert (code, err) == (0, "")
    assert "+ a" in out and "? b" in out and "* trustedWorkspaces" in out


@pytest.mark.parametrize("case", MISSING_CASES)
def test_missing_cli_fixtures(case, tmp_path, run_cli, monkeypatch):
    materialize(case, tmp_path)
    monkeypatch.chdir(tmp_path)
    code, out, err = run_cli(*case.flags(), "missing", "template.json", "target.json")
    assert (code, err) == (0, "")
    assert out == case.text("expected.txt")


@pytest.mark.parametrize("case", MERGE_CASES)
def test_push_fixture_cases(case, tmp_path, run_cli, monkeypatch):
    case.apply_env(monkeypatch)
    template, target = materialize(case, tmp_path)
    expected = case.text("expected.json")
    unchanged = expected == format_json(case.load("target.json"))
    assert run_cli(*case.flags(), "-q", template, target)[0] == (0 if unchanged else 1)
    assert run_cli(*case.flags(), "push", "-q", template, target)[0] == 0
    if not unchanged:
        assert target.read_text() == expected
    assert run_cli(*case.flags(), template, target) == (0, "", "")
    stamp = os.stat(target).st_mtime_ns
    assert run_cli(*case.flags(), "push", template, target) == (0, "", "")
    assert os.stat(target).st_mtime_ns == stamp


@pytest.mark.parametrize("case", PULL_CASES)
def test_pull_fixture_cases(case, tmp_path, run_cli, monkeypatch):
    case.apply_env(monkeypatch)
    template, target = materialize(case, tmp_path)
    assert run_cli(*case.flags(), "pull", "-q", template, target)[0] == 0
    assert format_json(json.loads(template.read_text())) == case.text("expected.json")
    assert run_cli(*case.flags(), "pull", "--diff", template, target) == (0, "", "")


def test_push_keeps_file_mode(tmp_path, run_cli):
    template, target = workspace(tmp_path, {"a": 1}, {})
    target.chmod(0o600)
    run_cli("push", "-q", template, target)
    assert stat.S_IMODE(target.stat().st_mode) == 0o600


def test_push_through_symlink(tmp_path, run_cli):
    template = tmp_path / "template.json"
    write_json(template, {"a": 1})
    real = tmp_path / "dotfiles" / "settings.json"
    write_json(real, {})
    link = tmp_path / "live.json"
    link.symlink_to(real)
    run_cli("push", "-q", template, link)
    assert link.is_symlink()
    assert '"a": 1' in real.read_text()


def test_same_file_through_symlink_is_rejected(tmp_path, run_cli):
    template, _ = workspace(tmp_path, {"a": 1})
    link = tmp_path / "link.json"
    link.symlink_to(template)
    code, _, err = run_cli("push", template, link)
    assert code == 2
    assert "are the same file" in err


@pytest.mark.parametrize(
    "error,expected",
    [
        (
            OSError(28, "No space left on device", "somewhere/target.json"),
            "fsettings: somewhere/target.json: No space left on device\n",
        ),
        (OSError(28, "No space left on device"), "fsettings: No space left on device\n"),
        (OSError("odd failure"), "fsettings: odd failure\n"),
    ],
)
def test_write_error_is_reported(tmp_path, run_cli, monkeypatch, error, expected):
    template, target = workspace(tmp_path, {"a": 1}, {"b": 2})
    before = digest(target)

    def boom(*args, **kwargs):
        raise error

    monkeypatch.setattr(os, "replace", boom)
    code, _, err = run_cli("push", "-q", template, target)
    assert (code, err) == (2, expected)
    monkeypatch.undo()
    assert digest(target) == before
    assert sorted(p.name for p in tmp_path.iterdir()) == ["target.json", "template.json"]


def test_ported_prototype_scenarios(tmp_path, run_cli):
    template, target = tmp_path / "template.json", tmp_path / "target.json"
    write_json(template, {
        "allowNonWorkspaceAccess": True,
        "enableTerminalSandbox": False,
        "title": {"command": "~/.gemini/title-command.sh", "enabled": True},
        "trustedWorkspaces": [],
    })
    write_json(target, {
        "model": "gemini-test",
        "trustedWorkspaces": ["/private/project/path"],
        "permissions": {"allow": ["command(cat)", "command(python3 /home/tester/private.py)"]},
    })
    before = digest(target)
    assert run_cli(template, target)[0] == 1
    assert digest(target) == before
    assert run_cli("push", template, target)[0] == 0
    assert run_cli("-q", template, target)[0] == 0
    text = target.read_text()
    assert "/private/project/path" in text
    assert "command(cat)" in text
    assert "gemini-test" in text
    assert '"command": "/home/tester/.gemini/title-command.sh"' in text

    write_json(template, {"allowNonWorkspaceAccess": True, "=!trustedWorkspaces": ["~"]})
    assert run_cli("apply", template, target)[0] == 0
    text = target.read_text()
    assert "/private/project/path" not in text
    assert '"trustedWorkspaces"' in text and '"=!' not in text

    write_json(target, {
        "allowNonWorkspaceAccess": True,
        "permissions": {"allow": [
            "command(git status)", "command(ls)",
            "command(python3 /home/tester/.gemini/scratch.py)",
            "command(git -C /home/tester/project log)",
        ]},
        "trustedWorkspaces": ["/home/tester/work"],
    })
    write_json(template, {})
    assert run_cli("pull", template, target)[0] == 0
    pulled = template.read_text()
    assert "command(git status)" in pulled and "command(ls)" in pulled
    assert "/home/tester" not in pulled and "project" not in pulled

    code, out, _ = run_cli("missing", template, target)
    assert code == 0
    assert "trustedWorkspaces" in out


def test_python_dash_m_entry_point(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["fsettings", "--version"])
    with pytest.raises(SystemExit) as info:
        runpy.run_module("frankensettings", run_name="__main__")
    assert info.value.code == 0
    assert capsys.readouterr().out == f"fsettings {frankensettings.__version__}\n"


def test_repo_root_is_the_project():
    assert (ROOT / "frankensettings" / "cli.py").exists()
