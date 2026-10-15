# Contributing

Humans and agents decide intended behavior together. Agents choose implementation details.

## Bring a problem

For a bug, provide a small runnable reproduction, the command, and expected and actual results.
For a substantial change, bring a runnable example of a hard testing or specification problem:

- Show the workflow, specifications, tests and required execution contexts.
- Demonstrate the current limitation and expected results.
- Include a negative case that must not pass, such as missing required evidence.

You can start with a question and develop the example with an agent. You do not need to design
an API or implementation. The example must show why a change is needed.

## Get started

With uv installed, clone the repository and run this from the repository root:

```sh
uv run --locked prek install
```

This prepares the development environment and installs checks that run before commits.
Create a branch for your change.

## Make a change

Follow the [development and testing conventions](AGENTS.md#project-conventions-and-agreed-workflow).

Agents write acceptance tests first. Humans review the example and expected outcomes,
then explicitly approve the tests before implementation. Agents implement and demonstrate
both successful and negative outcomes. Keep domain-specific concepts in examples.

Prefer one coherent workflow. A stronger example may justify replacing an approach and breaking
compatibility, with human agreement on behavior. Explain why, provide migration notes and use
a major release.

Use the existing [acceptance tests](tests/acceptance) as a starting point for changes
users can observe. They run real pytest commands in isolated projects to keep
repository configuration out of each run. Use [unit tests](tests/unit) for focused logic.

Run the relevant test file while working:

```sh
uv run --locked pytest tests/acceptance/test_configuration.py -n 0
```

Replace the path with the file you are changing. `-n 0` runs tests serially,
which makes debugging easier.

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

## Open a pull request

Keep each pull request focused on one change. Link its proof case or bug reproduction,
show the before and after behavior and negative outcomes, and explain how you verified it.
Call out deliberate breaking changes and migration steps. Include a regression test for bug fixes.

Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/),
for example `docs: clarify requirement reporting`.
Wait for CI and review before merging.

Maintainers can follow [the release guide](docs/releasing.md) to publish a version.
