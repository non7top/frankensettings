"""Home-directory expansion on push and collapse on pull."""
import os


def _home():
    return os.environ.get("HOME", "").rstrip("/")


def expand_env(value):
    """Expand a leading ~ and $VAR or ${VAR} in string values, recursively. Keys are never touched."""
    if isinstance(value, str):
        home = _home()
        if home and (value == "~" or value.startswith("~/")):
            return home + os.path.expandvars(value[1:])
        return os.path.expandvars(value)
    if isinstance(value, dict):
        return {k: expand_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [expand_env(v) for v in value]
    return value


def collapse_env(value):
    """Replace the home directory with ~ at the start of string values, recursively."""
    home = _home()
    if not home:
        return value
    if isinstance(value, str):
        if value == home:
            return "~"
        if value.startswith(home + "/"):
            return "~" + value[len(home):]
        return value
    if isinstance(value, dict):
        return {k: collapse_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [collapse_env(v) for v in value]
    return value
