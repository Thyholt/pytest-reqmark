import pytest


@pytest.mark.tracereq("REQ-001")
def test_behavior():
    pytest.fail("Intentional acceptance scenario failure")
