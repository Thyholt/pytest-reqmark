from typing import NoReturn

import pytest


@pytest.fixture
def unavailable() -> NoReturn:
    pytest.skip("unavailable")
