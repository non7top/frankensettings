"""Run the installed entry point and python -m as real subprocesses (not counted toward coverage)."""
import json
import os
import shutil
import subprocess
import sys

import frankensettings


def _run(argv, **kwargs):
    env = dict(os.environ, HOME="/home/tester")
    return subprocess.run(argv, capture_output=True, text=True, env=env, **kwargs)


def test_entry_point_version():
    exe = shutil.which("fsettings")
    assert exe, "fsettings is not on PATH; install the package first"
    result = _run([exe, "--version"])
    assert (result.returncode, result.stdout.strip()) == (0, f"fsettings {frankensettings.__version__}")


def test_python_dash_m_version():
    result = _run([sys.executable, "-m", "frankensettings", "--version"])
    assert (result.returncode, result.stdout.strip()) == (0, f"fsettings {frankensettings.__version__}")


def test_end_to_end_exit_codes(tmp_path):
    template, target = tmp_path / "template.json", tmp_path / "target.json"
    template.write_text(json.dumps({"theme": "dark", "bin": "~/bin"}))
    target.write_text(json.dumps({"model": "local"}))
    exe = shutil.which("fsettings")
    assert _run([exe, str(template), str(target)]).returncode == 1
    assert _run([exe, "push", "-q", str(template), str(target)]).returncode == 0
    assert _run([exe, str(template), str(target)]).returncode == 0
    assert json.loads(target.read_text()) == {"model": "local", "theme": "dark", "bin": "/home/tester/bin"}
    bad = tmp_path / "bad.json"
    bad.write_text("{")
    result = _run([exe, str(template), str(bad)])
    assert result.returncode == 2
    assert result.stderr.startswith("fsettings: ")
    assert "Traceback" not in result.stderr
