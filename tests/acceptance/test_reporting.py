"""Reports show all declared requirements and count verified requirements, not tests."""

import pytest

from tests.acceptance.scenarios.reporting import empty_inventory, summary


def test_terminal_report_shows_requirement_statuses_test_counts_and_coverage(user_project):
    project = user_project(["REQ-001", "REQ-002", "REQ-003"], summary)

    result = project.runpytest_subprocess("--req-report")

    assert result.ret == pytest.ExitCode.OK
    result.stdout.fnmatch_lines(
        [
            "*pytest-reqmark*",
            "*REQ-001*PASSED*2*",
            "*REQ-002*MISSING*0*",
            "*REQ-003*SKIPPED*1*",
            "*Requirements:*3*",
            "*Passed:*1*",
            "*Unverified:*2*",
            "*Coverage:*33.3%*",
        ]
    )


def test_json_report_includes_all_requirements_individual_tests_and_summary(
    user_project, read_report
):
    project = user_project(["REQ-001", "REQ-002", "REQ-003"], summary)

    result = project.runpytest_subprocess("--req-json=report.json")

    assert result.ret == pytest.ExitCode.OK
    report = read_report(project)
    assert report["summary"] == {
        "requirements": 3,
        "passed": 1,
        "unverified": 2,
        "coverage": pytest.approx(100 / 3),
        "verified": False,
        "collection_errors": 0,
    }
    assert report["requirements"] == {
        "REQ-001": {
            "status": "PASSED",
            "tests": [
                {"nodeid": "test_behavior.py::test_first_behavior", "outcome": "PASSED"},
                {"nodeid": "test_behavior.py::test_second_behavior", "outcome": "PASSED"},
            ],
        },
        "REQ-002": {"status": "MISSING", "tests": []},
        "REQ-003": {
            "status": "SKIPPED",
            "tests": [{"nodeid": "test_behavior.py::test_third_behavior", "outcome": "SKIPPED"}],
        },
    }


@pytest.mark.parametrize("config_file", ["pyproject.toml", "pytest.ini"])
def test_an_empty_inventory_reports_zero_coverage_without_dividing_by_zero(
    user_project, read_report, config_file
):
    project = user_project([], empty_inventory)
    if config_file == "pytest.ini":
        (project.path / "pyproject.toml").unlink()
        project.makefile(".ini", pytest="[pytest]\nreq_requirements =\n")

    result = project.runpytest_subprocess("--req-strict", "--req-json=report.json")

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
