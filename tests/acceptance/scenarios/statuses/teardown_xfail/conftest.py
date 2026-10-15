from collections.abc import Iterator

import pytest


@pytest.fixture
def known_issue() -> Iterator[None]:
    yield
    pytest.xfail("known teardown issue")
