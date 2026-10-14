# pytest-reqmark

Stupid-simple requirement marking and tracking for pytest.

## Usage

Install `pytest-reqmark` into your pytest environment. The plugin is discovered
automatically; Python 3.10+ and pytest 8+ are supported.

Declare requirement IDs in `pyproject.toml`:

```toml
[tool.pytest-reqmark]
requirements = ["REQ-001", "REQ-002"]
```

Alternatively, use one ID per line in `pytest.ini`:

```ini
[pytest]
req_requirements =
    REQ-001
    REQ-002
```

Declaring inventories in both files is an error. Other files do not supply
inventories. IDs are opaque strings; duplicates and undeclared marked IDs are
rejected. No inventory, or an empty inventory, means zero requirements.

Associate existing tests using one marker per requirement:

```python
import pytest


@pytest.mark.req("REQ-001")
@pytest.mark.req("REQ-002")
def test_shared_behavior():
    assert 1 + 1 == 2
```

```sh
pytest --req-report                    # Print the acceptance report
pytest --req-json=report.json          # Export statuses and individual test outcomes
pytest --req-strict                    # Report and fail on unverified requirements
pytest -m req --req-strict             # Acceptance-only CI gate
```

A requirement is verified only when every associated test passes. Outcomes
aggregate in this order: `ERROR > FAILED > XPASSED > XFAILED > SKIPPED > DESELECTED
> PASSED`. Requirements without collected tests are `MISSING`. Collected tests
that never execute, including collect-only or early-stop runs, are `SKIPPED`.
Collection errors prevent a successful acceptance verdict.

Unmarked test outcomes do not affect acceptance verification; pytest retains its
ordinary exit behavior. With zero requirements and no collection errors the
acceptance verdict is successful and coverage is 0.0%. Plain `pytest` validates
inventories and markers without printing an acceptance report. Full collection
is required for authoritative coverage; `-k` and `-m` retain deselected identities,
while tests outside the collected paths cannot be identified.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, tests and pull requests.
