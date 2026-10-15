"""Reports show all declared requirements and count verified requirements, not tests."""

import pytest

from tests.acceptance.scenarios.cli import all_requirements_pass, collection_error
from tests.acceptance.scenarios.cli.unmarked_outcomes import failed
from tests.acceptance.scenarios.reporting import empty_inventory, summary


def test_terminal_report_shows_requirement_statuses_test_counts_and_coverage(user_project):
    project = user_project(["REQ-001", "REQ-002", "REQ-003"], summary)

    result = project.runpytest_subprocess("--xspec-report")

    assert result.ret == pytest.ExitCode.OK
    result.stdout.fnmatch_lines(
        [
            "*xspec*",
            "*REQ-001*PASSED*2*",
            "*REQ-002*MISSING*0*",
            "*REQ-003*SKIPPED*1*",
            "*Requirements:*3*",
            "*Passed:*1*",
            "*Unverified:*2*",
            "*Coverage:*33.3%*",
        ]
    )


@pytest.mark.parametrize(
    ("report_option", "expected_exit"),
    [
        pytest.param("--xspec-report", pytest.ExitCode.OK, id="report"),
        pytest.param("--xspec-strict", pytest.ExitCode.TESTS_FAILED, id="strict"),
    ],
)
def test_an_unverified_terminal_report_is_red(user_project, report_option, expected_exit):
    project = user_project(["REQ-001", "REQ-002", "REQ-003"], summary)

    result = project.runpytest_subprocess(report_option, "--color=yes")

    assert result.ret == expected_exit
    result.stdout.fnmatch_lines(
        [
            "\x1b[31m*xspec*\x1b[0m",
            "\x1b[31mRequirement*Status*Tests\x1b[0m",
            "\x1b[31mREQ-001*PASSED*2\x1b[0m",
            "\x1b[31mREQ-002*MISSING*0\x1b[0m",
            "\x1b[31mREQ-003*SKIPPED*1\x1b[0m",
            "\x1b[31mRequirements: 3\x1b[0m",
            "\x1b[31mPassed: 1\x1b[0m",
            "\x1b[31mUnverified: 2\x1b[0m",
            "\x1b[31mCoverage: 33.3%\x1b[0m",
        ]
    )


@pytest.mark.parametrize("report_option", ["--xspec-report", "--xspec-strict"])
def test_collection_errors_make_the_terminal_report_red_even_at_full_coverage(
    user_project, read_report, report_option
):
    project = user_project(["REQ-001"], collection_error)

    result = project.runpytest_subprocess(
        "--continue-on-collection-errors",
        report_option,
        "--color=yes",
        "--xspec-json=report.json",
    )

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    report = read_report(project)
    assert report["summary"]["coverage"] == 100.0
    assert report["summary"]["verified"] is False
    result.stdout.fnmatch_lines(
        [
            "\x1b[31m*xspec*\x1b[0m",
            "\x1b[31mRequirement*Status*Tests\x1b[0m",
            "\x1b[31mREQ-001*PASSED*1\x1b[0m",
            "\x1b[31mRequirements: 1\x1b[0m",
            "\x1b[31mPassed: 1\x1b[0m",
            "\x1b[31mUnverified: 0\x1b[0m",
            "\x1b[31mCoverage: 100.0%\x1b[0m",
            "\x1b[31mCollection errors: 1\x1b[0m",
        ]
    )


@pytest.mark.parametrize(
    ("requirements", "scenario", "expected_exit", "coverage"),
    [
        pytest.param(
            ["REQ-001"], all_requirements_pass, pytest.ExitCode.OK, "100.0%", id="all-verified"
        ),
        pytest.param([], empty_inventory, pytest.ExitCode.OK, "0.0%", id="zero-requirements"),
        pytest.param(
            ["REQ-001"], failed, pytest.ExitCode.TESTS_FAILED, "100.0%", id="unmarked-failure"
        ),
    ],
)
@pytest.mark.parametrize("report_option", ["--xspec-report", "--xspec-strict"])
def test_a_verified_terminal_report_is_green(
    user_project, read_report, requirements, scenario, expected_exit, coverage, report_option
):
    project = user_project(requirements, scenario)

    result = project.runpytest_subprocess(report_option, "--color=yes", "--xspec-json=report.json")

    assert result.ret == expected_exit
    report = read_report(project)
    assert report["summary"]["verified"] is True
    report_start = next(
        index for index, line in enumerate(result.stdout.lines) if " xspec " in line
    )
    report_end = next(
        index for index, line in enumerate(result.stdout.lines) if f"Coverage: {coverage}" in line
    )
    assert all(
        line.startswith("\x1b[32m") and line.endswith("\x1b[0m")
        for line in result.stdout.lines[report_start : report_end + 1]
    )


@pytest.mark.parametrize(
    ("requirements", "scenario", "coverage"),
    [
        pytest.param(["REQ-001"], all_requirements_pass, "100.0%", id="verified"),
        pytest.param(["REQ-001", "REQ-002", "REQ-003"], summary, "33.3%", id="unverified"),
    ],
)
def test_terminal_report_color_can_be_disabled(user_project, requirements, scenario, coverage):
    project = user_project(requirements, scenario)

    result = project.runpytest_subprocess("--xspec-report", "--color=no")

    assert result.ret == pytest.ExitCode.OK
    assert "\x1b[" not in result.stdout.str()
    result.stdout.fnmatch_lines(["*xspec*", f"Coverage: {coverage}"])


def test_json_report_includes_all_requirements_individual_tests_and_summary(
    user_project, read_report
):
    project = user_project(["REQ-001", "REQ-002", "REQ-003"], summary)

    result = project.runpytest_subprocess("--xspec-json=report.json")

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


def test_an_empty_inventory_reports_zero_coverage_without_dividing_by_zero(
    user_project, read_report
):
    project = user_project([], empty_inventory)

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
