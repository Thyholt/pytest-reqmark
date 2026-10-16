"""Derive verification solely from declared obligations and original pytest outcomes."""

from dataclasses import asdict
from typing import TypedDict, cast

from pytest_xspec.assessment_io import Plan, Reuse, SavedRun, Target
from pytest_xspec.execution import Execution
from pytest_xspec.outcomes import aggregate


class Mismatch(TypedDict):
    expected: str
    actual: str | None


class ReuseDecision(TypedDict):
    target: str
    execution: str
    obligation: str
    author: str
    reason: str


class Candidate(TypedDict):
    execution: str
    suite: str
    nodeid: str
    outcome: str
    source: str
    started_at: str
    finished_at: str
    specification: str | None
    context: dict[str, str]
    provenance: dict[str, str]
    applicable: bool
    mismatches: dict[str, Mismatch]
    reuse: ReuseDecision | None


class ObligationResult(TypedDict):
    id: str
    requirement: str
    configuration: str
    suite: str
    expected: dict[str, str]
    status: str
    tests: list[Candidate]


class AssessmentSummary(TypedDict):
    status: str
    verified: bool
    obligations: int
    passed: int
    unverified: int
    coverage: float
    collection_errors: int


class SourceExecution(TypedDict):
    source: str
    execution: Execution
    collection_errors: int


class Assessment(TypedDict):
    target: str
    specification: str
    specification_digest: str
    requirements: dict[str, str]
    obligations: list[ObligationResult]
    executions: list[SourceExecution]
    summary: AssessmentSummary


def _decisions(plan: Plan, target: Target, runs: list[SavedRun]) -> dict[tuple[str, str], Reuse]:
    decisions: dict[tuple[str, str], Reuse] = {}
    by_id = {run.execution["id"]: run for run in runs}
    obligations = {item.id: item for item in plan.obligations}
    for decision in target.reuse:
        run = by_id.get(decision.execution)
        obligation = obligations[decision.obligation]
        if run is None:
            raise ValueError(f"reuse references unknown execution {decision.execution!r}")

        if run.execution["suite"] != obligation.suite or not run.tests.get(obligation.requirement):
            raise ValueError(
                f"reuse execution {decision.execution!r} has no tests "
                f"for obligation {obligation.id!r}"
            )

        decisions[decision.execution, decision.obligation] = decision

    return decisions


def assess(plan: Plan, target: Target, runs: list[SavedRun]) -> Assessment:
    decisions = _decisions(plan, target, runs)
    results: list[ObligationResult] = []
    for obligation in plan.obligations:
        expected = {
            **plan.configurations[obligation.configuration],
            **target.context,
            **target.configurations.get(obligation.configuration, {}),
        }
        candidates: list[Candidate] = []
        for run in runs:
            if run.execution["suite"] != obligation.suite:
                continue

            context = run.execution["context"]
            mismatches: dict[str, Mismatch] = {
                key: {"expected": value, "actual": context.get(key)}
                for key, value in expected.items()
                if context.get(key) != value
            }
            baseline = run.execution.get("specification")
            if plan.identity and baseline != plan.identity:
                mismatches["execution.specification"] = {
                    "expected": plan.identity,
                    "actual": baseline,
                }
            decision = decisions.get((run.execution["id"], obligation.id))
            candidates.extend(
                {
                    "execution": run.execution["id"],
                    "suite": run.execution["suite"],
                    "nodeid": test["nodeid"],
                    "outcome": test["outcome"],
                    "source": run.source,
                    "started_at": run.execution["started_at"],
                    "finished_at": run.execution["finished_at"],
                    "specification": baseline,
                    "context": context,
                    "provenance": run.execution["provenance"],
                    "applicable": not mismatches or decision is not None,
                    "mismatches": mismatches,
                    # asdict serializes this validated, fixed-schema dataclass.
                    "reuse": cast(ReuseDecision, asdict(decision)) if decision else None,
                }
                for test in run.tests.get(obligation.requirement, [])
            )

        status = aggregate(test["outcome"] for test in candidates if test["applicable"])
        if status == "MISSING" and candidates:
            status = "INAPPLICABLE"

        results.append(
            {
                "id": obligation.id,
                "requirement": obligation.requirement,
                "configuration": obligation.configuration,
                "suite": obligation.suite,
                "expected": expected,
                "status": status,
                "tests": candidates,
            }
        )

    errors = sum(run.collection_errors for run in runs)
    passed = sum(result["status"] == "PASSED" for result in results)
    count = len(results)
    failed = errors > 0 or any(
        result["status"] in {"ERROR", "FAILED", "XPASSED"} for result in results
    )
    verdict = "FAILED" if failed else ("COMPLETE" if passed == count else "INCOMPLETE")
    precedence = {
        status: index
        for index, status in enumerate(
            (
                "PASSED",
                "INAPPLICABLE",
                "MISSING",
                "DESELECTED",
                "SKIPPED",
                "XFAILED",
                "XPASSED",
                "FAILED",
                "ERROR",
            )
        )
    }
    return {
        "target": target.id,
        "specification": plan.source,
        "specification_digest": plan.identity,
        "requirements": {
            identifier: max(
                (row["status"] for row in results if row["requirement"] == identifier),
                key=precedence.__getitem__,
                default="MISSING",
            )
            for identifier in plan.requirements
        },
        "obligations": results,
        "executions": [
            {
                "source": run.source,
                "execution": run.execution,
                "collection_errors": run.collection_errors,
            }
            for run in runs
        ],
        "summary": {
            "status": verdict,
            "verified": verdict == "COMPLETE",
            "obligations": count,
            "passed": passed,
            "unverified": count - passed,
            "coverage": passed / count * 100 if count else 0.0,
            "collection_errors": errors,
        },
    }
