import pytest


@pytest.mark.xspec("REQ-001")
@pytest.mark.parametrize("value", [1, 2], ids=["first", "second"])
def test_behavior(value: int) -> None:
    assert value > 0
