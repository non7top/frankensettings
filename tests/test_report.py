import pytest

from conftest import cases
from frankensettings import missing_report

REPORT_CASES = cases("missing", ["template.json", "target.json", "expected.txt"])


@pytest.mark.parametrize("case", REPORT_CASES)
def test_missing_fixtures(case):
    report = missing_report(
        case.load("template.json"), case.load("target.json"), case.excludes(), "template.json", "target.json"
    )
    assert report == case.text("expected.txt")


def test_report_accepts_any_collection_of_excludes():
    for excludes in ({"x"}, ["x"], ("x",)):
        report = missing_report({}, {"x": 1}, excludes, "t", "g")
        assert report.endswith("Excluded private settings present in target (1):\n  * x\n")


def test_report_strips_replace_prefix_only_on_the_template_side():
    report = missing_report({"=!a": 1}, {"a": 1, "=!b": 1}, set(), "t", "g")
    assert "Missing from target: (none)" in report
    assert "? =!b" in report
