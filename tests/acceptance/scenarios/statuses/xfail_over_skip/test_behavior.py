import pytest


@pytest.mark.xspec("REQ-001")
@pytest.mark.xfail(reason="known issue")
def test_expected_failure():
    pytest.fail("Intentional acceptance scenario failure")


@pytest.mark.xspec("REQ-001")
def test_skipped():
    pytest.skip("unavailable")
