# tracereq v0.1 — Refined specification

**Goal:** A lightweight, domain-agnostic pytest plugin that makes existing tests executable
acceptance criteria.

The plugin manages requirement IDs, collects test outcomes, reports verification status, and
optionally enforces acceptance coverage.

## 1. Core principles

- Requirements are identified by arbitrary, opaque string IDs.
- Existing tests are associated with requirements using pytest markers.
- One requirement can have multiple tests.
- One test can verify multiple requirements.
- Tests remain independent of file paths, modules and implementation details.
- Requirement granularity is entirely up to the user.
- **Only requirement-marked tests contribute to acceptance verification.** Unmarked tests are
  ignored, even when they fail.

## 2. Configuration

`pyproject.toml`

```toml
[tool.tracereq]
requirements = [
    "REQ-001",
    "REQ-002",
    "REQ-003",
]
```

Requirements are declared centrally. No additional metadata is required.

### Existing tests

```python
import pytest


@pytest.mark.tracereq("REQ-001")
def test_first_behavior():
    ...


@pytest.mark.tracereq("REQ-001")
def test_second_behavior():
    ...


@pytest.mark.tracereq("REQ-003")
def test_third_behavior():
    ...
```

Multiple markers are supported:

```python
@pytest.mark.tracereq("REQ-001")
@pytest.mark.tracereq("REQ-002")
def test_shared_behavior():
    ...
```

## 3. Status model

| Status | Definition |
|---|---|
| `PASSED` | All associated tests passed |
| `FAILED` | At least one associated test failed |
| `ERROR` | At least one associated test encountered a setup, teardown or collection error |
| `SKIPPED` | At least one associated test was skipped |
| `DESELECTED` | At least one associated test was deselected |
| `XFAILED` | At least one associated test failed as expected |
| `XPASSED` | At least one associated test unexpectedly passed |
| `MISSING` | No collected test references the requirement |

### Aggregation precedence

`ERROR > FAILED > XPASSED > XFAILED > SKIPPED > DESELECTED > PASSED`

`MISSING` applies only when no test references the requirement.

A requirement is verified only when every associated test passes.

## 4. Strict mode

```bash
pytest --tracereq-strict
```

Strict mode evaluates **only declared requirements and their associated marked tests**.

| Situation | Strict result |
|---|---|
| All requirements `PASSED` | Success |
| Marked test fails | Failure |
| Marked test skipped | Failure |
| Marked test deselected | Failure |
| Requirement `MISSING` | Failure |
| Unmarked test fails | Ignored by acceptance verification |
| Unmarked test skipped | Ignored |
| Unmarked test deselected | Ignored |

**Important distinction:** Strict mode controls the plugin's acceptance verdict, not pytest's
ordinary exit status. A failing unmarked test can still make the overall pytest command fail through
pytest's standard behavior.

To obtain an acceptance-only CI gate, use:

```bash
pytest -m tracereq --tracereq-strict
```

The plugin should automatically register the `tracereq` marker category or provide an equivalent
selection mechanism. Since `@pytest.mark.tracereq("REQ-001")` already registers that marker, `-m tracereq`
selects marked tests.

## 5. CLI

| Command | Behavior |
|---|---|
| `pytest` | Normal pytest execution |
| `pytest --tracereq-report` | Print acceptance report |
| `pytest --tracereq-strict` | Enforce requirement verification |
| `pytest -m tracereq --tracereq-strict` | Run only requirement-marked tests |
| `pytest --tracereq-json=report.json` | Export JSON results |

`--tracereq-strict` should imply report generation.

## 6. Reporting

```text
================ tracereq ================

Requirement                 Status       Tests
-----------------------------------------------------
REQ-001                    PASSED         2
REQ-002                    MISSING        0
REQ-003                    SKIPPED        1

-----------------------------------------------------
Requirements: 3
Passed:       1
Unverified:   2
Coverage:     33.3%
=====================================================
```

Verified coverage:

`PASSED requirements / Declared requirements × 100`

The JSON report includes all declared requirements, their statuses and associated test node IDs with
individual outcomes.

## 7. Collection and execution rules

- Collect requirement markers before pytest deselection.
- Preserve deselected test identities and report `DESELECTED`.
- Ignore unmarked tests when calculating requirement statuses.
- Reject unknown requirement IDs and malformed markers.
- Detect requirements with no associated tests as `MISSING`.
- Aggregate setup, call and teardown outcomes correctly.
- Treat `XFAILED` and `XPASSED` as unverified.
- Report collected tests that never execute as `SKIPPED`, including collect-only
  and early-stop runs.
- A collection error must not result in a successful strict verdict.
- If a test is never collected, it cannot be identified as deselected.

**Full collection is therefore required for authoritative acceptance coverage.** Filtering with `-m`
and `-k` is supported because pytest initially collects those tests.

## 8. Implementation

```text
pytest-tracereq/
├── pyproject.toml
├── src/
│   └── tracereq/
│       ├── __init__.py
│       ├── plugin.py
│       ├── config.py
│       ├── collector.py
│       ├── outcomes.py
│       └── reporting.py
└── tests/
    ├── test_config.py
    ├── test_collection.py
    ├── test_outcomes.py
    ├── test_reporting.py
    └── test_cli.py
```

Python 3.10+, pytest 8+, native pytest hooks, `pytest11` entry point, and no mandatory dependencies
beyond pytest.

## 9. Release scope

**v0.1 includes:** Requirement IDs, markers, central inventory, eight statuses, aggregation,
missing/unknown ID detection, strict enforcement, terminal and JSON reports, and automated plugin
tests.

**Deferred:** Report merging, requirement filtering, Markdown/HTML reporting, PR comparisons,
external integrations, and requirement descriptions.

### Final contract

The plugin answers one question:

**Have all declared requirements been verified by successfully executed pytest tests?**

It does not interpret requirements, prescribe test design, or depend on how tests are organized.
