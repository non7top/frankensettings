# Tasks: frankensettings v1

**Input**: specs/001-frankensettings-v1 (spec.md, plan.md, research.md, data-model.md, contracts/, test-plan.md)

**Tests**: required and written first (Constitution IV). Each story: fixtures and tests, watch them fail, then implement.

**Format**: `[ID] [P?] [Story] Description`; [P] = different files, no dependency on an unfinished task.

**Git rules for every task**: work on a branch, never on master; atomic commits by explicit path with Conventional Commit messages; the one push to master that seeds an empty remote needs the maintainer's explicit go-ahead; merging needs a separate go-ahead.

## Phase 0: Repo bootstrap (maintainer-gated)

- [x] T001 Ask the maintainer to approve creating the public repo `non7top/frankensettings` (default branch master) and how to seed the empty remote (the first push of master is the one allowed push to a default branch)
- [x] T002 `git init` (branch name from `git config --global init.defaultBranch`, currently master), add `.gitignore` (siblings' plus `.claude/` and `.specify/` local state review), initial commit of LICENSE, .gitignore and the spec-kit scaffolding
- [x] T003 Create branch `feat/frankensettings-v1` for all following work

## Phase 1: Setup

- [x] T004 [P] LICENSE (MIT, 2026, same holder line as the sibling repos), CHANGELOG.md placeholder, .flake8, .dockerignore, .gitignore
- [x] T005 [P] pyproject.toml: setuptools, name frankensettings, version 0.0.0, the FR-051 description string, readme, MIT, requires-python >=3.10, keywords, classifiers, URLs, scripts, `dev` extra (pytest, pytest-cov, flake8, build, twine), `[tool.pytest.ini_options]` and `[tool.coverage.*]` (branch = true, fail_under = 100, source = frankensettings)
- [x] T006 [P] Makefile whose targets run the build workflow with act (test, test-all, lint, package, check, clean); no Dockerfile or compose file, the act job container is the throwaway environment
- [x] T007 Empty package `frankensettings/__init__.py`, `py.typed`, `__main__.py`; `make build lint test` run green on an empty suite with the coverage gate configured (gate expected to pass vacuously)

## Phase 2: Foundation (blocks all stories)

- [x] T008 tests/conftest.py: fake_home, run_cli, cases(area), materialize (test-plan.md harness)
- [x] T009 [P] tests/test_public_text.py (FR-065) and tests/test_traceability.py (SC-002): they must fail loudly now (no FR rows implemented), then guard every later commit
- [x] T010 [P] tests/test_paths.py and tests/test_privacy.py tables (FR-015, FR-022, FR-023), then `frankensettings/paths.py` and `privacy.py`
- [x] T011 [P] tests/test_fileio.py (FR-040..044 file level: load, format, atomic write with failure injection, mode, symlink, parent dirs), then `frankensettings/fileio.py` including `InputError` and the diff helper

**Checkpoint**: foundation modules at 100% in isolation

## Phase 3: User Story 1 - push (P1) MVP

**Independent test**: merge fixture sweep plus CLI push on a fixture.

- [x] T012 [P] [US1] Create all fixtures/merge/* cases from test-plan.md (template, target, expected, args)
- [x] T013 [US1] tests/test_merge.py: sweep, non-mutation, idempotence, ambiguous replace keys (FR-010..017, FR-045)
- [x] T014 [US1] `frankensettings/merge.py` `deep_merge` until T013 passes
- [x] T015 [P] [US1] tests/test_cli_flags.py: global flags in any position, default-diff shim regression, exclude parsing (FR-002, FR-003, FR-017)
- [x] T016 [US1] `frankensettings/cli.py`: parser with parent options, `parse_excludes`, push and apply, error line, exit codes, `--version`
- [x] T017 [US1] tests/test_cli.py push scenarios (FR-001, FR-004..006, FR-042, ported prototype scenarios FR-064 for push)

## Phase 4: User Story 2 - diff (P1)

- [x] T018 [US2] tests/test_cli.py diff scenarios: drift exit 1, clean exit 0, no write (bytes and mtime), formatting-only difference, quiet, labels, missing target as empty (FR-004, FR-005, FR-042, FR-044)
- [x] T019 [US2] diff in cli.py plus default-subcommand logic until green

## Phase 5: User Story 5 - safe failures (P1)

- [x] T020 [P] [US5] fixtures/invalid/* cases
- [x] T021 [US5] tests/test_cli.py::test_invalid_fixtures, error-line format, usage errors, same-path, directory path (FR-006, FR-040, FR-044, FR-045)
- [x] T022 [US5] wire InputError handling and mode and symlink behaviour end to end until green (CLI level mode and symlink tests)

**Checkpoint**: push, diff and failure paths complete; MVP usable from a source checkout

## Phase 6: User Story 3 - pull (P2)

- [x] T023 [P] [US3] fixtures/pull/* cases (at least 25 private-marker cases for SC-004)
- [x] T024 [US3] tests/test_pull.py: sweep, non-mutation, round trip with no leak, leak scan (FR-020..025, FR-063)
- [x] T025 [US3] `frankensettings/pull.py` `pull_merge` incl. replace-key handling and permission filter
- [x] T026 [US3] tests/test_cli.py pull scenarios (dry-run, --diff before and after subcommand, bootstrap template, missing target error) then cli.py pull

## Phase 7: User Story 4 - missing (P3)

- [x] T027 [P] [US4] fixtures/missing/* cases
- [x] T028 [US4] tests/test_report.py then `frankensettings/report.py` and the cli subcommand (FR-030, FR-031)

## Phase 8: User Story 6 - PyPI-ready package (P2)

- [x] T029 [P] [US6] README.md as the long description: problem, install (pipx, uv tool, uvx), quick start, all four commands, merge rules, replace keys, path expansion, exclusions and the `-e` replace-not-add warning, permission scrubbing, exit codes, security note, limits (JSONC, Windows), badges; placeholders only
- [x] T030 [P] [US6] `__init__.py` public API and `__version__`; tests/test_packaging.py
- [x] T031 [US6] tests/test_smoke_subprocess.py and a container step that builds the wheel, installs it into a clean venv per Python version and runs it (SC-005)
- [x] T032 [US6] `make package` with `twine check --strict`; fix any rendering warnings
- [x] T033 [US6] `make test-all` on 3.10 to 3.14 at 100%; fix version-specific failures

## Phase 9: User Story 7 - release pipeline (P3)

- [x] T034 [P] [US7] .github/workflows: build.yml (lint, matrix test, package), conventional-commits.yml, release-please.yml, release-please-preview.yml, release.yml, copied from [non7top/antigravity-wakeup](https://github.com/non7top/antigravity-wakeup) with only the project-specific names changed; pin actions as the sibling pins them
- [x] T035 [P] [US7] release-please-config.json (python, bump-minor-pre-major), .release-please-manifest.json at 0.0.0, .github/dependabot.yml, .github/repo-config.json (description, topics, ruleset, labels, `pypi` environment)
- [x] T036 [US7] docs/releasing.md: one-time PyPI pending publisher, first-release checklist, how to verify cosign and attestation, how to yank
- [ ] T037 [US7] build.yml runs locally with act (done: lint, test matrix, package all green); still to run: release.yml up to the PyPI job, and confirm the tag-vs-version check fails on a mismatched tag
- [x] T038 [US7] tests/test_packaging.py workflow and docs presence tests (FR-054..056)

## Phase 10: Cleanup and landing

- [x] T039 Run the full suite once with output to a file (`make test-all`), read failures, fix, rerun only failing tests
- [ ] T040 Port check done (test_ported_prototype_scenarios); remove the prototype script and project.md in their own commit after importing them once so history keeps them (the bash test is dropped: it names a real local path)
- [ ] T041 Public-text scan: run test_public_text, grep specs and docs for local paths; check repo visibility before any push
- [ ] T042 Open the PR (ready for review) with the spec summary; do not merge
- [ ] T043 After the maintainer merges: verify the release-please PR proposes 0.1.0, maintainer registers the PyPI pending publisher, merge the release PR (explicit go-ahead), check the Release run, then verify `uvx frankensettings --version` from PyPI

## Dependencies

- Phase 0 -> 1 -> 2 -> stories. US1 -> US2 -> US5 share cli.py and run in that order; US3 and US4 depend on Phase 2 and on cli.py from US1 but not on each other.
- US6 needs US1-US5 (pull and missing can land after the first wheel build, but v0.1.0 ships all five).
- US7 can start after T007 (workflow files do not depend on behaviour) but T037 needs T032.
- Within a story: fixtures [P], tests, implementation. A story is done when its modules show 100% and traceability rows exist.
