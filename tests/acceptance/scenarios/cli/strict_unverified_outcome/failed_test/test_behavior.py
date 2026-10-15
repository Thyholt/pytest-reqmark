import pytest


@pytest.mark.xspec("REQ-001")
def test_behavior():
    pytest.fail("Intentional acceptance scenario failure")
