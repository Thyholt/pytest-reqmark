import pytest


@pytest.mark.req("REQ-001")
def test_pizza_has_two_slices():
    pizza = ["slice", "slice"]

    slices = len(pizza)

    assert slices == 2
