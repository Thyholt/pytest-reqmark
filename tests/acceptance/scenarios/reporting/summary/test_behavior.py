import pytest


@pytest.mark.xspec("REQ-001")
def test_first_behavior() -> None:
    pass


@pytest.mark.xspec("REQ-001")
def test_second_behavior() -> None:
    pass


@pytest.mark.xspec("REQ-003")
def test_third_behavior() -> None:
    pytest.skip("not ready")
