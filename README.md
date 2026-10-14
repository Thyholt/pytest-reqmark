# pytest-tracereq

Requirement marking and tracing for pytest.

## Usage

Install `pytest-tracereq` into your pytest environment. The plugin is discovered
automatically. Python 3.10+ and pytest 8+ are supported.

```sh
pip install pytest-tracereq
```

### Declare requirements

Declare requirement IDs in `pyproject.toml`.

```toml
[tool.tracereq]
requirements = ["REQ-001", "REQ-002"]
```

Alternatively, use one ID per line in `pytest.ini`.

```ini
[pytest]
tracereq =
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


@pytest.mark.tracereq("REQ-001")
@pytest.mark.tracereq("REQ-002")
def test_shared_behavior():
    assert 1 + 1 == 2
```

### Run pytest

Plain `pytest` checks requirement configuration and markers without printing
a requirement report. Add `--tracereq-report` to see the report, or `--tracereq-strict`
to also fail the run when a requirement is unverified.

```sh
pytest --tracereq-report                # Print the acceptance report
pytest --tracereq-json=report.json       # Export statuses and individual test outcomes
pytest --tracereq-strict                # Report and fail on unverified requirements
pytest -m tracereq --tracereq-strict    # Run only marked requirement tests
```

The report is green when all requirements are verified and red when verification fails.
The first report shows the example above; the second shows a requirement without tests.

![Terminal reports showing verified requirements in green and a missing requirement in red.](https://raw.githubusercontent.com/Thyholt/pytest-tracereq/master/docs/images/terminal-reports.png)

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
can still make pytest fail. In [the duck example][acceptance-only],
the requirement passes, but the unmarked cheese test fails the pytest run.

### Check coverage

Coverage is the percentage of declared requirements that are verified. With
no declared requirements and no errors while finding tests, the acceptance
check succeeds and coverage is 0.0%.

Errors while finding tests make verification fail, even at 100% coverage. The report follows
pytest's color settings, so `--color=no` disables color.

For a complete report, let pytest find the whole test suite. With `-k` or `-m`,
the plugin still knows about the tests excluded by the filter and reports marked
ones as `DESELECTED`. If you run only one folder, it cannot see tests in other
folders.

## Runnable examples

Start with [the pizza][pizza], then try the other
examples to see what makes a requirement pass or remain unverified.

Run the commands below from the repository root. Dependencies are installed automatically.

| Example | With `--tracereq-strict` | Exit code |
| --- | --- | --- |
| [Quickstart][quickstart] - Two slices of pizza | `PASSED`, 100% coverage | 0 |
| [Missing requirement][missing-requirement] - A lost sock | `MISSING`, 50% coverage | 1 |
| [Partial verification][partial-verification] - Cat skips a meeting | `SKIPPED`, 0% coverage | 1 |
| [Acceptance only][acceptance-only] - Duck versus cheese | `PASSED` with `-m tracereq` | 0 |

### Run an example

Run the `Quickstart` example, then replace `quickstart` with another example folder.

```sh
uv run --locked pytest examples/quickstart --tracereq-strict
```

For `acceptance_only`, add `-m tracereq` to run only the marked test.
Without that filter, the unmarked test makes pytest fail.

### Inspect the JSON report

Export the example results to see the requirement status and individual test outcomes.

```sh
uv run --locked pytest examples/quickstart --tracereq-json=examples/quickstart/report.json
```

Open [examples/quickstart/report.json][report] after running the command.

### Verify all examples

Check that every example behaves as described.

```sh
uv run --locked pytest examples/test_examples.py -n 0
```

All five checks should pass, including checks for the examples that deliberately
fail. The examples are also verified in CI.

## Contributing

See [CONTRIBUTING.md][contributing] for setup, tests and pull requests.

[acceptance-only]: https://github.com/Thyholt/pytest-tracereq/tree/master/examples/acceptance_only
[pizza]: https://github.com/Thyholt/pytest-tracereq/blob/master/examples/quickstart/test_behavior.py
[quickstart]: https://github.com/Thyholt/pytest-tracereq/tree/master/examples/quickstart
[missing-requirement]: https://github.com/Thyholt/pytest-tracereq/tree/master/examples/missing_requirement
[partial-verification]: https://github.com/Thyholt/pytest-tracereq/tree/master/examples/partial_verification
[report]: https://github.com/Thyholt/pytest-tracereq/blob/master/examples/quickstart/report.json
[contributing]: https://github.com/Thyholt/pytest-tracereq/blob/master/CONTRIBUTING.md
