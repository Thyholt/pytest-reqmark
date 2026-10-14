"""Declaring requirements and linking existing tests without changing their structure."""

import pytest

from tests.acceptance.scenarios.requirements import (
    class_markers,
    invalid_deselected_marker,
    invalid_inventory,
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
        pytest.param("training.yolo.config", dotted, id="training.yolo.config"),
        pytest.param("Krav / æøå : 1", unicode, id="Krav / æøå : 1"),
    ],
)
def test_requirement_ids_are_opaque_strings(user_project, read_report, requirement, scenario):
    project = user_project([requirement], scenario)
    result = project.runpytest_subprocess("--req-json=report.json", "--strict-markers")
    assert result.ret == pytest.ExitCode.OK
    assert read_report(project)["requirements"][requirement]["status"] == "PASSED"


def test_one_test_can_verify_several_requirements(user_project, read_report):
    project = user_project(["REQ-001", "REQ-002"], multiple_requirements)
    assert project.runpytest_subprocess("--req-json=report.json").ret == pytest.ExitCode.OK
    requirements = read_report(project)["requirements"]
    assert set(requirements) == {"REQ-001", "REQ-002"}
    for requirement in requirements.values():
        assert requirement["status"] == "PASSED"
        assert requirement["tests"] == [
            {"nodeid": "test_behavior.py::test_shared_behavior", "outcome": "PASSED"}
        ]


def test_every_parameterized_case_is_an_individual_acceptance_test(user_project, read_report):
    project = user_project(["REQ-001"], parameterized_cases)
    result = project.runpytest_subprocess("--req-json=report.json")
    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=2)
    tests = read_report(project)["requirements"]["REQ-001"]["tests"]
    assert tests == [
        {"nodeid": "test_behavior.py::test_behavior[first]", "outcome": "PASSED"},
        {"nodeid": "test_behavior.py::test_behavior[second]", "outcome": "PASSED"},
    ]


def test_requirement_markers_can_be_inherited_from_a_test_class(user_project, read_report):
    project = user_project(["REQ-001"], class_markers)
    result = project.runpytest_subprocess("--req-json=report.json")
    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=2)
    requirement = read_report(project)["requirements"]["REQ-001"]
    assert requirement == {
        "status": "PASSED",
        "tests": [
            {"nodeid": "test_behavior.py::TestBehavior::test_first", "outcome": "PASSED"},
            {"nodeid": "test_behavior.py::TestBehavior::test_second", "outcome": "PASSED"},
        ],
    }


def test_repeating_a_marker_does_not_count_the_same_test_twice(user_project, read_report):
    project = user_project(["REQ-001"], repeated_marker)
    result = project.runpytest_subprocess("--req-json=report.json")
    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=1)
    assert read_report(project)["requirements"]["REQ-001"] == {
        "status": "PASSED",
        "tests": [{"nodeid": "test_behavior.py::test_behavior", "outcome": "PASSED"}],
    }


@pytest.mark.parametrize(
    ("scenario", "diagnostic"),
    [
        pytest.param(unknown_id, "UNKNOWN", id='req("UNKNOWN")-UNKNOWN'),
        pytest.param(missing_id, "req", id="req()-req"),
        pytest.param(non_string_id, "req", id="req(123)-req"),
        pytest.param(multiple_ids, "req", id='req("REQ-001", "REQ-002")-req'),
        pytest.param(keyword_id, "req", id='req(id="REQ-001")-req'),
    ],
)
@pytest.mark.parametrize("reporting", [(), ("--req-report",)], ids=["plain-pytest", "with-report"])
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
    result = project.runpytest_subprocess("-k", "selected", "--req-report")
    assert result.ret != pytest.ExitCode.OK
    assert "UNKNOWN" in result.stdout.str() + result.stderr.str()


@pytest.mark.parametrize("inventory", ['"REQ-001"', "[123]", '["REQ-001", "REQ-001"]'])
def test_invalid_requirement_configuration_is_rejected(user_project, inventory):
    project = user_project([], invalid_inventory)
    (project.path / "pyproject.toml").write_text(
        f"[tool.pytest-reqmark]\nrequirements = {inventory}\n", encoding="utf-8"
    )
    result = project.runpytest_subprocess("--req-report")
    assert result.ret != pytest.ExitCode.OK
    message = result.stdout.str() + result.stderr.str()
    assert "unrecognized arguments" not in message.lower()
    assert "requirements" in message.lower()
