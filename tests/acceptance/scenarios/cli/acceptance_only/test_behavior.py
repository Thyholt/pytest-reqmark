import pytest


@pytest.mark.xspec("REQ-001")
def test_marked() -> None:
    pass


def test_unmarked() -> None:
    pytest.fail("Intentional acceptance scenario failure")
