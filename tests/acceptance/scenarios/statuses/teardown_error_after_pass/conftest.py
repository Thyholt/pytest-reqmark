from collections.abc import Iterator

import pytest


@pytest.fixture
def broken() -> Iterator[None]:
    yield
    raise RuntimeError("teardown failed")
