import pytest


@pytest.mark.tracereq("REQ-001")
def test_behavior():
    assert 1 == 2, "the text [XPASS(strict)] is not an unexpected pass"
