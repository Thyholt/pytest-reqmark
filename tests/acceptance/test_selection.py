"""Selection preserves known test identities; uncollected tests cannot be identified."""

import pytest


@pytest.mark.parametrize("selection", [("-k", "selected"), ("-m", "chosen")])
def test_selection_keeps_deselected_requirement_tests_in_the_report(
    user_project, read_report, selection
):
    project = user_project(
        ["REQ-001", "REQ-002"],
        """
@pytest.mark.chosen
@pytest.mark.req("REQ-001")
def test_selected():
    pass

def test_other():
    pass
""",
    )
    project.makepyfile(
        test_excluded='import pytest\n@pytest.mark.req("REQ-002")\ndef test_other():\n    pass\n'
    )
    project.makefile(".ini", pytest="[pytest]\nmarkers = chosen: selected test\n")
    project.runpytest_subprocess("--req-json=report.json", *selection)
    requirements = read_report(project)["requirements"]
    assert requirements["REQ-001"]["status"] == "PASSED"
    assert requirements["REQ-002"] == {
        "status": "DESELECTED",
        "tests": [{"nodeid": "test_excluded.py::test_other", "outcome": "DESELECTED"}],
    }


def test_a_requirement_without_any_collected_test_is_missing(user_project, read_report):
    project = user_project(["REQ-001"], "def test_unmarked():\n    pass\n")
    project.runpytest_subprocess("--req-json=report.json")
    assert read_report(project)["requirements"]["REQ-001"] == {"status": "MISSING", "tests": []}


def test_a_test_outside_the_collected_path_is_not_reported_as_deselected(user_project, read_report):
    project = user_project(["REQ-001"], "def test_unmarked():\n    pass\n")
    project.makepyfile(
        test_not_collected=(
            'import pytest\n@pytest.mark.req("REQ-001")\ndef test_other():\n    pass\n'
        )
    )
    project.runpytest_subprocess("test_behavior.py", "--req-json=report.json")
    assert read_report(project)["requirements"]["REQ-001"] == {"status": "MISSING", "tests": []}
