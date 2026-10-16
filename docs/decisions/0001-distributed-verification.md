# ADR-001: Assess declared obligations over saved pytest executions

## Status

Accepted for the verification challenge implementation.

## Date

2026-10-16

## Context

Independent suites can all pass while a required configuration has no applicable evidence.
A requirement-to-test inventory within one pytest invocation cannot express the missing
configuration, and a passing execution from an earlier artifact must retain its original identity.
The MediFlow challenge requires complete, incomplete and failed conclusions across suites.

## Decision

Keep pytest as the sole source of execution outcomes. Extend its existing report with optional
execution identity, specification digest, suite, timestamps, context and external provenance
references. Read that context from user-owned TOML rather than introducing measurement-submission
fixtures or another test-outcome protocol.

Use one TOML specification for requirement content, parent references, named configurations and
explicit obligations. Use TOML target documents for assessment context, configuration overrides
and narrowly scoped reuse decisions. JSON exchanges recorded pytest outcomes. Markdown is a
readable projection, not a competing declaration format.

Provide a command that assesses saved reports without collecting tests. An obligation identifies
a requirement, suite and configuration. Match the declared context and original specification
baseline. Evaluate every applicable supplied execution, preserving all individual outcomes.
Absent configurations remain required because the declaration, not available evidence, defines
the obligation set. Parent relationships do not propagate verification.

Use SHA-256 of the selected specification document as a conservative baseline reference.
Even an editorial change produces a mismatch. This avoids silently treating changed requirements
as verified by prior tests. Reuse remains possible only through an explicit decision scoped to
one target, execution and obligation with an author and reason. Reuse accepts applicability,
not test success, and cannot turn unsuccessful outcomes into passing ones.

Domain tools establish what artifact, firmware, hardware and measurement source an execution
used. The package records those assertions and compares opaque strings. It does not authenticate
instruments, judge engineering compatibility or decide product safety and release authorization.
The example uses unique execution directories with artifact/specification snapshots and tagged
measurement rows, so a repair run cannot overwrite or mix prior evidence.

## Alternatives considered

Keeping the example's fictional reviewer would leave the central capability unimplemented and
would permit a first-matching-result shortcut. It is removed.

Encoding every release/configuration into requirement IDs would accommodate the existing design
at the cost of duplicating requirement identity and obscuring the missing-configuration problem.
Explicit obligations retain one requirement inventory.

Inferring required configurations from available reports would make wholly missing configurations
invisible. Selecting the newest or passing execution implicitly would conceal supplied failures.
Both are rejected in favor of explicit declarations and caller-selected input sets.

A domain-specific evidence system inside the plugin would duplicate testing infrastructure and
violate the library's responsibility boundaries. Generic reference matching and pytest-outcome
aggregation solve the demonstrated problem without collecting measurements.

## Consequences

Existing single-run configuration, markers and report behavior remain available. Contextual
assessment requires executions bound to a specification baseline, or a recorded reuse decision.
Malformed records and conflicting execution identities are input errors rather than optimistic
verification. Repeated identical inputs are deduplicated.

The new model adds configurations, obligations and targets because each is needed to distinguish
required work, observed execution context and the subject being assessed. It adds no automatic
compatibility policy, evidence database, scheduler, medical rules or hardware management.

The full example exercises both hardware revisions, stale artifacts, a system failure invisible
to component tests, native deselection, changed firmware and explicit reuse, plus rejection of
simulation when physical evidence is required. Domain meaning remains in the example.
