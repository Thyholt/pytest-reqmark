"""Read requirement inventories from the two supported project files."""

import configparser
import sys
from importlib import import_module

import pytest


def load_requirements(config: pytest.Config) -> list[str]:
    inventories: dict[str, object] = {}
    pyproject = config.rootpath / "pyproject.toml"
    ini = config.rootpath / "pytest.ini"

    try:
        if pyproject.is_file():
            # pytest supplies tomli on Python 3.10; newer Python supplies tomllib.
            toml = import_module("tomllib" if sys.version_info >= (3, 11) else "tomli")
            with pyproject.open("rb") as stream:
                section = toml.load(stream).get("tool", {}).get("pytest-reqmark", {})

            if not isinstance(section, dict):
                raise pytest.UsageError("pyproject.toml: pytest-reqmark must be a table")

            if "requirements" in section:
                inventories[pyproject.name] = section["requirements"]

        if ini.is_file():
            parser = configparser.ConfigParser(interpolation=None)
            parser.read(ini, encoding="utf-8")

            if parser.has_option("pytest", "req_requirements"):
                inventories[ini.name] = [
                    line.strip()
                    for line in parser.get("pytest", "req_requirements").splitlines()
                    if line.strip()
                ]
    except (OSError, ValueError, configparser.Error) as error:
        raise pytest.UsageError(f"Cannot read pytest-reqmark requirements: {error}") from error

    if len(inventories) > 1:
        raise pytest.UsageError("Declare requirements in only one of pyproject.toml and pytest.ini")

    if not inventories:
        return []

    filename, requirements = next(iter(inventories.items()))
    if not isinstance(requirements, list) or any(
        not isinstance(requirement, str) for requirement in requirements
    ):
        raise pytest.UsageError(f"{filename}: requirements must be a list of string IDs")

    seen: set[str] = set()
    for requirement in requirements:
        if requirement in seen:
            raise pytest.UsageError(f"{filename}: duplicate requirements ID {requirement!r}")

        seen.add(requirement)

    return requirements
