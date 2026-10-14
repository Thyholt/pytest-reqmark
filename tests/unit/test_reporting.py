"""An incomplete execution cannot become successful acceptance verification."""

from pytest_reqmark.reporting import build_report


def test_a_collected_test_without_an_execution_result_is_skipped():
    requirements = {"REQ-001": ["test_behavior.py::test_first", "test_behavior.py::test_second"]}
    outcomes = {"test_behavior.py::test_first": "PASSED", "test_behavior.py::test_second": None}

    report = build_report(requirements, outcomes, collection_errors=0)

    assert report == {
        "requirements": {
            "REQ-001": {
                "status": "SKIPPED",
                "tests": [
                    {"nodeid": "test_behavior.py::test_first", "outcome": "PASSED"},
                    {"nodeid": "test_behavior.py::test_second", "outcome": "SKIPPED"},
                ],
            }
        },
        "summary": {
            "requirements": 1,
            "passed": 0,
            "unverified": 1,
            "coverage": 0.0,
            "verified": False,
            "collection_errors": 0,
        },
    }
