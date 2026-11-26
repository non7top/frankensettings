# CLI contract: fsettings

```
fsettings [options] [diff|push|apply|pull|missing] TEMPLATE TARGET
fsettings --version | -h
```

(options may appear before or after the subcommand and between positionals)

| Option | Applies to | Meaning |
|---|---|---|
| `-e, --exclude NAMES` | all | comma separated, repeatable; replaces the default set; `""` or `[]` clears |
| `--no-exclude` | all | empty exclusion set |
| `-q, --quiet` | diff, push, apply, pull | suppress diff output; exit codes and writes unchanged |
| `--diff, --dry-run` | pull | print diff, write nothing; exit 1 if it would change |
| `--version` | - | print `fsettings <version>`, exit 0 |

No subcommand: `fsettings TEMPLATE TARGET` is `diff`.

## Per command

| Command | Reads | Writes | Stdout | Exit |
|---|---|---|---|---|
| diff | both | nothing | unified diff target vs merged | 0 clean, 1 drift |
| push, apply | both | target (atomic) if changed | unified diff | 0 |
| pull | both | template (atomic) if changed and not --diff | unified diff | 0, or with --diff 0 clean / 1 would change |
| missing | both | nothing | report (data-model.md) | 0 |

## Diff labels

diff: `TARGET` / `TARGET (merged)`; push, apply: `TARGET` / `TARGET (updated)`; pull: `TEMPLATE` / `TEMPLATE (pulled)`. A missing file diffs against `{}`.

## Errors (stderr, exit 2, no traceback)

```
fsettings: PATH: invalid JSON: Expecting ',' delimiter (line 3, column 5)
fsettings: PATH: top level must be a JSON object, got list
fsettings: PATH: no such file
fsettings: PATH: is a directory
fsettings: PATH: permission denied
fsettings: TEMPLATE and TARGET are the same file
fsettings: TEMPLATE: key 'a.b': both 'k' and '=!k' present
fsettings: TEMPLATE: key 'a': empty name after replace prefix
```

Usage errors (unknown option, missing positional) come from argparse: usage text plus one error line on stderr, exit 2.

## Stability

Everything above is the public contract (Constitution VI). Wording of error messages after the `fsettings: PATH:` prefix is not.
