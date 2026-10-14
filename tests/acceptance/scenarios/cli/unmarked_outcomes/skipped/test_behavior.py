import pytest


@pytest.mark.req("REQ-001")
def test_marked():
    pass


def test_unmarked():
    pytest.skip("optional")
