import pytest


@pytest.fixture
def broken():
    raise RuntimeError("setup failed")
