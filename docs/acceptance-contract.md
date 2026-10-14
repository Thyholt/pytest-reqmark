# Acceptance contract

These executable acceptance requirements define the implemented v0.1 behavior.
The v0.1 specification uses the agreed project name in
[specification-v0.1.md](specification-v0.1.md).

## Configuration: two supported files

Declare opaque requirement IDs in either:

```toml
# pyproject.toml
[tool.tracereq]
requirements = ["REQ-001", "REQ-002"]
```

```ini
# pytest.ini
[pytest]
tracereq_requirements =
    REQ-001
    REQ-002
```

Accepted configuration decisions:

- `tracereq_requirements` uses one ID per line in `pytest.ini`.
- If both files declare inventories, fail with a message naming both files rather
  than merge them or silently choose one. A `pytest.ini` without an inventory can
  coexist with an inventory in `pyproject.toml`.
- No inventory is read from `setup.cfg`, `tox.ini`, JSON, YAML or other files.
  Ordinary pytest may still use its own supported configuration files.
- Duplicate IDs and non-string IDs are rejected. Each `tracereq` marker takes exactly
  one positional string ID and no keyword arguments. Multiple IDs use multiple markers.

Project naming is fixed: distribution and repository `pytest-tracereq`, Python
package `tracereq`, pytest entry point `tracereq`, and TOML inventory
section `[tool.tracereq]`.

Confirmed requirement: zero declared requirements means success with zero
requirements, both for an explicitly empty inventory and when no requirement
configuration exists. The report contains zero requirements, zero passed and
zero unverified. Numeric coverage for this case is 0.0%.
A marked test referencing an undeclared ID is still rejected.

## User-facing acceptance scenarios

Acceptance examples use domain-neutral requirement IDs and test names. IDs remain
opaque strings, including dotted IDs such as `requirement.group.item` and IDs
containing Unicode, spaces or punctuation.

| Test file | What a user can rely on |
| --- | --- |
| `test_configuration.py` | Only the two supported files supply requirement inventories; conflicts are explained. |
| `test_requirements.py` | Arbitrary IDs, several requirements per test, parameterized cases, inherited markers, no double counting, invalid marker and configuration rejection. |
| `test_statuses.py` | Execution statuses, setup/teardown errors and XFAILs, fixture skips, strict and non-strict XPASS, assertion text containing XPASS, and aggregation precedence. |
| `test_selection.py` | Deselected tests retain their identities; missing or uncollected tests are MISSING. |
| `test_cli.py` | Normal pytest, strict enforcement, acceptance-only selection, unmarked outcomes, and collection errors. |
| `test_reporting.py` | Terminal status/counts, JSON node IDs/outcomes, and coverage based on requirements. |

Tests invoke the installed plugin through pytest, without importing its internal
modules. Small helper fixtures only create user projects and read JSON files.
Unit tests cover domain edge cases alongside these user-facing scenarios.

## JSON contract

```json
{
  "requirements": {
    "REQ-001": {
      "status": "PASSED",
      "tests": [
        {"nodeid": "test_behavior.py::test_behavior", "outcome": "PASSED"}
      ]
    },
    "REQ-002": {"status": "MISSING", "tests": []}
  },
  "summary": {
    "requirements": 2,
    "passed": 1,
    "unverified": 1,
    "coverage": 50.0,
    "verified": false,
    "collection_errors": 0
  }
}
```

Inventory order determines terminal rows; test collection order determines JSON
test lists. Coverage remains a numeric percentage in JSON and is rounded to one
decimal place in the terminal. Tests with setup/call/teardown reports have one
final outcome per node ID.

Collected tests that never execute are reported as `SKIPPED`, including tests
left after an early stop and tests collected with `--collect-only`. They retain
their node IDs and keep associated requirements unverified.
A requirement shared by a passed test and an unexecuted test is `SKIPPED`,
including when an unmarked failure stops execution before the remaining test.

Expected failures raised by fixtures during setup or teardown are `XFAILED` and
remain unverified in strict mode. Assertion text containing `[XPASS(strict)]`
does not turn an ordinary test failure into an unexpected pass.

`summary.verified` is the acceptance verdict, independently of pytest's exit
status. It is true only when all declared requirements are PASSED and there
are no collection errors. It is true for zero requirements and no collection
errors. A failed unmarked test does not change this verdict, while pytest can
still return a failure. Requirement coverage can be 100% after a partial
collection, but `verified` must remain false when collection errors exist.

When terminal colors are enabled, the entire acceptance report is red if
`summary.verified` is false, both with `--tracereq-report` and `--tracereq-strict`.
Successful verification retains the normal color, including zero requirements
and runs with failing unmarked tests. The report respects pytest's color
settings, including `--color=no`.

A collection error must prevent successful strict verification. Tests cannot
always be linked to requirement IDs when collection itself fails; the terminal
must therefore print `Collection errors: 1` inside the acceptance report for a
single collection error, instead of implying authoritative
successful verification. This suite does not invent a requirement association
for an uncollected test.

Validation tests run both plain pytest and report mode, so an unrecognized CLI
option cannot masquerade as marker validation. Aggregation is verified in both
test collection orders. A test linked to several requirements must appear in
every declared requirement's result.

Unknown marked IDs are rejected even for empty inventories in either supported
format and when configuration is absent. Unsupported inventory files are ignored
for unmarked projects, yielding successful zero-requirement verification.
Association tests assert complete node-ID/outcome records, including ordering
and duplicate detection. Each outcome and precedence scenario keeps its source
in a named Python project under `tests/acceptance/scenarios`, with no imports from
other test modules or source substitutions. These files are linted and formatted;
acceptance tests refer to scenarios through package imports, which ty checks
without executing their test modules. Scenario leaf folders have empty
`__init__.py` files for editor navigation; parent folders remain namespace packages.
The harness copies each package directory into an isolated pytest project.
The outer test collection excludes the scenario directory, so deliberately
failing examples run only inside their acceptance scenarios.

## Verification

Keep these acceptance tests as the public contract. Unit tests cover meaningful
domain edge cases without mocking pytest's execution machinery. Both GitHub
Actions workflows check the implementation, including installed-wheel discovery.
