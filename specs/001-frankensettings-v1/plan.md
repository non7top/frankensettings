# Implementation Plan: frankensettings v1

**Branch**: `001-frankensettings-v1` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-frankensettings-v1/spec.md`

## Summary

Turn the single-file prototype into a packaged, typed, stdlib-only Python library and CLI, fix the
gaps the spec lists, cover it with a fixture-driven pytest suite gated at 100% line and branch
coverage, and ship it to PyPI through the same release-please, attestation, cosign and trusted
publishing pipeline the maintainer's sibling repos use (antigravity-wakeup, claude-chatter).

## Technical Context

**Language/Version**: Python >=3.10, tested on 3.10 to 3.14

**Primary Dependencies**: none at runtime (stdlib: argparse, json, difflib, os, pathlib, re, tempfile, shutil, importlib.metadata)

**Storage**: JSON files on disk

**Testing**: pytest, pytest-cov (branch coverage, fail-under 100), flake8; run by the build workflow, locally through act

**Target Platform**: Linux and macOS (POSIX)

**Project Type**: library + CLI

**Performance Goals**: files are small (KB); full suite under 60 s per Python version

**Constraints**: zero runtime deps; atomic, mode-preserving writes; no network; deterministic output

**Scale/Scope**: about 400 lines of library code in 6 modules, about 150 tests, about 70 fixture directories

## Constitution Check

| Principle | Status | How the plan satisfies it |
|---|---|---|
| I. Standard library only | Pass | `dependencies = []`; dev tools only in the `dev` extra and the test image |
| II. Private data never reaches the template | Pass | one scrub path in `pull.py` and `privacy.py`; SC-004 leak scan over every pull fixture; FR-065 scan of all tracked text for local paths, emails and IPs |
| III. Atomic, honest, minimal writes | Pass | single `fileio.write_atomic`; failure-injection tests; no write when unchanged |
| IV. Test-first at 100% | Pass | tasks put tests before code per story; `--cov-fail-under=100 --cov-branch` in Makefile and CI |
| V. Deterministic, idempotent | Pass | idempotence and non-mutation tests run over every fixture |
| VI. Stable CLI contract | Pass | contracts/cli.md is the source of truth; contract tests assert it |
| VII. CI is the only build path, signed releases | Pass | Makefile targets run .github/workflows/build.yml with act; release.yml adapted from the siblings (setup-python build instead of container build) |

No violations; Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/001-frankensettings-v1/
  spec.md
  plan.md
  research.md
  data-model.md
  quickstart.md
  test-plan.md
  tasks.md
  contracts/
    cli.md
    library-api.md
  checklists/
    requirements.md
```

### Source Code (repository root)

```text
frankensettings/
  __init__.py        # public API re-exports, __version__
  __main__.py        # python -m frankensettings
  py.typed
  cli.py             # argparse, subcommand dispatch, exit codes, error line
  merge.py           # deep_merge, replace keys, exclusions
  pull.py            # pull_merge
  paths.py           # expand_env, collapse_env
  privacy.py         # is_private_permission and its patterns
  report.py          # find_keys, missing_report
  fileio.py          # load_json, format_json, write_atomic, unified_diff, InputError
tests/
  conftest.py        # fake_home, run_cli, fixture discovery
  test_merge.py  test_pull.py  test_paths.py  test_privacy.py  test_report.py
  test_fileio.py  test_cli.py  test_cli_flags.py  test_packaging.py  test_traceability.py
  test_smoke_subprocess.py
  fixtures/
    merge/<case>/    template.json target.json expected.json [args.json]
    pull/<case>/     template.json target.json expected.json [args.json]
    missing/<case>/  template.json target.json expected.txt  [args.json]
    invalid/<case>/  input file + expected_error.txt
.github/
  workflows/  build.yml  conventional-commits.yml  release-please.yml
              release-please-preview.yml  release.yml
  dependabot.yml  repo-config.json
docs/
  releasing.md       # PyPI pending publisher, first release checklist
Makefile  pyproject.toml  README.md  LICENSE  CHANGELOG.md
release-please-config.json  .release-please-manifest.json  .flake8  .dockerignore  .gitignore
```

**Structure Decision**: flat package next to `pyproject.toml` with setuptools, as in antigravity-wakeup
(maintainer-confirmed). The prototype `fsettings` script and `tests/test_fsettings.sh` are deleted
once every assertion is ported (FR-064). `project.md` content moves into the README.

## Delivery order

1. Repo bootstrap on a branch (pyproject, Docker, Makefile, lint), empty package, red-green harness.
2. Test infrastructure and fixtures for paths, privacy, fileio (foundation).
3. Stories in priority order, each: fixtures and tests first, see them fail, implement, see 100% for that module.
4. Packaging, README as long description, docs, `twine check`.
5. CI and release workflows copied from siblings, run with `act`, then PR.
6. Maintainer steps (outside the repo): create repo, register PyPI pending publisher, merge, merge the release PR.

## Release pipeline (mirrors the siblings)

- `release-please.yml` and `release-please-preview.yml` call `non7top/gh-workflows` at `@main` (same as siblings); config `release-type: python`, `bump-minor-pre-major: true`, manifest starts at `0.0.0` so the first `feat:` yields v0.1.0 (siblings went Initial commit, feat PR, release PR, v0.1.0).
- `release.yml` is identical to the siblings': check-release-tag, release (make build, make package, attest, cosign, `gh release upload`), pypi (environment `pypi`, `id-token: write`, version-equals-tag check, `pypa/gh-action-pypi-publish`). Action versions follow whatever the siblings pin at copy time.
- `make package` gains `twine check --strict dist/*` (siblings only build); `twine` joins the test image.
- Trusted publishing needs no secret. Maintainer registers the pending publisher on pypi.org (project `frankensettings`, owner `non7top`, repo `frankensettings`, workflow `release.yml`, environment `pypi`) before the first stable tag; docs/releasing.md has the checklist.
- Repo settings come from `.github/repo-config.json` (applied with the maintainer's gh-repo-config tool), same ruleset as siblings: PR required to master, merge commits allowed, `pypi` environment declared.

## Open risks

- release-please bootstrap on a repo with no tags: confirm the first release PR proposes 0.1.0 and not 1.0.0 (a dry run with the preview workflow on the first PR settles it).
- Python 3.14 in the test matrix needs an official `python:3.14-slim` image; if unavailable at implementation time the matrix tops out at 3.13 and the spec's SC-003 and classifiers are adjusted in the same PR.

## Complexity Tracking

None.
