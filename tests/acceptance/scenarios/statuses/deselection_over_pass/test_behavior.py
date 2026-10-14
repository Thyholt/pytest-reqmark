import pytest


@pytest.mark.tracereq("REQ-001")
def test_excluded():
    pass


@pytest.mark.tracereq("REQ-001")
def test_passed():
    pass
