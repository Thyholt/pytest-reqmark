"""Requirement predicates compare complete reports without modifying them."""

from copy import deepcopy

import pytest

from tests.acceptance.expectations import expected


@pytest.mark.parametrize(
    ("requirement", "status", "expected_tests"),
    [
        pytest.param(
            {
                "status": "PASSED",
                "tests": [
                    {"nodeid": "test_behavior.py::test_first", "outcome": "PASSED"},
                    {"nodeid": "test_behavior.py::test_second", "outcome": "PASSED"},
                ],
            },
            "PASSED",
            [
                ("test_behavior.py::test_first", "PASSED"),
                ("test_behavior.py::test_second", "PASSED"),
            ],
            id="associated-tests",
        ),
        pytest.param({"status": "MISSING", "tests": []}, "MISSING", [], id="no-associated-tests"),
    ],
)
def test_matching_requirement_reports_are_accepted(requirement, status, expected_tests):
    expectation = expected(requirement)

    matches = expectation.to_have(status=status, tests=expected_tests)

    assert matches is True


@pytest.mark.parametrize(
    "requirement",
    [
        pytest.param(
            {
                "status": "FAILED",
                "tests": [
                    {"nodeid": "test_behavior.py::test_first", "outcome": "PASSED"},
                    {"nodeid": "test_behavior.py::test_second", "outcome": "PASSED"},
                ],
            },
            id="wrong-status",
        ),
        pytest.param(
            {
                "status": "PASSED",
                "tests": [
                    {"nodeid": "test_behavior.py::test_other", "outcome": "PASSED"},
                    {"nodeid": "test_behavior.py::test_second", "outcome": "PASSED"},
                ],
            },
            id="wrong-identity",
        ),
        pytest.param(
            {
                "status": "PASSED",
                "tests": [
                    {"nodeid": "test_behavior.py::test_first", "outcome": "FAILED"},
                    {"nodeid": "test_behavior.py::test_second", "outcome": "PASSED"},
                ],
            },
            id="wrong-outcome",
        ),
        pytest.param(
            {
                "status": "PASSED",
                "tests": [{"nodeid": "test_behavior.py::test_first", "outcome": "PASSED"}],
            },
            id="omitted-test",
        ),
        pytest.param(
            {
                "status": "PASSED",
                "tests": [
                    {"nodeid": "test_behavior.py::test_second", "outcome": "PASSED"},
                    {"nodeid": "test_behavior.py::test_first", "outcome": "PASSED"},
                ],
            },
            id="reordered-tests",
        ),
        pytest.param(
            {
                "status": "PASSED",
                "tests": [
                    {"nodeid": "test_behavior.py::test_first", "outcome": "PASSED"},
                    {"nodeid": "test_behavior.py::test_second", "outcome": "PASSED"},
                    {"nodeid": "test_behavior.py::test_first", "outcome": "PASSED"},
                ],
            },
            id="duplicated-test",
        ),
        pytest.param(
            {
                "tests": [
                    {"nodeid": "test_behavior.py::test_first", "outcome": "PASSED"},
                    {"nodeid": "test_behavior.py::test_second", "outcome": "PASSED"},
                ],
            },
            id="missing-status-field",
        ),
        pytest.param({"status": "PASSED"}, id="missing-tests-field"),
        pytest.param(
            {
                "status": "PASSED",
                "tests": [
                    {"nodeid": "test_behavior.py::test_first", "outcome": "PASSED"},
                    {"nodeid": "test_behavior.py::test_second", "outcome": "PASSED"},
                ],
                "unexpected": True,
            },
            id="unexpected-field",
        ),
    ],
)
def test_incorrect_or_incomplete_requirement_reports_are_rejected(requirement):
    expectation = expected(requirement)
    expected_tests = [
        ("test_behavior.py::test_first", "PASSED"),
        ("test_behavior.py::test_second", "PASSED"),
    ]

    matches = expectation.to_have(status="PASSED", tests=expected_tests)

    assert matches is False


@pytest.mark.parametrize(
    ("actual_status", "actual_nodeid"),
    [
        pytest.param("FAILED", "test_behavior.py::test_first", id="wrong-status"),
        pytest.param("PASSED", "test_behavior.py::test_other", id="wrong-identity"),
    ],
)
def test_checking_a_requirement_does_not_modify_the_report(actual_status, actual_nodeid):
    requirement = {
        "status": actual_status,
        "tests": [{"nodeid": actual_nodeid, "outcome": "PASSED"}],
    }
    original = deepcopy(requirement)
    expectation = expected(requirement)
    expected_tests = [("test_behavior.py::test_first", "PASSED")]

    matches = expectation.to_have(status="PASSED", tests=expected_tests)

    assert matches is False
    assert requirement == original
