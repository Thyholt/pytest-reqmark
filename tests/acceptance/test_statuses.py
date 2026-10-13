"""Users can see why a requirement is or is not verified."""

import pytest

SCENARIOS = {
    "PASSED": ("def test_behavior():\n    pass\n", ""),
    "FAILED": ("def test_behavior():\n    assert False\n", ""),
    "ERROR": (
        "def test_behavior(broken):\n    pass\n",
        "@pytest.fixture\ndef broken():\n    raise RuntimeError('setup failed')\n",
    ),
    "SKIPPED": ('def test_behavior():\n    pytest.skip("not available")\n', ""),
    "XFAILED": (
        '@pytest.mark.xfail(reason="known issue")\ndef test_behavior():\n    assert False\n',
        "",
    ),
    "XPASSED": (
        '@pytest.mark.xfail(reason="known issue")\ndef test_behavior():\n    pass\n',
        "",
    ),
}


@pytest.mark.parametrize("status", list(SCENARIOS))
def test_the_report_explains_the_outcome_of_a_marked_test(user_project, read_report, status):
    tests, fixtures = SCENARIOS[status]
    project = user_project(["REQ-001"], '@pytest.mark.req("REQ-001")\n' + tests, fixtures=fixtures)
    project.runpytest_subprocess("--req-json=report.json")
    report = read_report(project)
    requirement = report["requirements"]["REQ-001"]
    assert requirement["status"] == status
    assert report["summary"]["verified"] is (status == "PASSED")
    assert requirement["tests"] == [
        {"nodeid": "test_behavior.py::test_behavior", "outcome": status}
    ]


def test_teardown_errors_make_a_passing_test_unverified(user_project, read_report):
    project = user_project(
        ["REQ-001"],
        '@pytest.mark.req("REQ-001")\ndef test_behavior(broken):\n    pass\n',
        fixtures="@pytest.fixture\ndef broken():\n    yield\n    raise RuntimeError('teardown')\n",
    )
    project.runpytest_subprocess("--req-json=report.json")
    requirement = read_report(project)["requirements"]["REQ-001"]
    assert requirement["status"] == "ERROR"
    assert requirement["tests"] == [
        {"nodeid": "test_behavior.py::test_behavior", "outcome": "ERROR"}
    ]


def test_teardown_errors_take_precedence_over_a_test_failure(user_project, read_report):
    project = user_project(
        ["REQ-001"],
        '@pytest.mark.req("REQ-001")\ndef test_behavior(broken):\n    assert False\n',
        fixtures="@pytest.fixture\ndef broken():\n    yield\n    raise RuntimeError('teardown')\n",
    )
    project.runpytest_subprocess("--req-json=report.json")
    assert read_report(project)["requirements"]["REQ-001"]["status"] == "ERROR"


def test_a_fixture_skip_is_reported_as_skipped(user_project, read_report):
    project = user_project(
        ["REQ-001"],
        '@pytest.mark.req("REQ-001")\ndef test_behavior(unavailable):\n    pass\n',
        fixtures='@pytest.fixture\ndef unavailable():\n    pytest.skip("unavailable")\n',
    )
    project.runpytest_subprocess("--req-json=report.json")
    assert read_report(project)["requirements"]["REQ-001"]["status"] == "SKIPPED"


def test_strict_xfail_still_reports_an_unexpected_pass_as_xpassed(user_project, read_report):
    project = user_project(
        ["REQ-001"],
        """
@pytest.mark.req("REQ-001")
@pytest.mark.xfail(strict=True, reason="known issue")
def test_behavior():
    pass
""",
    )
    project.runpytest_subprocess("--req-json=report.json")
    assert read_report(project)["requirements"]["REQ-001"]["status"] == "XPASSED"


@pytest.mark.parametrize(
    ("higher", "lower"),
    [
        ("ERROR", "FAILED"),
        ("FAILED", "XPASSED"),
        ("XPASSED", "XFAILED"),
        ("XFAILED", "SKIPPED"),
        ("SKIPPED", "DESELECTED"),
        ("DESELECTED", "PASSED"),
    ],
)
@pytest.mark.parametrize("reverse_order", [False, True], ids=["higher-first", "lower-first"])
def test_a_requirement_reports_the_highest_priority_outcome(
    user_project, read_report, higher, lower, reverse_order
):
    sources = []
    fixtures = ""
    outcomes = [("higher", higher), ("lower", lower)]
    if reverse_order:
        outcomes.reverse()
    for name, status in outcomes:
        test, fixture = SCENARIOS.get(status, SCENARIOS["PASSED"])
        fixtures += fixture
        sources.append(
            '@pytest.mark.req("REQ-001")\n' + test.replace("test_behavior", f"test_{name}")
        )
    project = user_project(["REQ-001"], "\n".join(sources), fixtures=fixtures)
    deselected = "higher" if higher == "DESELECTED" else "lower"
    args = ["-k", f"not {deselected}"] if "DESELECTED" in (higher, lower) else []
    project.runpytest_subprocess("--req-json=report.json", *args)
    requirement = read_report(project)["requirements"]["REQ-001"]
    assert requirement["status"] == higher
    assert {test["outcome"] for test in requirement["tests"]} == {higher, lower}


def test_a_requirement_is_verified_only_when_all_its_tests_pass(user_project, read_report):
    project = user_project(
        ["REQ-001"],
        """
@pytest.mark.req("REQ-001")
def test_first():
    pass

@pytest.mark.req("REQ-001")
def test_second():
    pass
""",
    )
    assert project.runpytest_subprocess("--req-strict", "--req-json=report.json").ret == 0
    requirement = read_report(project)["requirements"]["REQ-001"]
    assert requirement["status"] == "PASSED"
    assert len(requirement["tests"]) == 2
