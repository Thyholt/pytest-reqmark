"""Select and discover exact requirement associations within pytest's collection scope."""

import pytest

from tests.acceptance.expectations import expected
from tests.acceptance.scenarios import requirement_selection
from tests.acceptance.scenarios.cli import collection_error
from tests.acceptance.scenarios.requirements import invalid_deselected_marker, multiple_requirements
from tests.acceptance.scenarios.selection import missing_requirement
from tests.acceptance.types import ReadReport, UserProject


@pytest.mark.parametrize("discovery", [False, True], ids=["execution", "discovery"])
def test_selection_preserves_collection_errors_from_imported_modules(
    user_project: UserProject, read_report: ReadReport, discovery: bool
) -> None:
    project = user_project(["REQ-001"], collection_error)
    options = ("--collect-only",) if discovery else ()

    result = project.runpytest_subprocess(
        "--xspec-select=REQ-001",
        "--continue-on-collection-errors",
        "--xspec-strict",
        "--xspec-json=report.json",
        *options,
    )

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    report = read_report(project)
    assert report["summary"]["collection_errors"] == 1
    assert report["summary"]["verified"] is False
    assert expected(report["requirements"]["REQ-001"]).to_have(
        status="SKIPPED" if discovery else "PASSED",
        tests=[("test_behavior.py::test_behavior", "SKIPPED" if discovery else "PASSED")],
    )


@pytest.mark.parametrize("shared_first", [False, True], ids=["excluded-first", "shared-first"])
def test_shared_evidence_and_deselection_aggregate_in_both_collection_orders(
    user_project: UserProject, read_report: ReadReport, shared_first: bool
) -> None:
    project = user_project(["REQ-001", "REQ-002"], requirement_selection)
    project.makefile(".ini", pytest="[pytest]\nmarkers = chosen: selected test\n")
    expected_tests = [
        ("test_behavior.py::test_shared_behavior", "PASSED"),
        ("test_behavior.py::test_second_behavior", "DESELECTED"),
    ]
    if not shared_first:
        expected_tests.reverse()

    result = project.runpytest_subprocess(
        *(nodeid for nodeid, _ in expected_tests),
        "--xspec-select=REQ-001",
        "--xspec-strict",
        "--xspec-json=report.json",
    )

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    result.assert_outcomes(passed=1, deselected=1)
    report = read_report(project)
    assert expected(report["requirements"]["REQ-001"]).to_have(
        status="PASSED", tests=[("test_behavior.py::test_shared_behavior", "PASSED")]
    )
    assert expected(report["requirements"]["REQ-002"]).to_have(
        status="DESELECTED", tests=expected_tests
    )


def test_without_requirement_selection_discovery_is_silent_and_execution_runs_all_tests(
    user_project: UserProject, read_report: ReadReport
) -> None:
    project = user_project(
        ["REQ-001", "REQ-002", "REQ-003", "REQ-004", "Krav / æøå : 1, del"],
        requirement_selection,
    )
    project.makefile(".ini", pytest="[pytest]\nmarkers = chosen: selected test\n")

    discovered = project.runpytest_subprocess("--collect-only", "-q", "-s")
    result = project.runpytest_subprocess("--xspec-strict", "--xspec-json=report.json", "-s")

    assert discovered.ret == pytest.ExitCode.OK
    assert "FIXTURE EXECUTED:" not in discovered.stdout.str()
    assert "TEST BODY EXECUTED:" not in discovered.stdout.str()
    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=8)
    report = read_report(project)
    assert list(report) == ["requirements", "summary"]
    assert report["summary"] == {
        "requirements": 5,
        "passed": 5,
        "unverified": 0,
        "coverage": 100.0,
        "verified": True,
        "collection_errors": 0,
    }
    assert [
        line.partition("FIXTURE EXECUTED: ")[2]
        for line in result.stdout.lines
        if "FIXTURE EXECUTED: " in line
    ] == [
        "test_behavior.py::test_first_behavior",
        "test_behavior.py::test_shared_behavior",
        "test_behavior.py::test_second_behavior",
        "test_behavior.py::test_unmarked_behavior",
        "test_behavior.py::test_opaque_behavior",
    ]
    assert [
        line.partition("TEST BODY EXECUTED: ")[2]
        for line in result.stdout.lines
        if "TEST BODY EXECUTED: " in line
    ] == [
        "test_behavior.py::test_first_behavior",
        "test_behavior.py::test_shared_behavior",
        "test_behavior.py::test_second_behavior",
        "test_behavior.py::test_unmarked_behavior",
        "test_behavior.py::test_opaque_behavior",
        "test_inherited.py::test_module_behavior",
        "test_inherited.py::TestBehavior::test_parameterized_behavior[first]",
        "test_inherited.py::TestBehavior::test_parameterized_behavior[second]",
    ]
    assert "Selected requirements:" not in result.stdout.str()


@pytest.mark.parametrize("discovery", [False, True], ids=["execution", "discovery"])
def test_terminal_and_json_describe_the_same_selection_scope(
    user_project: UserProject, read_report: ReadReport, discovery: bool
) -> None:
    project = user_project(["REQ-001", "REQ-002"], multiple_requirements)
    options = ("--collect-only",) if discovery else ()
    outcome = "SKIPPED" if discovery else "PASSED"

    result = project.runpytest_subprocess(
        "test_behavior.py",
        "--xspec-select=REQ-002",
        "--xspec-select=REQ-001",
        "--xspec-select=REQ-002",
        "-k",
        "shared",
        "-m",
        "xspec",
        "--xspec-strict",
        "--xspec-json=report.json",
        *options,
    )

    assert result.ret == (pytest.ExitCode.TESTS_FAILED if discovery else pytest.ExitCode.OK)
    report = read_report(project)
    assert report == {
        "requirements": {
            "REQ-001": {
                "status": outcome,
                "tests": [{"nodeid": "test_behavior.py::test_shared_behavior", "outcome": outcome}],
            },
            "REQ-002": {
                "status": outcome,
                "tests": [{"nodeid": "test_behavior.py::test_shared_behavior", "outcome": outcome}],
            },
        },
        "summary": {
            "requirements": 2,
            "passed": 0 if discovery else 2,
            "unverified": 2 if discovery else 0,
            "coverage": 0.0 if discovery else 100.0,
            "verified": not discovery,
            "collection_errors": 0,
        },
        "scope": {
            "selected_requirements": ["REQ-002", "REQ-001"],
            "collection_paths": ["test_behavior.py"],
            "keyword_expression": "shared",
            "marker_expression": "xspec",
            "collect_only": discovery,
        },
    }
    for line in (
        'Selected requirements: ["REQ-002", "REQ-001"]',
        'Collection paths: ["test_behavior.py"]',
        "Keyword filter: shared",
        "Marker filter: xspec",
        f"Discovery only: {'yes' if discovery else 'no'}",
    ):
        assert line in result.stdout.lines


def test_report_scope_preserves_configured_collection_paths(
    user_project: UserProject, read_report: ReadReport
) -> None:
    project = user_project(["REQ-003", "REQ-004"], requirement_selection)
    project.makefile(".ini", pytest="[pytest]\ntestpaths = test_inherited.py\n")

    result = project.runpytest_subprocess("--xspec-select=REQ-004", "--xspec-json=report.json")

    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=2, deselected=1)
    report = read_report(project)
    assert report.get("scope") == {
        "selected_requirements": ["REQ-004"],
        "collection_paths": ["test_inherited.py"],
        "keyword_expression": "",
        "marker_expression": "",
        "collect_only": False,
    }


@pytest.mark.parametrize("strict", [False, True], ids=["ordinary", "strict"])
@pytest.mark.parametrize(
    ("options", "outcome", "expected_exit"),
    [
        ((), "PASSED", pytest.ExitCode.OK),
        (("--collect-only",), "SKIPPED", pytest.ExitCode.OK),
        (("-k", "absent"), "DESELECTED", pytest.ExitCode.NO_TESTS_COLLECTED),
    ],
    ids=["execution", "discovery", "all-matches-filtered-out"],
)
def test_selection_keeps_all_declared_requirements_in_strict_verification_and_coverage(
    user_project: UserProject,
    read_report: ReadReport,
    strict: bool,
    options: tuple[str, ...],
    outcome: str,
    expected_exit: pytest.ExitCode,
) -> None:
    project = user_project(
        ["REQ-001", "REQ-002", "REQ-003", "REQ-004", "Krav / æøå : 1, del"],
        requirement_selection,
    )
    project.makefile(".ini", pytest="[pytest]\nmarkers = chosen: selected test\n")
    strict_options = ("--xspec-strict",) if strict else ()

    result = project.runpytest_subprocess(
        "--xspec-select=REQ-001",
        "--xspec-report",
        "--xspec-json=report.json",
        *options,
        *strict_options,
    )

    assert result.ret == (pytest.ExitCode.TESTS_FAILED if strict else expected_exit)
    report = read_report(project)
    assert list(report["requirements"]) == [
        "REQ-001",
        "REQ-002",
        "REQ-003",
        "REQ-004",
        "Krav / æøå : 1, del",
    ]
    assert expected(report["requirements"]["REQ-001"]).to_have(
        status=outcome,
        tests=[
            ("test_behavior.py::test_first_behavior", outcome),
            ("test_behavior.py::test_shared_behavior", outcome),
        ],
    )
    assert report["summary"] == {
        "requirements": 5,
        "passed": 1 if outcome == "PASSED" else 0,
        "unverified": 4 if outcome == "PASSED" else 5,
        "coverage": 20.0 if outcome == "PASSED" else 0.0,
        "verified": False,
        "collection_errors": 0,
    }
    result.stdout.fnmatch_lines(
        ["Requirements: 5", f"Coverage: {'20.0%' if outcome == 'PASSED' else '0.0%'}"]
    )


@pytest.mark.parametrize("selection", [("UNKNOWN",), ("REQ-001", "UNKNOWN"), ("REQ-00",)])
@pytest.mark.parametrize("discovery", [False, True], ids=["execution", "discovery"])
def test_unknown_selected_ids_are_usage_errors_before_execution(
    user_project: UserProject, selection: tuple[str, ...], discovery: bool
) -> None:
    project = user_project(
        ["REQ-001", "REQ-002", "REQ-003", "REQ-004", "Krav / æøå : 1, del"],
        requirement_selection,
    )
    project.makefile(".ini", pytest="[pytest]\nmarkers = chosen: selected test\n")
    options = ("--collect-only",) if discovery else ()

    result = project.runpytest_subprocess(
        *(f"--xspec-select={identifier}" for identifier in selection), "-s", *options
    )

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    message = result.stdout.str() + result.stderr.str()
    assert "unrecognized arguments" not in message.lower()
    assert "unknown" in message.lower()
    assert selection[-1] in message
    assert "FIXTURE EXECUTED:" not in result.stdout.str()
    assert "TEST BODY EXECUTED:" not in result.stdout.str()


@pytest.mark.parametrize("strict", [False, True], ids=["ordinary", "strict"])
def test_selecting_a_declared_requirement_without_links_reports_an_empty_unverified_result(
    user_project: UserProject, read_report: ReadReport, strict: bool
) -> None:
    project = user_project(["REQ-001"], missing_requirement)
    options = ("--xspec-strict",) if strict else ()

    result = project.runpytest_subprocess(
        "--xspec-select=REQ-001", "--xspec-report", "--xspec-json=report.json", *options
    )

    assert result.ret == (
        pytest.ExitCode.TESTS_FAILED if strict else pytest.ExitCode.NO_TESTS_COLLECTED
    )
    result.assert_outcomes(deselected=1)
    result.stdout.fnmatch_lines(["*REQ-001*MISSING*0*", "Unverified: 1", "Coverage: 0.0%"])
    report = read_report(project)
    assert expected(report["requirements"]["REQ-001"]).to_have(status="MISSING", tests=[])
    assert report["summary"]["verified"] is False


def test_invalid_collected_markers_are_rejected_even_if_selection_excludes_the_test(
    user_project: UserProject,
) -> None:
    project = user_project(["REQ-001"], invalid_deselected_marker)

    result = project.runpytest_subprocess("--xspec-select=REQ-001", "-k", "selected")

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    message = result.stdout.str() + result.stderr.str()
    assert "unrecognized arguments" not in message.lower()
    assert "UNKNOWN" in message
    assert "test_behavior.py::test_invalid" in message


def test_selecting_one_requirement_excludes_unrelated_and_unmarked_tests(
    user_project: UserProject, read_report: ReadReport
) -> None:
    project = user_project(
        ["REQ-001", "REQ-002", "REQ-003", "REQ-004", "Krav / æøå : 1, del"],
        requirement_selection,
    )
    project.makefile(".ini", pytest="[pytest]\nmarkers = chosen: selected test\n")

    result = project.runpytest_subprocess(
        "--xspec-select=REQ-001", "--xspec-json=report.json", "-s"
    )

    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=2, deselected=6)
    assert [
        line.partition("FIXTURE EXECUTED: ")[2]
        for line in result.stdout.lines
        if "FIXTURE EXECUTED: " in line
    ] == [
        "test_behavior.py::test_first_behavior",
        "test_behavior.py::test_shared_behavior",
    ]
    report = read_report(project)
    assert report.get("scope") == {
        "selected_requirements": ["REQ-001"],
        "collection_paths": ["."],
        "keyword_expression": "",
        "marker_expression": "",
        "collect_only": False,
    }
    assert expected(report["requirements"]["REQ-001"]).to_have(
        status="PASSED",
        tests=[
            ("test_behavior.py::test_first_behavior", "PASSED"),
            ("test_behavior.py::test_shared_behavior", "PASSED"),
        ],
    )
    assert expected(report["requirements"]["REQ-002"]).to_have(
        status="DESELECTED",
        tests=[
            ("test_behavior.py::test_shared_behavior", "PASSED"),
            ("test_behavior.py::test_second_behavior", "DESELECTED"),
        ],
    )


@pytest.mark.parametrize(
    ("filters", "executed", "first_outcome", "shared_outcome"),
    [
        (("-k", "shared"), "test_shared_behavior", "DESELECTED", "PASSED"),
        (("-m", "chosen"), "test_first_behavior", "PASSED", "DESELECTED"),
        (
            ("-k", "first or second", "-m", "chosen"),
            "test_first_behavior",
            "PASSED",
            "DESELECTED",
        ),
    ],
    ids=["keyword", "marker", "both"],
)
def test_requirement_selection_intersects_with_native_filters_within_collected_paths(
    user_project: UserProject,
    read_report: ReadReport,
    filters: tuple[str, ...],
    executed: str,
    first_outcome: str,
    shared_outcome: str,
) -> None:
    project = user_project(
        ["REQ-001", "REQ-002", "REQ-003", "REQ-004", "Krav / æøå : 1, del"],
        requirement_selection,
    )
    project.makefile(".ini", pytest="[pytest]\nmarkers = chosen: selected test\n")

    result = project.runpytest_subprocess(
        "test_behavior.py", "--xspec-select=REQ-001", *filters, "--xspec-json=report.json", "-s"
    )

    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=1, deselected=4)
    assert [
        line.partition("FIXTURE EXECUTED: ")[2]
        for line in result.stdout.lines
        if "FIXTURE EXECUTED: " in line
    ] == [f"test_behavior.py::{executed}"]
    report = read_report(project)
    assert expected(report["requirements"]["REQ-001"]).to_have(
        status="DESELECTED",
        tests=[
            ("test_behavior.py::test_first_behavior", first_outcome),
            ("test_behavior.py::test_shared_behavior", shared_outcome),
        ],
    )
    assert expected(report["requirements"]["REQ-002"]).to_have(
        status="DESELECTED",
        tests=[
            ("test_behavior.py::test_shared_behavior", shared_outcome),
            ("test_behavior.py::test_second_behavior", "DESELECTED"),
        ],
    )
    assert expected(report["requirements"]["REQ-003"]).to_have(status="MISSING", tests=[])
    assert expected(report["requirements"]["REQ-004"]).to_have(status="MISSING", tests=[])


@pytest.mark.parametrize(
    "selection",
    [
        ("--xspec-select=REQ-001", "--xspec-select=REQ-002", "--xspec-select=REQ-001"),
        ("--xspec-select=REQ-002", "--xspec-select=REQ-001", "--xspec-select=REQ-002"),
    ],
    ids=["first-then-second", "second-then-first"],
)
def test_repeated_selections_and_overlapping_markers_run_each_test_once(
    user_project: UserProject, read_report: ReadReport, selection: tuple[str, ...]
) -> None:
    project = user_project(
        ["REQ-001", "REQ-002", "REQ-003", "REQ-004", "Krav / æøå : 1, del"],
        requirement_selection,
    )
    project.makefile(".ini", pytest="[pytest]\nmarkers = chosen: selected test\n")

    result = project.runpytest_subprocess(*selection, "--xspec-json=report.json", "-s")

    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=3, deselected=5)
    assert [
        line.partition("FIXTURE EXECUTED: ")[2]
        for line in result.stdout.lines
        if "FIXTURE EXECUTED: " in line
    ] == [
        "test_behavior.py::test_first_behavior",
        "test_behavior.py::test_shared_behavior",
        "test_behavior.py::test_second_behavior",
    ]
    report = read_report(project)
    assert expected(report["requirements"]["REQ-001"]).to_have(
        status="PASSED",
        tests=[
            ("test_behavior.py::test_first_behavior", "PASSED"),
            ("test_behavior.py::test_shared_behavior", "PASSED"),
        ],
    )
    assert expected(report["requirements"]["REQ-002"]).to_have(
        status="PASSED",
        tests=[
            ("test_behavior.py::test_shared_behavior", "PASSED"),
            ("test_behavior.py::test_second_behavior", "PASSED"),
        ],
    )


@pytest.mark.parametrize("requirement", ["REQ-003", "REQ-004"])
@pytest.mark.parametrize("discovery", [False, True], ids=["execution", "discovery"])
def test_inherited_markers_select_complete_parameterized_node_ids(
    user_project: UserProject, read_report: ReadReport, requirement: str, discovery: bool
) -> None:
    project = user_project(["REQ-003", "REQ-004"], requirement_selection)
    options = ("--collect-only", "-q") if discovery else ()
    outcome = "SKIPPED" if discovery else "PASSED"
    expected_tests = [
        ("test_inherited.py::TestBehavior::test_parameterized_behavior[first]", outcome),
        ("test_inherited.py::TestBehavior::test_parameterized_behavior[second]", outcome),
    ]

    result = project.runpytest_subprocess(
        "test_inherited.py",
        f"--xspec-select={requirement}",
        "--xspec-json=report.json",
        "-s",
        *options,
    )

    assert result.ret == pytest.ExitCode.OK
    report = read_report(project)
    assert expected(report["requirements"]["REQ-004"]).to_have(status=outcome, tests=expected_tests)
    assert expected(report["requirements"]["REQ-003"]).to_have(
        status=outcome if discovery or requirement == "REQ-003" else "DESELECTED",
        tests=[
            (
                "test_inherited.py::test_module_behavior",
                outcome if requirement == "REQ-003" else "DESELECTED",
            ),
            *expected_tests,
        ],
    )
    if discovery:
        assert [line for line in result.stdout.lines if line.startswith("test_inherited.py::")] == [
            test["nodeid"] for test in report["requirements"][requirement]["tests"]
        ]
        assert "TEST BODY EXECUTED:" not in result.stdout.str()

    else:
        assert [
            line.partition("TEST BODY EXECUTED: ")[2]
            for line in result.stdout.lines
            if "TEST BODY EXECUTED: " in line
        ] == [test["nodeid"] for test in report["requirements"][requirement]["tests"]]


def test_selection_treats_unicode_spaces_and_a_comma_as_one_exact_id(
    user_project: UserProject, read_report: ReadReport
) -> None:
    project = user_project(
        ["REQ-001", "REQ-002", "REQ-003", "REQ-004", "Krav / æøå : 1, del", "Krav / æøå : 1"],
        requirement_selection,
    )
    project.makefile(".ini", pytest="[pytest]\nmarkers = chosen: selected test\n")

    result = project.runpytest_subprocess(
        "--xspec-select=Krav / æøå : 1, del", "--xspec-json=report.json", "--strict-markers"
    )

    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=1, deselected=7)
    report = read_report(project)
    assert expected(report["requirements"]["Krav / æøå : 1, del"]).to_have(
        status="PASSED", tests=[("test_behavior.py::test_opaque_behavior", "PASSED")]
    )
    assert expected(report["requirements"]["Krav / æøå : 1"]).to_have(status="MISSING", tests=[])


def test_discovery_lists_the_execution_selection_without_running_fixtures_or_bodies(
    user_project: UserProject, read_report: ReadReport
) -> None:
    project = user_project(
        ["REQ-001", "REQ-002", "REQ-003", "REQ-004", "Krav / æøå : 1, del"],
        requirement_selection,
    )
    project.makefile(".ini", pytest="[pytest]\nmarkers = chosen: selected test\n")

    discovered = project.runpytest_subprocess(
        "--xspec-select=REQ-001", "--collect-only", "-q", "--xspec-json=report.json", "-s"
    )
    discovery_report = read_report(project)
    executed = project.runpytest_subprocess(
        "--xspec-select=REQ-001", "--xspec-json=report.json", "-s"
    )
    execution_report = read_report(project)

    assert discovered.ret == executed.ret == pytest.ExitCode.OK
    assert "FIXTURE EXECUTED:" not in discovered.stdout.str()
    assert "TEST BODY EXECUTED:" not in discovered.stdout.str()
    assert [line for line in discovered.stdout.lines if line.startswith("test_behavior.py::")] == [
        "test_behavior.py::test_first_behavior",
        "test_behavior.py::test_shared_behavior",
    ]
    assert expected(discovery_report["requirements"]["REQ-001"]).to_have(
        status="SKIPPED",
        tests=[
            ("test_behavior.py::test_first_behavior", "SKIPPED"),
            ("test_behavior.py::test_shared_behavior", "SKIPPED"),
        ],
    )
    assert expected(execution_report["requirements"]["REQ-001"]).to_have(
        status="PASSED",
        tests=[
            ("test_behavior.py::test_first_behavior", "PASSED"),
            ("test_behavior.py::test_shared_behavior", "PASSED"),
        ],
    )
    assert [
        line.partition("FIXTURE EXECUTED: ")[2]
        for line in executed.stdout.lines
        if "FIXTURE EXECUTED: " in line
    ] == [
        "test_behavior.py::test_first_behavior",
        "test_behavior.py::test_shared_behavior",
    ]
    assert [
        line.partition("TEST BODY EXECUTED: ")[2]
        for line in executed.stdout.lines
        if "TEST BODY EXECUTED: " in line
    ] == [
        "test_behavior.py::test_first_behavior",
        "test_behavior.py::test_shared_behavior",
    ]
