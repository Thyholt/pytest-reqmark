import pytest


@pytest.mark.xspec("REQ-001")
def test_skipped() -> None:
    pytest.skip("unavailable")


@pytest.mark.xspec("REQ-001")
def test_excluded() -> None:
    pass
