"""Users can see why a requirement is or is not verified."""

import pytest

from tests.acceptance.expectations import expected
from tests.acceptance.scenarios.statuses import (
    assertion_with_xpass_text,
    both_tests_pass,
    deselection_over_pass,
    early_stop,
    failure_over_xpass,
    fixture_skip,
    setup_error_over_failure,
    setup_xfail,
    skip_over_deselection,
    strict_xpass,
    teardown_error_after_failure,
    teardown_error_after_pass,
    teardown_xfail,
    xfail_over_skip,
    xpass_over_xfail,
)
from tests.acceptance.scenarios.statuses.partial_verification import (
    one_failed_test,
    one_skipped_test,
    one_unexecuted_test,
)
from tests.acceptance.scenarios.statuses.reported_outcome import (
    expected_failure,
    failed_test,
    passing_test,
    setup_error,
    skipped_test,
    unexpected_pass,
)


@pytest.mark.parametrize(
    ("scenario", "status"),
    [
        pytest.param(passing_test, "PASSED", id="passing-test"),
        pytest.param(failed_test, "FAILED", id="failed-test"),
        pytest.param(setup_error, "ERROR", id="setup-error"),
        pytest.param(skipped_test, "SKIPPED", id="skipped-test"),
        pytest.param(expected_failure, "XFAILED", id="expected-failure"),
        pytest.param(unexpected_pass, "XPASSED", id="unexpected-pass"),
    ],
)
def test_the_report_explains_the_outcome_of_a_marked_test(
    user_project, read_report, scenario, status
):
    project = user_project(["REQ-001"], scenario)

    project.runpytest_subprocess("--xspec-json=report.json")

    report = read_report(project)
    assert expected(report["requirements"]["REQ-001"]).to_have(
        status=status, tests=[("test_behavior.py::test_behavior", status)]
    )
    assert report["summary"]["verified"] is (status == "PASSED")


def test_teardown_errors_make_a_passing_test_unverified(user_project, read_report):
    project = user_project(["REQ-001"], teardown_error_after_pass)

    result = project.runpytest_subprocess("--xspec-json=report.json")

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    report = read_report(project)
    assert expected(report["requirements"]["REQ-001"]).to_have(
        status="ERROR", tests=[("test_behavior.py::test_behavior", "ERROR")]
    )


def test_teardown_errors_take_precedence_over_a_test_failure(user_project, read_report):
    project = user_project(["REQ-001"], teardown_error_after_failure)

    result = project.runpytest_subprocess("--xspec-json=report.json")

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    report = read_report(project)
    assert expected(report["requirements"]["REQ-001"]).to_have(
        status="ERROR", tests=[("test_behavior.py::test_behavior", "ERROR")]
    )


def test_a_fixture_skip_is_reported_as_skipped(user_project, read_report):
    project = user_project(["REQ-001"], fixture_skip)

    result = project.runpytest_subprocess("--xspec-json=report.json")

    assert result.ret == pytest.ExitCode.OK
    report = read_report(project)
    assert expected(report["requirements"]["REQ-001"]).to_have(
        status="SKIPPED",
        tests=[("test_behavior.py::test_behavior", "SKIPPED")],
    )


@pytest.mark.parametrize(
    "scenario",
    [pytest.param(setup_xfail, id="setup"), pytest.param(teardown_xfail, id="teardown")],
)
@pytest.mark.parametrize(
    ("options", "expected_exit"),
    [
        pytest.param((), pytest.ExitCode.OK, id="report"),
        pytest.param(("--xspec-strict",), pytest.ExitCode.TESTS_FAILED, id="strict"),
    ],
)
def test_fixture_expected_failures_are_xfailed_and_keep_requirements_unverified(
    user_project, read_report, scenario, options, expected_exit
):
    project = user_project(["REQ-001"], scenario)

    result = project.runpytest_subprocess("--xspec-json=report.json", *options)

    assert result.ret == expected_exit
    report = read_report(project)
    assert expected(report["requirements"]["REQ-001"]).to_have(
        status="XFAILED", tests=[("test_behavior.py::test_behavior", "XFAILED")]
    )
    assert report["summary"]["verified"] is False


def test_strict_xfail_still_reports_an_unexpected_pass_as_xpassed(user_project, read_report):
    project = user_project(["REQ-001"], strict_xpass)

    result = project.runpytest_subprocess("--xspec-json=report.json")

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    report = read_report(project)
    assert expected(report["requirements"]["REQ-001"]).to_have(
        status="XPASSED",
        tests=[("test_behavior.py::test_behavior", "XPASSED")],
    )


def test_an_assertion_mentioning_xpass_is_reported_as_failed(user_project, read_report):
    project = user_project(["REQ-001"], assertion_with_xpass_text)

    result = project.runpytest_subprocess("--xspec-strict", "--xspec-json=report.json")

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    report = read_report(project)
    assert expected(report["requirements"]["REQ-001"]).to_have(
        status="FAILED", tests=[("test_behavior.py::test_behavior", "FAILED")]
    )
    assert report["summary"]["verified"] is False


@pytest.mark.parametrize(
    "test_order",
    [("test_setup_error", "test_failure"), ("test_failure", "test_setup_error")],
)
def test_setup_errors_take_priority_over_test_failures(user_project, read_report, test_order):
    project = user_project(["REQ-001"], setup_error_over_failure)
    node_ids = [f"test_behavior.py::{name}" for name in test_order]
    expected_outcomes = {
        "test_behavior.py::test_setup_error": "ERROR",
        "test_behavior.py::test_failure": "FAILED",
    }
    expected_tests = [(node_id, expected_outcomes[node_id]) for node_id in node_ids]

    result = project.runpytest_subprocess("--xspec-json=report.json", *node_ids)

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    report = read_report(project)
    assert expected(report["requirements"]["REQ-001"]).to_have(status="ERROR", tests=expected_tests)


@pytest.mark.parametrize(
    "test_order",
    [("test_failure", "test_unexpected_pass"), ("test_unexpected_pass", "test_failure")],
)
def test_failures_take_priority_over_unexpected_passes(user_project, read_report, test_order):
    project = user_project(["REQ-001"], failure_over_xpass)
    node_ids = [f"test_behavior.py::{name}" for name in test_order]
    expected_outcomes = {
        "test_behavior.py::test_failure": "FAILED",
        "test_behavior.py::test_unexpected_pass": "XPASSED",
    }
    expected_tests = [(node_id, expected_outcomes[node_id]) for node_id in node_ids]

    result = project.runpytest_subprocess("--xspec-json=report.json", *node_ids)

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    report = read_report(project)
    assert expected(report["requirements"]["REQ-001"]).to_have(
        status="FAILED", tests=expected_tests
    )


@pytest.mark.parametrize(
    "test_order",
    [
        ("test_unexpected_pass", "test_expected_failure"),
        ("test_expected_failure", "test_unexpected_pass"),
    ],
)
def test_unexpected_passes_take_priority_over_expected_failures(
    user_project, read_report, test_order
):
    project = user_project(["REQ-001"], xpass_over_xfail)
    node_ids = [f"test_behavior.py::{name}" for name in test_order]
    expected_outcomes = {
        "test_behavior.py::test_unexpected_pass": "XPASSED",
        "test_behavior.py::test_expected_failure": "XFAILED",
    }
    expected_tests = [(node_id, expected_outcomes[node_id]) for node_id in node_ids]

    result = project.runpytest_subprocess("--xspec-json=report.json", *node_ids)

    assert result.ret == pytest.ExitCode.OK
    report = read_report(project)
    assert expected(report["requirements"]["REQ-001"]).to_have(
        status="XPASSED", tests=expected_tests
    )


@pytest.mark.parametrize(
    "test_order",
    [("test_expected_failure", "test_skipped"), ("test_skipped", "test_expected_failure")],
)
def test_expected_failures_take_priority_over_skips(user_project, read_report, test_order):
    project = user_project(["REQ-001"], xfail_over_skip)
    node_ids = [f"test_behavior.py::{name}" for name in test_order]
    expected_outcomes = {
        "test_behavior.py::test_expected_failure": "XFAILED",
        "test_behavior.py::test_skipped": "SKIPPED",
    }
    expected_tests = [(node_id, expected_outcomes[node_id]) for node_id in node_ids]

    result = project.runpytest_subprocess("--xspec-json=report.json", *node_ids)

    assert result.ret == pytest.ExitCode.OK
    report = read_report(project)
    assert expected(report["requirements"]["REQ-001"]).to_have(
        status="XFAILED", tests=expected_tests
    )


@pytest.mark.parametrize(
    "test_order",
    [("test_skipped", "test_excluded"), ("test_excluded", "test_skipped")],
)
def test_skips_take_priority_over_deselection(user_project, read_report, test_order):
    project = user_project(["REQ-001"], skip_over_deselection)
    node_ids = [f"test_behavior.py::{name}" for name in test_order]
    expected_outcomes = {
        "test_behavior.py::test_skipped": "SKIPPED",
        "test_behavior.py::test_excluded": "DESELECTED",
    }
    expected_tests = [(node_id, expected_outcomes[node_id]) for node_id in node_ids]

    result = project.runpytest_subprocess(
        "--xspec-json=report.json", *node_ids, "-k", "not excluded"
    )

    assert result.ret == pytest.ExitCode.OK
    report = read_report(project)
    assert expected(report["requirements"]["REQ-001"]).to_have(
        status="SKIPPED", tests=expected_tests
    )


@pytest.mark.parametrize(
    "test_order",
    [("test_excluded", "test_passed"), ("test_passed", "test_excluded")],
)
def test_deselection_prevents_verification_despite_a_passing_test(
    user_project, read_report, test_order
):
    project = user_project(["REQ-001"], deselection_over_pass)
    node_ids = [f"test_behavior.py::{name}" for name in test_order]
    expected_outcomes = {
        "test_behavior.py::test_excluded": "DESELECTED",
        "test_behavior.py::test_passed": "PASSED",
    }
    expected_tests = [(node_id, expected_outcomes[node_id]) for node_id in node_ids]

    result = project.runpytest_subprocess(
        "--xspec-json=report.json", *node_ids, "-k", "not excluded"
    )

    assert result.ret == pytest.ExitCode.OK
    report = read_report(project)
    assert expected(report["requirements"]["REQ-001"]).to_have(
        status="DESELECTED", tests=expected_tests
    )


def test_a_requirement_is_verified_when_both_associated_tests_pass(user_project, read_report):
    project = user_project(["REQ-001"], both_tests_pass)

    result = project.runpytest_subprocess("--xspec-strict", "--xspec-json=report.json")

    assert result.ret == pytest.ExitCode.OK
    report = read_report(project)
    assert expected(report["requirements"]["REQ-001"]).to_have(
        status="PASSED",
        tests=[
            ("test_behavior.py::test_first", "PASSED"),
            ("test_behavior.py::test_second", "PASSED"),
        ],
    )
    assert report["summary"]["verified"] is True


@pytest.mark.parametrize(
    ("scenario", "status"),
    [
        pytest.param(one_failed_test, "FAILED", id="one-failed-test"),
        pytest.param(one_skipped_test, "SKIPPED", id="one-skipped-test"),
    ],
)
def test_one_passing_test_does_not_verify_a_requirement_with_an_unverified_test(
    user_project, read_report, scenario, status
):
    project = user_project(["REQ-001"], scenario)

    result = project.runpytest_subprocess("--xspec-strict", "--xspec-json=report.json")

    assert result.ret != pytest.ExitCode.OK
    report = read_report(project)
    assert expected(report["requirements"]["REQ-001"]).to_have(
        status=status,
        tests=[
            ("test_behavior.py::test_first", "PASSED"),
            ("test_behavior.py::test_second", status),
        ],
    )
    assert report["summary"]["verified"] is False


def test_collect_only_keeps_associated_tests_unverified(user_project, read_report):
    project = user_project(["REQ-001"], both_tests_pass)

    result = project.runpytest_subprocess(
        "--collect-only", "--xspec-strict", "--xspec-json=report.json"
    )

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    report = read_report(project)
    assert expected(report["requirements"]["REQ-001"]).to_have(
        status="SKIPPED",
        tests=[
            ("test_behavior.py::test_first", "SKIPPED"),
            ("test_behavior.py::test_second", "SKIPPED"),
        ],
    )
    assert report["summary"]["verified"] is False


def test_early_stop_reports_a_collected_but_unexecuted_test_as_skipped(user_project, read_report):
    project = user_project(["REQ-001", "REQ-002"], early_stop)

    result = project.runpytest_subprocess(
        "--maxfail=1", "--xspec-strict", "--xspec-json=report.json"
    )

    assert result.ret != pytest.ExitCode.OK
    report = read_report(project)
    assert expected(report["requirements"]["REQ-001"]).to_have(
        status="FAILED", tests=[("test_behavior.py::test_first", "FAILED")]
    )
    assert expected(report["requirements"]["REQ-002"]).to_have(
        status="SKIPPED", tests=[("test_behavior.py::test_second", "SKIPPED")]
    )
    assert report["summary"]["verified"] is False


@pytest.mark.parametrize(
    "test_order", [("test_first", "test_second"), ("test_second", "test_first")]
)
def test_a_passing_test_does_not_verify_a_requirement_when_another_test_never_runs(
    user_project, read_report, test_order
):
    project = user_project(["REQ-001"], one_unexecuted_test)
    node_ids = [
        f"test_behavior.py::{test_order[0]}",
        "test_behavior.py::test_unmarked_failure",
        f"test_behavior.py::{test_order[1]}",
    ]

    result = project.runpytest_subprocess(
        "--maxfail=1", "--xspec-strict", "--xspec-json=report.json", *node_ids
    )

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    report = read_report(project)
    assert expected(report["requirements"]["REQ-001"]).to_have(
        status="SKIPPED", tests=[(node_ids[0], "PASSED"), (node_ids[2], "SKIPPED")]
    )
    assert report["summary"] == {
        "requirements": 1,
        "passed": 0,
        "unverified": 1,
        "coverage": 0.0,
        "verified": False,
        "collection_errors": 0,
    }
