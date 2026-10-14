"""Invalid requirement configuration produces actionable usage errors."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from pytest_tracereq.config import load_requirements


@pytest.mark.parametrize(
    ("content", "diagnostic"),
    [
        pytest.param(
            '[tool]\ntracereq = ["REQ-001"]\n',
            "pyproject.toml: tracereq must be a table",
            id="non-table-section",
        ),
        pytest.param(
            "[tool.tracereq\n",
            "Cannot read tracereq requirements:",
            id="malformed-toml",
        ),
    ],
)
def test_invalid_toml_produces_a_usage_error(tmp_path: Path, content: str, diagnostic: str):
    config = Mock(spec=pytest.Config, rootpath=tmp_path)
    (tmp_path / "pyproject.toml").write_text(content, encoding="utf-8")

    with pytest.raises(pytest.UsageError) as error:
        load_requirements(config)

    assert diagnostic in str(error.value)
