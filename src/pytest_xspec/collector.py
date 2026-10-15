"""Validate requirement associations before pytest filters collected tests."""

from collections.abc import Collection

import pytest


def requirement_ids(item: pytest.Item, inventory: Collection[str]) -> tuple[str, ...]:
    identifiers: dict[str, None] = {}

    for marker in item.iter_markers("xspec"):
        if len(marker.args) != 1 or marker.kwargs or not isinstance(marker.args[0], str):
            raise pytest.UsageError(
                f"{item.nodeid}: xspec requires exactly one positional string ID and no keywords"
            )

        identifier = marker.args[0]
        if identifier not in inventory:
            raise pytest.UsageError(f"{item.nodeid}: unknown xspec requirement ID {identifier!r}")

        identifiers[identifier] = None

    return tuple(identifiers)
