"""Run each acceptance scenario as a real user's isolated pytest project."""

import json
from collections.abc import Callable
from pathlib import Path
from shutil import copytree, ignore_patterns
from types import ModuleType

import pytest

collect_ignore = ["scenarios"]


@pytest.fixture
def file_project(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> Callable[[ModuleType], pytest.Pytester]:
    """Copy a scenario, leaving requirement files for the test to provide explicitly."""
    monkeypatch.delenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", raising=False)
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)
    monkeypatch.delenv("PYTEST_PLUGINS", raising=False)

    def create(scenario: ModuleType) -> pytest.Pytester:
        (scenario_path,) = scenario.__path__
        copytree(
            scenario_path, pytester.path, dirs_exist_ok=True, ignore=ignore_patterns("__pycache__")
        )
        return pytester

    return create


@pytest.fixture
def user_project(
    file_project: Callable[[ModuleType], pytest.Pytester],
) -> Callable[[list[str], ModuleType], pytest.Pytester]:
    """Supply a real TOML requirement inventory for a behavior scenario."""

    def create(requirements: list[str], scenario: ModuleType) -> pytest.Pytester:
        project = file_project(scenario)
        project.makefile(
            ".toml",
            pyproject=(
                f"[tool.xspec]\nrequirements = {json.dumps(requirements, ensure_ascii=False)}\n"
            ),
        )
        return project

    return create


@pytest.fixture
def read_report() -> Callable[[pytest.Pytester], dict]:
    def read(project: pytest.Pytester) -> dict:
        report_path: Path = project.path / "report.json"
        assert report_path.is_file(), "The user must receive the requested JSON report"
        return json.loads(report_path.read_text(encoding="utf-8"))

    return read
