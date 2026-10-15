"""Static contracts for project fixtures and the public JSON report."""

from collections.abc import Callable
from types import ModuleType
from typing import TypeAlias, TypedDict

import pytest


class ReportedTest(TypedDict):
    nodeid: str
    outcome: str


class ReportedRequirement(TypedDict):
    status: str
    tests: list[ReportedTest]


class ReportSummary(TypedDict):
    requirements: int
    passed: int
    unverified: int
    coverage: float
    verified: bool
    collection_errors: int


class AcceptanceReport(TypedDict):
    requirements: dict[str, ReportedRequirement]
    summary: ReportSummary


FileProject: TypeAlias = Callable[[ModuleType], pytest.Pytester]
UserProject: TypeAlias = Callable[[list[str], ModuleType], pytest.Pytester]
ReadReport: TypeAlias = Callable[[pytest.Pytester], AcceptanceReport]
