import pytest

from frankensettings import is_private_permission

PRIVATE = [
    "command(python3 /home/tester/x.py)",
    "command(cat /tmp/x)",
    "Read(/Users/alice/x)",
    "COMMAND(CAT /HOME/TESTER/X)",
    "Read(/USERS/alice)",
    "Read(~/x/**)",
    "command(git -C project log)",
    "command(git -c core.pager=cat log)",
    "command(tool -c /conf)",
    "/start/of/rule",
    "command(cat /etc/hosts)",
    "command(x=/etc y)",
    "command(cat '/etc/hosts')",
    'command(cat "/etc/hosts")',
    "Read(//etc/hosts)",
    "command(cd (/etc))",
    "command(cat $HOME/x)",
    "command(cat ${HOME}/x)",
    "command(cat $home/x)",
]

GENERIC = [
    "command(git status)",
    "command(ls)",
    "command(ls /)",
    "WebFetch(domain:example.com)",
    "command(curl https://example.com/a/b)",
    "command(sed s/a/b/)",
    "command(echo a/b)",
    "command(echo $HOMEBREW_PREFIX)",
    "",
]

NOT_STRINGS = [None, 1, 1.5, True, [], {}, ["/home/tester/x"], {"a": "/home/tester/x"}]


@pytest.mark.parametrize("rule", PRIVATE)
def test_private_rule_table(rule):
    assert is_private_permission(rule) is True


@pytest.mark.parametrize("rule", GENERIC)
def test_generic_rules_are_kept(rule):
    assert is_private_permission(rule) is False


@pytest.mark.parametrize("value", NOT_STRINGS)
def test_non_strings_are_never_private(value):
    assert is_private_permission(value) is False
