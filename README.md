# frankensettings

[![PyPI](https://img.shields.io/pypi/v/frankensettings)](https://pypi.org/project/frankensettings/)
[![Python](https://img.shields.io/pypi/pyversions/frankensettings)](https://pypi.org/project/frankensettings/)
[![License: MIT](https://img.shields.io/pypi/l/frankensettings)](https://github.com/non7top/frankensettings/blob/master/LICENSE)

Keep one `settings.json` in sync between a public template in your dotfiles repo and the private live
file a tool actually reads: merge the template in, pull changes back, and scrub local paths on the way.
The command is `fsettings`. It has no dependencies and needs Python 3.10 or newer.

## The problem

Many developer tools and coding agents (Claude Code, VS Code, Cursor, Google Antigravity) keep all their
configuration in one `settings.json` with no include files and no `settings.d/` directory. That file mixes
two kinds of data:

- preferences you want on every machine and in version control (themes, status line commands, generic allowed commands);
- machine-local state (trusted workspace paths, approval history, local model choices).

Commit the file and you leak private paths. Leave it out of version control and you reconfigure every machine
by hand. `fsettings` treats the repo file as the public baseline and the live file as the target, and stitches
them together in both directions.

## Install

```bash
pipx install frankensettings        # or: uv tool install frankensettings
uvx frankensettings --version       # run without installing
```

## Quick start

```bash
# 1. See what would change (exit 1 if the live file differs from the merged template)
fsettings dotfiles/tool/settings.json ~/.config/tool/settings.json

# 2. Apply the template; unmanaged keys in the live file are kept
fsettings push dotfiles/tool/settings.json ~/.config/tool/settings.json

# 3. Pull a change made inside the tool back into the template, scrubbed
fsettings pull --dry-run dotfiles/tool/settings.json ~/.config/tool/settings.json
fsettings pull dotfiles/tool/settings.json ~/.config/tool/settings.json

# 4. Audit what each side lacks
fsettings missing dotfiles/tool/settings.json ~/.config/tool/settings.json
```

The order is always `TEMPLATE TARGET`. Without a command, `fsettings TEMPLATE TARGET` means `diff`.

## Commands

| Command | What it does | Writes | Exit code |
| --- | --- | --- | --- |
| `diff` (default) | prints a unified diff of the target against the merged result | nothing | 0 clean, 1 differs |
| `push`, `apply` | merges the template into the target, prints the diff | the target, atomically, only if it changed | 0 |
| `pull` | copies generic settings from the target into the template | the template, only if it changed | 0 (with `--diff` or `--dry-run`: 0 clean, 1 would change) |
| `missing` | lists template keys the target lacks, target keys the template does not manage, and excluded keys present | nothing | 0 |

Exit code 2 means a usage or input error (unreadable path, invalid JSON, top level not an object); the message is
one line on stderr and nothing is written.

Options can go anywhere on the command line: `-q` hides diffs (exit codes stay the same), `-e NAMES` and
`--no-exclude` set the exclusions, `--version`, `-h`.

## Merge rules (diff and push)

- **Objects** merge recursively. Keys only in the target stay, in their order; keys only in the template are appended.
- **Lists** are unioned: target items first, then template items not already present (compared by value). An empty
  list in the template leaves the target list alone.
- **Scalars and type changes**: the template value wins.
- **Replace keys**: a template key written as `"=!allow"` (or `"=allow"`) replaces the target value wholesale
  and is written without the prefix. Use it to reset a list, for example `"=!trustedWorkspaces": []`.
- **Paths**: a leading `~` and `$VAR` or `${VAR}` references in string values are expanded on push, so tools that do not
  understand `~` get absolute paths. Unset variables, `~otheruser` and dictionary keys are left alone.
- A key spelled both `k` and `=!k` in the same template object is an error.

Differences are detected on parsed content, so reformatting alone never counts as a change, and running push
twice writes nothing the second time.

## Pull: scrubbing

Pull starts from the template and applies the target's values on top, then removes private data:

- keys in the exclusion set are not copied (an empty list or object placeholder is added if the template lacks them);
- your home directory is collapsed back to `~` in string values;
- items of `permissions.allow` that reference machine-local places are dropped: paths under `/home/`, `/tmp/`,
  `/Users/`, `~/`, any other absolute path, `$HOME`, and `git -c` style overrides. Rules such as
  `command(git status)`, `WebFetch(domain:example.com)` stay;
- lists in the target replace the template's lists instead of being unioned;
- a template key written with `=!` keeps its prefix and is updated in place.

Review the diff before committing: scrubbing is a safety net, not a guarantee.

## Exclusions

By default `trustedWorkspaces` is excluded at any depth: push never changes it and pull never copies it.

```bash
fsettings -e trustedWorkspaces,approvals push template.json settings.json   # these names
fsettings --no-exclude push template.json settings.json                     # nothing excluded
```

Note that `-e` replaces the default list, it does not add to it. A replace key (`"=!name"`) in the template
overrides an exclusion.

## Use as a library

```python
from frankensettings import deep_merge, pull_merge

merged = deep_merge(target_dict, template_dict, excludes={"trustedWorkspaces"})
template_update = pull_merge(template_dict, target_dict, excludes={"trustedWorkspaces"})
```

Both return new dictionaries and never modify their arguments.

## Limits

- Input must be strict JSON. Files with comments or trailing commas (JSONC, as VS Code allows) are rejected with a
  clear error.
- Linux and macOS. Windows is not supported yet.
- Duplicate keys inside one JSON object: the last one wins.

## Security

fsettings reads and writes only the two files you name and makes no network connections. Writes go through a
temporary file in the same directory and an atomic rename, keep the file's permissions and follow symlinks.
Release files on GitHub carry build provenance and cosign signatures.

## Development

The Makefile runs the build workflow locally with [act](https://github.com/nektos/act), so local checks and CI
are the same jobs: `make test` (100% line and branch coverage required), `make test-all` (Python 3.10 to 3.14),
`make lint`, `make package`, `make check` (everything). See `docs/releasing.md` for how releases are cut.

## License

MIT
