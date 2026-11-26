# frankensettings Constitution

## Core Principles

### I. Standard library only
The runtime has zero third-party dependencies and supports Python 3.10 and newer.
Dev and test tooling (pytest, coverage, build, twine, flake8) lives in the `dev` extra and the
test image, never in `dependencies`. A new runtime dependency needs a constitution amendment.

### II. Private data never reaches the template
`pull` is the only path from a live settings file to a tracked file, and it must scrub:
excluded keys are not copied, the user's home directory is collapsed to `~`, and permission rules
that reference machine-local paths are dropped. The tool never reads outside the two files named on
the command line, never touches the network, and never writes a value from the target into any
output other than the template (a diff on stdout is the exception and is documented).

### III. Writes are atomic, honest and minimal
Every write goes through one function: temp file in the destination directory, content flushed to
disk, then rename over the destination. The destination keeps its file mode and symlinks are
followed. A command that reports a change either wrote it or (dry run) did not touch the disk. A
run that changes nothing writes nothing.

### IV. Test-first, with fixtures, at 100%
Every functional requirement has at least one test written before the code that satisfies it.
Merge, pull and report behaviour is specified by fixture directories (template, target, expected
output), not by inline JSON in test bodies. The test gate is 100% line AND branch coverage of the
package, enforced in the container target and in CI. A coverage exclusion needs a one-line reason
next to it.

### V. Deterministic and idempotent
Same inputs, same bytes out: two-space indent, UTF-8 without ASCII escaping, trailing newline,
target key order preserved, new keys appended in template order. After `push`, `diff` exits 0 and a
second `push` writes nothing. Comparison is on parsed content, never on whitespace.

### VI. Stable CLI contract
Exit codes are 0 (clean or done), 1 (differences found by a read-only comparison) and 2 (usage or
input error). Diffs go to stdout, errors to stderr as one line prefixed `fsettings:` with no
traceback. Argument order is always template then target. Changing any of this is a breaking change.

### VII. CI is the only build path, signed releases
Linting, tests and packaging are jobs in the build workflow. Locally the Makefile runs that same
workflow with act (throwaway containers), so a local run and CI cannot differ; nothing is installed
or run on the host. Releases come from release-please and Conventional Commits, are built once,
attested and signed, and are published to PyPI only by trusted publishing from CI. No PyPI token
exists anywhere.

## Additional Constraints

- License: MIT. Author and copyright line match the sibling repos.
- Platforms: Linux and macOS (POSIX). Windows is out of scope for v1.
- Input format: strict JSON objects. JSONC (comments, trailing commas) is out of scope for v1.
- The repo owns no Docker objects (no Dockerfile or compose file); act supplies the containers.

## Development Workflow

- Default branch is `master`. Every change goes through a branch and a pull request; merging needs
  an explicit go-ahead from the maintainer.
- Commits are atomic and use Conventional Commits with the feature or area as scope.
- A pull request is mergeable only with lint, the full test suite at 100% coverage on the supported
  Python matrix, a successful package build and `twine check` all green.
- Public text (README, PyPI description, issues, PRs) never contains real home paths, host names,
  SSIDs, tokens or private repo names. Examples use placeholders.

## Governance

This constitution supersedes ad-hoc practice. Amendments are a pull request that edits this file,
states the reason and bumps the version below. Plans must pass the Constitution Check against it,
and violations are recorded in the plan's Complexity Tracking table.

**Version**: 1.1.0 | **Ratified**: 2026-11-26 | **Last Amended**: 2026-11-26

Amendment 1.1.0: principle VII changed from repo-owned compose containers to the act-driven build workflow, at the maintainer's request.
