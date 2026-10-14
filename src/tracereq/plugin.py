"""Pytest entry point for executable requirement verification."""

from collections.abc import Generator, Sequence
from pathlib import Path

import pytest
from _pytest.terminal import TerminalReporter

from tracereq.collector import requirement_ids
from tracereq.config import load_requirements
from tracereq.outcomes import aggregate, phase_outcome
from tracereq.reporting import build_report, write_json, write_terminal


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("tracereq")
    group.addoption("--tracereq-report", action="store_true", help="Print requirement verification")
    group.addoption(
        "--tracereq-strict", action="store_true", help="Fail on unverified requirements"
    )
    group.addoption(
        "--tracereq-json", metavar="PATH", help="Write requirement verification as JSON"
    )

    parser.addini(
        "tracereq_requirements", "Requirement IDs, one per line (pytest.ini only)", "linelist"
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "tracereq(id): associate a test with a declared requirement")
    config.pluginmanager.register(RequirementPlugin(config), "tracereq-results")


class RequirementPlugin:
    def __init__(self, config: pytest.Config) -> None:
        self.config = config
        self.requirements: dict[str, list[str]] = {
            identifier: [] for identifier in load_requirements(config)
        }
        self.outcomes: dict[str, str | None] = {}
        self.collection_errors = 0

    @pytest.hookimpl(wrapper=True, tryfirst=True)
    def pytest_collection_modifyitems(self, items: list[pytest.Item]) -> Generator[None]:
        for item in items:
            identifiers = requirement_ids(item, self.requirements)

            if identifiers and item.nodeid not in self.outcomes:
                self.outcomes[item.nodeid] = None

                for identifier in identifiers:
                    self.requirements[identifier].append(item.nodeid)

        yield

    def pytest_deselected(self, items: Sequence[pytest.Item]) -> None:
        for item in items:
            if item.nodeid in self.outcomes:
                self.outcomes[item.nodeid] = "DESELECTED"

    def pytest_collectreport(self, report: pytest.CollectReport) -> None:
        if report.failed:
            self.collection_errors += 1

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if report.nodeid in self.outcomes:
            outcome = phase_outcome(
                report.when,
                report.outcome,
                wasxfail=hasattr(report, "wasxfail"),
                longrepr=report.longrepr,
            )

            if outcome is not None:
                previous = self.outcomes[report.nodeid]
                self.outcomes[report.nodeid] = aggregate(
                    [previous, outcome] if previous is not None else [outcome]
                )

    def pytest_sessionfinish(self, session: pytest.Session) -> None:
        report = build_report(self.requirements, self.outcomes, self.collection_errors)

        path = self.config.getoption("tracereq_json")
        if path:
            write_json(report, Path(path))

        if (
            self.config.getoption("tracereq_strict")
            and not report["summary"]["verified"]
            and session.exitstatus in (pytest.ExitCode.OK, pytest.ExitCode.NO_TESTS_COLLECTED)
        ):
            session.exitstatus = pytest.ExitCode.TESTS_FAILED

    def pytest_terminal_summary(self, terminalreporter: TerminalReporter) -> None:
        if self.config.getoption("tracereq_report") or self.config.getoption("tracereq_strict"):
            write_terminal(
                build_report(self.requirements, self.outcomes, self.collection_errors),
                terminalreporter,
            )
