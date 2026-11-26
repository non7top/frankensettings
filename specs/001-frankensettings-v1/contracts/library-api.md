# Library API: frankensettings

Importable without side effects; all functions are pure except `fileio` and `cli.main`. Typed (`py.typed`).

| Name | Module | Signature | Notes |
|---|---|---|---|
| `deep_merge` | merge | `(target: dict, template: dict, excludes: Collection[str]) -> dict` | never mutates inputs; raises `InputError` on ambiguous replace keys |
| `pull_merge` | pull | `(template: dict, target: dict, excludes: Collection[str]) -> dict` | scrubs per FR-021..024 |
| `expand_env` | paths | `(value: JSON) -> JSON` | FR-015 |
| `collapse_env` | paths | `(value: JSON) -> JSON` | FR-022 |
| `is_private_permission` | privacy | `(rule: object) -> bool` | FR-023 |
| `missing_report` | report | `(template: dict, target: dict, excludes, template_path, target_path) -> str` | FR-030, FR-031 |
| `parse_excludes` | cli | `(raw: list[str] or None, no_exclude: bool) -> set[str]` | FR-017 |
| `load_json` | fileio | `(path, *, required: bool) -> dict` | FR-040, FR-044 |
| `format_json` | fileio | `(data) -> str` | FR-041 |
| `write_atomic` | fileio | `(path, content: str) -> None` | FR-043 |
| `InputError` | fileio | `Exception` | message is the text after `fsettings:` |
| `main` | cli | `(argv: list[str] or None = None) -> int` | returns the exit code; does not call `sys.exit` |
| `__version__` | package | `str` | from metadata |

Semver applies to this table and to contracts/cli.md.
