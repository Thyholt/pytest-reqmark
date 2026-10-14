import pytest


@pytest.fixture
def unavailable():
    pytest.skip("unavailable")
