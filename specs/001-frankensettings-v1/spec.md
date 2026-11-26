# Feature Specification: frankensettings v1 (tested CLI and library, published on PyPI)

**Feature Branch**: `001-frankensettings-v1`

**Created**: 2026-11-26

**Status**: Draft

**Input**: User description: "explore project, speckify it. ask questions. be sure to add proper tests and fixtures for full coverage. plan to publish to pypi (see how we publish other projects). proper description, license MIT"

## Background

`fsettings` exists today as a single prototype script (`fsettings`, about 330 lines) plus one bash test.
This feature turns it into a maintained Python package: a library and the `fsettings` command, with
a fixture-driven test suite at 100% line and branch coverage, and a release pipeline that publishes
to PyPI the way the maintainer's other projects (claude-chatter, antigravity-wakeup) do.
Gaps found in the prototype by running it (project.md describes behaviour the prototype does not have)
are fixed here, not preserved. The maintainer confirmed: "fix all issues, the existing files are just
prototypes".

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Push a public template into a live settings file (Priority: P1)

A user keeps a settings template in their dotfiles repo. They run `fsettings push template.json
~/.tool/settings.json` and the live file gains the template's settings while keeping everything
only the host tool knows about (local model choice, trusted workspaces, tokens).

**Why this priority**: This is the reason the tool exists. Without it nothing else matters.

**Independent Test**: Run push on a template and target from a fixture directory and compare the
target with the expected file byte for byte. Needs no other story.

**Acceptance Scenarios**:

1. **Given** a template with new keys and a target with unrelated keys, **When** the user runs push, **Then** the target contains both, target key order is kept, new keys follow in template order, and the diff is printed.
2. **Given** a template list and a target list, **When** pushed, **Then** the result is the target items followed by template items not already present (set union, order preserved).
3. **Given** a template key written as `=!allow` or `=allow`, **When** pushed, **Then** the target value is replaced wholesale and the written file contains `allow` with no prefix.
4. **Given** a template value `"~/bin/x"`, `"~"` or `"$HOME/x"`, **When** pushed, **Then** the target holds the absolute path under the current user's home.
5. **Given** an excluded key (default `trustedWorkspaces`) in the template, **When** pushed, **Then** the target's value is untouched; if the target lacks it, an empty list or object is created to match the template value's type.
6. **Given** a target that already matches the merged result, **When** pushed, **Then** nothing is written, nothing is printed and the exit code is 0.

---

### User Story 2 - See what would change without writing (Priority: P1)

Before applying, or in a CI or login check, the user runs `fsettings template.json target.json` (or
`diff`) to see a unified diff and learn from the exit code whether the live file has drifted.

**Why this priority**: Makes push safe to trust and lets scripts detect drift.

**Independent Test**: Run diff on fixtures, assert stdout, exit code 1 on drift and 0 when clean, and
that the target file's bytes and mtime are unchanged.

**Acceptance Scenarios**:

1. **Given** drift, **When** the user runs diff (explicitly or by omitting the subcommand), **Then** a unified diff is printed to stdout, exit code is 1 and no file changes.
2. **Given** no drift, **When** diff runs, **Then** there is no output and exit code is 0.
3. **Given** a target that is valid but differently formatted (compact JSON, other key order of equal content), **When** diff runs, **Then** it reports no drift because comparison is on parsed content.
4. **Given** `-q`, **When** drift exists, **Then** nothing is printed and the exit code is still 1.

---

### User Story 3 - Pull live changes back into the template without leaking (Priority: P2)

The user changed a setting inside the host tool and wants it in the repo template. `fsettings pull`
copies it back while scrubbing anything private.

**Why this priority**: Closes the loop, and it is the risky direction (a bug leaks private data into a
public repo), so it is specified and tested hardest.

**Independent Test**: Run pull on a fixture target containing private paths and compare the template with
the expected file; grep the result for the placeholder private markers.

**Acceptance Scenarios**:

1. **Given** a target containing excluded keys, **When** pulled, **Then** their values never appear in the template (an empty list or object placeholder is added if the template lacks the key).
2. **Given** string values equal to or beginning with the user's home directory, **When** pulled, **Then** the template stores `~` or `~/...` instead.
3. **Given** `permissions.allow` rules, **When** pulled, **Then** rules with machine-local paths (home, tmp, other absolute paths, `~/`, workspace directories) are dropped and generic rules such as `command(git status)` are kept.
4. **Given** a template that uses `=!key`, **When** pulled, **Then** the marker key is kept and updated in place; no second unprefixed copy appears.
5. **Given** `--diff` or `--dry-run` (before or after the subcommand), **When** pulled, **Then** the diff is printed, the template is not written, and the exit code is 1 if it would change and 0 if not.
6. **Given** a template file that does not exist yet, **When** pulled, **Then** it is created (bootstrap); a missing target is an error.

---

### User Story 4 - Audit what is missing on each side (Priority: P3)

`fsettings missing` lists template keys the target lacks, target keys the template does not manage,
and excluded private keys present in the target.

**Why this priority**: Helpful for deciding what to pull, but nothing depends on it.

**Independent Test**: Run on fixtures and compare stdout with the expected report.

**Acceptance Scenarios**:

1. **Given** nested keys on both sides, **When** run, **Then** dotted key paths are listed in three sorted groups with `+`, `?` and `*` markers, or "(none)" for an empty group.
2. **Given** a template key spelled `=!key`, **When** run, **Then** it is compared as `key`.
3. **Given** an excluded key at any nesting depth, **When** run, **Then** it is reported only in the excluded group.

---

### User Story 5 - Failures are safe and clear (Priority: P1)

A malformed file, wrong path or full disk never corrupts the live settings file and never prints a traceback.

**Why this priority**: The target is a file another tool depends on at startup.

**Independent Test**: Feed each broken input through the CLI; assert exit code 2, a one-line stderr message,
and that all file bytes and modes are unchanged.

**Acceptance Scenarios**:

1. **Given** invalid JSON, a top-level array or scalar, or an unreadable path, **When** any command runs, **Then** stderr has one line `fsettings: <path>: <reason>`, exit code is 2, nothing is written.
2. **Given** a missing template for diff, push or missing, **Then** it is an error (a typo must not look like an empty template); a missing target for diff and push is treated as an empty object and push creates it, with parent directories.
3. **Given** a write that fails half way, **Then** the original target is intact and no temp file remains.
4. **Given** a target with mode 0600, or a symlink into a dotfiles checkout, **When** pushed, **Then** the mode is preserved and the symlink stays a symlink with its destination updated.
5. **Given** an empty or whitespace-only file, **Then** it is read as an empty object.

---

### User Story 6 - Install from PyPI and use the command (Priority: P2)

A user runs `pipx install frankensettings`, `uv tool install frankensettings` or `uvx frankensettings` and
gets the `fsettings` command. The PyPI page explains the problem, shows the commands and lists the merge rules.

**Why this priority**: Publishing is the stated goal, but it depends on stories 1-5 being right.

**Independent Test**: Build the wheel in the package job, install it into a clean venv on every supported
Python, run `fsettings --version` and an end-to-end push, and run `twine check`.

**Acceptance Scenarios**:

1. **Given** the built wheel, **When** installed in a clean environment, **Then** `fsettings --version` prints the package version and `python -m frankensettings` works.
2. **Given** the sdist and wheel, **Then** `twine check --strict` passes, the long description renders, and the metadata has name, one-sentence description, MIT license, Python >=3.10, keywords, classifiers, project URLs and no runtime dependencies.
3. **Given** the README, **Then** it is the PyPI long description and contains a problem statement, install, quick start for all four commands, merge rules, exclusions, exit codes and a security note, with placeholders only.

---

### User Story 7 - Maintainer cuts a release (Priority: P3)

Merging Conventional Commits to master makes release-please open a release PR; merging that publishes
the GitHub release with signed artifacts and uploads to PyPI through trusted publishing.

**Why this priority**: Needed to ship, but it is repeatable repo plumbing copied from sibling repos.

**Independent Test**: Run the workflows locally with `act` up to the publish job; verify the tag-to-version
check rejects a mismatched tag; the first real publish is a maintainer-run checklist.

**Acceptance Scenarios**:

1. **Given** a stable tag `vX.Y.Z`, **When** the Release workflow runs, **Then** it builds in the container, attaches SHA256SUMS, build provenance and cosign bundles to the GitHub release, then the `pypi` job uploads the same artifacts.
2. **Given** a non-stable tag or a built version that differs from the tag, **Then** nothing is published to PyPI.
3. **Given** the PyPI project does not exist yet, **Then** the docs list the one-time pending-publisher setup the maintainer must do on pypi.org.

### Edge Cases

- Template value type differs from target (object vs list vs scalar vs null): template wins, no error.
- Template has `[]` for a non-excluded list: target's list is kept (documented; use `=!key: []` to clear).
- `=!` on an excluded key overrides the exclusion (this is how a template resets `trustedWorkspaces`).
- `=` and `=!` both mean replace; a bare key named `=` or `=!` (empty name) is an input error.
- Both `key` and `=!key` in one template object is an input error (ambiguous).
- `~user/x` (another user's home) and unknown `$VARS` are left as written; `$HOME` and `${HOME}` expand; dictionary keys are never expanded.
- HOME unset: `~` and `$HOME` are left as written on push; collapse on pull is skipped.
- Home directory is a prefix of a longer sibling (`/home/alice` vs `/home/alice2/x`): collapse only on a path boundary.
- Exclusions apply to a key name at any nesting depth, on push, pull and missing.
- Non-ASCII text in values round-trips unchanged; non-string scalars are never touched by expansion or collapse.
- `-e foo` replaces the default exclusion list (so `trustedWorkspaces` is no longer protected unless listed); the help text and README say so.
- Target or template given as the same path, or a directory: error, exit 2.
- Duplicate JSON keys: last one wins (standard parser behaviour), documented.

## Requirements *(mandatory)*

### Functional Requirements

**Commands and CLI**

- **FR-001**: The system MUST provide the command `fsettings` with subcommands `diff`, `push`, `apply` (alias of push), `pull` and `missing`, each taking `<template> <target>` in that order.
- **FR-002**: When the first positional argument is not a subcommand, the system MUST behave as `diff`.
- **FR-003**: Global options `-e/--exclude`, `--no-exclude`, `-q/--quiet` and `--version` MUST be accepted before or after the subcommand and in any order with the positionals; `--diff` and its alias `--dry-run` MUST be accepted by `pull` in the same way.
- **FR-004**: Exit codes MUST be 0 (success, or no differences), 1 (differences found by `diff` or `pull --diff`), 2 (usage or input error). `push`, `apply`, `pull` and `missing` exit 0 on success even when they changed something.
- **FR-005**: Diffs MUST be unified diffs on stdout with labels `<target>` and `<target> (merged)` for diff, `<target> (updated)` for push, `<template>` and `<template> (pulled)` for pull; `-q` suppresses them without changing exit codes or writes.
- **FR-006**: Errors MUST be one line on stderr, `fsettings: <message>`, exit 2, never a traceback; `--help` and `--version` exit 0; no arguments or an unknown subcommand argument count shows usage and exits 2.

**Merge (diff and push)**

- **FR-010**: Objects MUST merge recursively; target-only keys are preserved with their order; template-only keys are appended in template order.
- **FR-011**: A non-empty template list MUST be unioned into the target list (target items first, then template items not present, compared by value, template duplicates collapsed); an empty template list MUST leave the target list as is.
- **FR-012**: Any other template value (scalar, null, type mismatch) MUST replace the target value.
- **FR-013**: A template key beginning with `=!` or `=` MUST replace the target value wholesale at that level (after expansion), MUST bypass exclusions, and MUST be written without the prefix.
- **FR-014**: Excluded keys (by name, at any depth) MUST never be modified by a template value; if absent from the target and the template value is a list or object, an empty list or object MUST be created.
- **FR-015**: String values from the template MUST be expanded on push: leading `~` or `~/`, and `$VAR` or `${VAR}` for environment variables that are set; recursively through lists and objects; keys, numbers, booleans and null untouched.
- **FR-016**: Merging MUST not mutate its inputs and MUST be idempotent: merge(merge(t, x), x) equals merge(t, x).
- **FR-017**: The default exclusion set MUST be `trustedWorkspaces`; `-e a,b` (repeatable, comma separated) sets it to exactly those names; `--no-exclude`, `-e ""` or `-e []` clear it.

**Pull**

- **FR-020**: Pull MUST start from the template and apply target values over it: objects merge recursively, any other value (including lists) is taken from the target, template-only keys are kept.
- **FR-021**: Pull MUST NOT copy excluded keys, at any depth, including inside objects nested in lists and under objects the template lacks; if the template lacks the key and the target value is a list or object, an empty list or object MUST be added.
- **FR-022**: Pull MUST collapse the current user's home directory to `~` in every string value that equals it or starts with it followed by `/`.
- **FR-023**: Pull MUST drop items of `permissions.allow` (at any depth) that reference private or machine-local locations. A rule is private when it contains any of: `/home/`, `/tmp/`, `/users/` (case-insensitive), `~/`, an absolute path token (a `/` at the start of the rule or after whitespace, `(`, `=` or a quote, followed by a path character), a `$HOME` reference, `git -c` or `-c /`. Other `permissions` keys pass through unchanged.
- **FR-024**: A template key written with `=!` or `=` MUST be updated in place under its original spelling when the target has that key; pull MUST NOT create an unprefixed duplicate.
- **FR-025**: `pull --diff` and `--dry-run` MUST print the diff and not write; without them pull writes the template when it changed. A missing template is created; a missing target is an error.

**Missing**

- **FR-030**: `missing` MUST print the header (`Template: <path>`, `Target:   <path>`), then three groups: `Missing from target` (`  + key`), `Missing from template` (`  ? key`) and `Excluded private settings present in target (N)` (`  * key`), each sorted, with "(none)" for the first two when empty and the third omitted when empty.
- **FR-031**: Keys MUST be dotted paths over nested objects (lists are leaves); template keys are compared with `=!` and `=` stripped; a path is excluded when any segment is an excluded name; `missing` always exits 0 on success.

**Files and safety**

- **FR-040**: JSON MUST be read as UTF-8; an empty or whitespace-only file is an empty object; any other non-object top level is an input error.
- **FR-041**: Output JSON MUST use two-space indent, no ASCII escaping, a trailing newline, and keep key order as built.
- **FR-042**: Changes MUST be detected on parsed content, not text; an unchanged result MUST NOT be written.
- **FR-043**: Writes MUST be atomic (temp file in the destination directory, flush and fsync, rename), MUST create missing parent directories, MUST keep the existing file's permission bits, MUST follow a symlink destination and replace its target, and MUST leave no temp file after success or failure.
- **FR-044**: A missing template is an input error for diff, push, apply and missing; a missing target is an empty object for diff and push, and an input error for missing; identical template and target paths are an input error.
- **FR-045**: Template objects containing both `k` and `=!k` (or `=k`), or a replace marker with an empty name, MUST be rejected as an input error naming the key path.

**Packaging and release**

- **FR-050**: The project MUST be a pure-Python package `frankensettings` (import name `frankensettings`, command `fsettings`, `python -m frankensettings`) with a typed public API (`deep_merge`, `pull_merge`, `expand_env`, `collapse_env`, `is_private_permission`, `missing_report`) and `__version__` read from package metadata.
- **FR-051**: Package metadata MUST include: name `frankensettings`; description "Keep one settings.json in sync between a public template and a private live file: merge, pull back, and scrub local paths."; `readme = README.md` (text/markdown); `license = "MIT"` with `license-files = ["LICENSE"]`; `requires-python = ">=3.10"`; no dependencies; keywords (settings, json, dotfiles, config, merge, sync, claude-code, vscode, cursor); Python 3.10-3.14 and OS-independent POSIX classifiers; `Typing :: Typed`; `Environment :: Console`; URLs for Homepage, Source, Issues and Changelog; `[project.scripts] fsettings`.
- **FR-052**: A `LICENSE` file with the MIT license text MUST be present, matching the sibling repos' copyright holder, with year 2026.
- **FR-053**: The README MUST serve as the PyPI long description (sections listed in User Story 6) and MUST NOT contain real home paths, usernames, hosts or private repo names.
- **FR-054**: The repo MUST provide a Makefile whose targets `test` (one Python version, coverage gate), `test-all` (Python 3.10-3.14), `lint`, `package` (build, `twine check --strict`, clean-venv smoke run), `check` (whole workflow) and `clean` run the build workflow with `act`, so local and CI runs are the same jobs; the repo has no Dockerfile or compose file.
- **FR-055**: CI MUST mirror the sibling repos: build workflow on pull requests (lint, test matrix, package), conventional-commits check, release-please (shared workflow) with preview, Release workflow (build, attest, cosign, GitHub release assets, then PyPI via trusted publishing in the `pypi` environment, stable tags only, version-equals-tag check), Dependabot (pip, docker, actions), and a `.github/repo-config.json` for the declarative repo settings including the `pypi` environment.
- **FR-056**: The repo MUST document the one-time PyPI pending trusted publisher registration (project `frankensettings`, owner `non7top`, repository `frankensettings`, workflow `release.yml`, environment `pypi`) and a first-release checklist.

**Test suite**

- **FR-060**: Tests MUST reach 100% line and branch coverage of `frankensettings` (fail-under 100) and every FR above MUST map to at least one named test (traceability table in test-plan.md).
- **FR-061**: Merge, pull and report cases MUST be fixture directories (`template.json`, `target.json`, expected output, optional `args.json` for excludes) discovered automatically, run with a controlled HOME.
- **FR-062**: CLI tests MUST run in-process (for coverage) and a small smoke set MUST run the installed entry point and `python -m` as subprocesses.
- **FR-063**: Tests MUST include idempotence (push twice, push then diff), non-mutation of inputs, push-then-pull round trip with no private leak, atomic-write failure injection, mode and symlink preservation.
- **FR-065**: A test MUST scan every tracked text file (README, docs, specs, fixtures, workflows, source) and fail on a real-looking home path (`/home/<name>` or `/Users/<name>` where the name is not in an allow-list of placeholders such as `tester`, `alice`, `user`), on home-relative checkout directories of other projects, on email addresses other than the LICENSE copyright line, and on IPv4 addresses outside documentation ranges. References to sibling projects MUST be public GitHub URLs, never local paths.
- **FR-064**: The prototype bash test MUST be ported (every assertion has a pytest equivalent) and then removed together with the prototype script.

### Key Entities

- **Template**: JSON object tracked in a repo; may use `=!` replace keys, `~` and `$HOME` paths, and empty placeholders for excluded keys. Never contains private data after a pull.
- **Target**: JSON object owned by a host tool; may hold keys the template does not know; never loses unmanaged keys on push.
- **Exclusion set**: Key names (any depth) that push never writes and pull never copies.
- **Replace key**: A template key with `=!` or `=` prefix meaning replace, not merge.
- **Private permission rule**: A `permissions.allow` string matching FR-023.
- **Fixture case**: A directory of inputs and expected outputs for one merge, pull or report behaviour.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Line and branch coverage of the package is 100% in the container test target and in CI, and the build fails below that.
- **SC-002**: Every FR-xxx has at least one test; the traceability table has no empty row (checked by a test that parses it).
- **SC-003**: The full suite runs green on Python 3.10, 3.11, 3.12, 3.13 and 3.14 and finishes in under 60 seconds per version.
- **SC-004**: The pull fixtures contain at least 25 private values (excluded paths, home paths, private rules) and a scan of all pull outputs finds zero occurrences of the fixture home directory, the fixture workspace paths and any dropped rule.
- **SC-005**: `twine check --strict` passes on sdist and wheel, and a wheel installed in a clean venv on each supported Python runs `fsettings --version` and a push, diff, pull, missing round trip with exit codes per FR-004.
- **SC-006**: A tag push for a stable version produces a GitHub release with wheel, sdist, SHA256SUMS and cosign bundles, and the same files on PyPI; a mismatched or pre-release tag publishes nothing to PyPI (verified with `act` up to the publish step, then once for real).
- **SC-007**: A new user can go from the PyPI page to a first successful `push` in under 5 minutes using only the README.

## Assumptions

- Maintainer, owner and copyright holder follow the sibling repos (non7top, MIT, 2026); the GitHub repo will be public at `non7top/frankensettings` with default branch `master` (maintainer-confirmed layout: flat package, not src/).
- PyPI names `frankensettings` and `fsettings` were both unregistered when checked on 2026-11-26 (HTTP 404 from the PyPI JSON API); the maintainer registers a pending trusted publisher for `frankensettings` before the first tag.
- Defaults chosen without asking, open to veto: broadened absolute-path detection in FR-023 (the prototype only matched a few fixed substrings, including one specific to the maintainer's own checkout layout, although project.md promises "absolute paths"; that substring is dropped because the general rule covers it inside any absolute path); `~` alone expands on push (the prototype collapsed it on pull but did not expand it back); missing template is an error on push and diff (the prototype silently treated it as empty); `-e` replaces the default exclusions instead of adding to them (prototype behaviour, kept); pull replaces lists from the target instead of union (prototype behaviour, kept).
- Out of scope for v1: JSONC input, Windows, TOML or YAML targets, per-key merge strategies beyond replace, a config file for exclusions, a `settings.d` directory mode.
- The prototype `project.md` is superseded by the README and this spec; it is kept in the repo history only.
