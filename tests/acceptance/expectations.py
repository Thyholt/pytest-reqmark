"""Compare complete requirement reports using concise expected test pairs."""


class RequirementExpectation:
    def __init__(self, requirement: dict) -> None:
        self._requirement = requirement

    def to_have(self, *, status: str, tests: list[tuple[str, str]]) -> bool:
        expected = {
            "status": status,
            "tests": [{"nodeid": identity, "outcome": result} for identity, result in tests],
        }
        return self._requirement == expected


def expected(requirement: dict) -> RequirementExpectation:
    return RequirementExpectation(requirement)
