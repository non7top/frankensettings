"""The fsettings command line."""
import argparse
import sys
from pathlib import Path

from . import __version__
from .fileio import InputError, format_json, load_json, unified_diff, write_atomic
from .merge import KeyConflictError, deep_merge
from .pull import pull_merge
from .report import missing_report

DEFAULT_EXCLUDES = ("trustedWorkspaces",)
COMMANDS = ("diff", "push", "apply", "pull", "missing")

_DESCRIPTION = """\
Keep one settings file in sync between a public template and a private live file.

commands:
  diff     show what push would change; exit 1 if the target differs (default)
  push     merge the template into the target and write it atomically
  apply    alias for push
  pull     copy generic settings from the target back into the template,
           scrubbing excluded keys, home paths and private permission rules
  missing  list keys missing on either side and excluded keys present in the target

Template keys written as =!key or =key replace the target value instead of merging.
Exit codes: 0 ok or clean, 1 differences found (diff, pull --diff), 2 usage or input error.
"""


def parse_excludes(raw, no_exclude=False):
    """Build the exclusion set: -e replaces the defaults; '' and '[]' clear them."""
    if no_exclude:
        return set()
    if raw is None:
        return set(DEFAULT_EXCLUDES)
    names = set()
    for item in raw:
        for part in item.split(","):
            part = part.strip()
            if part and part != "[]":
                names.add(part)
    return names


def build_parser():
    parser = argparse.ArgumentParser(
        prog="fsettings",
        usage="fsettings [options] [COMMAND] TEMPLATE TARGET",
        description=_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("words", nargs="*", metavar="[COMMAND] TEMPLATE TARGET", help=argparse.SUPPRESS)
    parser.add_argument(
        "-e", "--exclude", action="append", metavar="NAMES",
        help="comma-separated key names to leave alone (repeatable); replaces the default"
        " (trustedWorkspaces), so list it again to keep it protected; '' or [] clears",
    )
    parser.add_argument("--no-exclude", action="store_true", help="exclude no keys at all")
    parser.add_argument("-q", "--quiet", action="store_true", help="do not print diffs; exit codes are unchanged")
    parser.add_argument(
        "--diff", "--dry-run", dest="dry_run", action="store_true",
        help="pull only: print the diff and do not write the template",
    )
    parser.add_argument("--version", action="version", version=f"fsettings {__version__}")
    return parser


def _same_file(first, second):
    return Path(first).resolve() == Path(second).resolve()


def _merge_or_conflict(action, template, target, template_path, target_path, excludes):
    try:
        return action(template, target, excludes)
    except KeyConflictError as exc:
        owner = template_path if exc.source == "template" else target_path
        raise InputError(f"{owner}: {exc}") from None


def _show(diff, quiet):
    if diff and not quiet:
        sys.stdout.write(diff)


def cmd_diff(template_path, target_path, excludes, quiet):
    template = load_json(template_path, required=True)
    target = load_json(target_path, required=False)
    merged = _merge_or_conflict(
        lambda t, g, x: deep_merge(g, t, x), template, target, template_path, target_path, excludes
    )
    old, new = format_json(target), format_json(merged)
    if old == new:
        return 0
    _show(unified_diff(old, new, str(target_path), f"{target_path} (merged)"), quiet)
    return 1


def cmd_push(template_path, target_path, excludes, quiet):
    template = load_json(template_path, required=True)
    target = load_json(target_path, required=False)
    merged = _merge_or_conflict(
        lambda t, g, x: deep_merge(g, t, x), template, target, template_path, target_path, excludes
    )
    old, new = format_json(target), format_json(merged)
    if old != new:
        _show(unified_diff(old, new, str(target_path), f"{target_path} (updated)"), quiet)
        write_atomic(target_path, new)
    return 0


def cmd_pull(template_path, target_path, excludes, quiet, dry_run):
    template = load_json(template_path, required=False)
    target = load_json(target_path, required=True)
    pulled = _merge_or_conflict(pull_merge, template, target, template_path, target_path, excludes)
    old, new = format_json(template), format_json(pulled)
    if old == new:
        return 0
    _show(unified_diff(old, new, str(template_path), f"{template_path} (pulled)"), quiet)
    if dry_run:
        return 1
    write_atomic(template_path, new)
    return 0


def cmd_missing(template_path, target_path, excludes):
    template = load_json(template_path, required=True)
    target = load_json(target_path, required=True)
    sys.stdout.write(missing_report(template, target, excludes, template_path, target_path))
    return 0


def _parse(argv):
    parser = build_parser()
    args = parser.parse_intermixed_args(argv)
    words = list(args.words)
    command = "diff"
    if words and words[0] in COMMANDS:
        command = words.pop(0)
    if len(words) != 2:
        parser.error("expected TEMPLATE and TARGET after the optional command")
    if args.dry_run and command != "pull":
        parser.error("--diff and --dry-run only apply to pull")
    return command, words[0], words[1], args


def _run(command, template_path, target_path, args):
    if _same_file(template_path, target_path):
        raise InputError(f"{template_path} and {target_path} are the same file")
    excludes = parse_excludes(args.exclude, args.no_exclude)
    if command == "diff":
        return cmd_diff(template_path, target_path, excludes, args.quiet)
    if command in ("push", "apply"):
        return cmd_push(template_path, target_path, excludes, args.quiet)
    if command == "pull":
        return cmd_pull(template_path, target_path, excludes, args.quiet, args.dry_run)
    return cmd_missing(template_path, target_path, excludes)


def main(argv=None):
    """Run the command and return its exit code."""
    try:
        command, template_path, target_path, args = _parse(argv)
    except SystemExit as exc:
        return exc.code
    try:
        return _run(command, template_path, target_path, args)
    except InputError as exc:
        message = str(exc)
    except OSError as exc:
        message = ": ".join(str(part) for part in (exc.filename, exc.strerror or exc) if part)
    print(f"fsettings: {message}", file=sys.stderr)
    return 2
