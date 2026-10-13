"""Reports show all declared requirements and count verified requirements, not tests."""

import pytest

REPORT_SCENARIO = """
@pytest.mark.req("training.yolo.config")
def test_parameters_logged():
    pass

@pytest.mark.req("training.yolo.config")
def test_source_logged():
    pass

@pytest.mark.req("dataset.versioning")
def test_version_stable():
    pytest.skip("not ready")
"""


def test_terminal_report_shows_requirement_statuses_test_counts_and_coverage(user_project):
    project = user_project(
        ["training.yolo.config", "training.rfdetr.config", "dataset.versioning"], REPORT_SCENARIO
    )
    result = project.runpytest_subprocess("--req-report")
    assert result.ret == pytest.ExitCode.OK
    result.stdout.fnmatch_lines(
        [
            "*pytest-reqmark*",
            "*training.yolo.config*PASSED*2*",
            "*training.rfdetr.config*MISSING*0*",
            "*dataset.versioning*SKIPPED*1*",
            "*Requirements:*3*",
            "*Passed:*1*",
            "*Unverified:*2*",
            "*Coverage:*33.3%*",
        ]
    )


def test_json_report_includes_all_requirements_individual_tests_and_summary(
    user_project, read_report
):
    project = user_project(
        ["training.yolo.config", "training.rfdetr.config", "dataset.versioning"], REPORT_SCENARIO
    )
    assert project.runpytest_subprocess("--req-json=report.json").ret == pytest.ExitCode.OK
    report = read_report(project)
    assert report["summary"] == {
        "requirements": 3,
        "passed": 1,
        "unverified": 2,
        "coverage": pytest.approx(100 / 3),
        "verified": False,
        "collection_errors": 0,
    }
    assert report["requirements"] == {
        "training.yolo.config": {
            "status": "PASSED",
            "tests": [
                {"nodeid": "test_behavior.py::test_parameters_logged", "outcome": "PASSED"},
                {"nodeid": "test_behavior.py::test_source_logged", "outcome": "PASSED"},
            ],
        },
        "training.rfdetr.config": {"status": "MISSING", "tests": []},
        "dataset.versioning": {
            "status": "SKIPPED",
            "tests": [{"nodeid": "test_behavior.py::test_version_stable", "outcome": "SKIPPED"}],
        },
    }


@pytest.mark.parametrize("config_file", ["pyproject.toml", "pytest.ini"])
def test_an_empty_inventory_reports_zero_coverage_without_dividing_by_zero(
    user_project, read_report, config_file
):
    project = user_project([], "def test_unmarked():\n    pass\n")
    if config_file == "pytest.ini":
        (project.path / "pyproject.toml").unlink()
        project.makefile(".ini", pytest="[pytest]\nreq_requirements =\n")
    result = project.runpytest_subprocess("--req-strict", "--req-json=report.json")
    assert result.ret == pytest.ExitCode.OK
    assert read_report(project) == {
        "requirements": {},
        "summary": {
            "requirements": 0,
            "passed": 0,
            "unverified": 0,
            "coverage": 0.0,
            "verified": True,
            "collection_errors": 0,
        },
    }
