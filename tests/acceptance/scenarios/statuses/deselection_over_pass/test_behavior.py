import pytest


@pytest.mark.xspec("REQ-001")
def test_excluded() -> None:
    pass


@pytest.mark.xspec("REQ-001")
def test_passed() -> None:
    pass
