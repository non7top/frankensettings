import json
import re
from importlib import metadata

import pytest

import frankensettings
from conftest import ROOT

DESCRIPTION = (
    "Keep one settings.json in sync between a public template and a private live file: "
    "merge, pull back, and scrub local paths."
)


def _meta():
    return metadata.metadata("frankensettings")


def test_public_api_importable():
    for name in frankensettings.__all__:
        assert hasattr(frankensettings, name), name
    assert (ROOT / "frankensettings" / "py.typed").exists()


def test_version_matches_metadata():
    assert frankensettings.__version__ == metadata.version("frankensettings")


def test_version_falls_back_for_source_checkouts(monkeypatch):
    def missing(name):
        raise metadata.PackageNotFoundError(name)

    monkeypatch.setattr(frankensettings, "version", missing)
    assert frankensettings._read_version() == "0+unknown"


def test_metadata():
    meta = _meta()
    assert meta["Name"] == "frankensettings"
    assert meta["Summary"] == DESCRIPTION
    assert meta["License-Expression"] == "MIT"
    assert meta["Requires-Python"] == ">=3.10"
    assert meta["Description-Content-Type"] == "text/markdown"
    assert "Keywords" in meta and "dotfiles" in meta["Keywords"]
    runtime_requirements = [r for r in (meta.get_all("Requires-Dist") or []) if "extra ==" not in r]
    assert runtime_requirements == []
    classifiers = meta.get_all("Classifier")
    for expected in (
        "Environment :: Console",
        "Typing :: Typed",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.14",
    ):
        assert expected in classifiers
    urls = {entry.split(", ")[0] for entry in meta.get_all("Project-URL")}
    assert urls == {"Homepage", "Source", "Issues", "Changelog"}
    scripts = {ep.name: ep.value for ep in metadata.entry_points(group="console_scripts")}
    assert scripts["fsettings"] == "frankensettings.cli:main"
    assert len(meta.get_payload() or meta["Description"] or "") > 1000


def test_license_is_mit():
    text = (ROOT / "LICENSE").read_text()
    assert text.startswith("MIT License\n")
    assert "Copyright (c) 2026 " in text
    assert "Permission is hereby granted, free of charge" in text


README_HEADINGS = [
    "## The problem",
    "## Install",
    "## Quick start",
    "## Commands",
    "## Merge rules",
    "## Pull: scrubbing",
    "## Exclusions",
    "## Use as a library",
    "## Limits",
    "## Security",
    "## License",
]


def test_readme_sections():
    text = (ROOT / "README.md").read_text()
    for heading in README_HEADINGS:
        assert heading in text, heading
    installs = ("pipx install frankensettings", "uv tool install frankensettings", "uvx frankensettings")
    for needle in (*installs, "Exit code"):
        assert needle in text, needle
    for command in ("diff", "push", "apply", "pull", "missing"):
        assert f"`{command}`" in text


def test_makefile_targets():
    text = (ROOT / "Makefile").read_text()
    for target in ("test", "test-all", "lint", "package", "check", "clean"):
        assert re.search(rf"^{re.escape(target)}:", text, re.M), target
    assert "act" in text and "build.yml" in text


WORKFLOWS = ["build.yml", "conventional-commits.yml", "release-please.yml", "release-please-preview.yml", "release.yml"]


def test_workflows_present():
    for name in WORKFLOWS:
        assert (ROOT / ".github" / "workflows" / name).exists(), name
    assert (ROOT / ".github" / "dependabot.yml").exists()
    config = json.loads((ROOT / ".github" / "repo-config.json").read_text())
    assert "pypi" in config["environments"]
    release = (ROOT / ".github" / "workflows" / "release.yml").read_text()
    assert "environment: pypi" in release
    assert "id-token: write" in release
    assert "pypa/gh-action-pypi-publish" in release
    please = json.loads((ROOT / "release-please-config.json").read_text())
    assert please["packages"]["."]["release-type"] == "python"
    assert (ROOT / ".release-please-manifest.json").exists()


@pytest.mark.parametrize("phrase", ["pending publisher", "release.yml", "environment", "pypi"])
def test_release_docs_present(phrase):
    text = (ROOT / "docs" / "releasing.md").read_text()
    assert phrase in text
