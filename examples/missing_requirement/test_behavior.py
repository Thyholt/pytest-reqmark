import pytest


@pytest.mark.req("REQ-001")
def test_one_sock_survives():
    socks = ["left", "right"]

    socks.remove("right")

    assert socks == ["left"]


# REQ-002 has no test. The other sock is still missing.
