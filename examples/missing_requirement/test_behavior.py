import pytest


@pytest.mark.xspec("REQ-001")
def test_one_sock_survives() -> None:
    socks = ["left", "right"]

    socks.remove("right")

    assert socks == ["left"]


# REQ-002 has no test. The other sock is still missing.
