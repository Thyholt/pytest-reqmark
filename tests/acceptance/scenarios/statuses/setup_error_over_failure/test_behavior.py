import pytest


@pytest.mark.xspec("REQ-001")
def test_setup_error(broken: None) -> None:
    pass


@pytest.mark.xspec("REQ-001")
def test_failure() -> None:
    pytest.fail("Intentional acceptance scenario failure")
