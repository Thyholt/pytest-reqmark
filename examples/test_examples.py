"""Run the example projects and check that their advertised behavior stays true."""

import json
import sys
from collections.abc import Callable
from pathlib import Path
from shutil import copytree, ignore_patterns
from types import ModuleType

import pytest

from examples import (
    acceptance_only,
    medical_verification,
    missing_requirement,
    partial_verification,
    quickstart,
    specification_document,
)

pytest_plugins = ["pytester"]


def test_medical_challenge_preserves_evidence_across_all_seven_assessments(
    example_project: Callable[[ModuleType], pytest.Pytester],
) -> None:
    project = example_project(medical_verification)

    result = project.run(sys.executable, "run.py")

    assert result.ret == 0
    result.stdout.fnmatch_lines(
        [
            "3.1: COMPLETE",
            "3.2: INCOMPLETE",
            "3.3: FAILED",
            "equipment-unavailable: INCOMPLETE",
            "firmware-change: INCOMPLETE",
            "firmware-reuse: COMPLETE",
            "physical-required: INCOMPLETE",
        ]
    )
    directory = project.path / "results"
    index = json.loads((directory / "report.json").read_text(encoding="utf-8"))
    assert index == [
        {"scenario": name, "status": status, "report": f"{name}.json"}
        for name, status in (
            ("3.1", "COMPLETE"),
            ("3.2", "INCOMPLETE"),
            ("3.3", "FAILED"),
            ("equipment-unavailable", "INCOMPLETE"),
            ("firmware-change", "INCOMPLETE"),
            ("firmware-reuse", "COMPLETE"),
            ("physical-required", "INCOMPLETE"),
        )
    ]
    for scenario in index:
        name = scenario["scenario"]
        report = json.loads((directory / scenario["report"]).read_text(encoding="utf-8"))
        assert report["target"] == name
        assert report["summary"]["status"] == scenario["status"]
        assert [row["id"] for row in report["obligations"]] == [
            f"{requirement}-{hardware}"
            for hardware in ("A", "B")
            for requirement in ("SW-001", "SW-002", "HW-001", "SYS-001")
        ]
        assert [row["status"] for row in report["obligations"]] == (
            ["INAPPLICABLE"] * 8
            if name == "physical-required"
            else ["PASSED"] * 7
            + [
                {
                    "3.2": "INAPPLICABLE",
                    "3.3": "FAILED",
                    "equipment-unavailable": "DESELECTED",
                    "firmware-change": "INAPPLICABLE",
                }.get(name, "PASSED")
            ]
        )
        assert (directory / f"{name}.md").is_file()
        assert f"[Assessment]({name}.md)" in (directory / "report.md").read_text(encoding="utf-8")
        for row in report["obligations"]:
            suite, test_name = {
                "SW-001": ("software", "occlusion_is_detected"),
                "SW-002": ("software", "stop_command_follows_detection"),
                "HW-001": ("hardware", "controller_bench_stops_delivery"),
                "SYS-001": ("system", "fluid_delivery_stops"),
            }[row["requirement"]]
            assert row["suite"] == suite
            assert row["id"] == f"{row['requirement']}-{row['configuration']}"
            outcome = (
                "FAILED"
                if (name, row["id"]) == ("3.3", "SYS-001-B")
                else "DESELECTED"
                if (name, row["id"]) == ("equipment-unavailable", "SYS-001-B")
                else "PASSED"
            )
            expected_tests = (
                []
                if row["status"] == "INAPPLICABLE"
                else [(suite, f"test_behavior.py::test_{test_name}", outcome, row["configuration"])]
            )
            assert [
                (test["suite"], test["nodeid"], test["outcome"], test["context"]["hardware"])
                for test in row["tests"]
                if test["applicable"]
            ] == expected_tests
            for test in row["tests"]:
                original = json.loads(Path(test["source"]).read_text(encoding="utf-8"))
                assert test["execution"] == original["execution"]["id"]
                assert test["context"] == original["execution"]["context"]
                assert test["provenance"] == original["execution"]["provenance"]
                assert test["started_at"] == original["execution"]["started_at"]
                assert test["finished_at"] == original["execution"]["finished_at"]
                assert original["requirements"][row["requirement"]]["tests"] == [
                    {"nodeid": test["nodeid"], "outcome": test["outcome"]}
                ]
                assert test["context"]["environment"] == "simulation"
        assert [entry["execution"] for entry in report["executions"]] == [
            json.loads(Path(entry["source"]).read_text(encoding="utf-8"))["execution"]
            for entry in report["executions"]
        ]

    baseline = json.loads((directory / "3.1.json").read_text(encoding="utf-8"))
    original_source = next(
        Path(entry["source"])
        for entry in baseline["executions"]
        if entry["execution"]["suite"] == "system"
        and entry["execution"]["context"]["hardware"] == "B"
    )
    original = json.loads(original_source.read_text(encoding="utf-8"))
    stale = json.loads((directory / "3.2.json").read_text(encoding="utf-8"))
    assert [
        (test["execution"], test["context"], test["outcome"], test["applicable"])
        for test in stale["obligations"][-1]["tests"]
        if test["context"]["hardware"] == "B"
    ] == [(original["execution"]["id"], original["execution"]["context"], "PASSED", False)]
    changed = json.loads((directory / "firmware-change.json").read_text(encoding="utf-8"))
    reused = json.loads((directory / "firmware-reuse.json").read_text(encoding="utf-8"))
    assert changed["obligations"][-1]["expected"]["firmware"] == "fw-b-2"
    assert [
        (test["execution"], test["context"]["firmware"], test["outcome"], test["reuse"])
        for test in reused["obligations"][-1]["tests"]
        if test["applicable"]
    ] == [
        (
            original["execution"]["id"],
            "fw-b-1",
            "PASSED",
            {
                "target": "firmware-reuse",
                "execution": original["execution"]["id"],
                "obligation": "SYS-001-B",
                "author": "Fictional verification engineer",
                "reason": "Demonstration approval: firmware changes diagnostics only. "
                "The simulated motor and fluid behavior is unchanged. "
                "This is not a real engineering approval.",
            },
        )
    ]
    equipment = json.loads((directory / "equipment-unavailable.json").read_text(encoding="utf-8"))
    equipment_source = next(
        Path(entry["source"])
        for entry in equipment["executions"]
        if entry["execution"]["suite"] == "system"
        and entry["execution"]["context"]["hardware"] == "B"
    )
    defective = json.loads((directory / "3.3.json").read_text(encoding="utf-8"))
    defective_source = next(
        Path(test["source"]) for test in defective["obligations"][-1]["tests"] if test["applicable"]
    )
    assert "SIMULATED_EXECUTION" in (original_source.parent / "console.log").read_text(
        encoding="utf-8"
    )
    assert "SIMULATED_EXECUTION" not in (equipment_source.parent / "console.log").read_text(
        encoding="utf-8"
    )
    assert "FLOW_STOPPED_AT 340 ms" in (defective_source.parent / "console.log").read_text(
        encoding="utf-8"
    )


def test_medical_challenge_repair_verifies_the_system_without_relabeling_stale_evidence(
    example_project: Callable[[ModuleType], pytest.Pytester],
) -> None:
    project = example_project(medical_verification)
    directory = project.path / "results"
    original_result = project.run(sys.executable, "run.py")
    assert original_result.ret == 0
    original = json.loads((directory / "3.3.json").read_text(encoding="utf-8"))
    original_test = next(
        test for test in original["obligations"][-1]["tests"] if test["applicable"]
    )
    original_record = Path(original_test["source"])
    original_measurements = Path(original_test["provenance"]["measurements"])
    original_record_bytes = original_record.read_bytes()
    original_measurement_bytes = original_measurements.read_bytes()

    result = project.run(sys.executable, "run.py", "--fix-residual-flow")

    assert result.ret == 0
    result.stdout.fnmatch_lines(["3.1: COMPLETE", "3.2: INCOMPLETE", "3.3: COMPLETE"])
    repaired = json.loads((directory / "3.3.json").read_text(encoding="utf-8"))
    stale = json.loads((directory / "3.2.json").read_text(encoding="utf-8"))
    assert repaired["summary"]["status"] == "COMPLETE"
    assert [row["status"] for row in repaired["obligations"]] == ["PASSED"] * 8
    assert stale["summary"]["status"] == "INCOMPLETE"
    assert stale["obligations"][-1]["status"] == "INAPPLICABLE"
    repaired_test = next(
        test for test in repaired["obligations"][-1]["tests"] if test["applicable"]
    )
    repaired_record = Path(repaired_test["source"])
    repaired_measurements = Path(repaired_test["provenance"]["measurements"])
    assert original_record.read_bytes() == original_record_bytes
    assert original_measurements.read_bytes() == original_measurement_bytes
    assert repaired_record != original_record
    assert repaired_measurements != original_measurements
    assert original_measurements.read_text(encoding="utf-8").splitlines() == [
        "test_nodeid,time_ms,delivered_ul",
        *[f"test_behavior.py::test_fluid_delivery_stops,{time_ms},1" for time_ms in range(340)],
        "test_behavior.py::test_fluid_delivery_stops,340,0",
    ]
    assert repaired_measurements.read_text(encoding="utf-8").splitlines() == [
        "test_nodeid,time_ms,delivered_ul",
        *[f"test_behavior.py::test_fluid_delivery_stops,{time_ms},1" for time_ms in range(240)],
        "test_behavior.py::test_fluid_delivery_stops,240,0",
    ]


@pytest.fixture
def example_project(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> Callable[[ModuleType], pytest.Pytester]:
    monkeypatch.delenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", raising=False)
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)
    monkeypatch.delenv("PYTEST_PLUGINS", raising=False)

    def copy(example: ModuleType) -> pytest.Pytester:
        (example_path,) = example.__path__
        copytree(
            example_path,
            pytester.path,
            dirs_exist_ok=True,
            ignore=ignore_patterns("__pycache__", ".pytest_cache", "report.json", "results"),
        )
        return pytester

    return copy


def test_quickstart_verifies_the_pizza(
    example_project: Callable[[ModuleType], pytest.Pytester],
) -> None:
    project = example_project(quickstart)

    result = project.runpytest_subprocess("--xspec-strict", "--xspec-json=report.json")

    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=1)
    report = json.loads((project.path / "report.json").read_text(encoding="utf-8"))
    assert report == json.loads(
        (Path(quickstart.__path__[0]) / "report.json").read_text(encoding="utf-8")
    )
    assert report["requirements"] == {
        "REQ-001": {
            "status": "PASSED",
            "tests": [
                {"nodeid": "test_behavior.py::test_pizza_has_two_slices", "outcome": "PASSED"}
            ],
        },
    }
    assert report["summary"]["verified"] is True
    assert report["summary"]["coverage"] == 100.0
    result.stdout.fnmatch_lines(["*REQ-001*PASSED*", "*Coverage:*100.0%*"])


def test_specification_document_verifies_the_addition_requirements(
    example_project: Callable[[ModuleType], pytest.Pytester],
) -> None:
    project = example_project(specification_document)

    result = project.runpytest_subprocess("--xspec-strict", "--xspec-json=report.json")

    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=2)
    report = json.loads((project.path / "report.json").read_text(encoding="utf-8"))
    assert report["requirements"] == {
        "REQ-001": {
            "status": "PASSED",
            "tests": [
                {
                    "nodeid": "test_behavior.py::test_adding_two_integers_returns_their_sum",
                    "outcome": "PASSED",
                },
                {
                    "nodeid": "test_behavior.py::test_adding_zero_preserves_the_value",
                    "outcome": "PASSED",
                },
            ],
        },
        "REQ-002": {
            "status": "PASSED",
            "tests": [
                {
                    "nodeid": "test_behavior.py::test_adding_zero_preserves_the_value",
                    "outcome": "PASSED",
                },
            ],
        },
    }
    assert report["summary"]["verified"] is True
    assert report["summary"]["coverage"] == 100.0
    result.stdout.fnmatch_lines(["*REQ-001*PASSED*2*", "*REQ-002*PASSED*1*"])


def test_missing_requirement_reports_the_other_sock(
    example_project: Callable[[ModuleType], pytest.Pytester],
) -> None:
    project = example_project(missing_requirement)

    result = project.runpytest_subprocess("--xspec-strict", "--xspec-json=report.json")

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    result.assert_outcomes(passed=1)
    report = json.loads((project.path / "report.json").read_text(encoding="utf-8"))
    assert report["requirements"] == {
        "REQ-001": {
            "status": "PASSED",
            "tests": [
                {"nodeid": "test_behavior.py::test_one_sock_survives", "outcome": "PASSED"},
            ],
        },
        "REQ-002": {"status": "MISSING", "tests": []},
    }
    assert report["summary"]["verified"] is False
    assert report["summary"]["coverage"] == 50.0
    result.stdout.fnmatch_lines(["*REQ-002*MISSING*", "*Coverage:*50.0%*"])


def test_partial_verification_keeps_the_cat_unverified(
    example_project: Callable[[ModuleType], pytest.Pytester],
) -> None:
    project = example_project(partial_verification)

    result = project.runpytest_subprocess("--xspec-strict", "--xspec-json=report.json")

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    result.assert_outcomes(passed=1, skipped=1)
    report = json.loads((project.path / "report.json").read_text(encoding="utf-8"))
    assert report["requirements"] == {
        "REQ-001": {
            "status": "SKIPPED",
            "tests": [
                {"nodeid": "test_behavior.py::test_cat_has_a_name", "outcome": "PASSED"},
                {"nodeid": "test_behavior.py::test_cat_attends_meetings", "outcome": "SKIPPED"},
            ],
        },
    }
    assert report["summary"]["verified"] is False
    assert report["summary"]["coverage"] == 0.0
    result.stdout.fnmatch_lines(["*REQ-001*SKIPPED*", "*Coverage:*0.0%*"])


def test_acceptance_only_verifies_the_duck_without_the_moon_test(
    example_project: Callable[[ModuleType], pytest.Pytester],
) -> None:
    project = example_project(acceptance_only)

    result = project.runpytest_subprocess(
        "-m", "xspec", "--xspec-strict", "--xspec-json=report.json"
    )

    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=1, deselected=1)
    report = json.loads((project.path / "report.json").read_text(encoding="utf-8"))
    assert report["requirements"] == {
        "REQ-001": {
            "status": "PASSED",
            "tests": [{"nodeid": "test_behavior.py::test_duck_says_quack", "outcome": "PASSED"}],
        },
    }
    assert report["summary"]["verified"] is True
    assert report["summary"]["coverage"] == 100.0


def test_plain_pytest_in_acceptance_only_still_fails_the_moon_test(
    example_project: Callable[[ModuleType], pytest.Pytester],
) -> None:
    project = example_project(acceptance_only)

    result = project.runpytest_subprocess("--xspec-strict", "--xspec-json=report.json")

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    result.assert_outcomes(passed=1, failed=1)
    report = json.loads((project.path / "report.json").read_text(encoding="utf-8"))
    assert report["requirements"] == {
        "REQ-001": {
            "status": "PASSED",
            "tests": [{"nodeid": "test_behavior.py::test_duck_says_quack", "outcome": "PASSED"}],
        },
    }
    assert report["summary"]["verified"] is True
    result.stdout.fnmatch_lines(["*test_moon_is_made_of_cheese*", "*REQ-001*PASSED*"])
