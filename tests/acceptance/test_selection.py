"""Selection preserves known test identities; uncollected tests cannot be identified."""

import pytest

from tests.acceptance.expectations import expected
from tests.acceptance.scenarios.selection import (
    deselected_tests,
    missing_requirement,
    outside_collected_path,
)


@pytest.mark.parametrize("selection", [("-k", "selected"), ("-m", "chosen")])
def test_selection_keeps_deselected_requirement_tests_in_the_report(
    user_project, read_report, selection
):
    project = user_project(["REQ-001", "REQ-002"], deselected_tests)
    project.makefile(".ini", pytest="[pytest]\nmarkers = chosen: selected test\n")

    project.runpytest_subprocess("--xspec-json=report.json", *selection)

    report = read_report(project)
    assert report["requirements"]["REQ-001"]["status"] == "PASSED"
    assert expected(report["requirements"]["REQ-002"]).to_have(
        status="DESELECTED",
        tests=[("test_excluded.py::test_other", "DESELECTED")],
    )


def test_a_requirement_without_any_collected_test_is_missing(user_project, read_report):
    project = user_project(["REQ-001"], missing_requirement)

    project.runpytest_subprocess("--xspec-json=report.json")

    report = read_report(project)
    assert expected(report["requirements"]["REQ-001"]).to_have(status="MISSING", tests=[])


def test_a_test_outside_the_collected_path_is_not_reported_as_deselected(user_project, read_report):
    project = user_project(["REQ-001"], outside_collected_path)

    project.runpytest_subprocess("test_behavior.py", "--xspec-json=report.json")

    report = read_report(project)
    assert expected(report["requirements"]["REQ-001"]).to_have(status="MISSING", tests=[])
