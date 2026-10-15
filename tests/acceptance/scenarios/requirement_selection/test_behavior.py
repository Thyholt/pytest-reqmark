import pytest


@pytest.fixture(autouse=True)
def record_fixture_execution(request: pytest.FixtureRequest) -> None:
    print(f"FIXTURE EXECUTED: {request.node.nodeid}")


@pytest.mark.chosen
@pytest.mark.xspec("REQ-001")
@pytest.mark.xspec("REQ-001")
def test_first_behavior() -> None:
    print("TEST BODY EXECUTED: test_behavior.py::test_first_behavior")


@pytest.mark.xspec("REQ-001")
@pytest.mark.xspec("REQ-002")
def test_shared_behavior() -> None:
    print("TEST BODY EXECUTED: test_behavior.py::test_shared_behavior")


@pytest.mark.chosen
@pytest.mark.xspec("REQ-002")
def test_second_behavior() -> None:
    print("TEST BODY EXECUTED: test_behavior.py::test_second_behavior")


def test_unmarked_behavior() -> None:
    print("TEST BODY EXECUTED: test_behavior.py::test_unmarked_behavior")


@pytest.mark.xspec("Krav / æøå : 1, del")
def test_opaque_behavior() -> None:
    print("TEST BODY EXECUTED: test_behavior.py::test_opaque_behavior")
