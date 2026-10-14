import pytest


@pytest.mark.tracereq("REQ-001")
def test_first():
    pass


def test_unmarked_failure():
    pytest.fail("Stop execution before the remaining requirement test")


@pytest.mark.tracereq("REQ-001")
def test_second():
    pass
