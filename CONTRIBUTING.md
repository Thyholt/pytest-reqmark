# Contributing

For a bug report, include a small example, the command you ran, and the expected
and actual results.
Discuss changes to public behavior before implementing them.

## Get started

With uv installed, clone the repository and run this from the repository root:

```sh
uv run --locked prek install
```

This prepares the development environment and installs checks that run before commits.
Create a branch for your change.

## Make a change

For a bug fix, first add a test that reproduces it. For new behavior, agree on the
acceptance tests before changing the plugin. Make the test pass, then simplify.

Use the existing [acceptance tests](tests/acceptance) as a starting point for changes
users can observe. They run real pytest commands in isolated projects to keep
repository configuration out of each run. Use [unit tests](tests/unit) for focused logic.

Run the relevant test file while working:

```sh
uv run --locked pytest tests/acceptance/test_configuration.py -n 0
```

Replace the path with the file you are changing. `-n 0` runs tests serially,
which makes debugging easier.

Update the usage documentation when users need to do something differently.

## Check your work

Run the configured checks:

```sh
uv run --locked prek run --all-files
```

Run the full test suite:

```sh
uv run --locked pytest
```

Measure line and branch coverage, including the acceptance scenarios' pytest subprocesses:

```sh
uv run --locked pytest --cov --cov-report=term-missing --cov-report=xml
```

Coverage settings live in `pyproject.toml`. The subprocess patch collects execution
inside the isolated user projects; pytest-cov combines their results with the main
suite and xdist workers. The terminal shows missing lines and branches, and
`coverage.xml` contains the machine-readable report uploaded to Codecov by CI.
This measures the plugin's code, independently of the requirement verification
coverage shown in its reports. No minimum percentage is enforced initially.

Fix reported problems before submitting. Check definitions live in
[prek.toml](prek.toml), tool settings in [pyproject.toml](pyproject.toml), and
CI jobs in [.github/workflows](.github/workflows).

## Dependency security scans

Create a [Snyk account](https://app.snyk.io/login), then add its authentication token as `SNYK_TOKEN`
[GitHub Actions repository secret](https://github.com/Thyholt/pytest-tracereq/settings/secrets/actions).
Do not put the token in source files or pull requests.

The Snyk workflow scans runtime and development dependencies exported from
`uv.lock` as standard pip requirements. This avoids requiring Snyk's Enterprise-only
uv integration. The workflow fails when scanning cannot complete or vulnerabilities
are found; its logs show vulnerability counts and severity, and its `snyk-results`
artifact contains the JSON report. The README badge shows the latest `master`
scan status and links to these results. Fork pull requests do not receive the token.

## Open a pull request

Keep each pull request focused on one change. Explain the problem, what users
will experience, and how you verified it. Include a regression test for bug fixes.

Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/),
for example `docs: clarify requirement reporting`.
Wait for CI and review before merging.

Maintainers can follow [the release guide](docs/releasing.md) to publish a version.
