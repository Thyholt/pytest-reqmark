import pytest


@pytest.mark.xspec("REQ-001")
def test_first() -> None:
    pytest.fail("Stop execution before the second test")


@pytest.mark.xspec("REQ-002")
def test_second() -> None:
    assert True
