import pytest


@pytest.mark.req("REQ-001")
@pytest.mark.xfail(strict=True, reason="known issue")
def test_behavior():
    pass
