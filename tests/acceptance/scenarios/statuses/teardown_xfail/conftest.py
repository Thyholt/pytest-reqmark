import pytest


@pytest.fixture
def known_issue():
    yield
    pytest.xfail("known teardown issue")
