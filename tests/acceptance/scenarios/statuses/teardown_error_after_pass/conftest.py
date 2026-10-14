import pytest


@pytest.fixture
def broken():
    yield
    raise RuntimeError("teardown failed")
