"""Attach caller-declared context and provenance to an identified pytest execution."""

from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict
from uuid import uuid4

import pytest

from pytest_xspec.declarations import load_toml, string, string_map


class _Specification(TypedDict, total=False):
    specification: str


class Execution(_Specification):
    schema: int
    id: str
    suite: str
    started_at: str
    finished_at: str
    context: dict[str, str]
    provenance: dict[str, str]


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def start_execution(path: Path, *, specification: str | None = None) -> Execution:
    try:
        document = load_toml(path)
        suite = string(document.get("suite"), "suite")
        context = string_map(document.get("context"), "context")
        provenance = string_map(document.get("provenance", {}), "provenance")
    except (OSError, ValueError) as error:
        raise pytest.UsageError(f"Cannot read xspec execution context {path}: {error}") from error

    started_at = timestamp()
    execution: Execution = {
        "schema": 1,
        "id": str(uuid4()),
        "suite": suite,
        "started_at": started_at,
        "finished_at": started_at,
        "context": context,
        "provenance": provenance,
    }
    if specification is not None:
        execution["specification"] = specification

    return execution
