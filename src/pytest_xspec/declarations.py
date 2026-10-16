"""Read and validate user declarations at the file boundary."""

import hashlib
import sys
from importlib import import_module
from pathlib import Path
from typing import cast


class ValidationError(ValueError):
    """A declaration or persisted record does not satisfy its input schema."""


def document_identity(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def load_toml(path: Path) -> dict[str, object]:
    toml = import_module("tomllib" if sys.version_info >= (3, 11) else "tomli")
    try:
        with path.open("rb") as stream:
            value: object = toml.load(stream)
    except (OSError, ValueError) as error:
        raise ValidationError(f"Cannot read {path}: {error}") from error

    return table(value, str(path))


def table(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValidationError(f"{label} must be a table")

    return cast(dict[str, object], value)


def tables(value: object, label: str) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ValidationError(f"{label} must be a list of tables")

    return [table(item, label) for item in value]


def string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{label} must be a nonempty string")

    return value


def string_map(value: object, label: str) -> dict[str, str]:
    result = table(value, label)
    if any(not isinstance(item, str) for item in result.values()):
        raise ValidationError(f"{label} must contain only string values")

    return cast(dict[str, str], result)


def validate_requirements(value: object, source: str) -> list[str]:
    if not isinstance(value, list):
        raise ValidationError(f"{source}: requirements must be a list of tables")

    parents: dict[str, str | None] = {}
    for position, item in enumerate(value, start=1):
        entry = table(item, f"{source}: requirement {position}")
        identifier = entry.get("id")
        if not isinstance(identifier, str):
            raise ValidationError(f"{source}: requirement {position} must have a string id")

        if identifier in parents:
            raise ValidationError(f"{source}: duplicate requirements ID {identifier!r}")

        for field in ("description", "rationale", "parent"):
            if field in entry and not isinstance(entry[field], str):
                raise ValidationError(
                    f"{source}: requirement {identifier!r}: {field} must be a string"
                )

        parents[identifier] = cast(str | None, entry.get("parent"))

    for identifier, parent in parents.items():
        if parent is not None and parent not in parents:
            raise ValidationError(
                f"{source}: unknown parent {parent!r} for requirement {identifier!r}"
            )

        seen = {identifier}
        while parent is not None:
            if parent in seen:
                raise ValidationError(f"{source}: cyclic parent relationship at {parent!r}")

            seen.add(parent)
            parent = parents.get(parent)

    return list(parents)
