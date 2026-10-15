from typing import NoReturn

import pytest


@pytest.fixture
def broken() -> NoReturn:
    raise RuntimeError("setup failed")
