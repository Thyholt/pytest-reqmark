from typing import NoReturn

import pytest


@pytest.fixture
def known_issue() -> NoReturn:
    pytest.xfail("known setup issue")
