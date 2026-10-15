import pytest


@pytest.mark.xspec("REQ-001")
@pytest.mark.usefixtures("broken")
def test_behavior() -> None:
    pytest.fail("Intentional acceptance scenario failure")
