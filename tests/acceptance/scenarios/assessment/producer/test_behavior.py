import os

import pytest


@pytest.mark.xspec("REQ-001")
@pytest.mark.selected
def test_primary_behavior() -> None:
    result = os.environ.get("ASSESSMENT_RESULT", "passed")

    print("PRIMARY_EXECUTED")

    assert result == "passed"


@pytest.mark.xspec("REQ-002")
def test_secondary_behavior() -> None:
    result = "passed"

    print("SECONDARY_EXECUTED")

    assert result == "passed"
