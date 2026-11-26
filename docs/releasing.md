# Releasing frankensettings

Releases follow the same pipeline as the maintainer's other Python projects:
release-please opens a release pull request from Conventional Commits, merging it tags the release, the
Release workflow builds, attests and signs the files and attaches them to the GitHub release, and the
final job publishes to PyPI with trusted publishing. No PyPI token exists anywhere.

## One-time setup (before the first release)

1. Create the project on PyPI as a **pending publisher** (pypi.org, Your projects, Publishing, Add a new pending publisher):

   | Field | Value |
   | --- | --- |
   | PyPI project name | frankensettings |
   | Owner | non7top |
   | Repository name | frankensettings |
   | Workflow name | release.yml |
   | Environment name | pypi |

2. Make sure the GitHub repository has an environment named `pypi` (it is declared in
   `.github/repo-config.json`; apply that file with the repo-config tool or create the environment by hand).
3. Enable the repository ruleset that requires a pull request for `master` (also in `repo-config.json`).

The first successful publish turns the pending publisher into a normal trusted publisher.

## Cutting a release

1. Merge pull requests with Conventional Commit messages (`feat:`, `fix:`, `docs:`, ...) into `master`.
2. release-please opens or updates a pull request named like `chore(master): release 0.1.0` with the changelog and
   the version bump in `pyproject.toml`. The first `feat:` after the initial setup produces 0.1.0
   (`bump-minor-pre-major` is on, so breaking changes before 1.0 bump the minor version).
3. Merge that pull request when you want to ship. release-please creates the tag `vX.Y.Z` and the GitHub release.
4. The Release workflow runs on the tag. It builds the sdist and wheel, runs `twine check --strict`, writes
   `SHA256SUMS`, creates build provenance attestations, signs each file with cosign, uploads everything to the
   GitHub release, and then the `pypi` job uploads the same files to PyPI. Only stable `vX.Y.Z` tags publish; the job
   also checks that the built filenames carry the tag's version.
5. Verify from a clean environment: `uvx frankensettings --version`.

To rebuild or republish a tag, run the Release workflow by hand (workflow_dispatch) and give the tag.

## Local rehearsal

The build workflow runs locally with act, and the Makefile does exactly that:

```bash
make lint          # lint job
make test          # test job on one Python version (PYTHON_VERSION=3.13 by default)
make test-all      # test job on Python 3.10 to 3.14
make package       # build, twine check and a clean-venv smoke run of the wheel
make check         # the whole build workflow
```

## Verifying a release

- Checksums: `sha256sum -c SHA256SUMS` next to the downloaded files.
- Provenance: `gh attestation verify <file> --repo non7top/frankensettings`.
- Signature: `cosign verify-blob --bundle <file>.cosign.bundle <file>` with the certificate identity of the Release workflow.

## If something goes wrong

- A bad upload cannot be replaced on PyPI. Yank the release on pypi.org (Manage, Releases) and ship a fixed patch version.
- A wrong tag: delete the GitHub release and tag, fix the cause, and let release-please propose the next version.
