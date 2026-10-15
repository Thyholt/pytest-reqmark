"""Users keep requirements in a TOML document when no other inventory is declared."""

from pathlib import Path
from shutil import copyfile

import pytest

from tests.acceptance.expectations import expected
from tests.acceptance.scenarios.configuration import (
    document_requirements,
    document_validation,
    pyproject_with_pytest_ini,
    specification_documents,
)
from tests.acceptance.types import FileProject, ReadReport

DOCUMENTS = Path(specification_documents.__path__[0])


@pytest.mark.parametrize(
    "document",
    [
        pytest.param(
            "requirements.toml",
            id="one-table-per-requirement",
        ),
        pytest.param(
            "inline_requirements.toml",
            id="equivalent-inline-tables",
        ),
    ],
)
def test_a_user_can_verify_requirements_from_a_document_without_reporting_its_metadata(
    file_project: FileProject, read_report: ReadReport, document: str
) -> None:
    project = file_project(document_requirements)
    copyfile(DOCUMENTS / document, project.path / "xspec.toml")

    result = project.runpytest_subprocess("--xspec-strict", "--xspec-json=report.json")

    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=2)
    report = read_report(project)
    assert list(report["requirements"]) == ["REQ-002", "REQ-001"]
    assert report == {
        "requirements": {
            "REQ-002": {
                "status": "PASSED",
                "tests": [
                    {"nodeid": "test_behavior.py::test_second_behavior", "outcome": "PASSED"}
                ],
            },
            "REQ-001": {
                "status": "PASSED",
                "tests": [{"nodeid": "test_behavior.py::test_first_behavior", "outcome": "PASSED"}],
            },
        },
        "summary": {
            "requirements": 2,
            "passed": 2,
            "unverified": 0,
            "coverage": 100.0,
            "verified": True,
            "collection_errors": 0,
        },
    }
    result.stdout.fnmatch_lines(["*REQ-002*PASSED*1*", "*REQ-001*PASSED*1*"])
    assert "Description from the document." not in result.stdout.str()
    assert "Rationale from the document." not in result.stdout.str()
    assert "Document owner" not in result.stdout.str()


def test_the_project_document_is_used_even_when_running_from_a_subdirectory(
    file_project: FileProject, read_report: ReadReport, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = file_project(document_requirements)
    project.makefile(".ini", pytest="[pytest]\n")
    copyfile(DOCUMENTS / "no_inventory.toml", project.path / "pyproject.toml")
    copyfile(DOCUMENTS / "requirement_ids.toml", project.path / "xspec.toml")
    subdirectory = project.path / "working_directory"
    subdirectory.mkdir()
    copyfile(DOCUMENTS / "malformed.toml.invalid", subdirectory / "xspec.toml")
    monkeypatch.chdir(subdirectory)

    result = project.runpytest_subprocess(
        "-c",
        project.path / "pytest.ini",
        project.path / "test_behavior.py",
        "--xspec-strict",
        f"--xspec-json={project.path / 'report.json'}",
    )

    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=2)
    report = read_report(project)
    assert list(report["requirements"]) == ["REQ-001", "REQ-002"]
    assert expected(report["requirements"]["REQ-001"]).to_have(
        status="PASSED", tests=[("test_behavior.py::test_first_behavior", "PASSED")]
    )
    assert expected(report["requirements"]["REQ-002"]).to_have(
        status="PASSED", tests=[("test_behavior.py::test_second_behavior", "PASSED")]
    )


@pytest.mark.parametrize(
    ("filename", "configuration"),
    [
        pytest.param("pyproject.toml", "explicit_inventory.toml", id="pyproject"),
        pytest.param("pytest.ini", "explicit_inventory.ini", id="pytest-ini"),
    ],
)
@pytest.mark.parametrize(
    "document",
    [
        pytest.param("other_requirements.toml", id="different-requirements"),
        pytest.param("malformed.toml.invalid", id="malformed-document"),
    ],
)
def test_an_explicit_inventory_takes_precedence_over_the_document(
    file_project: FileProject,
    read_report: ReadReport,
    filename: str,
    configuration: str,
    document: str,
) -> None:
    project = file_project(pyproject_with_pytest_ini)
    copyfile(DOCUMENTS / configuration, project.path / filename)
    copyfile(DOCUMENTS / document, project.path / "xspec.toml")

    result = project.runpytest_subprocess("--xspec-strict", "--xspec-json=report.json")

    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=1)
    report = read_report(project)
    assert list(report["requirements"]) == ["REQ-001"]
    assert expected(report["requirements"]["REQ-001"]).to_have(
        status="PASSED", tests=[("test_behavior.py::test_behavior", "PASSED")]
    )


@pytest.mark.parametrize(
    ("document", "diagnostic"),
    [
        pytest.param("malformed.toml.invalid", "xspec.toml", id="malformed-toml"),
        pytest.param("missing_requirements.toml", "requirements", id="no-requirements-section"),
        pytest.param(
            "duplicate_requirements.toml",
            "duplicate",
            id="duplicate-code",
        ),
    ],
)
def test_an_invalid_document_is_explained_before_any_tests_run(
    file_project: FileProject, document: str, diagnostic: str
) -> None:
    project = file_project(document_validation)
    copyfile(DOCUMENTS / document, project.path / "xspec.toml")

    result = project.runpytest_subprocess("-s", "--xspec-report")

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    message = result.stdout.str() + result.stderr.str()
    assert "xspec.toml" in message
    assert diagnostic in message.lower()
    assert "DOCUMENT_TEST_EXECUTED" not in result.stdout.str()


def test_a_document_can_explicitly_declare_zero_requirements(
    file_project: FileProject, read_report: ReadReport
) -> None:
    project = file_project(document_validation)
    copyfile(DOCUMENTS / "zero_requirements.toml", project.path / "xspec.toml")

    result = project.runpytest_subprocess("-s", "--xspec-strict", "--xspec-json=report.json")

    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=1)
    assert "DOCUMENT_TEST_EXECUTED" in result.stdout.str()
    report = read_report(project)
    assert report["requirements"] == {}
    assert report["summary"]["verified"] is True
    assert report["summary"]["coverage"] == 0.0
