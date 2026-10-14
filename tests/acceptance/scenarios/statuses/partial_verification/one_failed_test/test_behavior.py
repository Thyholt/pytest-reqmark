import pytest


@pytest.mark.req("REQ-001")
def test_first():
    pass


@pytest.mark.req("REQ-001")
def test_second():
    pytest.fail("Intentional acceptance scenario failure")
