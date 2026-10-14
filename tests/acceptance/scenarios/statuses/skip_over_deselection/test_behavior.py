import pytest


@pytest.mark.req("REQ-001")
def test_skipped():
    pytest.skip("unavailable")


@pytest.mark.req("REQ-001")
def test_excluded():
    pass
