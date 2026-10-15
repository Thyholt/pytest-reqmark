"""Strict mode enforces acceptance; pytest retains its ordinary failure behavior."""

from types import ModuleType

import pytest

from tests.acceptance.scenarios.cli import (
    acceptance_only,
    all_requirements_pass,
    collection_error,
    deselected_requirement,
    missing_requirement,
    plain_pytest,
)
from tests.acceptance.scenarios.cli.strict_unverified_outcome import (
    expected_failure,
    failed_test,
    setup_error,
    skipped_test,
    unexpected_pass,
)
from tests.acceptance.scenarios.cli.unmarked_outcomes import failed, skipped
from tests.acceptance.types import ReadReport, UserProject


def test_plain_pytest_runs_normally_without_an_acceptance_report(user_project: UserProject) -> None:
    project = user_project(["REQ-001"], plain_pytest)

    result = project.runpytest_subprocess()

    result.assert_outcomes(passed=1)
    assert result.ret == pytest.ExitCode.OK
    assert " xspec " not in result.stdout.str()


@pytest.mark.parametrize(
    ("scenario", "status"),
    [
        pytest.param(skipped_test, "SKIPPED", id="skipped-test"),
        pytest.param(expected_failure, "XFAILED", id="expected-failure"),
        pytest.param(unexpected_pass, "XPASSED", id="unexpected-pass"),
        pytest.param(failed_test, "FAILED", id="failed-test"),
        pytest.param(setup_error, "ERROR", id="setup-error"),
    ],
)
def test_strict_mode_rejects_every_executed_unverified_outcome(
    user_project: UserProject, scenario: ModuleType, status: str
) -> None:
    project = user_project(["REQ-001"], scenario)

    result = project.runpytest_subprocess("--xspec-strict")

    assert result.ret != pytest.ExitCode.OK
    output = result.stdout.str()
    assert " xspec " in output
    assert status in output


def test_strict_mode_rejects_missing_requirements(user_project: UserProject) -> None:
    project = user_project(["REQ-001"], missing_requirement)

    result = project.runpytest_subprocess("--xspec-strict")

    assert result.ret != pytest.ExitCode.OK
    assert "MISSING" in result.stdout.str()


def test_strict_mode_rejects_deselected_requirement_tests(user_project: UserProject) -> None:
    project = user_project(["REQ-001"], deselected_requirement)

    result = project.runpytest_subprocess("-k", "selected", "--xspec-strict")

    assert result.ret != pytest.ExitCode.OK
    assert "DESELECTED" in result.stdout.str()


def test_strict_mode_succeeds_and_prints_a_report_when_every_requirement_passes(
    user_project: UserProject,
) -> None:
    project = user_project(["REQ-001"], all_requirements_pass)

    result = project.runpytest_subprocess("--xspec-strict")

    assert result.ret == pytest.ExitCode.OK
    output = result.stdout.str()
    assert " xspec " in output
    assert "PASSED" in output


@pytest.mark.parametrize(
    ("scenario", "expected_exit"),
    [
        pytest.param(failed, pytest.ExitCode.TESTS_FAILED, id="assert False"),
        pytest.param(skipped, pytest.ExitCode.OK, id='pytest.skip("optional")'),
    ],
)
def test_unmarked_outcomes_do_not_change_acceptance_verification(
    user_project: UserProject,
    read_report: ReadReport,
    scenario: ModuleType,
    expected_exit: pytest.ExitCode,
) -> None:
    project = user_project(["REQ-001"], scenario)

    result = project.runpytest_subprocess("--xspec-strict", "--xspec-json=report.json")

    report = read_report(project)
    assert report["requirements"]["REQ-001"]["status"] == "PASSED"
    assert report["summary"]["verified"] is True
    assert result.ret == expected_exit


def test_acceptance_only_ci_ignores_failing_unmarked_tests(
    user_project: UserProject, read_report: ReadReport
) -> None:
    project = user_project(["REQ-001"], acceptance_only)

    result = project.runpytest_subprocess(
        "-m", "xspec", "--xspec-strict", "--xspec-json=report.json"
    )

    assert result.ret == pytest.ExitCode.OK
    report = read_report(project)
    assert report["summary"]["unverified"] == 0


def test_a_collection_error_prevents_a_successful_strict_verdict(
    user_project: UserProject, read_report: ReadReport
) -> None:
    project = user_project(["REQ-001"], collection_error)

    result = project.runpytest_subprocess(
        "--continue-on-collection-errors", "--xspec-strict", "--xspec-json=report.json"
    )

    assert result.ret != pytest.ExitCode.OK
    result.stdout.fnmatch_lines(["*xspec*", "*Collection errors:*1*"])
    report = read_report(project)
    assert report["requirements"]["REQ-001"]["status"] == "PASSED"
    assert report["summary"]["verified"] is False
    assert report["summary"]["collection_errors"] == 1
