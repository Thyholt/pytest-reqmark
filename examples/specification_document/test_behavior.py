import pytest


@pytest.mark.xspec("REQ-001")
def test_adding_two_integers_returns_their_sum() -> None:
    first = 2
    second = 3

    result = first + second

    assert result == 5


@pytest.mark.xspec("REQ-001")
@pytest.mark.xspec("REQ-002")
def test_adding_zero_preserves_the_value() -> None:
    value = 2

    result = value + 0

    assert result == value
