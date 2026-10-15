# Acceptance contract

These executable acceptance requirements define the supported behavior, including
the specification-document extension to the original v0.1 specification in
[specification-v0.1.md](specification-v0.1.md).

## Configuration: explicit inventories and a fallback document

Declare opaque requirement IDs in either:

```toml
# pyproject.toml
[tool.xspec]
requirements = ["REQ-001", "REQ-002"]
```

```ini
# pytest.ini
[pytest]
xspec =
    REQ-001
    REQ-002
```

When neither file declares an inventory, read `xspec.toml` from pytest's project root:

```toml
[[requirements]]
id = "REQ-001"
description = "A short statement of the requirement."
rationale = "Why the requirement matters."

[[requirements]]
id = "REQ-002"
```

The document is an array of requirement tables. Each entry requires a string `id`.
Descriptions and rationales are optional strings and may be empty. Unknown fields
are ignored. Only IDs enter verification and reports, preserving the existing report schema.
Equivalent TOML syntax, including inline tables inside an array, is accepted.

Accepted configuration decisions:

- `xspec` uses one ID per line in `pytest.ini`.
- If both files declare inventories, fail with a message naming both files rather
  than merge them or silently choose one. A `pytest.ini` without an inventory can
  coexist with an inventory in `pyproject.toml`.
- An explicitly empty inventory in either file also disables the document fallback.
  When an inventory is declared, `xspec.toml` is not opened or validated. Invalid
  existing configuration remains an error rather than triggering fallback.
- An existing configuration file without an inventory does not disable the fallback.
  The document is read from the project root regardless of the working directory.
- `requirements = []` in `xspec.toml` declares zero requirements. A selected document
  without `requirements`, including an empty file, is rejected. Invalid document
  syntax or contents produce a configuration error naming `xspec.toml` before tests run.
- No inventory is read from `setup.cfg`, `tox.ini`, JSON, YAML or other files.
  Ordinary pytest may still use its own supported configuration files.
- Duplicate IDs and non-string IDs are rejected. Each `xspec` marker takes exactly
  one positional string ID and no keyword arguments. Multiple IDs use multiple markers.

Project naming is fixed: distribution and repository `pytest-xspec`, Python
package `pytest_xspec`, pytest entry point `xspec`, and TOML inventory
section `[tool.xspec]`.

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
| `test_configuration.py` | Explicit inventories retain precedence, including empty or invalid inventories; conflicts are explained. |
| `test_specification_document.py` | The fallback document supplies IDs without reporting metadata; source selection, document errors and zero requirements are explained. |
| `test_requirements.py` | Arbitrary IDs, several requirements per test, parameterized cases, inherited markers, no double counting and invalid marker rejection. |
| `test_statuses.py` | Execution statuses, setup/teardown errors and XFAILs, fixture skips, strict and non-strict XPASS, assertion text containing XPASS, and aggregation precedence. |
| `test_selection.py` | Deselected tests retain their identities; missing or uncollected tests are MISSING. |
| `test_requirement_selection.py` | Exact requirement selection, discovery, native filters, shared evidence and report scope preserve full-inventory strict verification. |
| `test_cli.py` | Normal pytest, strict enforcement, acceptance-only selection, unmarked outcomes, and collection errors. |
| `test_reporting.py` | Terminal status/counts, JSON node IDs/outcomes, and coverage based on requirements. |

Tests invoke the installed plugin through real pytest subprocesses.
Configuration tests use `file_project` and create the actual configuration files.
Behavior tests use `user_project`, which writes a real `pyproject.toml` inventory.
Both setups exercise normal configuration loading, validation, collection, execution and reporting.
Other pytest settings, such as marker registration, also use real configuration files.

Unit tests validate inventories and document contents directly using Python values,
independently of pytest configuration and the filesystem. File parsing and loading
are covered by configuration acceptance tests. TOML test data lives in lintable
files, with deliberately malformed syntax in `.toml.invalid` files.

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
`summary.verified` is false, both with `--xspec-report` and `--xspec-strict`.
Successful verification makes the entire report green, including zero requirements
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

Unknown marked IDs are rejected even for empty inventories and when configuration
is absent. Unsupported inventory files are ignored
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

## Requirement selection and discovery (#15)

The user approved this section and `test_requirement_selection.py` before plugin implementation.
The existing v0.1 contract above remains unchanged without selection.

Repeat `--xspec-select=ID` to select the union of exact, opaque requirement IDs. Repeated IDs and
overlapping markers never duplicate a test. Commas, spaces and Unicode belong to the ID, with no
splitting or prefix matching. Unmarked tests are excluded. Pytest collection paths, `-k` and `-m`
intersect with requirement selection. Associations are recorded before filtering, and normal
pytest deselection notifications preserve excluded test identities and all shared associations.
Module and class markers apply to each complete parameterized node ID.

`--collect-only -q` lists the same selected node IDs as execution, without running fixtures or test
bodies. Collected modules still import and need their normal dependencies. Collection errors keep
verification unsuccessful. Invalid collected markers remain errors even when filters exclude them.
Unknown selected IDs produce a usage error (exit code 4) identifying the ID, before fixtures or
tests execute, including mixed known and unknown selections.

A declared requirement with no associated collected tests is `MISSING`, with an empty test list.
If native filters remove its associated tests, those tests remain `DESELECTED`. Both cases remain
unverified. An empty selection preserves pytest's exit code 5 without strict mode. Strict mode
continues to evaluate every declared requirement and returns exit code 1 for unverified results.
Discovery preserves test identities as `SKIPPED`, never passing evidence. Unselected requirements
remain in reports and the coverage denominator, including any evidence shared with selected ones.
Tests outside collected paths have no invented identities or deselected records.

When selection is active, JSON adds one top-level `scope` object. Existing result fields stay intact:

```json
{
  "selected_requirements": ["REQ-002", "REQ-001"],
  "collection_paths": ["test_behavior.py"],
  "keyword_expression": "shared",
  "marker_expression": "xspec",
  "collect_only": false
}
```

Selected IDs retain first-occurrence order with duplicates removed. Collection paths are pytest's
effective collection arguments, including explicit node IDs, in their original order. With no
explicit paths, pytest uses configured `testpaths`, or `["."]` when none are configured. Absent
`-k` and `-m` expressions are empty strings. `collect_only` is a boolean. Without requirement
selection, the `scope` key and terminal scope lines are absent.

With `--xspec-report` or `--xspec-strict`, terminal reports add the same scope information:

```text
Selected requirements: ["REQ-002", "REQ-001"]
Collection paths: ["test_behavior.py"]
Keyword filter: shared
Marker filter: xspec
Discovery only: no
```

Arrays use JSON notation to preserve opaque IDs, and empty filter expressions display `(none)`.
Discovery displays `yes`. Requirement counts and coverage continue to describe the entire inventory.

## Verification

Keep these acceptance tests as the public contract. Unit tests cover meaningful
domain edge cases without mocking pytest's execution machinery. Both GitHub
Actions workflows check the implementation, including installed-wheel discovery.
