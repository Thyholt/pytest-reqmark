"""Strict mode enforces acceptance; pytest retains its ordinary failure behavior."""

import pytest

from test_statuses import SCENARIOS


def test_plain_pytest_runs_normally_without_an_acceptance_report(user_project):
    project = user_project(["REQ-001"], "def test_unmarked():\n    pass\n")
    result = project.runpytest_subprocess()
    result.assert_outcomes(passed=1)
    assert result.ret == pytest.ExitCode.OK
    assert "pytest-reqmark" not in result.stdout.str()


@pytest.mark.parametrize("status", ["SKIPPED", "XFAILED", "XPASSED", "FAILED", "ERROR"])
def test_strict_mode_rejects_every_executed_unverified_outcome(user_project, status):
    tests, fixtures = SCENARIOS[status]
    project = user_project(["REQ-001"], '@pytest.mark.req("REQ-001")\n' + tests, fixtures=fixtures)
    result = project.runpytest_subprocess("--req-strict")
    assert result.ret != pytest.ExitCode.OK
    assert "pytest-reqmark" in result.stdout.str()
    assert status in result.stdout.str()


def test_strict_mode_rejects_missing_requirements(user_project):
    project = user_project(["REQ-001"], "def test_unmarked():\n    pass\n")
    result = project.runpytest_subprocess("--req-strict")
    assert result.ret != pytest.ExitCode.OK
    assert "MISSING" in result.stdout.str()


def test_strict_mode_rejects_deselected_requirement_tests(user_project):
    project = user_project(
        ["REQ-001"],
        '@pytest.mark.req("REQ-001")\ndef test_marked():\n    pass\n'
        "\ndef test_selected():\n    pass\n",
    )
    result = project.runpytest_subprocess("-k", "selected", "--req-strict")
    assert result.ret != pytest.ExitCode.OK
    assert "DESELECTED" in result.stdout.str()


def test_strict_mode_succeeds_and_prints_a_report_when_every_requirement_passes(user_project):
    project = user_project(
        ["REQ-001"], '@pytest.mark.req("REQ-001")\ndef test_behavior():\n    pass\n'
    )
    result = project.runpytest_subprocess("--req-strict")
    assert result.ret == pytest.ExitCode.OK
    assert "pytest-reqmark" in result.stdout.str()
    assert "PASSED" in result.stdout.str()


@pytest.mark.parametrize("unmarked", ["assert False", 'pytest.skip("optional")'])
def test_unmarked_outcomes_do_not_change_acceptance_verification(
    user_project, read_report, unmarked
):
    project = user_project(
        ["REQ-001"],
        '@pytest.mark.req("REQ-001")\ndef test_marked():\n    pass\n'
        f"\ndef test_unmarked():\n    {unmarked}\n",
    )
    result = project.runpytest_subprocess("--req-strict", "--req-json=report.json")
    report = read_report(project)
    assert report["requirements"]["REQ-001"]["status"] == "PASSED"
    assert report["summary"]["verified"] is True
    expected = pytest.ExitCode.TESTS_FAILED if unmarked == "assert False" else pytest.ExitCode.OK
    assert result.ret == expected


def test_acceptance_only_ci_ignores_failing_unmarked_tests(user_project, read_report):
    project = user_project(
        ["REQ-001"],
        '@pytest.mark.req("REQ-001")\ndef test_marked():\n    pass\n'
        "\ndef test_unmarked():\n    assert False\n",
    )
    result = project.runpytest_subprocess("-m", "req", "--req-strict", "--req-json=report.json")
    assert result.ret == pytest.ExitCode.OK
    assert read_report(project)["summary"]["unverified"] == 0


def test_a_collection_error_prevents_a_successful_strict_verdict(user_project, read_report):
    project = user_project(
        ["REQ-001"], '@pytest.mark.req("REQ-001")\ndef test_behavior():\n    pass\n'
    )
    project.makepyfile(test_broken="raise RuntimeError('collection failed')")
    result = project.runpytest_subprocess(
        "--continue-on-collection-errors", "--req-strict", "--req-json=report.json"
    )
    assert result.ret != pytest.ExitCode.OK
    result.stdout.fnmatch_lines(["*pytest-reqmark*", "*Collection errors:*1*"])
    report = read_report(project)
    assert report["requirements"]["REQ-001"]["status"] == "PASSED"
    assert report["summary"]["verified"] is False
    assert report["summary"]["collection_errors"] == 1
