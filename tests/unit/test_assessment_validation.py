"""Saved evidence is validated before it can influence verification decisions."""

import pytest

from pytest_xspec.assessment import assess
from pytest_xspec.assessment_io import (
    Obligation,
    Plan,
    Target,
    validate_execution,
    validate_run,
)


def execution_document() -> dict[str, object]:
    return {
        "schema": 1,
        "id": "a1111111-1111-4111-8111-111111111111",
        "suite": "behavior",
        "started_at": "2026-10-16T10:00:00+00:00",
        "finished_at": "2026-10-16T10:00:01+00:00",
        "context": {"artifact": "build-1", "configuration": "A"},
        "provenance": {"kind": "simulation"},
    }


def report_document() -> dict[str, object]:
    return {
        "execution": execution_document(),
        "requirements": {
            "REQ-001": {
                "status": "PASSED",
                "tests": [{"nodeid": "test_behavior.py::test_behavior", "outcome": "PASSED"}],
            }
        },
        "summary": {"verified": True, "coverage": 100.0, "collection_errors": 0},
    }


@pytest.fixture
def plan() -> Plan:
    return Plan(
        source="specification",
        requirements=["REQ-001", "REQ-002"],
        configurations={"A": {"configuration": "A"}},
        obligations=[
            Obligation("behavior-A", "REQ-001", "behavior", "A"),
            Obligation("related-A", "REQ-002", "behavior", "A"),
        ],
    )


def test_execution_preserves_context_and_provenance() -> None:
    document = execution_document()

    execution = validate_execution(document, "report.json")

    assert execution == document


def test_execution_accepts_missing_optional_provenance() -> None:
    document = execution_document()
    del document["provenance"]

    execution = validate_execution(document, "report.json")

    assert execution["provenance"] == {}
    assert execution["context"] == {"artifact": "build-1", "configuration": "A"}


@pytest.mark.parametrize(
    ("field", "value", "diagnostic"),
    [
        pytest.param("schema", True, "schema", id="boolean-schema"),
        pytest.param("schema", 2, "schema", id="unsupported-schema"),
        pytest.param("id", "run-1", "UUID", id="malformed-execution-id"),
        pytest.param(
            "id",
            "A1111111-1111-4111-8111-111111111111",
            "canonical UUID",
            id="noncanonical-execution-id",
        ),
        pytest.param("suite", " ", "suite", id="empty-suite"),
        pytest.param("started_at", "yesterday", "UTC ISO timestamp", id="malformed-timestamp"),
        pytest.param(
            "started_at", "2026-10-16T10:00:00", "UTC ISO timestamp", id="naive-timestamp"
        ),
        pytest.param(
            "finished_at",
            "2026-10-16T12:00:01+02:00",
            "UTC ISO timestamp",
            id="non-utc-timestamp",
        ),
        pytest.param(
            "finished_at",
            "2026-10-16T09:59:59+00:00",
            "precedes started_at",
            id="finish-before-start",
        ),
        pytest.param("context", ["build-1"], "context", id="context-is-not-a-table"),
        pytest.param("context", {"artifact": 1}, "context", id="non-string-context-value"),
        pytest.param("provenance", {"kind": False}, "provenance", id="non-string-provenance-value"),
    ],
)
def test_invalid_execution_metadata_is_rejected(field: str, value: object, diagnostic: str) -> None:
    document = execution_document()
    document[field] = value

    with pytest.raises(ValueError, match=r"report\.json:") as error:
        validate_execution(document, "report.json")

    assert "report.json" in str(error.value)
    assert diagnostic in str(error.value)


def test_run_preserves_one_shared_test_associated_with_two_requirements(plan: Plan) -> None:
    document = report_document()
    document["requirements"] = {
        identifier: {
            "status": "PASSED",
            "tests": [{"nodeid": "test_behavior.py::test_behavior", "outcome": "PASSED"}],
        }
        for identifier in ("REQ-001", "REQ-002")
    }

    run = validate_run(document, "report.json", plan)

    assert run.source == "report.json"
    assert run.tests == {
        "REQ-001": [{"nodeid": "test_behavior.py::test_behavior", "outcome": "PASSED"}],
        "REQ-002": [{"nodeid": "test_behavior.py::test_behavior", "outcome": "PASSED"}],
    }
    assert run.collection_errors == 0


def test_unknown_test_outcome_is_rejected(plan: Plan) -> None:
    document = report_document()
    document["requirements"] = {
        "REQ-001": {
            "status": "PASSED",
            "tests": [{"nodeid": "test_behavior.py::test_behavior", "outcome": "SUCCESS"}],
        }
    }

    with pytest.raises(ValueError, match=r"report\.json:") as error:
        validate_run(document, "report.json", plan)

    assert "invalid test outcome 'SUCCESS'" in str(error.value)


def test_duplicate_test_identity_within_one_requirement_is_rejected(plan: Plan) -> None:
    document = report_document()
    document["requirements"] = {
        "REQ-001": {
            "status": "PASSED",
            "tests": [
                {"nodeid": "test_behavior.py::test_behavior", "outcome": "PASSED"},
                {"nodeid": "test_behavior.py::test_behavior", "outcome": "PASSED"},
            ],
        }
    }

    with pytest.raises(ValueError, match=r"report\.json:") as error:
        validate_run(document, "report.json", plan)

    assert "duplicate test 'test_behavior.py::test_behavior'" in str(error.value)


def test_conflicting_outcomes_for_one_test_across_requirements_are_rejected(plan: Plan) -> None:
    document = report_document()
    document["requirements"] = {
        identifier: {
            "status": outcome,
            "tests": [{"nodeid": "test_behavior.py::test_behavior", "outcome": outcome}],
        }
        for identifier, outcome in (("REQ-001", "PASSED"), ("REQ-002", "FAILED"))
    }

    with pytest.raises(ValueError, match=r"report\.json:") as error:
        validate_run(document, "report.json", plan)

    assert "conflicting outcomes for test 'test_behavior.py::test_behavior'" in str(error.value)


def test_evidence_for_an_unknown_requirement_is_rejected(plan: Plan) -> None:
    document = report_document()
    document["requirements"] = {"REQ-UNKNOWN": {"status": "MISSING", "tests": []}}

    with pytest.raises(ValueError, match=r"report\.json:") as error:
        validate_run(document, "report.json", plan)

    assert "unknown requirement 'REQ-UNKNOWN'" in str(error.value)


@pytest.mark.parametrize(
    "collection_errors",
    [
        pytest.param(True, id="boolean-count"),
        pytest.param(-1, id="negative-count"),
        pytest.param(1.0, id="non-integer-count"),
    ],
)
def test_invalid_collection_error_count_is_rejected(plan: Plan, collection_errors: object) -> None:
    document = report_document()
    document["summary"] = {"collection_errors": collection_errors}

    with pytest.raises(ValueError, match=r"report\.json:") as error:
        validate_run(document, "report.json", plan)

    assert "collection_errors must be a nonnegative integer" in str(error.value)


@pytest.mark.parametrize(
    ("status", "tests"),
    [
        pytest.param(
            "PASSED",
            [{"nodeid": "test_behavior.py::test_behavior", "outcome": "FAILED"}],
            id="passing-status-with-failing-test",
        ),
        pytest.param(
            "FAILED",
            [{"nodeid": "test_behavior.py::test_behavior", "outcome": "PASSED"}],
            id="failing-status-with-passing-test",
        ),
        pytest.param("PASSED", [], id="passing-status-without-tests"),
    ],
)
def test_requirement_status_must_agree_with_test_outcomes(
    plan: Plan, status: str, tests: list[dict[str, str]]
) -> None:
    document = report_document()
    document["requirements"] = {"REQ-001": {"status": status, "tests": tests}}

    with pytest.raises(ValueError, match=r"report\.json:") as error:
        validate_run(document, "report.json", plan)

    assert "status disagrees with test outcomes" in str(error.value)


@pytest.mark.parametrize(
    ("outcome", "reported_verified", "reported_coverage", "expected_status"),
    [
        pytest.param("PASSED", False, 0.0, "COMPLETE", id="pessimistic-summary"),
        pytest.param("FAILED", True, 100.0, "FAILED", id="optimistic-summary"),
    ],
)
def test_report_summary_cannot_override_original_test_outcomes(
    outcome: str, reported_verified: bool, reported_coverage: float, expected_status: str
) -> None:
    plan = Plan(
        "specification",
        ["REQ-001"],
        {"A": {"configuration": "A"}},
        [Obligation("behavior-A", "REQ-001", "behavior", "A")],
    )
    target = Target("build-1", {"artifact": "build-1"}, {}, [])
    document = report_document()
    document["requirements"] = {
        "REQ-001": {
            "status": outcome,
            "tests": [{"nodeid": "test_behavior.py::test_behavior", "outcome": outcome}],
        }
    }
    document["summary"] = {
        "verified": reported_verified,
        "coverage": reported_coverage,
        "collection_errors": 0,
    }

    run = validate_run(document, "report.json", plan)
    assessment = assess(plan, target, [run])

    assert assessment["summary"]["status"] == expected_status
    assert assessment["requirements"] == {"REQ-001": outcome}
    assert assessment["obligations"][0]["tests"][0]["outcome"] == outcome
