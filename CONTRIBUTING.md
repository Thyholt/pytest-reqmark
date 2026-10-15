# Contributing

pytest-xspec aims to do one thing exceptionally well: executable specifications and feedback. It
connects requirements to tests and reports their results.

The goal is not to accumulate features, but to solve increasingly difficult problems in executable
specifications and feedback exceptionally well.

## Proposing changes

Development is driven by problems, not feature requests.

Contributors should bring difficult, realistic examples that challenge pytest-xspec. Proposals
should demonstrate:

- The problem: A concrete challenge involving executable specifications or feedback.
- The example: Requirements, tests, and expected results that make the problem reproducible and
  verifiable.
- The value: Why solving the problem matters beyond the example itself.

Examples should challenge the library's assumptions, not accommodate its existing design.

Challenging examples are living references, not fixed implementation plans. Large problems should be
broken into coherent, verifiable increments, each delivering meaningful progress. Examples may evolve
as understanding improves, but must never be simplified merely to accommodate the existing
implementation.

For bugs, provide a minimal reproduction, the command executed, and the expected and actual results.

## Architecture follows evidence

pytest-xspec favors one excellent way of doing things over multiple competing approaches.

No API, configuration format, or architectural decision is permanent. When a convincing example
demonstrates a better general approach, pytest-xspec should adopt it, even if that requires breaking
changes.

Backward compatibility must not preserve an inferior design. Users who prefer an earlier approach
can continue using or fork a previous major release.

## Get started

With uv installed, clone the repository and run this from the repository root:

```sh
uv run --locked prek install
```

This prepares the development environment and installs checks that run before commits. Create a
branch for your change.

## Make a change

Use the existing [acceptance tests](tests/acceptance) as a starting point for changes users can
observe. They run real pytest commands in isolated projects to keep repository configuration out of
each run. Use [unit tests](tests/unit) for focused logic.

Run the relevant test file while working:

```sh
uv run --locked pytest tests/acceptance/test_configuration.py -n 0
```

Replace the path with the file you are changing. `-n 0` runs tests serially, which makes debugging
easier.

## Check your work

Run the configured checks:

```sh
uv run --locked prek run --all-files
```

Run the full test suite:

```sh
uv run --locked pytest
```

Measure line and branch coverage, including acceptance test subprocesses:

```sh
uv run --locked pytest --cov --cov-report=term-missing --cov-report=xml
```

Coverage settings live in `pyproject.toml`. Results are reported in the terminal and `coverage.xml`.
No minimum coverage percentage is enforced.

Fix reported problems before submitting. Check definitions live in `prek.toml`, tool settings in
`pyproject.toml`, and CI jobs in [`.github/workflows`](.github/workflows).

## Open a pull request

Keep each pull request focused on one change. Explain the problem, what users will experience, and
how you verified it. Include a regression test for bug fixes.

Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/), for example `docs:
clarify requirement reporting`. Wait for CI and review before merging.

Maintainers can follow the [release guide](docs/releasing.md) to publish a version.
