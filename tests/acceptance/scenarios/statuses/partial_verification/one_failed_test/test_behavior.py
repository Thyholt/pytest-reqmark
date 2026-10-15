import pytest


@pytest.mark.xspec("REQ-001")
def test_first():
    pass


@pytest.mark.xspec("REQ-001")
def test_second():
    pytest.fail("Intentional acceptance scenario failure")
