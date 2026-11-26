"""Detection of permission rules that reference machine-local locations."""
import re

_SUBSTRINGS = ("/home/", "/tmp/", "/users/", "~/", "git -c", "-c /")
# An absolute path token: / or // at the start or after whitespace, ( = or a quote, then a path character.
_ABSOLUTE_PATH = re.compile(r"""(?:^|[\s(="'])//?[^/\s)]""")
_HOME_VARIABLE = re.compile(r"\$\{?home\b")


def is_private_permission(rule):
    if not isinstance(rule, str):
        return False
    lowered = rule.lower()
    if any(part in lowered for part in _SUBSTRINGS):
        return True
    return bool(_ABSOLUTE_PATH.search(rule) or _HOME_VARIABLE.search(lowered))
