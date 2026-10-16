"""Users assess independent pytest executions against an explicit verification plan."""

import json
import sys

import pytest

from tests.acceptance.scenarios.assessment import producer
from tests.acceptance.types import FileProject


def record(project: pytest.Pytester, context: str, name: str, *options: str) -> str:
    behavior = "secondary" if context in {"secondary", "stale", "firmware"} else "primary"
    result = project.runpytest_subprocess(
        f"test_behavior.py::test_{behavior}_behavior",
        "--xspec-spec=xspec.toml",
        f"--xspec-context={context}.toml",
        f"--xspec-json={name}.json",
        "-s",
        *options,
    )
    assert result.ret in (
        pytest.ExitCode.OK,
        pytest.ExitCode.TESTS_FAILED,
        pytest.ExitCode.NO_TESTS_COLLECTED,
    )
    (project.path / f"{name}.stdout").write_text(result.stdout.str(), encoding="utf-8")
    return f"{name}.json"


def assess(
    project: pytest.Pytester, *reports: str, target: str = "target.toml"
) -> pytest.RunResult:
    return project.run(
        sys.executable,
        "-m",
        "pytest_xspec",
        "assess",
        "xspec.toml",
        "--target",
        target,
        "--json",
        "assessment.json",
        "--markdown",
        "assessment.md",
        *reports,
    )


def test_independent_partial_runs_satisfy_the_declared_plan(file_project: FileProject) -> None:
    project = file_project(producer)
    primary = record(project, "primary", "primary")
    secondary = record(project, "secondary", "secondary")

    result = assess(project, primary, secondary)

    assert result.ret == 0
    result.stdout.fnmatch_lines(["*COMPLETE*", "*REQ-001-a*PASSED*", "*REQ-002-b*PASSED*"])
    report = json.loads((project.path / "assessment.json").read_text(encoding="utf-8"))
    assert report["summary"] == {
        "status": "COMPLETE",
        "verified": True,
        "obligations": 2,
        "passed": 2,
        "unverified": 0,
        "coverage": 100.0,
        "collection_errors": 0,
    }
    assert [
        (row["id"], row["requirement"], row["configuration"], row["status"])
        for row in report["obligations"]
    ] == [
        ("REQ-001-a", "REQ-001", "platform-a", "PASSED"),
        ("REQ-002-b", "REQ-002", "platform-b", "PASSED"),
    ]
    for row, source, nodeid in zip(
        report["obligations"],
        (primary, secondary),
        ("test_behavior.py::test_primary_behavior", "test_behavior.py::test_secondary_behavior"),
        strict=True,
    ):
        original = json.loads((project.path / source).read_text(encoding="utf-8"))
        assert [
            (test["execution"], test["nodeid"], test["outcome"], test["applicable"])
            for test in row["tests"]
        ] == [(original["execution"]["id"], nodeid, "PASSED", True)]
        assert row["tests"][0]["context"] == original["execution"]["context"]
        assert row["tests"][0]["provenance"] == original["execution"]["provenance"]
    assert "PRIMARY_EXECUTED" in (project.path / "primary.stdout").read_text(encoding="utf-8")
    assert "SECONDARY_EXECUTED" in (project.path / "secondary.stdout").read_text(encoding="utf-8")
    assert "COMPLETE" in (project.path / "assessment.md").read_text(encoding="utf-8")


def test_a_missing_configuration_remains_required_and_children_do_not_verify_parents(
    file_project: FileProject,
) -> None:
    project = file_project(producer)
    secondary = record(project, "secondary", "secondary")

    result = assess(project, secondary)

    assert result.ret == 1
    report = json.loads((project.path / "assessment.json").read_text(encoding="utf-8"))
    assert [(row["id"], row["status"]) for row in report["obligations"]] == [
        ("REQ-001-a", "MISSING"),
        ("REQ-002-b", "PASSED"),
    ]
    assert report["obligations"][0]["tests"] == []
    assert report["summary"]["status"] == "INCOMPLETE"
    assert report["requirements"] == {"REQ-001": "MISSING", "REQ-002": "PASSED"}


def test_stale_passing_evidence_remains_visible_without_satisfying_the_target(
    file_project: FileProject,
) -> None:
    project = file_project(producer)
    primary = record(project, "primary", "primary")
    stale = record(project, "stale", "stale")
    original = (project.path / stale).read_text(encoding="utf-8")

    result = assess(project, primary, stale)

    assert result.ret == 1
    report = json.loads((project.path / "assessment.json").read_text(encoding="utf-8"))
    assert report["summary"]["status"] == "INCOMPLETE"
    assert report["obligations"][1]["status"] == "INAPPLICABLE"
    assert [
        (test["nodeid"], test["outcome"], test["applicable"])
        for test in report["obligations"][1]["tests"]
    ] == [("test_behavior.py::test_secondary_behavior", "PASSED", False)]
    assert report["obligations"][1]["tests"][0]["mismatches"] == {
        "artifact": {"expected": "build-42", "actual": "build-41"}
    }
    assert (project.path / stale).read_text(encoding="utf-8") == original
    result.stdout.fnmatch_lines(["*INCOMPLETE*", "*artifact*build-42*build-41*"])


@pytest.mark.parametrize("reverse", [False, True], ids=["stale-first", "current-first"])
def test_stale_evidence_cannot_hide_an_applicable_execution(
    file_project: FileProject, reverse: bool
) -> None:
    project = file_project(producer)
    primary = record(project, "primary", "primary")
    stale = record(project, "stale", "stale")
    secondary = record(project, "secondary", "secondary")
    candidates = [stale, secondary]
    if reverse:
        candidates.reverse()

    result = assess(project, primary, *candidates)

    assert result.ret == 0
    report = json.loads((project.path / "assessment.json").read_text(encoding="utf-8"))
    assert report["obligations"][1]["status"] == "PASSED"
    assert [
        (test["nodeid"], test["outcome"], test["applicable"])
        for test in report["obligations"][1]["tests"]
    ] == [
        ("test_behavior.py::test_secondary_behavior", "PASSED", reverse),
        ("test_behavior.py::test_secondary_behavior", "PASSED", not reverse),
    ]


@pytest.mark.parametrize("reverse", [False, True], ids=["failure-first", "pass-first"])
def test_an_applicable_failure_cannot_be_hidden_by_a_passing_execution(
    file_project: FileProject, monkeypatch: pytest.MonkeyPatch, reverse: bool
) -> None:
    project = file_project(producer)
    monkeypatch.setenv("ASSESSMENT_RESULT", "failed")
    failing = record(project, "primary", "failed")
    monkeypatch.delenv("ASSESSMENT_RESULT")
    passing = record(project, "primary", "passed")
    secondary = record(project, "secondary", "secondary")
    candidates = [failing, passing]
    if reverse:
        candidates.reverse()

    result = assess(project, *candidates, secondary)

    assert result.ret == 1
    report = json.loads((project.path / "assessment.json").read_text(encoding="utf-8"))
    assert report["summary"]["status"] == "FAILED"
    assert report["obligations"][0]["status"] == "FAILED"
    assert [(test["nodeid"], test["outcome"]) for test in report["obligations"][0]["tests"]] == [
        ("test_behavior.py::test_primary_behavior", "PASSED" if reverse else "FAILED"),
        ("test_behavior.py::test_primary_behavior", "FAILED" if reverse else "PASSED"),
    ]
    assert (
        report["obligations"][0]["tests"][0]["execution"]
        != report["obligations"][0]["tests"][1]["execution"]
    )


@pytest.mark.parametrize(
    ("options", "outcome"),
    [(("--collect-only",), "SKIPPED"), (("-m", "not selected"), "DESELECTED")],
    ids=["discovery", "deselection"],
)
def test_unexecuted_tests_retain_their_identities_and_cannot_verify(
    file_project: FileProject, options: tuple[str, ...], outcome: str
) -> None:
    project = file_project(producer)
    primary = record(project, "primary", "primary", *options)
    secondary = record(project, "secondary", "secondary")

    result = assess(project, primary, secondary)

    assert result.ret == 1
    report = json.loads((project.path / "assessment.json").read_text(encoding="utf-8"))
    assert report["summary"]["status"] == "INCOMPLETE"
    assert [(test["nodeid"], test["outcome"]) for test in report["obligations"][0]["tests"]] == [
        ("test_behavior.py::test_primary_behavior", outcome)
    ]
    assert "PRIMARY_EXECUTED" not in (project.path / "primary.stdout").read_text(encoding="utf-8")
    assert "SECONDARY_EXECUTED" in (project.path / "secondary.stdout").read_text(encoding="utf-8")


def test_simulations_cannot_satisfy_a_physical_evidence_requirement(
    file_project: FileProject,
) -> None:
    project = file_project(producer)
    primary = record(project, "primary", "primary")
    secondary = record(project, "secondary", "secondary")

    result = assess(project, primary, secondary, target="physical.toml")

    assert result.ret == 1
    report = json.loads((project.path / "assessment.json").read_text(encoding="utf-8"))
    assert [row["status"] for row in report["obligations"]] == ["INAPPLICABLE", "INAPPLICABLE"]
    for row in report["obligations"]:
        assert row["tests"][0]["context"]["environment"] == "simulation"
        assert row["tests"][0]["mismatches"]["environment"] == {
            "expected": "physical",
            "actual": "simulation",
        }


def test_reuse_is_explicit_scoped_and_preserves_the_original_execution(
    file_project: FileProject,
) -> None:
    project = file_project(producer)
    primary = record(project, "primary", "primary")
    firmware = record(project, "firmware", "firmware")
    original = json.loads((project.path / firmware).read_text(encoding="utf-8"))
    template = project.path / "reuse.toml"
    template.write_text(
        template.read_text(encoding="utf-8").replace(
            "execution-to-reuse", original["execution"]["id"]
        ),
        encoding="utf-8",
    )

    rejected = assess(project, primary, firmware)
    accepted = assess(project, primary, firmware, target="reuse.toml")

    assert rejected.ret == 1
    assert accepted.ret == 0
    report = json.loads((project.path / "assessment.json").read_text(encoding="utf-8"))
    assert report["obligations"][1]["status"] == "PASSED"
    assert report["obligations"][1]["tests"][0]["context"]["firmware"] == "v0"
    assert report["obligations"][1]["tests"][0]["reuse"] == {
        "execution": original["execution"]["id"],
        "obligation": "REQ-002-b",
        "target": "build-42",
        "author": "Verification owner",
        "reason": "Reviewed equivalence for this exact obligation and target.",
    }
    assert report["obligations"][0]["tests"][0]["reuse"] is None
    assert json.loads((project.path / firmware).read_text(encoding="utf-8")) == original


def test_repeated_inputs_do_not_duplicate_execution_records(file_project: FileProject) -> None:
    project = file_project(producer)
    primary = record(project, "primary", "primary")
    secondary = record(project, "secondary", "secondary")

    result = assess(project, primary, primary, secondary)

    assert result.ret == 0
    report = json.loads((project.path / "assessment.json").read_text(encoding="utf-8"))
    assert [(test["nodeid"], test["outcome"]) for test in report["obligations"][0]["tests"]] == [
        ("test_behavior.py::test_primary_behavior", "PASSED")
    ]


def test_conflicting_execution_identities_are_rejected(file_project: FileProject) -> None:
    project = file_project(producer)
    primary = record(project, "primary", "primary")
    changed = json.loads((project.path / primary).read_text(encoding="utf-8"))
    changed["execution"]["context"]["artifact"] = "different-build"
    (project.path / "conflicting.json").write_text(json.dumps(changed), encoding="utf-8")

    result = assess(project, primary, "conflicting.json")

    assert result.ret == 4
    assert "conflicting execution" in (result.stdout.str() + result.stderr.str()).lower()


def test_collection_errors_survive_assessment(file_project: FileProject) -> None:
    project = file_project(producer)
    primary = record(project, "primary", "primary")
    secondary = record(project, "secondary", "secondary")
    broken = project.runpytest_subprocess(
        "collection_error.py",
        "--xspec-spec=xspec.toml",
        "--xspec-context=secondary.toml",
        "--xspec-json=broken.json",
    )

    result = assess(project, primary, secondary, "broken.json")

    assert broken.ret == pytest.ExitCode.INTERRUPTED
    assert result.ret == 1
    report = json.loads((project.path / "assessment.json").read_text(encoding="utf-8"))
    assert report["summary"]["status"] == "FAILED"
    assert report["summary"]["collection_errors"] == 1


def test_invalid_execution_outcomes_are_rejected_instead_of_trusting_the_summary(
    file_project: FileProject,
) -> None:
    project = file_project(producer)
    primary = record(project, "primary", "primary")
    changed = json.loads((project.path / primary).read_text(encoding="utf-8"))
    changed["requirements"]["REQ-001"]["tests"][0]["outcome"] = "COMPLETE"
    (project.path / "invalid.json").write_text(json.dumps(changed), encoding="utf-8")

    result = assess(project, "invalid.json")

    assert result.ret == 4
    assert "outcome" in (result.stdout.str() + result.stderr.str()).lower()


@pytest.mark.parametrize("alias", ["input", "output"])
def test_assessment_cannot_overwrite_a_hardlinked_input_or_output(
    file_project: FileProject, alias: str
) -> None:
    project = file_project(producer)
    primary = record(project, "primary", "primary")
    original = (project.path / primary).read_bytes()
    if alias == "input":
        (project.path / "assessment.json").hardlink_to(project.path / primary)
    else:
        (project.path / "assessment.json").write_text("existing assessment", encoding="utf-8")
        (project.path / "assessment.md").hardlink_to(project.path / "assessment.json")

    result = assess(project, primary)

    assert result.ret == 4
    assert "overwrite" in (result.stdout.str() + result.stderr.str()).lower()
    assert (project.path / primary).read_bytes() == original
    if alias == "output":
        assert (project.path / "assessment.json").read_text(
            encoding="utf-8"
        ) == "existing assessment"


@pytest.mark.parametrize(
    ("options", "outcome", "conclusion"),
    [
        ((), "FAILED", "FAILED"),
        (("--collect-only",), "SKIPPED", "INCOMPLETE"),
        (("-m", "not selected"), "DESELECTED", "INCOMPLETE"),
    ],
    ids=["failed", "discovered", "deselected"],
)
def test_reuse_never_changes_unsuccessful_original_outcomes(
    file_project: FileProject,
    monkeypatch: pytest.MonkeyPatch,
    options: tuple[str, ...],
    outcome: str,
    conclusion: str,
) -> None:
    project = file_project(producer)
    monkeypatch.setenv("ASSESSMENT_RESULT", "failed")
    primary = record(project, "old-primary", "old-primary", *options)
    monkeypatch.delenv("ASSESSMENT_RESULT")
    secondary = record(project, "secondary", "secondary")
    original = json.loads((project.path / primary).read_text(encoding="utf-8"))
    template = project.path / "reuse-primary.toml"
    template.write_text(
        template.read_text(encoding="utf-8").replace(
            "execution-to-reuse", original["execution"]["id"]
        ),
        encoding="utf-8",
    )

    result = assess(project, primary, secondary, target="reuse-primary.toml")

    assert result.ret == 1
    report = json.loads((project.path / "assessment.json").read_text(encoding="utf-8"))
    assert report["summary"]["status"] == conclusion
    assert report["obligations"][0]["status"] == outcome
    assert [
        (test["nodeid"], test["outcome"], test["applicable"])
        for test in report["obligations"][0]["tests"]
    ] == [("test_behavior.py::test_primary_behavior", outcome, True)]
    assert report["obligations"][0]["tests"][0]["reuse"]["execution"] == original["execution"]["id"]


def test_reuse_cannot_be_applied_to_an_unrelated_obligation(file_project: FileProject) -> None:
    project = file_project(producer)
    primary = record(project, "primary", "primary")
    original = json.loads((project.path / primary).read_text(encoding="utf-8"))
    template = project.path / "reuse.toml"
    template.write_text(
        template.read_text(encoding="utf-8").replace(
            "execution-to-reuse", original["execution"]["id"]
        ),
        encoding="utf-8",
    )

    result = assess(project, primary, target="reuse.toml")

    assert result.ret == 4
    assert "reuse" in (result.stdout.str() + result.stderr.str()).lower()
    assert "REQ-002-b" in result.stdout.str() + result.stderr.str()


def test_evidence_from_a_different_specification_baseline_cannot_verify_revised_requirements(
    file_project: FileProject,
) -> None:
    project = file_project(producer)
    primary = record(project, "primary", "primary")
    secondary = record(project, "secondary", "secondary")

    result = project.run(
        sys.executable,
        "-m",
        "pytest_xspec",
        "assess",
        "revised.toml",
        "--target",
        "target.toml",
        "--json",
        "assessment.json",
        primary,
        secondary,
    )

    assert result.ret == 1
    report = json.loads((project.path / "assessment.json").read_text(encoding="utf-8"))
    assert report["summary"]["status"] == "INCOMPLETE"
    assert [row["status"] for row in report["obligations"]] == ["INAPPLICABLE", "INAPPLICABLE"]
    for row in report["obligations"]:
        assert [(test["outcome"], test["applicable"]) for test in row["tests"]] == [
            ("PASSED", False)
        ]
        assert (
            row["tests"][0]["mismatches"]["execution.specification"]["expected"]
            == report["specification_digest"]
        )
        assert (
            row["tests"][0]["mismatches"]["execution.specification"]["actual"]
            != report["specification_digest"]
        )


@pytest.mark.parametrize(
    ("target", "diagnostic"),
    [
        ("wrong-target.toml", "target"),
        ("unknown-obligation.toml", "obligation"),
        ("missing-reason.toml", "reason"),
        ("duplicate-reuse.toml", "duplicate reuse"),
        ("unknown-configuration.toml", "configuration"),
    ],
)
def test_invalid_target_declarations_cannot_silently_produce_verification(
    file_project: FileProject,
    target: str,
    diagnostic: str,
) -> None:
    project = file_project(producer)
    primary = record(project, "primary", "primary")
    secondary = record(project, "secondary", "secondary")
    original = json.loads((project.path / secondary).read_text(encoding="utf-8"))
    document = project.path / target
    document.write_text(
        document.read_text(encoding="utf-8").replace(
            "execution-to-reuse", original["execution"]["id"]
        ),
        encoding="utf-8",
    )

    result = assess(project, primary, secondary, target=target)

    assert result.ret == 4
    message = result.stdout.str() + result.stderr.str()
    assert target in message
    assert diagnostic in message.lower()
