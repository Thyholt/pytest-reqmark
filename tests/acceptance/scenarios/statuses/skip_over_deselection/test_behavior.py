import pytest


@pytest.mark.xspec("REQ-001")
def test_skipped():
    pytest.skip("unavailable")


@pytest.mark.xspec("REQ-001")
def test_excluded():
    pass
