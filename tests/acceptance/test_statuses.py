"""Users can see why a requirement is or is not verified."""

import pytest


@pytest.mark.parametrize(
    ("tests", "fixtures", "status"),
    [
        pytest.param(
            """
@pytest.mark.req("REQ-001")
def test_behavior():
    pass
""",
            "",
            "PASSED",
            id="passing-test",
        ),
        pytest.param(
            """
@pytest.mark.req("REQ-001")
def test_behavior():
    assert False
""",
            "",
            "FAILED",
            id="failed-test",
        ),
        pytest.param(
            """
@pytest.mark.req("REQ-001")
def test_behavior(broken):
    pass
""",
            """
@pytest.fixture
def broken():
    raise RuntimeError("setup failed")
""",
            "ERROR",
            id="setup-error",
        ),
        pytest.param(
            """
@pytest.mark.req("REQ-001")
def test_behavior():
    pytest.skip("not available")
""",
            "",
            "SKIPPED",
            id="skipped-test",
        ),
        pytest.param(
            """
@pytest.mark.req("REQ-001")
@pytest.mark.xfail(reason="known issue")
def test_behavior():
    assert False
""",
            "",
            "XFAILED",
            id="expected-failure",
        ),
        pytest.param(
            """
@pytest.mark.req("REQ-001")
@pytest.mark.xfail(reason="known issue")
def test_behavior():
    pass
""",
            "",
            "XPASSED",
            id="unexpected-pass",
        ),
    ],
)
def test_the_report_explains_the_outcome_of_a_marked_test(
    user_project, read_report, tests, fixtures, status
):
    project = user_project(["REQ-001"], tests, fixtures=fixtures)

    project.runpytest_subprocess("--req-json=report.json")

    report = read_report(project)
    assert report["requirements"]["REQ-001"] == {
        "status": status,
        "tests": [{"nodeid": "test_behavior.py::test_behavior", "outcome": status}],
    }
    assert report["summary"]["verified"] is (status == "PASSED")


def test_teardown_errors_make_a_passing_test_unverified(user_project, read_report):
    project = user_project(
        ["REQ-001"],
        """
@pytest.mark.req("REQ-001")
def test_behavior(broken):
    pass
""",
        fixtures="""
@pytest.fixture
def broken():
    yield
    raise RuntimeError("teardown failed")
""",
    )

    result = project.runpytest_subprocess("--req-json=report.json")

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    assert read_report(project)["requirements"]["REQ-001"] == {
        "status": "ERROR",
        "tests": [{"nodeid": "test_behavior.py::test_behavior", "outcome": "ERROR"}],
    }


def test_teardown_errors_take_precedence_over_a_test_failure(user_project, read_report):
    project = user_project(
        ["REQ-001"],
        """
@pytest.mark.req("REQ-001")
def test_behavior(broken):
    assert False
""",
        fixtures="""
@pytest.fixture
def broken():
    yield
    raise RuntimeError("teardown failed")
""",
    )

    result = project.runpytest_subprocess("--req-json=report.json")

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    assert read_report(project)["requirements"]["REQ-001"] == {
        "status": "ERROR",
        "tests": [{"nodeid": "test_behavior.py::test_behavior", "outcome": "ERROR"}],
    }


def test_a_fixture_skip_is_reported_as_skipped(user_project, read_report):
    project = user_project(
        ["REQ-001"],
        """
@pytest.mark.req("REQ-001")
def test_behavior(unavailable):
    pass
""",
        fixtures="""
@pytest.fixture
def unavailable():
    pytest.skip("unavailable")
""",
    )

    result = project.runpytest_subprocess("--req-json=report.json")

    assert result.ret == pytest.ExitCode.OK
    assert read_report(project)["requirements"]["REQ-001"] == {
        "status": "SKIPPED",
        "tests": [{"nodeid": "test_behavior.py::test_behavior", "outcome": "SKIPPED"}],
    }


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

    result = project.runpytest_subprocess("--req-json=report.json")

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    assert read_report(project)["requirements"]["REQ-001"] == {
        "status": "XPASSED",
        "tests": [{"nodeid": "test_behavior.py::test_behavior", "outcome": "XPASSED"}],
    }


@pytest.mark.parametrize(
    "test_order",
    [("test_setup_error", "test_failure"), ("test_failure", "test_setup_error")],
)
def test_setup_errors_take_priority_over_test_failures(user_project, read_report, test_order):
    project = user_project(
        ["REQ-001"],
        """
@pytest.mark.req("REQ-001")
def test_setup_error(broken):
    pass

@pytest.mark.req("REQ-001")
def test_failure():
    assert False
""",
        fixtures="""
@pytest.fixture
def broken():
    raise RuntimeError("setup failed")
""",
    )
    node_ids = [f"test_behavior.py::{name}" for name in test_order]

    result = project.runpytest_subprocess("--req-json=report.json", *node_ids)

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    requirement = read_report(project)["requirements"]["REQ-001"]
    assert requirement["status"] == "ERROR"
    outcomes = {
        "test_behavior.py::test_setup_error": "ERROR",
        "test_behavior.py::test_failure": "FAILED",
    }
    assert requirement["tests"] == [
        {"nodeid": node_id, "outcome": outcomes[node_id]} for node_id in node_ids
    ]


@pytest.mark.parametrize(
    "test_order",
    [("test_failure", "test_unexpected_pass"), ("test_unexpected_pass", "test_failure")],
)
def test_failures_take_priority_over_unexpected_passes(user_project, read_report, test_order):
    project = user_project(
        ["REQ-001"],
        """
@pytest.mark.req("REQ-001")
def test_failure():
    assert False

@pytest.mark.req("REQ-001")
@pytest.mark.xfail(reason="known issue")
def test_unexpected_pass():
    pass
""",
    )
    node_ids = [f"test_behavior.py::{name}" for name in test_order]

    result = project.runpytest_subprocess("--req-json=report.json", *node_ids)

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    requirement = read_report(project)["requirements"]["REQ-001"]
    assert requirement["status"] == "FAILED"
    outcomes = {
        "test_behavior.py::test_failure": "FAILED",
        "test_behavior.py::test_unexpected_pass": "XPASSED",
    }
    assert requirement["tests"] == [
        {"nodeid": node_id, "outcome": outcomes[node_id]} for node_id in node_ids
    ]


@pytest.mark.parametrize(
    "test_order",
    [
        ("test_unexpected_pass", "test_expected_failure"),
        ("test_expected_failure", "test_unexpected_pass"),
    ],
)
def test_unexpected_passes_take_priority_over_expected_failures(
    user_project, read_report, test_order
):
    project = user_project(
        ["REQ-001"],
        """
@pytest.mark.req("REQ-001")
@pytest.mark.xfail(reason="known issue")
def test_unexpected_pass():
    pass

@pytest.mark.req("REQ-001")
@pytest.mark.xfail(reason="known issue")
def test_expected_failure():
    assert False
""",
    )
    node_ids = [f"test_behavior.py::{name}" for name in test_order]

    result = project.runpytest_subprocess("--req-json=report.json", *node_ids)

    assert result.ret == pytest.ExitCode.OK
    requirement = read_report(project)["requirements"]["REQ-001"]
    assert requirement["status"] == "XPASSED"
    outcomes = {
        "test_behavior.py::test_unexpected_pass": "XPASSED",
        "test_behavior.py::test_expected_failure": "XFAILED",
    }
    assert requirement["tests"] == [
        {"nodeid": node_id, "outcome": outcomes[node_id]} for node_id in node_ids
    ]


@pytest.mark.parametrize(
    "test_order",
    [("test_expected_failure", "test_skipped"), ("test_skipped", "test_expected_failure")],
)
def test_expected_failures_take_priority_over_skips(user_project, read_report, test_order):
    project = user_project(
        ["REQ-001"],
        """
@pytest.mark.req("REQ-001")
@pytest.mark.xfail(reason="known issue")
def test_expected_failure():
    assert False

@pytest.mark.req("REQ-001")
def test_skipped():
    pytest.skip("unavailable")
""",
    )
    node_ids = [f"test_behavior.py::{name}" for name in test_order]

    result = project.runpytest_subprocess("--req-json=report.json", *node_ids)

    assert result.ret == pytest.ExitCode.OK
    requirement = read_report(project)["requirements"]["REQ-001"]
    assert requirement["status"] == "XFAILED"
    outcomes = {
        "test_behavior.py::test_expected_failure": "XFAILED",
        "test_behavior.py::test_skipped": "SKIPPED",
    }
    assert requirement["tests"] == [
        {"nodeid": node_id, "outcome": outcomes[node_id]} for node_id in node_ids
    ]


@pytest.mark.parametrize(
    "test_order",
    [("test_skipped", "test_excluded"), ("test_excluded", "test_skipped")],
)
def test_skips_take_priority_over_deselection(user_project, read_report, test_order):
    project = user_project(
        ["REQ-001"],
        """
@pytest.mark.req("REQ-001")
def test_skipped():
    pytest.skip("unavailable")

@pytest.mark.req("REQ-001")
def test_excluded():
    pass
""",
    )
    node_ids = [f"test_behavior.py::{name}" for name in test_order]

    result = project.runpytest_subprocess("--req-json=report.json", *node_ids, "-k", "not excluded")

    assert result.ret == pytest.ExitCode.OK
    requirement = read_report(project)["requirements"]["REQ-001"]
    assert requirement["status"] == "SKIPPED"
    outcomes = {
        "test_behavior.py::test_skipped": "SKIPPED",
        "test_behavior.py::test_excluded": "DESELECTED",
    }
    assert requirement["tests"] == [
        {"nodeid": node_id, "outcome": outcomes[node_id]} for node_id in node_ids
    ]


@pytest.mark.parametrize(
    "test_order",
    [("test_excluded", "test_passed"), ("test_passed", "test_excluded")],
)
def test_deselection_prevents_verification_despite_a_passing_test(
    user_project, read_report, test_order
):
    project = user_project(
        ["REQ-001"],
        """
@pytest.mark.req("REQ-001")
def test_excluded():
    pass

@pytest.mark.req("REQ-001")
def test_passed():
    pass
""",
    )
    node_ids = [f"test_behavior.py::{name}" for name in test_order]

    result = project.runpytest_subprocess("--req-json=report.json", *node_ids, "-k", "not excluded")

    assert result.ret == pytest.ExitCode.OK
    requirement = read_report(project)["requirements"]["REQ-001"]
    assert requirement["status"] == "DESELECTED"
    outcomes = {
        "test_behavior.py::test_excluded": "DESELECTED",
        "test_behavior.py::test_passed": "PASSED",
    }
    assert requirement["tests"] == [
        {"nodeid": node_id, "outcome": outcomes[node_id]} for node_id in node_ids
    ]


def test_a_requirement_is_verified_when_both_associated_tests_pass(user_project, read_report):
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

    result = project.runpytest_subprocess("--req-strict", "--req-json=report.json")

    assert result.ret == pytest.ExitCode.OK
    report = read_report(project)
    assert report["requirements"]["REQ-001"] == {
        "status": "PASSED",
        "tests": [
            {"nodeid": "test_behavior.py::test_first", "outcome": "PASSED"},
            {"nodeid": "test_behavior.py::test_second", "outcome": "PASSED"},
        ],
    }
    assert report["summary"]["verified"] is True


@pytest.mark.parametrize(
    ("tests", "status"),
    [
        pytest.param(
            """
@pytest.mark.req("REQ-001")
def test_first():
    pass

@pytest.mark.req("REQ-001")
def test_second():
    assert False
""",
            "FAILED",
            id="one-failed-test",
        ),
        pytest.param(
            """
@pytest.mark.req("REQ-001")
def test_first():
    pass

@pytest.mark.req("REQ-001")
def test_second():
    pytest.skip("unavailable")
""",
            "SKIPPED",
            id="one-skipped-test",
        ),
    ],
)
def test_one_passing_test_does_not_verify_a_requirement_with_an_unverified_test(
    user_project, read_report, tests, status
):
    project = user_project(["REQ-001"], tests)

    result = project.runpytest_subprocess("--req-strict", "--req-json=report.json")

    assert result.ret != pytest.ExitCode.OK
    report = read_report(project)
    assert report["requirements"]["REQ-001"] == {
        "status": status,
        "tests": [
            {"nodeid": "test_behavior.py::test_first", "outcome": "PASSED"},
            {"nodeid": "test_behavior.py::test_second", "outcome": status},
        ],
    }
    assert report["summary"]["verified"] is False
