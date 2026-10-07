---
description: "Read-only pre-implementation gate that blocks speculative MVP complexity."
---

# MVP Complexity Guard — Preflight

## Purpose

Run a mandatory, **read-only** semantic review immediately before implementation. The goal is not to make the design maximally general or robust; it is to verify that the planned implementation is the smallest architecture that satisfies current MVP requirements and mandatory safety/integrity constraints.

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

## Build four inventories

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

## Required output

```text
## MVP Complexity Preflight

| ID | Severity | Location | Complexity | Current evidence | Simpler alternative | Disposition |
|----|----------|----------|------------|------------------|---------------------|-------------|
| C-01 | HIGH | plan.md ... | ... | none | ... | REMOVE / SIMPLIFY / JUSTIFY |

Protected safety/integrity controls:
- ...

Result: MVP_COMPLEXITY_GUARD: PASS | BLOCK
```

When the result is `BLOCK`, explicitly state:

> Mandatory `before_implement` gate failed. Do not write implementation code. Remediate the spec/plan/tasks and rerun the gate.

When there are no findings, report PASS explicitly. Never create findings just to populate the table.
