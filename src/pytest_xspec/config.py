"""Validate requirement inventories independently of their project-file source."""

import configparser
import sys
from importlib import import_module
from typing import cast

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
                section = toml.load(stream).get("tool", {}).get("xspec", {})

            if not isinstance(section, dict):
                raise pytest.UsageError("pyproject.toml: xspec must be a table")

            if "requirements" in section:
                inventories[pyproject.name] = section["requirements"]

        if ini.is_file():
            parser = configparser.ConfigParser(interpolation=None)
            parser.read(ini, encoding="utf-8")

            if parser.has_option("pytest", "xspec"):
                inventories[ini.name] = [
                    line.strip()
                    for line in parser.get("pytest", "xspec").splitlines()
                    if line.strip()
                ]
    except (OSError, ValueError, configparser.Error) as error:
        raise pytest.UsageError(f"Cannot read xspec requirements: {error}") from error

    if len(inventories) > 1:
        raise pytest.UsageError("Declare requirements in only one of pyproject.toml and pytest.ini")

    if not inventories:
        document = config.rootpath / "xspec.toml"
        if not document.is_file():
            return []

        try:
            toml = import_module("tomllib" if sys.version_info >= (3, 11) else "tomli")
            with document.open("rb") as stream:
                requirements = toml.load(stream).get("requirements")
        except (OSError, ValueError) as error:
            raise pytest.UsageError(
                f"Cannot read xspec requirements from {document.name}: {error}"
            ) from error

        return _validate_document(requirements, document.name)

    source, requirements = next(iter(inventories.items()))
    return _validate_inventory(requirements, source)


def _validate_document(requirements: object, source: str) -> list[str]:
    if not isinstance(requirements, list):
        raise pytest.UsageError(f"{source}: requirements must be a list of tables")

    identifiers: list[str] = []
    for position, requirement in enumerate(requirements, start=1):
        if not isinstance(requirement, dict):
            raise pytest.UsageError(f"{source}: requirement {position} must be a table")

        identifier = requirement.get("id")
        if not isinstance(identifier, str):
            raise pytest.UsageError(f"{source}: requirement {position} must have a string id")

        for field in ("description", "rationale"):
            if field in requirement and not isinstance(requirement[field], str):
                raise pytest.UsageError(
                    f"{source}: requirement {identifier!r}: {field} must be a string"
                )

        identifiers.append(identifier)

    return _validate_inventory(identifiers, source)


def _validate_inventory(requirements: object, source: str) -> list[str]:
    if not isinstance(requirements, list) or any(
        not isinstance(requirement, str) for requirement in requirements
    ):
        raise pytest.UsageError(f"{source}: requirements must be a list of string IDs")

    seen: set[str] = set()
    for requirement in requirements:
        if requirement in seen:
            raise pytest.UsageError(f"{source}: duplicate requirements ID {requirement!r}")

        seen.add(requirement)

    # The element checks above establish the list's type, which ty cannot narrow.
    return cast(list[str], requirements)
