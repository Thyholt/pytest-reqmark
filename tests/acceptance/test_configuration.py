"""Users configure their inventory in pyproject.toml or pytest.ini only."""

import pytest

MARKED_TEST = '@pytest.mark.req("REQ-001")\ndef test_behavior():\n    pass\n'


def test_requirements_can_be_declared_in_pytest_ini(user_project, read_report):
    project = user_project(["REQ-001"], MARKED_TEST)
    (project.path / "pyproject.toml").unlink()
    project.makefile(".ini", pytest="[pytest]\nreq_requirements =\n    REQ-001\n    REQ-002\n")
    project.runpytest_subprocess("--req-json=report.json")
    requirements = read_report(project)["requirements"]
    assert requirements["REQ-001"]["status"] == "PASSED"
    assert requirements["REQ-002"] == {"status": "MISSING", "tests": []}


def test_pyproject_inventory_is_read_even_when_pytest_ini_controls_pytest(
    user_project, read_report
):
    project = user_project(["REQ-001"], MARKED_TEST)
    project.makefile(".ini", pytest="[pytest]\naddopts = -q\n")
    assert project.runpytest_subprocess("--req-strict", "--req-json=report.json").ret == 0
    assert read_report(project)["requirements"]["REQ-001"]["status"] == "PASSED"


def test_declaring_an_inventory_in_both_supported_files_is_rejected(user_project):
    project = user_project(["REQ-001"], MARKED_TEST)
    project.makefile(".ini", pytest="[pytest]\nreq_requirements =\n    REQ-002\n")
    result = project.runpytest_subprocess("--req-report")
    assert result.ret != pytest.ExitCode.OK
    message = result.stdout.str() + result.stderr.str()
    assert "pyproject.toml" in message
    assert "pytest.ini" in message


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("setup.cfg", "[tool:pytest]\nreq_requirements = REQ-001\n"),
        ("tox.ini", "[pytest]\nreq_requirements = REQ-001\n"),
        ("requirements.json", '{"requirements": ["REQ-001"]}'),
        ("requirements.yaml", "requirements:\n  - REQ-001\n"),
    ],
)
def test_other_configuration_files_do_not_supply_a_requirement_inventory(
    user_project, filename, content
):
    project = user_project(["REQ-001"], MARKED_TEST)
    (project.path / "pyproject.toml").unlink()
    (project.path / filename).write_text(content, encoding="utf-8")
    result = project.runpytest_subprocess("--req-strict")
    assert result.ret != pytest.ExitCode.OK
    assert "REQ-001" in result.stdout.str() + result.stderr.str()


def test_normal_pytest_without_requirement_configuration_still_works(user_project):
    project = user_project([], "def test_behavior():\n    pass\n")
    (project.path / "pyproject.toml").unlink()
    result = project.runpytest_subprocess()
    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=1)


def test_no_requirement_configuration_means_success_with_zero_requirements(
    user_project, read_report
):
    project = user_project([], "def test_behavior():\n    pass\n")
    (project.path / "pyproject.toml").unlink()
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


def test_duplicate_requirement_ids_in_pytest_ini_are_rejected(user_project):
    project = user_project(["REQ-001"], MARKED_TEST)
    (project.path / "pyproject.toml").unlink()
    project.makefile(".ini", pytest="[pytest]\nreq_requirements =\n    REQ-001\n    REQ-001\n")
    result = project.runpytest_subprocess()
    assert result.ret != pytest.ExitCode.OK
    message = result.stdout.str() + result.stderr.str()
    assert "requirements" in message.lower()
    assert "REQ-001" in message
