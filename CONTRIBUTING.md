# Contributing

Use the [architectural principles](docs/architecture_principles.md) to understand the library's
responsibility boundaries when proposing changes.

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

## AI-assisted contributions

This repository uses a pinned copy of [Addy Osmani's Agent Skills](https://github.com/addyosmani/agent-skills)
as its current engineering workflow skillset. We draw on guidance written by experienced
practitioners to give contributors a shared approach to specifying, changing and releasing
the library.

Shared skills are included when you clone the repository, grouped by upstream author under
`.agents/skills/<author>/`. Keep each author's skills, supporting references, license and
source record together, preserving the upstream directory layout and relative links.
No separate skill installation is needed. Use the bundled workflows through your agent's
established skill-discovery mechanism. Avoid installing competing workflow collections for
this project. Specialist skills may supplement the bundle when the task requires them.

The [source record](.agents/skills/addyosmani/source.txt) identifies the exact upstream revision
and imported paths. The [upstream license](.agents/skills/addyosmani/LICENSE) is included with
the copy.
Keep imported files unchanged and keep project-specific rules in repository instructions.
Review skill additions and upgrades through pull requests: inspect the changed instructions
and scripts, check supporting references, and try representative tasks to verify discovery
and behavior. Update the source record and preserve the applicable licenses and attribution.

## Make a change

Use the [specification](docs/specification.md) to identify supported behavior and the affected
[acceptance tests](tests/acceptance). Update it when observable behavior changes. Acceptance tests
run real pytest commands in isolated projects to keep repository configuration out of each run.
Use [unit tests](tests/unit) for focused logic.

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
