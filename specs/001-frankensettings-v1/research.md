# Research: frankensettings v1

Evidence gathered on 2026-11-26. "Prototype" means the `fsettings` script in the repo root.

## Prototype gaps reproduced in a throwaway container (python:3.13-slim, source mounted read-only)

| # | Observation | Resulting requirement |
|---|---|---|
| 1 | `fsettings pull --diff t g` (the project.md example) fails: "unrecognized arguments: --diff", exit 2. Same for `-q` after the subcommand. | FR-003 |
| 2 | `fsettings -e foo t g` fails: the default-diff shim takes the option value `foo` for the first positional and inserts `diff` before it. | FR-002, FR-003 |
| 3 | Invalid JSON prints a raw `JSONDecodeError` traceback. | FR-006, FR-040 |
| 4 | `pull` with template key `=!trustedWorkspaces` appends a second, unprefixed `trustedWorkspaces` next to it. | FR-024 |
| 5 | `push` onto a mode 0600 target leaves 0644. | FR-043 |
| 6 | Template `"p": "~"` is written as `"~"` (collapse maps home to `~`, expand does not map it back). | FR-015 |
| 7 | Template `"l": []` keeps the target list (kept, documented). | FR-011 |
| 8 | `missing` always exits 0; a `=!key` template key is reported under its raw name and escapes the exclusion check. | FR-031 |

Also read from the code (not run): `--dry-run` promised by project.md does not exist; exclusion in `missing`
tests only the first path segment while merge and pull test every depth; a missing template is silently read as
{}; a top-level non-object JSON value is not rejected; private-rule detection is a fixed substring list, while
project.md promises "absolute paths".

## Decisions

- **Argument parsing**: one `argparse` parser; shared options live on a parent parser attached to every subparser, with `default=argparse.SUPPRESS` on subparsers so values given before the subcommand are not overwritten. Default-diff: `parse_known_args` first; if no subcommand is recognised, re-parse with `diff` prepended. Rationale: removes the hand-rolled first-non-flag scan that breaks on option values. Alternative rejected: click/typer (runtime dependency).
- **Atomic write**: `tempfile.NamedTemporaryFile(dir=dest.parent, delete=False)`, write, flush, `os.fsync`, `shutil.copymode` from the existing file (or default mode for a new file), `os.replace`, cleanup in `finally`. Destination resolved with `Path.resolve()` so symlinks survive.
- **Home handling**: use `os.environ["HOME"]` (not `expanduser` for the collapse) so tests control it with `monkeypatch.setenv`; expand uses the same variable for `~` so push and pull are symmetric.
- **Absolute-path detection** (FR-023): one compiled regex over the rule text for the path-token case plus the fixed substring list from the prototype, so nothing the prototype scrubbed is let through.
- **Comparison on parsed content**: serialise both sides with the same formatter and compare strings (this is what the prototype does and is order-sensitive for objects; kept, since key order is part of the output contract in Principle V).
- **Version source**: `pyproject.toml` static version (release-please `python` type bumps it), `__version__` via `importlib.metadata.version` with a fallback string for source checkouts.
- **JSONC**: deferred. VS Code's real `settings.json` allows comments; v1 fails clearly on them (exit 2, message names the line and column) and says so in the README. Worth a follow-up issue.
- **Test stack**: pytest with parametrisation over auto-discovered fixture directories; coverage via pytest-cov with `--cov-branch`; CLI in-process through `cli.main(argv)` with `capsys`, plus a handful of subprocess smoke tests (not counted toward coverage). Alternative rejected: unittest (siblings use it) because parametrised fixture sweeps are the core of this suite.
- **Local runs**: the Makefile runs the build workflow with `act` (image from the user's act config, `NODE_OPTIONS=--no-network-family-autoselection` for slow container connects, no bind mount so nothing is written to the checkout). Tests install the package with `pip install -e ".[dev]"` inside the job. Alternative rejected: a repo-owned Dockerfile and compose file (used by the sibling repos), because the job container already is the throwaway environment and CI would otherwise test a different setup than local runs.

## Sibling-repo facts used

Read from the public repos [non7top/antigravity-wakeup](https://github.com/non7top/antigravity-wakeup) (config, Makefile, Dockerfile, workflows) and [non7top/claude-chatter](https://github.com/non7top/claude-chatter) (release.yml only): setuptools backend, `[project.scripts]`, `release-please-config.json` with `release-type: python`, shared workflows in `non7top/gh-workflows`, `release.yml` (identical in claude-chatter, claude-chatter-mcp, antigravity-wakeup), `environments.pypi` in `repo-config.json`, Dependabot config, `.flake8`, Makefile targets and Dockerfile pattern. antigravity-wakeup history: Initial commit, feat PR, release-please PR, tag v0.1.0.
