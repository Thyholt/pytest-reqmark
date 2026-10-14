import pytest


@pytest.mark.tracereq("REQ-001")
def test_marked():
    pass


def test_unmarked():
    pytest.fail("Intentional acceptance scenario failure")
