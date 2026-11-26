"""Reading, formatting, diffing and atomically writing JSON settings files."""
import difflib
import json
import os
import shutil
import tempfile
from pathlib import Path


class InputError(Exception):
    """A user-facing input problem; the message is what follows 'fsettings:'."""


_JSON_TYPE_NAMES = {list: "list", str: "string", bool: "boolean", int: "number", float: "number", type(None): "null"}


def load_json(path, *, required):
    """Read a settings object. A missing file is {} unless required; an empty file is {}."""
    p = Path(path)
    if not p.exists():
        if required:
            raise InputError(f"{path}: no such file")
        return {}
    if p.is_dir():
        raise InputError(f"{path}: is a directory")
    try:
        text = p.read_text(encoding="utf-8-sig")
    except PermissionError:
        raise InputError(f"{path}: permission denied") from None
    except UnicodeDecodeError:
        raise InputError(f"{path}: not valid UTF-8") from None
    except OSError as exc:
        raise InputError(f"{path}: {exc.strerror or exc}") from None
    if not text.strip():
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise InputError(f"{path}: invalid JSON: {exc.msg} (line {exc.lineno}, column {exc.colno})") from None
    if not isinstance(data, dict):
        raise InputError(f"{path}: top level must be a JSON object, got {_JSON_TYPE_NAMES[type(data)]}")
    return data


def format_json(data):
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def unified_diff(old_text, new_text, old_name, new_name):
    return "".join(
        difflib.unified_diff(
            old_text.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            fromfile=old_name,
            tofile=new_name,
        )
    )


def _current_umask():
    mask = os.umask(0)
    os.umask(mask)
    return mask


def write_atomic(path, content):
    """Replace path with content via a temp file in the same directory; keep mode, follow symlinks."""
    dest = Path(path).resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=dest.parent, prefix=f".{dest.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if dest.exists():
            shutil.copymode(dest, tmp)
        else:
            os.chmod(tmp, 0o666 & ~_current_umask())
        os.replace(tmp, dest)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
