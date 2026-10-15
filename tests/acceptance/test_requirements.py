"""Declaring requirements and linking existing tests without changing their structure."""

import pytest

from tests.acceptance.expectations import expected
from tests.acceptance.scenarios.requirements import (
    class_markers,
    invalid_deselected_marker,
    multiple_requirements,
    parameterized_cases,
    repeated_marker,
)
from tests.acceptance.scenarios.requirements.invalid_markers import (
    keyword_id,
    missing_id,
    multiple_ids,
    non_string_id,
    unknown_id,
)
from tests.acceptance.scenarios.requirements.opaque_ids import dotted, simple, unicode


@pytest.mark.parametrize(
    ("requirement", "scenario"),
    [
        pytest.param("REQ-001", simple, id="REQ-001"),
        pytest.param("requirement.group.item", dotted, id="requirement.group.item"),
        pytest.param("Krav / æøå : 1", unicode, id="Krav / æøå : 1"),
    ],
)
def test_requirement_ids_are_opaque_strings(user_project, read_report, requirement, scenario):
    project = user_project([requirement], scenario)

    result = project.runpytest_subprocess("--xspec-json=report.json", "--strict-markers")

    assert result.ret == pytest.ExitCode.OK
    report = read_report(project)
    assert report["requirements"][requirement]["status"] == "PASSED"


def test_one_test_can_verify_several_requirements(user_project, read_report):
    project = user_project(["REQ-001", "REQ-002"], multiple_requirements)
    expected_tests = [("test_behavior.py::test_shared_behavior", "PASSED")]

    result = project.runpytest_subprocess("--xspec-json=report.json")

    assert result.ret == pytest.ExitCode.OK
    report = read_report(project)
    assert set(report["requirements"]) == {"REQ-001", "REQ-002"}
    for requirement in report["requirements"].values():
        assert expected(requirement).to_have(status="PASSED", tests=expected_tests)


def test_every_parameterized_case_is_an_individual_acceptance_test(user_project, read_report):
    project = user_project(["REQ-001"], parameterized_cases)
    expected_tests = [
        ("test_behavior.py::test_behavior[first]", "PASSED"),
        ("test_behavior.py::test_behavior[second]", "PASSED"),
    ]

    result = project.runpytest_subprocess("--xspec-json=report.json")

    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=2)
    report = read_report(project)
    assert expected(report["requirements"]["REQ-001"]).to_have(
        status="PASSED", tests=expected_tests
    )


def test_requirement_markers_can_be_inherited_from_a_test_class(user_project, read_report):
    project = user_project(["REQ-001"], class_markers)

    result = project.runpytest_subprocess("--xspec-json=report.json")

    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=2)
    report = read_report(project)
    assert expected(report["requirements"]["REQ-001"]).to_have(
        status="PASSED",
        tests=[
            ("test_behavior.py::TestBehavior::test_first", "PASSED"),
            ("test_behavior.py::TestBehavior::test_second", "PASSED"),
        ],
    )


def test_repeating_a_marker_does_not_count_the_same_test_twice(user_project, read_report):
    project = user_project(["REQ-001"], repeated_marker)

    result = project.runpytest_subprocess("--xspec-json=report.json")

    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=1)
    report = read_report(project)
    assert expected(report["requirements"]["REQ-001"]).to_have(
        status="PASSED", tests=[("test_behavior.py::test_behavior", "PASSED")]
    )


@pytest.mark.parametrize(
    ("scenario", "diagnostic"),
    [
        pytest.param(unknown_id, "UNKNOWN", id='xspec("UNKNOWN")-UNKNOWN'),
        pytest.param(missing_id, "xspec", id="xspec()-xspec"),
        pytest.param(non_string_id, "xspec", id="xspec(123)-xspec"),
        pytest.param(multiple_ids, "xspec", id='xspec("REQ-001", "REQ-002")-xspec'),
        pytest.param(keyword_id, "xspec", id='xspec(id="REQ-001")-xspec'),
    ],
)
@pytest.mark.parametrize(
    "reporting", [(), ("--xspec-report",)], ids=["plain-pytest", "with-report"]
)
def test_invalid_requirement_markers_are_rejected_with_a_useful_message(
    user_project, scenario, diagnostic, reporting
):
    project = user_project(["REQ-001", "REQ-002"], scenario)

    result = project.runpytest_subprocess(*reporting)

    assert result.ret != pytest.ExitCode.OK
    message = result.stdout.str() + result.stderr.str()
    assert "unrecognized arguments" not in message.lower()
    assert diagnostic in message
    assert "test_behavior.py::test_behavior" in message


def test_invalid_markers_are_rejected_even_when_the_test_is_deselected(user_project):
    project = user_project(["REQ-001"], invalid_deselected_marker)

    result = project.runpytest_subprocess("-k", "selected", "--xspec-report")

    assert result.ret != pytest.ExitCode.OK
    message = result.stdout.str() + result.stderr.str()
    assert "UNKNOWN" in message
