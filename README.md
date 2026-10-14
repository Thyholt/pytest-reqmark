# pytest-reqmark

Stupid simple requirement marking and tracking for pytest.

## Usage

Install `pytest-reqmark` into your pytest environment. The plugin is discovered
automatically. Python 3.10+ and pytest 8+ are supported.

### Declare requirements

Declare requirement IDs in `pyproject.toml`.

```toml
[tool.pytest-reqmark]
requirements = ["REQ-001", "REQ-002"]
```

Alternatively, use one ID per line in `pytest.ini`.

```ini
[pytest]
req_requirements =
    REQ-001
    REQ-002
```

Declare requirements in one of these files. Using both is an error, and other
files do not supply requirements. IDs are opaque strings. Duplicates and marked
IDs that have not been declared are rejected. No inventory, or an empty inventory,
means zero requirements.

### Mark tests

Associate tests with requirements, using one marker per requirement.

```python
import pytest


@pytest.mark.req("REQ-001")
@pytest.mark.req("REQ-002")
def test_shared_behavior():
    assert 1 + 1 == 2
```

### Run pytest

Plain `pytest` checks requirement configuration and markers without printing
a requirement report. Add `--req-report` to see the report, or `--req-strict`
to also fail the run when a requirement is unverified.

```sh
pytest --req-report                    # Print the acceptance report
pytest --req-json=report.json          # Export statuses and individual test outcomes
pytest --req-strict                    # Report and fail on unverified requirements
pytest -m req --req-strict             # Run only marked requirement tests
```

### Read requirement statuses

A requirement is verified when every test marked with its ID passes. One passing
test is not enough if another test for the same requirement fails or skips.

When those tests have different results, the report uses the first matching
status in this table, reading from top to bottom.

| Status | Meaning |
| --- | --- |
| `ERROR` | A test's setup or cleanup failed. |
| `FAILED` | A test failed. |
| `XPASSED` | A test marked as an expected failure passed instead. |
| `XFAILED` | A test failed as expected. |
| `SKIPPED` | A test was skipped or never ran. |
| `DESELECTED` | A test was excluded by a filter such as `-k` or `-m`. |
| `PASSED` | Every test for the requirement passed. |

For example, if one test passes and another skips, the requirement is `SKIPPED`
and remains unverified. If one test fails and another skips, it is `FAILED`.

### Missing and unfinished tests

Pytest first finds tests, then runs them. If it finds no marked tests for a
declared requirement, that requirement is `MISSING`. Tests that were found but
never ran are `SKIPPED`, including runs that only find tests or stop early.
If pytest encounters an error while finding tests, such as a broken import,
the acceptance check cannot succeed.

### Tests without markers

Tests without a requirement marker do not change requirement statuses. They
can still make pytest fail. In [the duck example](examples/acceptance_only),
the requirement passes, but the unmarked cheese test fails the pytest run.

### Check coverage

Coverage is the percentage of declared requirements that are verified. With
no declared requirements and no errors while finding tests, the acceptance
check succeeds and coverage is 0.0%.

For a complete report, let pytest find the whole test suite. With `-k` or `-m`,
the plugin still knows about the tests excluded by the filter and reports marked
ones as `DESELECTED`. If you run only one folder, it cannot see tests in other
folders.

## Runnable examples

Start with [the pizza](examples/quickstart/test_behavior.py), then try the other
examples to see what makes a requirement pass or remain unverified.

Run the commands below from the repository root. Dependencies are installed automatically.

| Example | With `--req-strict` | Exit code |
| --- | --- | --- |
| [Quickstart](examples/quickstart) - Two slices of pizza | `PASSED`, 100% coverage | 0 |
| [Missing requirement](examples/missing_requirement) - A lost sock | `MISSING`, 50% coverage | 1 |
| [Partial verification](examples/partial_verification) - Cat skips a meeting | `SKIPPED`, 0% coverage | 1 |
| [Acceptance only](examples/acceptance_only) - Duck versus cheese | `PASSED` with `-m req` | 0 |

### Run an example

Run the `Quickstart` example, then replace `quickstart` with another example folder.

```sh
uv run --locked pytest examples/quickstart --req-strict
```

For `acceptance_only`, add `-m req` to run only the marked test.
Without that filter, the unmarked test makes pytest fail.

### Inspect the JSON report

Export the example results to see the requirement status and individual test outcomes.

```sh
uv run --locked pytest examples/quickstart --req-json=examples/quickstart/report.json
```

Open [examples/quickstart/report.json](examples/quickstart/report.json) after running the command.

### Verify all examples

Check that every example behaves as described.

```sh
uv run --locked pytest examples/test_examples.py -n 0
```

All five checks should pass, including checks for the examples that deliberately
fail. The examples are also verified in CI.

## Development

Development uses Python 3.10 or newer, managed with uv. Run these commands from
the repository root.

```sh
uv sync --locked
uv run prek install
uv run prek run --all-files
uv run ruff check .
uv run ruff format --check .
uv run rumdl check .
uv run ty check
uv run pytest --collect-only -q
uv run pytest
```

[prek](https://prek.j178.dev/ci/) checks YAML and TOML syntax, merge conflicts,
private keys, whitespace, Python and Markdown lint, formatting and types before
commits and in CI.
The hooks are configured in [`prek.toml`](prek.toml) and use the dependency
versions in `uv.lock`. They report problems without modifying files. Apply fixes
with `uv run ruff check --fix .` or `uv run ruff format .` as needed, then stage
the fixes and commit again.

Markdown is checked with [rumdl](https://github.com/rvben/rumdl). The
[VS Code extension](https://marketplace.visualstudio.com/items?itemName=rvben.rumdl)
detects the binary in `.venv` and reads the rules from `pyproject.toml`, so the
editor uses the same version and configuration as CI.

Tests run in parallel with [pytest-xdist](https://pytest-xdist.readthedocs.io/en/stable/distribution.html).
The default `-n auto` selects the worker count from the available CPUs.
Use `uv run pytest -n 0` for serial execution or `uv run pytest -n 4` to choose
the worker count explicitly. Only the outer suite runs in parallel. Each
acceptance scenario and public example runs in its own isolated pytest project.

The `check` workflow runs prek, collection and tests as independent jobs.
Prek runs every hook even if another hook fails. The `integration` workflow
builds a wheel, installs it into a fresh environment and verifies acceptance
and public examples on Python 3.10 with pytest 8 and Python 3.13 with current pytest.
It verifies automatic plugin discovery through the `pytest11` entry point.
Both workflows run on pull requests and pushes to `master`, avoiding duplicate
push and pull request runs for feature branches.

Dependency versions are recorded in `uv.lock`, generated by uv in CI.
The check workflow uses `--locked` to reject dependency changes that have not
been recorded in the lockfile.
