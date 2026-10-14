import pytest


@pytest.mark.tracereq("REQ-001")
def test_first():
    pytest.fail("Stop execution before the second test")


@pytest.mark.tracereq("REQ-002")
def test_second():
    assert True
