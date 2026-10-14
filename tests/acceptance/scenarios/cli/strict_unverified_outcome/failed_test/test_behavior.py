import pytest


@pytest.mark.req("REQ-001")
def test_behavior():
    pytest.fail("Intentional acceptance scenario failure")
