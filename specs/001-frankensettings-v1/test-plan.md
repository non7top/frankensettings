# Test Plan: frankensettings v1

Gate: `pytest --cov` with `fail_under = 100` and branch coverage (from pyproject.toml) in the build workflow, locally via `make test` (Constitution IV).
Placeholders only: HOME is forced to `/home/tester`, other users are `alice` and `bob`, hosts use `example.com`.

## Harness (tests/conftest.py)

- `fake_home` (autouse): `monkeypatch.setenv("HOME", "/home/tester")`, clears variables other than the ones a test sets.
- `run_cli(*argv)`: calls `frankensettings.cli.main`, returns `(exit_code, stdout, stderr)` using `capsys`.
- `cases(area)`: discovers `tests/fixtures/<area>/*/`, yields ids and loaded files; a directory missing an expected file fails collection (so a fixture can never be silently skipped).
- `materialize(case, tmp_path)`: copies a case into `tmp_path` and returns template and target paths.

## Fixture catalog

Every case dir holds `template.json`, `target.json`, the expected output, and optional `args.json` (`{"exclude": [...], "no_exclude": false}`). A sweep test per area runs every case; per-case asserts live in the expected file, not in code.

### fixtures/merge (expected.json = target after push)

| Case | Pins |
|---|---|
| new-keys-appended | FR-010 order: target keys first, template-only keys after, in template order |
| scalar-overrides | FR-012 |
| nested-objects-merge | FR-010 recursion, three levels |
| list-union-order | FR-011 target first, template extras after |
| list-union-dedupe | FR-011 template duplicates collapsed; object items compared by value |
| list-empty-template-keeps-target | FR-011 and Edge Cases |
| list-nonempty-into-missing | FR-010 |
| type-mismatch-object-over-list | FR-012 (all six pairings of object, list, scalar, null) |
| null-and-false-values | FR-012 falsy values are not "missing" |
| replace-bang-list | FR-013 `=!allow` |
| replace-single-equals | FR-013 `=allow` |
| replace-nested-object | FR-013 at depth, prefix stripped at every level |
| replace-bypasses-exclude | FR-013 `=!trustedWorkspaces` |
| replace-with-empty | `=!k: []` clears a list |
| replace-expands-paths | FR-013 with FR-015 |
| exclude-keeps-target | FR-014 |
| exclude-initialises-list | FR-014 |
| exclude-initialises-object | FR-014 |
| exclude-scalar-not-initialised | FR-014 |
| exclude-nested-depth | FR-014 any depth |
| exclude-custom-names | FR-017 `-e a,b` and repeated `-e` |
| exclude-custom-drops-default | FR-017 default no longer protected |
| exclude-none | FR-017 `--no-exclude`, `-e ""`, `-e []` |
| expand-tilde-slash | FR-015 |
| expand-tilde-alone | FR-015 |
| expand-home-var-and-braces | FR-015 `$HOME` and `${HOME}` |
| expand-other-env-var | FR-015 set variable (via `args.json` env) |
| expand-unset-var-untouched | FR-015 |
| expand-other-user-untouched | `~bob/x` |
| expand-nested-lists-objects | FR-015 recursion |
| expand-ignores-keys-and-numbers | FR-015 |
| unicode-roundtrip | FR-041 |
| already-merged-noop | FR-042, FR-016 (expected equals target, no write) |
| target-missing-keys-only-template | FR-044 empty target |
| empty-template | no changes |

Home-unset behaviour (HOME removed from the environment) is a code test, not a fixture.

### fixtures/pull (expected.json = template after pull)

| Case | Pins |
|---|---|
| excluded-not-copied | FR-021 |
| excluded-placeholder-added-list / -object | FR-021 |
| excluded-nested | FR-021 any depth |
| collapse-home-string / -exact / -list / -nested | FR-022 |
| collapse-sibling-prefix-untouched | FR-022 boundary (alice vs alice2) |
| collapse-non-strings-untouched | FR-022 |
| perm-generic-kept | FR-023 `command(git status)`, `command(ls)` |
| perm-private-dropped-home / tmp / users / tilde / git-c / dash-c-slash | FR-023 each substring |
| perm-absolute-path-token-variants | FR-023 start, after space, after paren, after equals, after quote, `Read(/etc/hosts)` |
| perm-url-and-sed-kept | FR-023 negative: `WebFetch(domain:example.com)`, `command(curl https://example.com/a/b)`, `command(sed s/a/b/)` |
| perm-home-var-dropped | FR-023 `$HOME` |
| perm-mixed-case-dropped | FR-023 case-insensitive |
| perm-non-allow-keys-pass | FR-023 `deny`, `ask` untouched |
| perm-non-list-allow / perm-non-dict | FR-023 shape tolerance |
| perm-non-string-items-kept | FR-023 numbers and objects in the list |
| lists-replaced-not-unioned | FR-020 |
| template-only-keys-kept | FR-020 |
| new-target-keys-added | FR-020 |
| nested-merge | FR-020 |
| bang-key-updated-in-place | FR-024 |
| bang-key-excluded | FR-024 with FR-021 |
| single-equals-key-updated | FR-024 |
| template-empty-bootstrap | FR-025 (also CLI: missing template created) |
| no-change | FR-025 (no write) |

### fixtures/missing (expected.txt = stdout)

| Case | Pins |
|---|---|
| all-groups | FR-030 header, three groups, markers, sort order |
| none-missing | FR-030 "(none)" lines, excluded group omitted |
| nested-paths | FR-031 dotted paths, lists are leaves |
| bang-keys-normalised | FR-031 |
| excluded-any-depth | FR-031 |
| custom-excludes | FR-017 with FR-031 |

### fixtures/invalid (input file + expected_error.txt, exit 2)

| Case | Pins |
|---|---|
| bad-json-template / bad-json-target | FR-006, FR-040 message with line and column |
| top-level-array / scalar / null | FR-040 |
| bom-and-whitespace-only | FR-040 empty means {} |
| ambiguous-replace-keys | FR-045 |
| empty-replace-name | FR-045 |
| template-missing | FR-044 |
| target-missing-for-missing-cmd | FR-044 |
| same-path | FR-044 |
| directory-as-target | FR-006 |

## Test modules

| Module | Covers |
|---|---|
| test_paths.py | expand and collapse unit cases beyond fixtures, HOME unset, parametrised table |
| test_privacy.py | is_private_permission truth table (non-strings, each pattern, negatives) |
| test_merge.py | fixture sweep; non-mutation of inputs (deepcopy compare); idempotence (merge twice); replace-key errors |
| test_pull.py | fixture sweep; non-mutation; leak scan (SC-004); push-then-pull round trip leaves the template unchanged |
| test_report.py | fixture sweep; find_keys edge cases |
| test_fileio.py | load_json (missing, empty, BOM, directory, unreadable), format_json, write_atomic (new file, existing, mode 0600 kept, symlink followed, parent dirs created, `os.replace` failure leaves original and no temp, `fsync` failure same, temp name collision) |
| test_cli.py | each subcommand end to end on a fixture: exit codes, stdout labels, quiet, files untouched or written, default diff, apply alias, pull --diff, pull --dry-run, missing outputs, error lines, -h and --version, no args |
| test_cli_flags.py | every global flag before and after the subcommand and between positionals; `-e foo t g` default-diff shim regression; `--no-exclude`; combined and repeated `-e`; unknown option; missing positional |
| test_packaging.py | metadata of the installed distribution: name, description string, license, requires-python, no dependencies, classifiers, URLs, scripts entry, readme content type; `__version__` equals metadata; README contains required sections; LICENSE is MIT |
| test_public_text.py | FR-065 scan of all tracked text files |
| test_traceability.py | parses the table below; every FR in spec.md has a row, every row names an existing test function (SC-002) |
| test_smoke_subprocess.py | installed `fsettings` entry point and `python -m frankensettings`: version, push, diff exit 1 then 0 (excluded from coverage numbers) |

Ported from the prototype bash test (FR-064): default diff exits 1 and does not write; push makes diff clean; excluded private paths kept; permissions kept; unmanaged key kept; tilde expanded; `=!` wipes and strips prefix; pull keeps generic permissions and drops private ones; missing lists excluded keys. The prototype's real-looking home path is replaced by `/home/tester` in the ported fixtures.

## Failure-injection technique

`monkeypatch.setattr(os, "replace", boom)` and the same for `os.fsync` and `shutil.copymode`; assert the original bytes and mode are unchanged and `list(dir)` shows no extra files.

## Traceability (FR -> tests)

| FR | Tests |
|---|---|
| FR-001 | test_cli.py::test_subcommands_exist, test_cli.py::test_apply_is_push |
| FR-002 | test_cli_flags.py::test_default_subcommand_is_diff, test_cli_flags.py::test_default_diff_with_exclude_value |
| FR-003 | test_cli_flags.py::test_global_flags_any_position, test_cli_flags.py::test_pull_diff_after_subcommand |
| FR-004 | test_cli.py::test_exit_codes |
| FR-005 | test_cli.py::test_diff_labels, test_cli.py::test_quiet_suppresses_output_only |
| FR-006 | test_cli.py::test_invalid_fixtures, test_cli.py::test_usage_errors_exit_2 |
| FR-010 | test_merge.py::test_merge_fixtures |
| FR-011 | test_merge.py::test_merge_fixtures |
| FR-012 | test_merge.py::test_merge_fixtures |
| FR-013 | test_merge.py::test_merge_fixtures |
| FR-014 | test_merge.py::test_merge_fixtures |
| FR-015 | test_paths.py::test_expand_table, test_merge.py::test_merge_fixtures |
| FR-016 | test_merge.py::test_merge_does_not_mutate_inputs, test_merge.py::test_merge_is_idempotent |
| FR-017 | test_cli_flags.py::test_exclude_parsing, test_merge.py::test_merge_fixtures |
| FR-020 | test_pull.py::test_pull_fixtures |
| FR-021 | test_pull.py::test_pull_fixtures |
| FR-022 | test_paths.py::test_collapse_table, test_pull.py::test_pull_fixtures |
| FR-023 | test_privacy.py::test_private_rule_table, test_pull.py::test_pull_fixtures |
| FR-024 | test_pull.py::test_pull_fixtures |
| FR-025 | test_cli.py::test_pull_dry_run_does_not_write, test_cli.py::test_pull_creates_missing_template |
| FR-030 | test_report.py::test_missing_fixtures |
| FR-031 | test_report.py::test_missing_fixtures, test_cli.py::test_missing_exit_zero |
| FR-040 | test_fileio.py::test_load_json_top_level_must_be_object, test_cli.py::test_invalid_fixtures |
| FR-041 | test_fileio.py::test_format_json |
| FR-042 | test_cli.py::test_unchanged_result_not_written, test_cli.py::test_diff_ignores_formatting |
| FR-043 | test_fileio.py::test_write_atomic_cases_keeps_existing_mode, test_fileio.py::test_write_atomic_cases_follows_symlink, test_fileio.py::test_write_failure_leaves_original |
| FR-044 | test_cli.py::test_invalid_fixtures |
| FR-045 | test_merge.py::test_ambiguous_replace_keys |
| FR-050 | test_packaging.py::test_public_api_importable, test_packaging.py::test_version_matches_metadata |
| FR-051 | test_packaging.py::test_metadata |
| FR-052 | test_packaging.py::test_license_is_mit |
| FR-053 | test_packaging.py::test_readme_sections |
| FR-054 | test_packaging.py::test_makefile_targets |
| FR-055 | test_packaging.py::test_workflows_present |
| FR-056 | test_packaging.py::test_release_docs_present |
| FR-060 | enforced by --cov-fail-under=100 |
| FR-061 | conftest.py::cases (collection fails on an incomplete case) |
| FR-062 | test_cli.py::test_exit_codes, test_smoke_subprocess.py::test_entry_point_version |
| FR-063 | test_merge.py::test_merge_is_idempotent, test_pull.py::test_round_trip_no_leak, test_fileio.py::test_write_failure_leaves_original, test_fileio.py::test_write_atomic_cases_keeps_existing_mode |
| FR-064 | test_cli.py::test_ported_prototype_scenarios |
| FR-065 | test_public_text.py::test_no_private_text |

Success criteria mapping: SC-001 coverage gate, SC-002 test_traceability, SC-003 `make test-all` and the CI matrix, SC-004 test_pull.py::test_pull_leak_scan, SC-005 test_smoke_subprocess plus the package job, SC-006 `act` run then first real release, SC-007 README review (checklist item).
