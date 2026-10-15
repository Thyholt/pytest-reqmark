import pytest


@pytest.mark.xspec("REQ-001")
@pytest.mark.xfail(reason="known issue")
def test_behavior() -> None:
    pytest.fail("Intentional acceptance scenario failure")
