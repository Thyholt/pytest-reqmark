import pytest


@pytest.mark.xspec("REQ-001")
def test_first_behavior():
    pass


@pytest.mark.xspec("REQ-001")
def test_second_behavior():
    pass


@pytest.mark.xspec("REQ-003")
def test_third_behavior():
    pytest.skip("not ready")
