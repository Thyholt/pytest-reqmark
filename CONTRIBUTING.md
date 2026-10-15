# Contributing

Humans read acceptance tests and collaborate with AI agents to decide intended behavior.
Agents investigate solutions, decide implementation details and architecture, write the code
and unit tests, and demonstrate the results. Contributors can bring a problem without
designing the implementation.

## Bring a problem and a proof case

For a bug report, include a small runnable reproduction, the command you ran, and the expected
and actual results. For a substantial behavior change, bring a proof case: a runnable example
of a hard testing or specification problem that demonstrates why a change is needed.

Include:

- A concrete user workflow and the verification question it must answer.
- Specifications, executable tests and the execution contexts the problem requires.
- Commands showing the current limitation and the expected evidence.
- A negative case that must not be reported as success, such as missing required evidence.
- The boundary between the example's domain responsibilities and pytest-xspec's general role.

An issue can begin with a problem report or research question. Humans and agents can develop
the proof case together. Before accepting a substantial change, agents require a working
example that can expose an incorrect result. A proposed flag, file format or hook alone
does not establish the need.

## Get started

With uv installed, clone the repository and run this from the repository root:

```sh
uv run --locked prek install
```

This prepares the development environment and installs checks that run before commits.
Create a branch for your change.

## Make a change

Follow the [development and testing conventions](AGENTS.md#project-conventions-and-agreed-workflow).

Humans and agents collaborate to decide intended public behavior. Agents first turn the proof
case into readable acceptance tests. Humans review whether the example is realistic, whether
the expected results are correct and whether the negative case catches false success.
Obtain explicit human approval of the
acceptance tests before plugin implementation. Agents then choose the design and implement
the smallest general solution using red-green-refactor. They demonstrate the example before
and after the change, including negative outcomes. A passing suite alone is insufficient.

Prefer one coherent workflow. A stronger proof case can justify replacing an existing approach
and breaking compatibility when humans agree to the changed behavior. Explain what the change
solves and simplifies, provide migration notes, and make breaking changes in a major release.
Keep domain-specific concepts in the example rather than building them into the plugin.

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
