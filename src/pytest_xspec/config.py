"""Validate requirement inventories independently of their project-file source."""

import configparser
import sys
from importlib import import_module
from pathlib import Path
from typing import cast

import pytest

from pytest_xspec.declarations import document_identity, load_toml, validate_requirements

SPECIFICATION: pytest.StashKey[str] = pytest.StashKey()


def load_requirements(config: pytest.Config) -> list[str]:
    explicit_spec = config.getoption("xspec_spec", default=None)
    if explicit_spec is not None:
        document = Path(explicit_spec)
        if not document.is_absolute():
            document = config.invocation_params.dir / document

        return _load_document(document, config)

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

        return _load_document(document, config)

    source, requirements = next(iter(inventories.items()))
    return _validate_inventory(requirements, source)


def _load_document(document: Path, config: pytest.Config) -> list[str]:
    try:
        requirements = load_toml(document).get("requirements")
        config.stash[SPECIFICATION] = document_identity(document)
    except (OSError, ValueError) as error:
        raise pytest.UsageError(
            f"Cannot read xspec requirements from {document.name}: {error}"
        ) from error

    return _validate_document(requirements, document.name)


def _validate_document(requirements: object, source: str) -> list[str]:
    try:
        return validate_requirements(requirements, source)
    except ValueError as error:
        raise pytest.UsageError(str(error)) from error


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
