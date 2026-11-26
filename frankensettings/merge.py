"""Template-into-target merge used by diff and push."""
import copy
import json

from .fileio import InputError
from .paths import expand_env


class KeyConflictError(InputError):
    """A template or target key cannot be handled; source is 'template' or 'target'."""

    def __init__(self, message, source):
        super().__init__(message)
        self.source = source


def strip_prefix(key):
    """Split a template key into (name, is_replace); '=!k' and '=k' both mean replace."""
    if key.startswith("=!"):
        return key[2:], True
    if key.startswith("="):
        return key[1:], True
    return key, False


def _join(path, name):
    return f"{path}.{name}" if path else name


def check_template(template, path=""):
    """Reject empty replace names and a key spelled both plain and with a replace prefix."""
    seen = {}
    for raw, value in template.items():
        name, replace = strip_prefix(raw)
        if not name:
            raise KeyConflictError(f"key '{_join(path, raw)}': empty name after replace prefix", "template")
        if name in seen:
            raise KeyConflictError(
                f"key '{_join(path, name)}': both '{seen[name]}' and '{raw}' present", "template"
            )
        seen[name] = raw
        if not replace and isinstance(value, dict):
            check_template(value, _join(path, name))


def _identity(item):
    return json.dumps(item, sort_keys=True, ensure_ascii=False)


def _union(current, extra):
    merged = list(current)
    seen = {_identity(item) for item in merged}
    for item in extra:
        ident = _identity(item)
        if ident not in seen:
            seen.add(ident)
            merged.append(item)
    return merged


def _merge_into(result, template, excludes):
    for raw_key, value in template.items():
        key, replace = strip_prefix(raw_key)
        expanded = expand_env(value)

        if replace:
            result[key] = expanded
        elif key in excludes:
            if key not in result:
                if isinstance(value, list):
                    result[key] = []
                elif isinstance(value, dict):
                    result[key] = {}
        elif isinstance(result.get(key), dict) and isinstance(expanded, dict):
            _merge_into(result[key], expanded, excludes)
        elif isinstance(result.get(key), list) and isinstance(expanded, list):
            if expanded:
                result[key] = _union(result[key], expanded)
        else:
            result[key] = expanded


def deep_merge(target, template, excludes):
    """Return target with template merged in; neither argument is modified."""
    check_template(template)
    result = copy.deepcopy(target)
    _merge_into(result, template, frozenset(excludes))
    return result
