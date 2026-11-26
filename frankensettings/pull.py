"""Target-into-template merge used by pull, with scrubbing of private data."""
import copy

from .merge import KeyConflictError, check_template, strip_prefix
from .paths import collapse_env
from .privacy import is_private_permission


def _scrub_permissions(permissions):
    return {
        key: [rule for rule in value if not is_private_permission(rule)]
        if key == "allow" and isinstance(value, list)
        else value
        for key, value in permissions.items()
    }


def _clean(value, excludes):
    """Scrub a target value that has no template counterpart to merge into."""
    if isinstance(value, dict):
        cleaned = {}
        _pull_into(cleaned, value, excludes)
        return cleaned
    if isinstance(value, list):
        return [_clean(item, excludes) for item in value]
    return collapse_env(value)


def _pull_into(result, target, excludes):
    spelled = {strip_prefix(raw)[0]: raw for raw in result}
    for key, value in target.items():
        if key.startswith("="):
            raise KeyConflictError(f"key '{key}' starts with '=' and cannot be stored in a template", "target")
        if key in excludes:
            if key not in spelled:
                if isinstance(value, list):
                    result[key] = []
                elif isinstance(value, dict):
                    result[key] = {}
            continue
        if key == "permissions" and isinstance(value, dict):
            value = _scrub_permissions(value)
        slot = spelled.get(key, key)
        if isinstance(value, dict):
            if not isinstance(result.get(slot), dict):
                result[slot] = {}
            _pull_into(result[slot], value, excludes)
        else:
            result[slot] = _clean(value, excludes)


def pull_merge(template, target, excludes):
    """Return template updated from target, minus excluded keys, with home collapsed to ~."""
    check_template(template)
    result = copy.deepcopy(template)
    _pull_into(result, target, frozenset(excludes))
    return result
