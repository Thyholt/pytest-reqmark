"""Build and render the public requirement report."""

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TypedDict

import pytest
from _pytest.terminal import TerminalReporter

from pytest_reqmark.outcomes import aggregate


class TestResult(TypedDict):
    nodeid: str
    outcome: str


class RequirementResult(TypedDict):
    status: str
    tests: list[TestResult]


class Summary(TypedDict):
    requirements: int
    passed: int
    unverified: int
    coverage: float
    verified: bool
    collection_errors: int


class Report(TypedDict):
    requirements: dict[str, RequirementResult]
    summary: Summary


def build_report(
    requirements: Mapping[str, Sequence[str]],
    outcomes: Mapping[str, str | None],
    collection_errors: int,
) -> Report:
    results: dict[str, RequirementResult] = {}

    for identifier, nodeids in requirements.items():
        tests: list[TestResult] = [
            {"nodeid": nodeid, "outcome": outcomes[nodeid] or "SKIPPED"} for nodeid in nodeids
        ]
        results[identifier] = {
            "status": aggregate(test["outcome"] for test in tests),
            "tests": tests,
        }

    count = len(results)
    passed = sum(result["status"] == "PASSED" for result in results.values())

    return {
        "requirements": results,
        "summary": {
            "requirements": count,
            "passed": passed,
            "unverified": count - passed,
            "coverage": passed / count * 100 if count else 0.0,
            "verified": passed == count and collection_errors == 0,
            "collection_errors": collection_errors,
        },
    }


def write_json(report: Report, path: Path) -> None:
    try:
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError as error:
        raise pytest.UsageError(
            f"Cannot write pytest-reqmark JSON report {path}: {error}"
        ) from error


def write_terminal(report: Report, terminal: TerminalReporter) -> None:
    red = not report["summary"]["verified"]
    terminal.write_sep("=", "pytest-reqmark", red=red)

    width = max([len("Requirement"), *(len(identifier) for identifier in report["requirements"])])
    terminal.write_line(f"{'Requirement':<{width}}  {'Status':<10}  Tests", red=red)

    for identifier, result in report["requirements"].items():
        terminal.write_line(
            f"{identifier:<{width}}  {result['status']:<10}  {len(result['tests'])}", red=red
        )

    for label, field in (
        ("Requirements", "requirements"),
        ("Passed", "passed"),
        ("Unverified", "unverified"),
    ):
        terminal.write_line(f"{label}: {report['summary'][field]}", red=red)

    terminal.write_line(f"Coverage: {report['summary']['coverage']:.1f}%", red=red)

    if report["summary"]["collection_errors"]:
        terminal.write_line(f"Collection errors: {report['summary']['collection_errors']}", red=red)
