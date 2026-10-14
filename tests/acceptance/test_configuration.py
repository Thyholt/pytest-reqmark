"""Users configure their inventory in pyproject.toml or pytest.ini only."""

import pytest

from tests.acceptance.expectations import expected
from tests.acceptance.scenarios.configuration import (
    conflicting_inventories,
    duplicate_ini_ids,
    pyproject_with_pytest_ini,
    pytest_ini_inventory,
    unknown_id_without_inventory,
    unmarked_with_unsupported_inventory,
    unsupported_inventory,
    without_requirement_configuration,
    zero_requirements_without_configuration,
)


def test_requirements_can_be_declared_in_pytest_ini(user_project, read_report):
    project = user_project(["REQ-001"], pytest_ini_inventory)
    (project.path / "pyproject.toml").unlink()
    project.makefile(".ini", pytest="[pytest]\ntracereq_requirements =\n    REQ-001\n    REQ-002\n")

    result = project.runpytest_subprocess("--tracereq-json=report.json")

    assert result.ret == pytest.ExitCode.OK
    report = read_report(project)
    assert report["requirements"]["REQ-001"]["status"] == "PASSED"
    assert expected(report["requirements"]["REQ-002"]).to_have(status="MISSING", tests=[])


def test_pyproject_inventory_is_read_even_when_pytest_ini_controls_pytest(
    user_project, read_report
):
    project = user_project(["REQ-001"], pyproject_with_pytest_ini)
    project.makefile(".ini", pytest="[pytest]\naddopts = -q\n")

    result = project.runpytest_subprocess("--tracereq-strict", "--tracereq-json=report.json")

    assert result.ret == 0
    report = read_report(project)
    assert report["requirements"]["REQ-001"]["status"] == "PASSED"


def test_declaring_an_inventory_in_both_supported_files_is_rejected(user_project):
    project = user_project(["REQ-001"], conflicting_inventories)
    project.makefile(".ini", pytest="[pytest]\ntracereq_requirements =\n    REQ-002\n")

    result = project.runpytest_subprocess("--tracereq-report")

    assert result.ret != pytest.ExitCode.OK
    message = result.stdout.str() + result.stderr.str()
    assert "pyproject.toml" in message
    assert "pytest.ini" in message


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("setup.cfg", "[tool:pytest]\ntracereq_requirements = REQ-001\n"),
        ("tox.ini", "[pytest]\ntracereq_requirements = REQ-001\n"),
        ("requirements.json", '{"requirements": ["REQ-001"]}'),
        ("requirements.yaml", "requirements:\n  - REQ-001\n"),
    ],
)
def test_other_configuration_files_do_not_supply_a_requirement_inventory(
    user_project, filename, content
):
    project = user_project(["REQ-001"], unsupported_inventory)
    (project.path / "pyproject.toml").unlink()
    (project.path / filename).write_text(content, encoding="utf-8")

    result = project.runpytest_subprocess("--tracereq-strict")

    assert result.ret != pytest.ExitCode.OK
    message = result.stdout.str() + result.stderr.str()
    assert "REQ-001" in message


def test_normal_pytest_without_requirement_configuration_still_works(user_project):
    project = user_project([], without_requirement_configuration)
    (project.path / "pyproject.toml").unlink()

    result = project.runpytest_subprocess()

    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=1)


def test_no_requirement_configuration_means_success_with_zero_requirements(
    user_project, read_report
):
    project = user_project([], zero_requirements_without_configuration)
    (project.path / "pyproject.toml").unlink()

    result = project.runpytest_subprocess("--tracereq-strict", "--tracereq-json=report.json")

    assert result.ret == pytest.ExitCode.OK
    report = read_report(project)
    assert report == {
        "requirements": {},
        "summary": {
            "requirements": 0,
            "passed": 0,
            "unverified": 0,
            "coverage": 0.0,
            "verified": True,
            "collection_errors": 0,
        },
    }


def test_duplicate_requirement_ids_in_pytest_ini_are_rejected(user_project):
    project = user_project(["REQ-001"], duplicate_ini_ids)
    (project.path / "pyproject.toml").unlink()
    project.makefile(".ini", pytest="[pytest]\ntracereq_requirements =\n    REQ-001\n    REQ-001\n")

    result = project.runpytest_subprocess()

    assert result.ret != pytest.ExitCode.OK
    message = result.stdout.str() + result.stderr.str()
    assert "requirements" in message.lower()
    assert "REQ-001" in message


@pytest.mark.parametrize("config_file", ["pyproject.toml", "pytest.ini", None])
def test_unknown_marked_ids_are_rejected_even_when_no_requirements_are_declared(
    user_project, config_file
):
    project = user_project([], unknown_id_without_inventory)
    if config_file != "pyproject.toml":
        (project.path / "pyproject.toml").unlink()
    if config_file == "pytest.ini":
        project.makefile(".ini", pytest="[pytest]\ntracereq_requirements =\n")

    result = project.runpytest_subprocess()

    assert result.ret != pytest.ExitCode.OK
    message = result.stdout.str() + result.stderr.str()
    assert "UNKNOWN" in message
    assert "test_behavior.py::test_behavior" in message


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("setup.cfg", "[tool:pytest]\ntracereq_requirements = REQ-001\n"),
        ("tox.ini", "[pytest]\ntracereq_requirements = REQ-001\n"),
        ("requirements.json", '{"requirements": ["REQ-001"]}'),
        ("requirements.yaml", "requirements:\n  - REQ-001\n"),
    ],
)
def test_unsupported_inventory_files_are_ignored_when_tests_are_unmarked(
    user_project, read_report, filename, content
):
    project = user_project([], unmarked_with_unsupported_inventory)
    (project.path / "pyproject.toml").unlink()
    (project.path / filename).write_text(content, encoding="utf-8")

    result = project.runpytest_subprocess("--tracereq-strict", "--tracereq-json=report.json")

    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=1)
    report = read_report(project)
    assert report == {
        "requirements": {},
        "summary": {
            "requirements": 0,
            "passed": 0,
            "unverified": 0,
            "coverage": 0.0,
            "verified": True,
            "collection_errors": 0,
        },
    }
