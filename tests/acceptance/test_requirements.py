"""Declaring requirements and linking existing tests without changing their structure."""

import pytest


@pytest.mark.parametrize("requirement", ["REQ-001", "training.yolo.config", "Krav / æøå : 1"])
def test_requirement_ids_are_opaque_strings(user_project, read_report, requirement):
    project = user_project(
        [requirement], f"@pytest.mark.req({requirement!r})\ndef test_behavior():\n    pass\n"
    )
    result = project.runpytest_subprocess("--req-json=report.json", "--strict-markers")
    assert result.ret == pytest.ExitCode.OK
    assert read_report(project)["requirements"][requirement]["status"] == "PASSED"


def test_one_test_can_verify_several_requirements(user_project, read_report):
    project = user_project(
        ["REQ-001", "REQ-002"],
        """
@pytest.mark.req("REQ-001")
@pytest.mark.req("REQ-002")
def test_shared_behavior():
    pass
""",
    )
    assert project.runpytest_subprocess("--req-json=report.json").ret == pytest.ExitCode.OK
    requirements = read_report(project)["requirements"]
    assert set(requirements) == {"REQ-001", "REQ-002"}
    for requirement in requirements.values():
        assert requirement["status"] == "PASSED"
        assert requirement["tests"] == [
            {"nodeid": "test_behavior.py::test_shared_behavior", "outcome": "PASSED"}
        ]


def test_every_parameterized_case_is_an_individual_acceptance_test(user_project, read_report):
    project = user_project(
        ["REQ-001"],
        """
@pytest.mark.req("REQ-001")
@pytest.mark.parametrize("value", [1, 2], ids=["first", "second"])
def test_behavior(value):
    assert value > 0
""",
    )
    result = project.runpytest_subprocess("--req-json=report.json")
    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=2)
    tests = read_report(project)["requirements"]["REQ-001"]["tests"]
    assert tests == [
        {"nodeid": "test_behavior.py::test_behavior[first]", "outcome": "PASSED"},
        {"nodeid": "test_behavior.py::test_behavior[second]", "outcome": "PASSED"},
    ]


def test_requirement_markers_can_be_inherited_from_a_test_class(user_project, read_report):
    project = user_project(
        ["REQ-001"],
        """
@pytest.mark.req("REQ-001")
class TestBehavior:
    def test_first(self):
        pass

    def test_second(self):
        pass
""",
    )
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
    project = user_project(
        ["REQ-001"],
        """
@pytest.mark.req("REQ-001")
@pytest.mark.req("REQ-001")
def test_behavior():
    pass
""",
    )
    result = project.runpytest_subprocess("--req-json=report.json")
    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=1)
    assert read_report(project)["requirements"]["REQ-001"] == {
        "status": "PASSED",
        "tests": [{"nodeid": "test_behavior.py::test_behavior", "outcome": "PASSED"}],
    }


@pytest.mark.parametrize(
    ("marker", "diagnostic"),
    [
        ('req("UNKNOWN")', "UNKNOWN"),
        ("req()", "req"),
        ("req(123)", "req"),
        ('req("REQ-001", "REQ-002")', "req"),
        ('req(id="REQ-001")', "req"),
    ],
)
@pytest.mark.parametrize("reporting", [(), ("--req-report",)], ids=["plain-pytest", "with-report"])
def test_invalid_requirement_markers_are_rejected_with_a_useful_message(
    user_project, marker, diagnostic, reporting
):
    project = user_project(
        ["REQ-001", "REQ-002"], f"@pytest.mark.{marker}\ndef test_behavior():\n    pass\n"
    )
    result = project.runpytest_subprocess(*reporting)
    assert result.ret != pytest.ExitCode.OK
    message = result.stdout.str() + result.stderr.str()
    assert "unrecognized arguments" not in message.lower()
    assert diagnostic in message
    assert "test_behavior.py::test_behavior" in message


def test_invalid_markers_are_rejected_even_when_the_test_is_deselected(user_project):
    project = user_project(
        ["REQ-001"],
        """
@pytest.mark.req("UNKNOWN")
def test_invalid():
    pass

def test_selected():
    pass
""",
    )
    result = project.runpytest_subprocess("-k", "selected", "--req-report")
    assert result.ret != pytest.ExitCode.OK
    assert "UNKNOWN" in result.stdout.str() + result.stderr.str()


@pytest.mark.parametrize("inventory", ['"REQ-001"', "[123]", '["REQ-001", "REQ-001"]'])
def test_invalid_requirement_configuration_is_rejected(user_project, inventory):
    project = user_project([], "def test_behavior():\n    pass\n")
    (project.path / "pyproject.toml").write_text(
        f"[tool.pytest-reqmark]\nrequirements = {inventory}\n", encoding="utf-8"
    )
    result = project.runpytest_subprocess("--req-report")
    assert result.ret != pytest.ExitCode.OK
    message = result.stdout.str() + result.stderr.str()
    assert "unrecognized arguments" not in message.lower()
    assert "requirements" in message.lower()
