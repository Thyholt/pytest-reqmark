import pytest


@pytest.mark.xspec("REQ-001")
def test_first() -> None:
    pass


def test_unmarked_failure() -> None:
    pytest.fail("Stop execution before the remaining requirement test")


@pytest.mark.xspec("REQ-001")
def test_second() -> None:
    pass
