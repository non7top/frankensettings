# Data Model: frankensettings v1

## Documents

- **Settings document**: UTF-8 JSON whose top level is an object. Empty or whitespace-only file = `{}`. Anything else at the top level (array, string, number, null) is an input error. Duplicate keys: last wins.
- **Template**: a settings document that may additionally contain replace keys.
- **Target**: a settings document written by a host tool.

## Key forms in a template

| Form | Meaning |
|---|---|
| `key` | merge into target (objects deep, lists union, scalars replace) |
| `=!key` or `=key` | replace target value wholesale; bypasses exclusions; written as `key` |
| `=!` / `=` (empty name) | input error |
| `key` and `=!key` in the same object | input error naming the path |

## Merge table (template value T onto target value G, key not excluded, no replace marker)

| T | G | Result |
|---|---|---|
| object | object | recursive merge (G order, then new keys in T order) |
| non-empty list | list | G items, then T items not in G (value equality, T duplicates collapsed) |
| empty list | list | G unchanged |
| anything | missing | T (expanded) |
| anything else | anything | T (expanded) |

## Pull table (target value G onto template value T, key not excluded)

| G | T | Result |
|---|---|---|
| object | object | recursive pull |
| anything else | anything | G (collapsed; permission filter applied for `permissions.allow`) |
| any | missing | G (collapsed) |
| (key absent) | present | T kept |

Replace-marker template keys match target keys by stripped name and keep their original spelling.

## Exclusion set

Set of key names; matched at every depth by exact name. Default `{"trustedWorkspaces"}`. Built from `-e` (replaces default), `--no-exclude` and `-e ""` / `-e []` (empty).

## Path rules

| Direction | Input | Output |
|---|---|---|
| expand (push) | `~` | `$HOME` |
| expand | `~/x` | `$HOME/x` |
| expand | `$HOME/x`, `${HOME}/x`, any set `$VAR` | substituted |
| expand | `~bob/x`, unset `$VAR`, HOME unset | unchanged |
| collapse (pull) | `$HOME` | `~` |
| collapse | `$HOME/x` | `~/x` |
| collapse | `$HOME2/x` (longer sibling), HOME unset | unchanged |

Only string values are transformed, never keys; recursion through lists and objects.

## Private permission rule (FR-023)

A string is private when, case-insensitively, it contains `/home/`, `/tmp/`, `/users/`, `~/`, `git -c` or `-c /`, or matches the absolute-path token pattern (a `/` at start, or after whitespace, `(`, `=`, `"` or `'`, followed by a character other than `/`, whitespace, `)` or end), or contains `$HOME` or `${HOME}`. Non-strings are never private. URLs (`https://host/path`) and regex or sed text (`s/a/b/`) must not match; fixtures pin both.

## Missing report

Key paths: dotted names over nested objects; lists and scalars are leaves; template names have replace prefixes stripped. Groups: missing from target (in template, not in target, not excluded), missing from template (in target, not in template, not excluded), excluded present (in target, any segment excluded).

## Exit codes and streams

| Situation | stdout | stderr | exit |
|---|---|---|---|
| diff clean / push, apply, pull done / missing | diff or report | - | 0 |
| diff or pull --diff with changes | unified diff (unless -q) | - | 1 |
| usage or input error | - | one line `fsettings: ...` (argparse usage for usage errors) | 2 |
