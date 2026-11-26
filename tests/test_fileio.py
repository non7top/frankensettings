import json
import os
import shutil
import stat
from pathlib import Path

import pytest

from frankensettings import fileio
from frankensettings.fileio import InputError, format_json, load_json, unified_diff, write_atomic

E_DIAERESIS = chr(0xEB)


def test_load_json_missing_not_required(tmp_path):
    assert load_json(tmp_path / "nope.json", required=False) == {}


def test_load_json_missing_required(tmp_path):
    with pytest.raises(InputError, match="no such file"):
        load_json(tmp_path / "nope.json", required=True)


@pytest.mark.parametrize("text", ["", "   \n\t\n"])
def test_load_json_empty_means_empty_object(tmp_path, text):
    path = tmp_path / "f.json"
    path.write_text(text)
    assert load_json(path, required=True) == {}


def test_load_json_accepts_bom(tmp_path):
    path = tmp_path / "f.json"
    path.write_bytes(b"\xef\xbb\xbf" + b'{"a": 1}')
    assert load_json(path, required=True) == {"a": 1}


def test_load_json_reads_utf8(tmp_path):
    path = tmp_path / "f.json"
    path.write_text('{"name": "Zo' + E_DIAERESIS + '"}', encoding="utf-8")
    assert load_json(path, required=True) == {"name": "Zo" + E_DIAERESIS}


def test_load_json_rejects_invalid_utf8(tmp_path):
    path = tmp_path / "f.json"
    path.write_bytes(b"\xff\xfe{}")
    with pytest.raises(InputError, match="not valid UTF-8"):
        load_json(path, required=True)


def test_load_json_rejects_directory(tmp_path):
    with pytest.raises(InputError, match="is a directory"):
        load_json(tmp_path, required=True)


def test_load_json_permission_denied(tmp_path, monkeypatch):
    path = tmp_path / "f.json"
    path.write_text("{}")

    def denied(self, *args, **kwargs):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(Path, "read_text", denied)
    with pytest.raises(InputError, match="permission denied"):
        load_json(path, required=True)


@pytest.mark.parametrize(
    "error,expected", [(OSError(5, "Input/output error"), "Input/output error"), (OSError("odd"), "odd")]
)
def test_load_json_other_os_errors(tmp_path, monkeypatch, error, expected):
    path = tmp_path / "f.json"
    path.write_text("{}")

    def boom(self, *args, **kwargs):
        raise error

    monkeypatch.setattr(Path, "read_text", boom)
    with pytest.raises(InputError, match=expected):
        load_json(path, required=True)


def test_load_json_invalid_json_reports_position(tmp_path):
    path = tmp_path / "f.json"
    path.write_text('{"a": }')
    with pytest.raises(InputError, match=r"invalid JSON: Expecting value \(line 1, column 7\)"):
        load_json(path, required=True)


@pytest.mark.parametrize(
    "text,kind",
    [("[1]", "list"), ('"x"', "string"), ("5", "number"), ("1.5", "number"), ("true", "boolean"), ("null", "null")],
)
def test_load_json_top_level_must_be_object(tmp_path, text, kind):
    path = tmp_path / "f.json"
    path.write_text(text)
    with pytest.raises(InputError, match=f"top level must be a JSON object, got {kind}"):
        load_json(path, required=True)


def test_format_json():
    text = format_json({"a": ["x", {"b": "Zo" + E_DIAERESIS}], "c": {}})
    expected = '{\n  "a": [\n    "x",\n    {\n      "b": "Zo' + E_DIAERESIS + '"\n    }\n  ],\n  "c": {}\n}\n'
    assert text == expected
    assert format_json({}) == "{}\n"


def test_unified_diff_labels():
    diff = unified_diff("a\n", "b\n", "old", "new")
    assert diff.startswith("--- old\n+++ new\n")
    assert "-a\n+b\n" in diff
    assert unified_diff("a\n", "a\n", "old", "new") == ""


def _listing(directory):
    return sorted(p.name for p in directory.iterdir())


def test_write_atomic_cases_new_file_creates_parents(tmp_path):
    dest = tmp_path / "deep" / "er" / "f.json"
    write_atomic(dest, '{"a": 1}\n')
    assert dest.read_text() == '{"a": 1}\n'
    assert _listing(dest.parent) == ["f.json"]


def test_write_atomic_cases_new_file_follows_umask(tmp_path):
    old = os.umask(0o022)
    try:
        write_atomic(tmp_path / "f.json", "x")
    finally:
        os.umask(old)
    assert stat.S_IMODE((tmp_path / "f.json").stat().st_mode) == 0o644


@pytest.mark.parametrize("mode", [0o600, 0o640, 0o444])
def test_write_atomic_cases_keeps_existing_mode(tmp_path, mode):
    dest = tmp_path / "f.json"
    dest.write_text("old")
    dest.chmod(mode)
    write_atomic(dest, "new")
    assert dest.read_text() == "new"
    assert stat.S_IMODE(dest.stat().st_mode) == mode
    assert _listing(tmp_path) == ["f.json"]


def test_write_atomic_cases_follows_symlink(tmp_path):
    real_dir = tmp_path / "dotfiles"
    real_dir.mkdir()
    real = real_dir / "settings.json"
    real.write_text("old")
    link = tmp_path / "live.json"
    link.symlink_to(real)
    write_atomic(link, "new")
    assert link.is_symlink()
    assert real.read_text() == "new"
    assert _listing(real_dir) == ["settings.json"]


def test_write_atomic_cases_dangling_symlink(tmp_path):
    real = tmp_path / "real.json"
    link = tmp_path / "live.json"
    link.symlink_to(real)
    write_atomic(link, "new")
    assert link.is_symlink()
    assert real.read_text() == "new"


@pytest.mark.parametrize("target", ["os.replace", "os.fsync", "shutil.copymode"])
def test_write_failure_leaves_original(tmp_path, monkeypatch, target):
    dest = tmp_path / "f.json"
    dest.write_text("old")
    dest.chmod(0o600)

    def boom(*args, **kwargs):
        raise OSError(28, "No space left on device")

    module, name = target.split(".")
    monkeypatch.setattr({"os": os, "shutil": shutil}[module], name, boom)
    with pytest.raises(OSError):
        write_atomic(dest, "new")
    monkeypatch.undo()
    assert dest.read_text() == "old"
    assert stat.S_IMODE(dest.stat().st_mode) == 0o600
    assert _listing(tmp_path) == ["f.json"]


def test_write_failure_for_new_file_leaves_nothing(tmp_path, monkeypatch):
    def boom(*args, **kwargs):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError):
        write_atomic(tmp_path / "f.json", "new")
    monkeypatch.undo()
    assert _listing(tmp_path) == []


def test_module_exports_input_error():
    assert issubclass(fileio.InputError, Exception)
    assert json.loads(format_json({"a": 1})) == {"a": 1}
