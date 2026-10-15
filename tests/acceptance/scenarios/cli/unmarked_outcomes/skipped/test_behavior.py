import pytest


@pytest.mark.xspec("REQ-001")
def test_marked():
    pass


def test_unmarked():
    pytest.skip("optional")
