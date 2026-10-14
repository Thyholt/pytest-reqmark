import pytest


@pytest.mark.tracereq("REQ-001")
@pytest.mark.parametrize("value", [1, 2], ids=["first", "second"])
def test_behavior(value):
    assert value > 0
