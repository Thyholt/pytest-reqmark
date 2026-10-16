import pytest


@pytest.mark.xspec("REQ-001")
def test_behavior() -> None:
    print("BEHAVIOR EXECUTED")
    assert 2 + 2 == 4
