---
description: "Read-only pre-implementation gate that blocks speculative architecture and disproportionate verification complexity."
---

# MVP Complexity Guard — Preflight

## Independent execution

The author/executor must not review its own output. The parent caller MUST use
Codex's built-in subagent execution to spawn `mvp-simplicity-controller` with
`agent_type: mvp-simplicity-controller`; do not perform the review below in the
author/executor session. Pass `speckit.mvp-complexity-guard.preflight`, the
project root, and any explicit `SPECIFY_FEATURE_DIRECTORY` to the controller.
The controller reads this installed command and executes the instructions
starting at Purpose independently. Only that separate controller execution
may perform the review below.

Wait for the controller and return its complete output unchanged to the parent
workflow, including findings and `MVP_COMPLEXITY_GUARD: PASS` or
`MVP_COMPLEXITY_GUARD: BLOCK`. On BLOCK, remediation remains with the original
author/executor; after remediation, rerun this command through the same
controller role. The controller must not modify the reviewed artifacts or
perform remediation. Continue implementation only after the controller returns
PASS. If the controller is unavailable or fails to return a guard result, report
`MVP_COMPLEXITY_GUARD: BLOCK` with the execution failure and return to the parent;
never fall back to self-review or treat missing review as PASS.

## Purpose

Run a mandatory, **read-only** semantic review immediately before implementation. The goal is not to make the design maximally general or robust; it is to verify that the planned implementation is the smallest architecture that satisfies current MVP requirements and mandatory safety/integrity constraints.

Verification strategy is an independent complexity surface: required behavior and safety invariants remain protected, but the method used to prove them is not automatically protected. Review the proportionality of planned proof as well as implementation architecture.

Do not edit `spec.md`, `plan.md`, `tasks.md`, source code, or configuration from this command.

## Resolve the active feature

From the project root:

1. If `SPECIFY_FEATURE_DIRECTORY` is explicitly available in the current environment/session, use it.
2. Otherwise read `.specify/feature.json` and use its `feature_directory` value.
3. If the feature directory cannot be resolved, return `MVP_COMPLEXITY_GUARD: BLOCK` and instruct the caller to select/create the active feature with Spec Kit. Do not guess a feature from unrelated directories.

Required artifacts:

- `<feature>/spec.md`
- `<feature>/plan.md`
- `<feature>/tasks.md`

Also read `.specify/memory/constitution.md` when present.

## Build five inventories

### A. Scope inventory

From `spec.md`, identify:

- Supported
- Handled Failures
- Explicitly Unsupported
- Deferred
- Edge Case Disposition entries
- FR/SC identifiers and acceptance criteria

If the MVP boundary sections are absent, flag that as a HIGH finding rather than inventing their contents.

### B. Architecture inventory

From `plan.md`, identify all non-trivial elements, especially:

- layers and services;
- interfaces/abstract base types;
- factories, registries, strategies, adapters, repositories;
- plugin/extension mechanisms and generic frameworks;
- configuration surfaces;
- persistent state beyond the direct domain model;
- queues, workers, caches, retries, circuit breakers;
- fallback/recovery paths;
- compatibility/migration paths;
- concurrency/synchronization machinery;
- extra states/state machines.

Read `## Complexity Budget` and `## Architecture Justification` when present.

### C. Task inventory

For each task, identify its stated or inferable current source: requirement, acceptance criterion, architecture decision, or mandatory safety/technical constraint.

Pay special attention to tasks with language such as:

- future / eventually / later;
- extensible / generic / reusable;
- robust / resilient without a concrete failure requirement;
- in case / might / could;
- support multiple ... when the specification currently requires one.

### D. Safety inventory

Identify requirements or controls related to security, privacy, data integrity, data loss, money movement, irreversible actions, authorization, and state corruption. These are protected from simplification unless the specification explicitly changes them.

A particular verification method is not protected merely because its requirement is safety-critical. Proof MAY be moved to a lower layer, merged, simplified, or reduced from exhaustive real-runtime coverage to representative real-runtime coverage plus exhaustive deterministic coverage, provided the underlying requirement remains conclusively verified.

### E. Verification inventory

Read `## Verification Complexity Budget` and `## Verification Justification` in `plan.md` when present. For each verification/acceptance task or materially inferable proof obligation in the current artifacts, determine where available:

- the exact claim being proved;
- its current source requirement, acceptance criterion, or safety constraint;
- the assigned verification layer;
- whether lower-level proof already exists or is planned;
- the incremental evidentiary value of the assigned higher layer;
- whether artificial fault/state construction is required;
- whether test-only hooks/instrumentation are required;
- whether another case proves the same invariant;
- any environment permutations and internal diagnostic evidence demanded by acceptance.

Record unavailable evidence as unknown; do not invent justification. Decompose bundled tasks into claims only as needed to assess their assigned proof methods. Do not design new tests during preflight: this is a proportionality and complexity review of current obligations.

Verification complexity includes over-elevated layers, duplicate proof without new evidence, exhaustive browser/E2E matrices, artificial delay/replay/synthetic ambiguity/internal-state manipulation used only to make a high-layer scenario possible, unnecessary test-only hooks, environment permutations, acceptance traces/IDs/timing/diagnostics, and expensive variants of the same invariant. Test count alone is not complexity: many cheap deterministic tests may be preferable to a few expensive browser/E2E tests.

## Verification rules

### Lowest sufficient verification layer

For every required claim, MUST use the lowest-cost deterministic verification layer that can conclusively prove it. The hierarchy is **unit → integration → real browser / E2E → human acceptance**. Higher does not mean automatically better; a higher layer MUST add a specific new proof obligation.

Escalate to browser/E2E only when the real browser/runtime materially participates in the behavior being proved. Examples include actual Chrome native context-menu routing, actual MV3 worker lifecycle, actual Chrome permission behavior, actual Chrome Side Panel behavior, and integration with the real target-page DOM. An internal state-machine invariant is not automatically a browser claim merely because it is security-sensitive.

Escalate to human acceptance only when the claim genuinely depends on human-observed interaction, comprehension, perception, accessibility use, or another property that machine evidence cannot conclusively establish.

### Incremental evidentiary value

For any verification assigned above the lowest sufficient layer, require an explicit answer:

> What additional claim becomes proven at this higher layer that is not already conclusively proven below?

“The same invariant is also exercised in a real browser” is insufficient by itself. If no material incremental evidence exists, require **DOWNLEVEL**, **MERGE**, or **REMOVE** of the unnecessary proof without weakening the underlying requirement. A source annotation such as `SECURITY` and a plan entry alone do not justify an expensive method.

Report verification findings using these rule IDs:

1. **V-01** — Verification is assigned above the lowest sufficient layer without material incremental evidence.
2. **V-02** — Browser/E2E merely repeats an invariant already conclusively covered at a deterministic lower layer.
3. **V-03** — Browser/E2E requires artificial delay, replay, synthetic ambiguity, direct internal-state manipulation, or comparable fault injection, unless the external runtime behavior itself is the subject of the claim.
4. **V-04** — Multiple browser/E2E scenarios exercise variants of one invariant where one representative real-runtime case plus exhaustive lower-level coverage is sufficient.
5. **V-05** — Test-only hooks/instrumentation are introduced solely because the claim was assigned to an unnecessarily high verification layer.
6. **V-06** — Acceptance requires internal traces/identities/timestamps or other diagnostics beyond what is necessary to establish the assigned external claim.
7. **V-07** — A higher-level verification task has no identifiable incremental evidentiary value relative to existing or planned lower-level proof.
8. **V-08** — Environment permutations are required without a current environment-specific requirement or risk.

Also report deviations from the Verification Complexity Budget without current justification. Consolidate overlapping findings for the same proof obligation and cite all applicable V-rule IDs; do not multiply findings simply because one task violates several rules. Keep justified real-runtime boundary proof (**KEEP**) and preserve conclusive lower-level coverage in every proposed simplification.

## Review rules

Report a finding when any of the following is true:

1. A `Deferred` scenario has an implementation task.
2. An `Explicitly Unsupported` scenario receives generalized support instead of minimal detection/rejection.
3. An architectural element has no current requirement/constraint and no current consumer.
4. The justification is only future flexibility, generic elegance, possible reuse, or hypothetical scale.
5. A single concrete implementation is wrapped in an interface/factory/registry/strategy hierarchy without a current boundary that requires it.
6. A new configuration option has no current consumer.
7. A fallback/retry/recovery chain exists without a current failure requirement.
8. New persistence, background processing, caching, queueing, synchronization, or compatibility machinery exists without current evidence.
9. The design adds states or transitions that are not required by supported behavior.
10. A task introduces architecture that is absent from the plan's Architecture Justification.
11. A task has no current source requirement/constraint.
12. The plan violates the project constitution.

Do **not** flag complexity merely because a pattern name looks sophisticated. A pattern is acceptable when current evidence shows that the simpler direct design is insufficient.

## Severity and blocking

Use:

- **CRITICAL** — constitution violation; security/data-integrity regression; implementation of explicitly deferred scope that materially changes the feature.
- **HIGH** — unjustified architectural layer/infrastructure; speculative generic framework; task with no current evidence; generalized support for unsupported behavior.
- **MEDIUM** — unnecessary state/configuration/indirection with limited blast radius.
- **LOW** — naming or small local cleanup that does not materially increase architecture.

Return `BLOCK` when at least one CRITICAL or HIGH finding exists. MEDIUM/LOW findings alone do not block, but must be reported.

Apply the same severity semantics to verification complexity. Materially expensive or architecture-affecting violations are **HIGH** and MUST block, including artificial browser fault/state construction, unnecessary test-only infrastructure, and exhaustive high-cost matrices without incremental evidence. Limited local verification overhead may be MEDIUM/LOW; do not downgrade a material violation because the underlying invariant is safety-critical. Loss of required safety proof remains a CRITICAL safety/integrity regression.

## Required output

```text
## MVP Complexity Preflight

| ID | Severity | Location | Complexity | Current evidence | Simpler alternative | Disposition |
|----|----------|----------|------------|------------------|---------------------|-------------|
| C-01 | HIGH | plan.md ... | ... | none | ... | REMOVE / SIMPLIFY / JUSTIFY |
| C-02 | HIGH | tasks.md ... | V-01 / V-07: ... | ... | ... | DOWNLEVEL / MERGE / REMOVE |

Verification inventory:
| Claim / source | Assigned layer | Existing/planned lower proof | Incremental evidence | Artificial state / hooks | Overlapping case / environment / diagnostics |
|----------------|----------------|------------------------------|----------------------|--------------------------|---------------------------------------------|
| ... | ... | ... | ... / unknown | ... | ... |

Protected safety/integrity controls:
- ...

Result: MVP_COMPLEXITY_GUARD: PASS | BLOCK
```

When the result is `BLOCK`, explicitly state:

> Mandatory `before_implement` gate failed. Do not write implementation code. Remediate the spec/plan/tasks and rerun the gate.

When there are no findings, report PASS explicitly. Never create findings just to populate the table.
