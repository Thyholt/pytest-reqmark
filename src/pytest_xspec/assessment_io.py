"""Validated declarations and saved pytest executions for contextual assessment."""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID

from pytest_xspec.declarations import (
    document_identity,
    load_toml,
    string,
    string_map,
    table,
    tables,
    validate_requirements,
)
from pytest_xspec.execution import Execution
from pytest_xspec.outcomes import PRECEDENCE, aggregate
from pytest_xspec.reporting import TestResult


@dataclass(frozen=True)
class Obligation:
    id: str
    requirement: str
    suite: str
    configuration: str


@dataclass(frozen=True)
class Plan:
    source: str
    requirements: list[str]
    configurations: dict[str, dict[str, str]]
    obligations: list[Obligation]
    identity: str = ""


@dataclass(frozen=True)
class Reuse:
    target: str
    execution: str
    obligation: str
    author: str
    reason: str


@dataclass(frozen=True)
class Target:
    id: str
    context: dict[str, str]
    configurations: dict[str, dict[str, str]]
    reuse: list[Reuse]


@dataclass(frozen=True)
class SavedRun:
    source: str
    execution: Execution
    tests: dict[str, list[TestResult]]
    collection_errors: int


def load_plan(path: Path) -> Plan:
    data = load_toml(path)
    requirements = validate_requirements(data.get("requirements"), str(path))
    configurations: dict[str, dict[str, str]] = {}
    for item in tables(data.get("configurations", []), f"{path}: configurations"):
        identifier = string(item.get("id"), f"{path}: configuration id")
        if identifier in configurations:
            raise ValueError(f"{path}: duplicate configuration {identifier!r}")

        configurations[identifier] = string_map(
            item.get("context"), f"{path}: configuration context"
        )

    obligations: list[Obligation] = []
    identifiers: set[str] = set()
    for item in tables(data.get("obligations", []), f"{path}: obligations"):
        identifier = string(item.get("id"), f"{path}: obligation id")
        requirement = item.get("requirement")
        configuration = string(item.get("configuration"), f"{path}: obligation configuration")
        if not isinstance(requirement, str) or requirement not in requirements:
            raise ValueError(
                f"{path}: obligation {identifier!r} references unknown requirement {requirement!r}"
            )

        if configuration not in configurations:
            raise ValueError(
                f"{path}: obligation {identifier!r} references "
                f"unknown configuration {configuration!r}"
            )

        if identifier in identifiers:
            raise ValueError(f"{path}: duplicate obligation {identifier!r}")

        identifiers.add(identifier)
        obligations.append(
            Obligation(
                identifier,
                requirement,
                string(item.get("suite"), f"{path}: obligation suite"),
                configuration,
            )
        )

    missing = set(requirements) - {item.requirement for item in obligations}
    if missing:
        raise ValueError(
            f"{path}: requirements without verification obligations: {sorted(missing)!r}"
        )

    return Plan(str(path), requirements, configurations, obligations, document_identity(path))


def load_target(path: Path, plan: Plan) -> Target:
    data = load_toml(path)
    identifier = string(data.get("id"), f"{path}: target id")
    context = string_map(data.get("context"), f"{path}: target context")
    overrides: dict[str, dict[str, str]] = {}
    for configuration, values in table(
        data.get("configurations", {}), f"{path}: configurations"
    ).items():
        if configuration not in plan.configurations:
            raise ValueError(f"{path}: unknown target configuration {configuration!r}")

        overrides[configuration] = string_map(values, f"{path}: configuration {configuration!r}")

    decisions: list[Reuse] = []
    seen: set[tuple[str, str]] = set()
    obligation_ids = {item.id for item in plan.obligations}
    for item in tables(data.get("reuse", []), f"{path}: reuse"):
        decision = Reuse(
            **{
                key: string(item.get(key), f"{path}: reuse {key}")
                for key in ("target", "execution", "obligation", "author", "reason")
            }
        )
        if decision.target != identifier:
            raise ValueError(
                f"{path}: reuse decision belongs to target {decision.target!r}, not {identifier!r}"
            )

        if decision.obligation not in obligation_ids:
            raise ValueError(f"{path}: reuse references unknown obligation {decision.obligation!r}")

        key = (decision.execution, decision.obligation)
        if key in seen:
            raise ValueError(f"{path}: duplicate reuse decision for {key!r}")

        seen.add(key)
        decisions.append(decision)

    return Target(identifier, context, overrides, decisions)


def _unique_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")

        result[key] = value

    return result


def _reject_constant(value: str) -> object:
    raise ValueError(f"invalid JSON constant {value}")


def _timestamp(value: object, label: str) -> tuple[str, datetime]:
    text = string(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{label} must be a UTC ISO timestamp") from error

    if parsed.utcoffset() != timedelta(0):
        raise ValueError(f"{label} must be a UTC ISO timestamp")

    return text, parsed


def validate_execution(value: object, source: str) -> Execution:
    data = table(value, f"{source}: execution")
    if type(data.get("schema")) is not int or data["schema"] != 1:
        raise ValueError(f"{source}: unsupported execution schema")

    identifier = string(data.get("id"), f"{source}: execution id")
    try:
        canonical = str(UUID(identifier))
    except ValueError as error:
        raise ValueError(f"{source}: execution id must be a UUID") from error

    if canonical != identifier:
        raise ValueError(f"{source}: execution id must be a canonical UUID")

    started, start = _timestamp(data.get("started_at"), f"{source}: started_at")
    finished, end = _timestamp(data.get("finished_at"), f"{source}: finished_at")
    if end < start:
        raise ValueError(f"{source}: execution finished_at precedes started_at")

    execution: Execution = {
        "schema": 1,
        "id": identifier,
        "suite": string(data.get("suite"), f"{source}: execution suite"),
        "started_at": started,
        "finished_at": finished,
        "context": string_map(data.get("context"), f"{source}: execution context"),
        "provenance": string_map(data.get("provenance", {}), f"{source}: execution provenance"),
    }
    if "specification" in data:
        execution["specification"] = string(
            data["specification"], f"{source}: specification digest"
        )

    return execution


def validate_run(data: dict[str, object], source: str, plan: Plan) -> SavedRun:
    execution = validate_execution(data.get("execution"), source)
    requirements = table(data.get("requirements"), f"{source}: requirements")
    tests: dict[str, list[TestResult]] = {}
    outcomes: dict[str, str] = {}
    for identifier, value in requirements.items():
        if identifier not in plan.requirements:
            raise ValueError(f"{source}: unknown requirement {identifier!r}")

        result = table(value, f"{source}: requirement {identifier!r}")
        associated: list[TestResult] = []
        nodeids: set[str] = set()
        for item in tables(result.get("tests"), f"{source}: requirement tests"):
            nodeid = string(item.get("nodeid"), f"{source}: test nodeid")
            outcome = string(item.get("outcome"), f"{source}: test outcome")
            if outcome not in PRECEDENCE:
                raise ValueError(f"{source}: invalid test outcome {outcome!r}")

            if nodeid in nodeids:
                raise ValueError(
                    f"{source}: duplicate test {nodeid!r} in requirement {identifier!r}"
                )

            if nodeid in outcomes and outcomes[nodeid] != outcome:
                raise ValueError(f"{source}: conflicting outcomes for test {nodeid!r}")

            nodeids.add(nodeid)
            outcomes[nodeid] = outcome
            associated.append({"nodeid": nodeid, "outcome": outcome})

        if result.get("status") != aggregate(item["outcome"] for item in associated):
            raise ValueError(
                f"{source}: requirement {identifier!r} status disagrees with test outcomes"
            )

        tests[identifier] = associated

    summary = table(data.get("summary"), f"{source}: summary")
    errors = summary.get("collection_errors")
    if not isinstance(errors, int) or isinstance(errors, bool) or errors < 0:
        raise ValueError(f"{source}: collection_errors must be a nonnegative integer")

    return SavedRun(source, execution, tests, errors)


def load_runs(paths: list[Path], plan: Plan) -> list[SavedRun]:
    records: dict[str, dict[str, object]] = {}
    runs: list[SavedRun] = []
    for path in paths:
        try:
            value: object = json.loads(
                path.read_text(encoding="utf-8"),
                object_pairs_hook=_unique_keys,
                parse_constant=_reject_constant,
            )
            data = table(value, str(path))
            run = validate_run(data, str(path), plan)
        except (OSError, ValueError) as error:
            raise ValueError(f"Cannot read execution report {path}: {error}") from error

        identifier = run.execution["id"]
        if identifier in records:
            if records[identifier] != data:
                raise ValueError(f"{path}: conflicting execution {identifier!r}")

            continue

        records[identifier] = data
        runs.append(run)

    return runs
