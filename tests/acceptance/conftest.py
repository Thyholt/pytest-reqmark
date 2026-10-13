"""Run each acceptance scenario as a real user's isolated pytest project."""

import json
from collections.abc import Callable
from pathlib import Path

import pytest


@pytest.fixture
def user_project(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> Callable[..., pytest.Pytester]:
    monkeypatch.delenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", raising=False)
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)
    monkeypatch.delenv("PYTEST_PLUGINS", raising=False)

    def create(requirements: list[str], tests: str, *, fixtures: str = "") -> pytest.Pytester:
        pytester.makefile(
            ".toml",
            pyproject=(
                "[tool.pytest-reqmark]\n"
                f"requirements = {json.dumps(requirements, ensure_ascii=False)}\n"
            ),
        )
        pytester.makepyfile(test_behavior="import pytest\n" + tests)
        if fixtures:
            pytester.makeconftest("import pytest\n" + fixtures)
        return pytester

    return create


@pytest.fixture
def read_report() -> Callable[[pytest.Pytester], dict]:
    def read(project: pytest.Pytester) -> dict:
        report_path: Path = project.path / "report.json"
        assert report_path.is_file(), "The user must receive the requested JSON report"
        return json.loads(report_path.read_text(encoding="utf-8"))

    return read
