import pytest


@pytest.mark.tracereq("REQ-001")
def test_skipped():
    pytest.skip("unavailable")


@pytest.mark.tracereq("REQ-001")
def test_excluded():
    pass
