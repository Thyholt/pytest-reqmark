import pytest


@pytest.mark.tracereq("REQ-001")
def test_first():
    pass


@pytest.mark.tracereq("REQ-001")
def test_second():
    pytest.fail("Intentional acceptance scenario failure")
