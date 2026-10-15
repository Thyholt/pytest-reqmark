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
from tests.acceptance.scenarios.requirements import invalid_inventory


def test_requirements_can_be_declared_in_pyproject_toml(file_project, read_report):
    project = file_project(pyproject_with_pytest_ini)
    project.makefile(".toml", pyproject='[tool.xspec]\nrequirements = ["REQ-001", "REQ-002"]\n')

    result = project.runpytest_subprocess("--xspec-json=report.json")

    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=1)
    report = read_report(project)
    assert report["requirements"] == {
        "REQ-001": {
            "status": "PASSED",
            "tests": [{"nodeid": "test_behavior.py::test_behavior", "outcome": "PASSED"}],
        },
        "REQ-002": {"status": "MISSING", "tests": []},
    }


def test_requirements_can_be_declared_in_pytest_ini(file_project, read_report):
    project = file_project(pytest_ini_inventory)
    project.makefile(".ini", pytest="[pytest]\nxspec =\n    REQ-001\n    REQ-002\n")

    result = project.runpytest_subprocess("--xspec-json=report.json")

    assert result.ret == pytest.ExitCode.OK
    report = read_report(project)
    assert report["requirements"]["REQ-001"]["status"] == "PASSED"
    assert expected(report["requirements"]["REQ-002"]).to_have(status="MISSING", tests=[])


def test_pyproject_inventory_is_read_even_when_pytest_ini_controls_pytest(
    file_project, read_report
):
    project = file_project(pyproject_with_pytest_ini)
    project.makefile(".toml", pyproject='[tool.xspec]\nrequirements = ["REQ-001"]\n')
    project.makefile(".ini", pytest="[pytest]\naddopts = -q\n")

    result = project.runpytest_subprocess("--xspec-strict", "--xspec-json=report.json")

    assert result.ret == 0
    report = read_report(project)
    assert report["requirements"]["REQ-001"]["status"] == "PASSED"


def test_declaring_an_inventory_in_both_supported_files_is_rejected(file_project):
    project = file_project(conflicting_inventories)
    project.makefile(".toml", pyproject='[tool.xspec]\nrequirements = ["REQ-001"]\n')
    project.makefile(".ini", pytest="[pytest]\nxspec =\n    REQ-002\n")

    result = project.runpytest_subprocess("--xspec-report")

    assert result.ret != pytest.ExitCode.OK
    message = result.stdout.str() + result.stderr.str()
    assert "pyproject.toml" in message
    assert "pytest.ini" in message


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("setup.cfg", "[tool:pytest]\nxspec = REQ-001\n"),
        ("tox.ini", "[pytest]\nxspec = REQ-001\n"),
        ("requirements.json", '{"requirements": ["REQ-001"]}'),
        ("requirements.yaml", "requirements:\n  - REQ-001\n"),
    ],
)
def test_other_configuration_files_do_not_supply_a_requirement_inventory(
    file_project, filename, content
):
    project = file_project(unsupported_inventory)
    (project.path / filename).write_text(content, encoding="utf-8")

    result = project.runpytest_subprocess("--xspec-strict")

    assert result.ret != pytest.ExitCode.OK
    message = result.stdout.str() + result.stderr.str()
    assert "REQ-001" in message


def test_normal_pytest_without_requirement_configuration_still_works(file_project):
    project = file_project(without_requirement_configuration)

    result = project.runpytest_subprocess()

    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=1)


def test_no_requirement_configuration_means_success_with_zero_requirements(
    file_project, read_report
):
    project = file_project(zero_requirements_without_configuration)

    result = project.runpytest_subprocess("--xspec-strict", "--xspec-json=report.json")

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


def test_duplicate_requirement_ids_in_pytest_ini_are_rejected(file_project):
    project = file_project(duplicate_ini_ids)
    project.makefile(".ini", pytest="[pytest]\nxspec =\n    REQ-001\n    REQ-001\n")

    result = project.runpytest_subprocess()

    assert result.ret != pytest.ExitCode.OK
    message = result.stdout.str() + result.stderr.str()
    assert "requirements" in message.lower()
    assert "REQ-001" in message


@pytest.mark.parametrize("config_file", ["pyproject.toml", "pytest.ini", None])
def test_unknown_marked_ids_are_rejected_even_when_no_requirements_are_declared(
    file_project, config_file
):
    project = file_project(unknown_id_without_inventory)
    if config_file == "pyproject.toml":
        project.makefile(".toml", pyproject="[tool.xspec]\nrequirements = []\n")

    if config_file == "pytest.ini":
        project.makefile(".ini", pytest="[pytest]\nxspec =\n")

    result = project.runpytest_subprocess()

    assert result.ret != pytest.ExitCode.OK
    message = result.stdout.str() + result.stderr.str()
    assert "UNKNOWN" in message
    assert "test_behavior.py::test_behavior" in message


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("setup.cfg", "[tool:pytest]\nxspec = REQ-001\n"),
        ("tox.ini", "[pytest]\nxspec = REQ-001\n"),
        ("requirements.json", '{"requirements": ["REQ-001"]}'),
        ("requirements.yaml", "requirements:\n  - REQ-001\n"),
    ],
)
def test_unsupported_inventory_files_are_ignored_when_tests_are_unmarked(
    file_project, read_report, filename, content
):
    project = file_project(unmarked_with_unsupported_inventory)
    (project.path / filename).write_text(content, encoding="utf-8")

    result = project.runpytest_subprocess("--xspec-strict", "--xspec-json=report.json")

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


@pytest.mark.parametrize("config_file", ["pyproject.toml", "pytest.ini"])
def test_an_empty_file_inventory_reports_success_with_zero_requirements(
    file_project, read_report, config_file
):
    project = file_project(zero_requirements_without_configuration)
    if config_file == "pyproject.toml":
        project.makefile(".toml", pyproject="[tool.xspec]\nrequirements = []\n")
    else:
        project.makefile(".ini", pytest="[pytest]\nxspec =\n")

    result = project.runpytest_subprocess("--xspec-strict", "--xspec-json=report.json")

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


@pytest.mark.parametrize(
    ("content", "diagnostic"),
    [
        pytest.param(
            '[tool]\nxspec = ["REQ-001"]\n',
            "pyproject.toml: xspec must be a table",
            id="non-table-section",
        ),
        pytest.param(
            "[tool.xspec\n",
            "Cannot read xspec requirements:",
            id="malformed-toml",
        ),
    ],
)
def test_invalid_configuration_structure_is_rejected(file_project, content, diagnostic):
    project = file_project(invalid_inventory)
    project.makefile(".ini", pytest="[pytest]\n")
    project.makefile(".toml", pyproject=content)

    result = project.runpytest_subprocess("-c", "pytest.ini", "--xspec-report")

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    message = result.stdout.str() + result.stderr.str()
    assert diagnostic in message


@pytest.mark.parametrize("inventory", ['"REQ-001"', "[123]", '["REQ-001", "REQ-001"]'])
def test_invalid_requirement_inventory_is_rejected(file_project, inventory):
    project = file_project(invalid_inventory)
    project.makefile(".toml", pyproject=f"[tool.xspec]\nrequirements = {inventory}\n")

    result = project.runpytest_subprocess("--xspec-report")

    assert result.ret != pytest.ExitCode.OK
    message = result.stdout.str() + result.stderr.str()
    assert "unrecognized arguments" not in message.lower()
    assert "requirements" in message.lower()
