# MediFlow verification challenge

All executed tests passed. Release 3.2 still lacks applicable verification evidence.

MediFlow is a fictional infusion pump with hardware revisions A and B. Software, controller
bench and complete-system suites run independently and publish pytest-xspec execution records.
The package assesses those records against the required configurations in
[xspec.toml](xspec.toml). The example contains no replacement verification algorithm.

## Run the complete challenge

Run this from the repository root. No equipment or additional setup is needed.

```sh
uv run --locked python examples/medical_verification/run.py
```

Open `examples/medical_verification/results/report.md` afterward. Each linked assessment shows
its obligations, original execution outcomes, context mismatches, reuse decisions and source files.
The adjacent JSON files are the machine-readable results. Execution logs and CSV flow samples
belong to the example's infrastructure, and are linked through each execution's provenance.
Every execution has its own directory under `results/executions`, containing immutable records,
test-tagged samples and snapshots of the application, firmware and specification. Rerunning the
demo or repairing the device preserves the earlier evidence.

Expected output:

```text
3.1: COMPLETE
3.2: INCOMPLETE
3.3: FAILED
equipment-unavailable: INCOMPLETE
firmware-change: INCOMPLETE
firmware-reuse: COMPLETE
physical-required: INCOMPLETE
```

The runner finishes successfully when all commands execute. Incomplete and failed assessments
are expected experiment results. An assessment command itself returns 0 only when verification
is complete, 1 for incomplete or failed verification, and 4 for invalid inputs.

## What must be verified

Every requirement needs evidence for both supported configurations, giving eight obligations.

| Requirement | Required behavior | Suite |
| --- | --- | --- |
| SYS-001 | Stop unintended fluid delivery within 300 ms of an occlusion. | System |
| SW-001 | Detect the occlusion within 150 ms. | Software |
| SW-002 | Issue a stop command within 50 ms of detection. | Software |
| HW-001 | Stop fluid delivery on the controller bench within 100 ms of the command. | Hardware |

The software and hardware requirements refine SYS-001. Their `parent` declarations document
that relationship. They never transfer passing status to SYS-001, which has its own system test.

The controller bench omits the complete pump's downstream fluid path. This is why successful
component measurements cannot establish the end-to-end requirement. Its timing budgets add to
300 ms, but system verification measures delivered fluid instead of adding those budgets.

## Three releases and two further experiments

Release 3.1 has applicable passing executions from all three suites on both hardware revisions.

Release 3.2 has passing executions everywhere except its B system qualification. The assessment
receives the actual saved 3.1/B system execution instead. Its original outcome remains PASSED.
Its artifact identity does not match 3.2, so the corresponding obligation is INAPPLICABLE and
verification remains incomplete. No execution or artifact identity is rewritten.

Release 3.3 contains a residual-flow defect in the complete B pump. Detection takes 120 ms,
the stop command follows 40 ms later, and the B motor stops after another 80 ms. The downstream
fluid path continues delivering for 100 ms, giving an observed stop at 340 ms. Lower-level
bench tests pass, while the independent system assertion fails.

The equipment experiment genuinely deselects the B system test with pytest's `-m` filter.
The record retains its DESELECTED identity, while the execution log contains no measurement
activity. The obligation remains unverified.

The firmware experiment requests firmware `fw-b-2` but initially supplies system evidence
from `fw-b-1`. Verification stays incomplete. A second target records an explicit reuse decision
scoped to the original execution, target and system obligation, with an author and rationale.
The package records that decision without changing the original firmware or test outcome.
This fictional approval illustrates the mechanism, not an automatic compatibility judgment.

A final assessment requires physical evidence. All supplied executions identify themselves as
simulations and remain inapplicable. Changing a target cannot relabel simulated execution records.

## Introduce or repair the defect

The simulator is a small state machine. The separate observer samples delivered fluid every
millisecond, independently of the motor stop signal. Genuine controller and flow-meter adapters
can replace the fixture in [infrastructure.py](infrastructure.py) while retaining these tests.

The injected delay is `residual_b_ms = 100` in [app-3.3.toml](artifacts/app-3.3.toml).
To demonstrate the repair without editing that artifact:

```sh
uv run --locked python examples/medical_verification/run.py --fix-residual-flow
```

The newly hashed repaired artifact makes 3.3 COMPLETE. Release 3.2 remains INCOMPLETE.
Rerun the original command to restore the defect experiment's reports.

## Independent suites and saved evidence

[Software](software/test_behavior.py), [hardware](hardware/test_behavior.py) and
[system](system/test_behavior.py) have their own pytest roots and configuration files.
They run in separate processes. They can run in different environments or repositories by
copying the shared specification and simulation adapter, or replacing the adapter with real tools.
No controller, dependencies or pytest interpreter is shared across executions by the package.

After the runner creates the device/context files, one suite can be rerun directly:

```sh
uv run --locked python examples/medical_verification/run.py --suite system --hardware B --release 3.1
```

Context records bind the simulator configuration to the application artifact's content hash.
The domain fixture checks that identity and the firmware before executing the model. The package
records the supplied context, a fresh execution ID, suite identity and UTC timestamps. It does
not operate instruments, authenticate hardware identities or collect the measurements itself.
The package also records the specification content digest. Changing requirements cannot make
old executions verify the new baseline implicitly.

The input declarations use TOML throughout. Saved pytest outcomes and assessment results use
JSON for exchange, and Markdown provides the readable view. Requirement descriptions and
rationales stay in the specification rather than being copied into execution records.

## Limits

All devices, firmware and measurements are simulated. The observer is not a calibrated physical
instrument. Timing limits are fictional demonstration values. This project establishes neither
medical safety nor certification, clinical validation, hazard completeness or regulatory approval.
The package establishes only whether the supplied executions satisfy the declared verification plan.
