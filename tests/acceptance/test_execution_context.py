"""Independent suites preserve execution identity and share a requirement specification."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict, cast
from uuid import UUID

import pytest

from tests.acceptance.scenarios.execution_context import project_files, separate_roots
from tests.acceptance.types import AcceptanceReport, FileProject, ReadReport


class Execution(TypedDict):
    schema: int
    id: str
    suite: str
    started_at: str
    finished_at: str
    context: dict[str, str]
    provenance: dict[str, str]


class ExecutionReport(AcceptanceReport):
    execution: Execution


def read_execution_report(path: Path) -> ExecutionReport:
    # Report assertions below verify this public serialization schema.
    return cast(ExecutionReport, json.loads(path.read_text(encoding="utf-8")))


def test_report_preserves_declared_execution_context_and_provenance(
    file_project: FileProject,
) -> None:
    project = file_project(project_files)

    result = project.runpytest_subprocess(
        "-s", "--xspec-context=context.toml", "--xspec-json=report.json"
    )

    assert result.ret == pytest.ExitCode.OK
    assert "BEHAVIOR EXECUTED" in result.stdout.str()
    report = read_execution_report(project.path / "report.json")
    assert report["requirements"] == {
        "REQ-001": {
            "status": "PASSED",
            "tests": [{"nodeid": "test_behavior.py::test_behavior", "outcome": "PASSED"}],
        }
    }
    assert report["execution"]["schema"] == 1
    assert report["execution"]["suite"] == "behavior-suite"
    assert report["execution"]["context"] == {"artifact": "build-1", "configuration": "A"}
    assert report["execution"]["provenance"] == {
        "kind": "simulation",
        "adapter": "example-adapter-1",
    }
    assert str(UUID(report["execution"]["id"])) == report["execution"]["id"]
    started = datetime.fromisoformat(report["execution"]["started_at"].replace("Z", "+00:00"))
    finished = datetime.fromisoformat(report["execution"]["finished_at"].replace("Z", "+00:00"))
    assert started.tzinfo == timezone.utc
    assert finished.tzinfo == timezone.utc
    assert started <= finished


def test_repeated_executions_keep_distinct_identities_for_the_same_test(
    file_project: FileProject,
) -> None:
    project = file_project(project_files)

    first = project.runpytest_subprocess("--xspec-context=context.toml", "--xspec-json=first.json")
    second = project.runpytest_subprocess(
        "--xspec-context=context.toml", "--xspec-json=second.json"
    )

    assert first.ret == second.ret == pytest.ExitCode.OK
    first_report = read_execution_report(project.path / "first.json")
    second_report = read_execution_report(project.path / "second.json")
    assert first_report["execution"]["id"] != second_report["execution"]["id"]
    assert first_report["execution"]["context"] == second_report["execution"]["context"]
    assert (
        first_report["requirements"]
        == second_report["requirements"]
        == {
            "REQ-001": {
                "status": "PASSED",
                "tests": [{"nodeid": "test_behavior.py::test_behavior", "outcome": "PASSED"}],
            }
        }
    )


def test_execution_metadata_is_optional_for_existing_report_consumers(
    file_project: FileProject, read_report: ReadReport
) -> None:
    project = file_project(project_files)

    result = project.runpytest_subprocess("--xspec-json=report.json")

    assert result.ret == pytest.ExitCode.OK
    report = read_report(project)
    assert report == {
        "requirements": {
            "REQ-001": {
                "status": "PASSED",
                "tests": [{"nodeid": "test_behavior.py::test_behavior", "outcome": "PASSED"}],
            }
        },
        "summary": {
            "requirements": 1,
            "passed": 1,
            "unverified": 0,
            "coverage": 100.0,
            "verified": True,
            "collection_errors": 0,
        },
    }


@pytest.mark.parametrize(
    ("context_file", "diagnostic"),
    [
        ("missing-suite.toml", "suite"),
        ("invalid-context.toml", "context"),
        ("invalid-provenance.toml", "provenance"),
        ("malformed.toml.invalid", "context"),
    ],
)
def test_invalid_execution_context_is_rejected_before_tests_execute(
    file_project: FileProject, context_file: str, diagnostic: str
) -> None:
    project = file_project(project_files)

    valid = project.runpytest_subprocess("-s", "--xspec-context=context.toml")
    invalid = project.runpytest_subprocess("-s", f"--xspec-context={context_file}")

    assert valid.ret == pytest.ExitCode.OK
    assert "BEHAVIOR EXECUTED" in valid.stdout.str()
    assert invalid.ret == pytest.ExitCode.USAGE_ERROR
    message = invalid.stdout.str() + invalid.stderr.str()
    assert "unrecognized arguments" not in message.lower()
    assert diagnostic in message.lower()
    assert context_file in message
    assert "BEHAVIOR EXECUTED" not in invalid.stdout.str()


def test_independent_pytest_roots_use_an_explicit_shared_specification(
    file_project: FileProject,
) -> None:
    project = file_project(separate_roots)

    first = project.runpytest_subprocess(
        "-c",
        "suite_a/pyproject.toml",
        "suite_a/test_behavior.py",
        "--xspec-spec=shared.toml",
        "--xspec-json=first.json",
        "--xspec-strict",
    )
    second = project.runpytest_subprocess(
        "-c",
        "suite_b/pyproject.toml",
        "suite_b/test_behavior.py",
        "--xspec-spec=shared.toml",
        "--xspec-json=second.json",
        "--xspec-strict",
    )

    assert first.ret == second.ret == pytest.ExitCode.OK
    assert read_execution_report(project.path / "first.json")["requirements"] == {
        "REQ-001": {
            "status": "PASSED",
            "tests": [{"nodeid": "test_behavior.py::test_behavior", "outcome": "PASSED"}],
        }
    }
    assert read_execution_report(project.path / "second.json")["requirements"] == {
        "REQ-001": {
            "status": "PASSED",
            "tests": [{"nodeid": "test_behavior.py::test_behavior", "outcome": "PASSED"}],
        }
    }


def test_passing_children_do_not_verify_their_parent_requirement(
    file_project: FileProject, read_report: ReadReport
) -> None:
    project = file_project(project_files)

    result = project.runpytest_subprocess(
        "--xspec-spec=hierarchy.toml", "--xspec-strict", "--xspec-json=report.json"
    )

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    report = read_report(project)
    assert report["requirements"] == {
        "REQ-000": {"status": "MISSING", "tests": []},
        "REQ-001": {
            "status": "PASSED",
            "tests": [{"nodeid": "test_behavior.py::test_behavior", "outcome": "PASSED"}],
        },
    }
    assert report["summary"]["verified"] is False


@pytest.mark.parametrize("spec_file", ["unknown-parent.toml", "cyclic-parents.toml"])
def test_invalid_parent_relationships_are_rejected_before_tests_execute(
    file_project: FileProject, spec_file: str
) -> None:
    project = file_project(project_files)

    valid = project.runpytest_subprocess("-s", "--xspec-spec=hierarchy.toml")
    invalid = project.runpytest_subprocess("-s", f"--xspec-spec={spec_file}")

    assert valid.ret == pytest.ExitCode.OK
    assert "BEHAVIOR EXECUTED" in valid.stdout.str()
    assert invalid.ret == pytest.ExitCode.USAGE_ERROR
    message = invalid.stdout.str() + invalid.stderr.str()
    assert "unrecognized arguments" not in message.lower()
    assert "parent" in message.lower()
    assert spec_file in message
    assert "BEHAVIOR EXECUTED" not in invalid.stdout.str()
