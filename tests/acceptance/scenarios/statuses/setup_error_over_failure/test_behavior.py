import pytest


@pytest.mark.xspec("REQ-001")
def test_setup_error(broken):
    pass


@pytest.mark.xspec("REQ-001")
def test_failure():
    pytest.fail("Intentional acceptance scenario failure")
