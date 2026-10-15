"""Compare complete requirement reports using concise expected test pairs."""

from collections.abc import Mapping


class RequirementExpectation:
    def __init__(self, requirement: Mapping[str, object]) -> None:
        self._requirement = requirement

    def to_have(self, *, status: str, tests: list[tuple[str, str]]) -> bool:
        expected = {
            "status": status,
            "tests": [{"nodeid": identity, "outcome": result} for identity, result in tests],
        }
        return self._requirement == expected


def expected(requirement: Mapping[str, object]) -> RequirementExpectation:
    return RequirementExpectation(requirement)
