# Architectural principles

These principles define the responsibility boundaries of pytest-xspec.

- **Domain meaning belongs to users.** Users define what their specifications mean,
  how detailed they are, and which tests support them. The library treats requirement
  IDs as opaque references and leaves test organization to users.
- **The library operates at pytest's boundary.** Its inputs are specification declarations,
  configuration and command-line options, and pytest's collected test associations and outcomes.
  Saved execution records preserve that boundary when independent runs are assessed together.
  Test bodies and fixtures translate domain behavior into pytest outcomes. The library
  neither inspects their implementations nor introduces a separate execution-outcome protocol.
- **Domain evidence stays with domain infrastructure.** Measurements, artifacts and logs
  are collected by users' testing tools. pytest-xspec does not provide fixtures for submitting
  that evidence. Test identities allow consumers to correlate results with external evidence.
- **Verification is a conclusion under explicit rules.** The library derives requirement
  statuses from test outcomes. Individual test identities and outcomes remain available
  alongside aggregated statuses. A successful verification verdict establishes that the
  library's rules were satisfied, without judging the quality or sufficiency of test assertions.
- **Specification content has one source.** Descriptions, rationale and domain metadata
  belong in users' specifications. Results reference requirements by ID so consumers can
  combine specifications and results without duplicating that content in the library's output.
  Execution context records observed identities and provenance references supplied by testing
  infrastructure. It does not copy requirement descriptions or collect the underlying evidence.
- **Feedback is generic, interpretation is domain-owned.** pytest-xspec provides structured
  results and terminal feedback. Consumers use those results to produce domain-specific
  reports and make compliance or release decisions.

See [CONTRIBUTING.md](../CONTRIBUTING.md) for how examples guide changes and how
contributors propose and evaluate them. Supported behavior and acceptance criteria are
defined in the [specification](specification.md).
