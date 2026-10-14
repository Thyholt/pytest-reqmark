import pytest


@pytest.mark.tracereq("REQ-001")
@pytest.mark.xfail(reason="known issue")
def test_unexpected_pass():
    pass


@pytest.mark.tracereq("REQ-001")
@pytest.mark.xfail(reason="known issue")
def test_expected_failure():
    pytest.fail("Intentional acceptance scenario failure")
