import pytest


@pytest.mark.chosen
@pytest.mark.tracereq("REQ-001")
def test_selected():
    pass


def test_other():
    pass
