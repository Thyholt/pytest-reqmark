import pytest


@pytest.mark.xspec("REQ-001")
def test_first() -> None:
    pass


@pytest.mark.xspec("REQ-001")
def test_second() -> None:
    pytest.fail("Intentional acceptance scenario failure")
