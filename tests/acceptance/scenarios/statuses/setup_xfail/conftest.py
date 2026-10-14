import pytest


@pytest.fixture
def known_issue():
    pytest.xfail("known setup issue")
