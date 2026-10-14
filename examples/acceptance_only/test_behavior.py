import pytest


@pytest.mark.req("REQ-001")
def test_duck_says_quack():
    duck = {"sound": "quack"}

    sound = duck["sound"]

    assert sound == "quack"


def test_moon_is_made_of_cheese():
    moon = {"material": "rock"}

    material = moon["material"]

    assert material == "cheese"
