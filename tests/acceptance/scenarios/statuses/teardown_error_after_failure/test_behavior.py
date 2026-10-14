import pytest


@pytest.mark.tracereq("REQ-001")
def test_behavior(broken):
    pytest.fail("Intentional acceptance scenario failure")
