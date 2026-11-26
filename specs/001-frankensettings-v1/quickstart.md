# Quickstart (for the implementer)

All checks are jobs of the build workflow; the Makefile runs them locally with act (Constitution VII).

```bash
make lint        # lint job of .github/workflows/build.yml, run with act
make test        # test job on one Python (PYTHON_VERSION=3.13 default), fails under 100% coverage
make test-all    # test job on Python 3.10 .. 3.14
make package     # build, twine check --strict, clean-venv smoke run of the wheel
make check       # the whole workflow
```

## End-to-end check of a built wheel (what SC-005 automates)

```bash
make package
# scripts/smoke_wheel.sh does this in a clean venv inside the package job
fsettings --version
fsettings push template.json target.json     # applies, prints diff, exit 0
fsettings template.json target.json          # clean, exit 0
fsettings pull template.json target.json     # scrubs, exit 0
fsettings missing template.json target.json  # report, exit 0
```

## Using it (README quick start, placeholders only)

```bash
pipx install frankensettings        # or: uv tool install frankensettings
fsettings dotfiles/tool/settings.json ~/.config/tool/settings.json          # drift check
fsettings push dotfiles/tool/settings.json ~/.config/tool/settings.json     # apply
fsettings pull --dry-run dotfiles/tool/settings.json ~/.config/tool/settings.json
```

## First release (maintainer, once)

1. Create the public repo and apply the repo settings (see docs/releasing.md); do not push to master directly.
2. On pypi.org add a pending publisher: project frankensettings, owner non7top, repository frankensettings, workflow release.yml, environment pypi.
3. Merge the feature PR, then the release-please PR; the tag v0.1.0 triggers Release and publishes.
4. In a clean environment run `uvx frankensettings --version`.
