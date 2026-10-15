import pytest


@pytest.mark.chosen
@pytest.mark.xspec("REQ-001")
def test_selected() -> None:
    pass


def test_other() -> None:
    pass
