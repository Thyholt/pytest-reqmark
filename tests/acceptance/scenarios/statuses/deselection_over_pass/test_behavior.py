import pytest


@pytest.mark.req("REQ-001")
def test_excluded():
    pass


@pytest.mark.req("REQ-001")
def test_passed():
    pass
