import pytest


@pytest.mark.xspec("REQ-001")
@pytest.mark.xfail(strict=True, reason="known issue")
def test_behavior() -> None:
    pass
