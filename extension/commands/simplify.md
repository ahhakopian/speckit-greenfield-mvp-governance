---
description: "Read-only post-implementation gate that finds removable implementation and verification complexity without weakening required behavior."
---

# MVP Complexity Guard — Simplification Review

## Independent execution

The author/executor must not review its own output. The parent caller MUST use
Codex's built-in subagent execution to spawn `mvp-simplicity-controller` with
`agent_type: mvp-simplicity-controller`; do not perform the review below in the
author/executor session. Pass `speckit.mvp-complexity-guard.simplify`, the
project root, and any explicit `SPECIFY_FEATURE_DIRECTORY` to the controller.
The controller reads this installed command and executes the instructions
starting at Purpose independently. Only that separate controller execution
may perform the review below.

Wait for the controller and return its complete output unchanged to the parent
workflow, including findings and `MVP_COMPLEXITY_GUARD: PASS` or
`MVP_COMPLEXITY_GUARD: BLOCK`. On BLOCK, remediation remains with the original
author/executor; after remediation, rerun this command through the same
controller role. The controller must not modify the reviewed artifacts or
perform remediation. Report completion only after the controller returns
PASS. If the controller is unavailable or fails to return a guard result, report
`MVP_COMPLEXITY_GUARD: BLOCK` with the execution failure and return to the parent;
never fall back to self-review or treat missing review as PASS.

## Purpose

Run a mandatory, **read-only** review after implementation and before the parent implementation workflow reports completion.

The question is deliberately narrow:

> What implementation or verification complexity exists that is not demanded by the current specification, plan, tasks, constitution, or mandatory safety/integrity constraints?

Do not edit files from this command. Do not optimize for fewer lines at the expense of correctness, readability, security, privacy, data integrity, or acceptance criteria.

## Resolve the active feature

1. Prefer explicit `SPECIFY_FEATURE_DIRECTORY` when available.
2. Otherwise read `.specify/feature.json` and use `feature_directory`.
3. If unresolved, return `MVP_COMPLEXITY_GUARD: BLOCK`; do not guess.

Read:

- `<feature>/spec.md`
- `<feature>/plan.md`
- `<feature>/tasks.md`
- `.specify/memory/constitution.md` when present

Then inspect the implementation and verification assets changed for the feature:

1. Prefer current VCS status/diff to identify touched implementation files, tests, acceptance scenarios, test-only hooks/instrumentation, and verification configuration.
2. If the diff is empty or unavailable, inspect implementation and verification paths referenced by completed tasks and the plan.
3. Exclude generated/vendor/build artifacts unless the feature intentionally owns them.

## Protected behavior

Do not recommend removing:

- a current acceptance criterion;
- security or authorization checks;
- privacy controls;
- validation preventing data loss/corruption;
- money/irreversible-action safeguards;
- required external contract handling;
- a mechanism explicitly justified by a current measurable performance/load constraint.

Security, authorization, privacy, data-integrity, state-corruption, and similar safety requirements remain protected. A particular verification method is not protected merely because the requirement is safety-critical. Proof MAY be moved to a lower layer, merged, simplified, or reduced from exhaustive real-runtime coverage to representative real-runtime coverage plus exhaustive deterministic coverage, provided the underlying requirement remains conclusively verified.

## Simplification review

For every newly introduced or materially changed element, ask:

1. Which current requirement, constraint, or task requires this element?
2. Which current consumer uses the flexibility it provides?
3. Can the same required behavior be implemented more directly with fewer states/layers/configuration/fallbacks?
4. Would removal change supported behavior or only remove hypothetical flexibility?

Look specifically for:

- interface + one implementation with no real boundary need;
- base classes used only once;
- factories/registries/strategies that select only one real option;
- adapters around a single concrete dependency with no current substitution requirement;
- repositories/services/managers that only forward calls;
- generic frameworks created for one feature;
- configuration options with one fixed current value and no current operator/user need;
- caches, queues, retries, circuit breakers, background workers, synchronization, or persistence added without evidence;
- multi-stage fallback or recovery trees where explicit failure is sufficient;
- legacy/compatibility/migration code in a true greenfield path without an external legacy contract;
- duplicate normalization/error-mapping layers;
- states/transitions that cannot occur in the supported MVP behavior;
- code that supports `Deferred` scenarios;
- tests whose only purpose is to lock in speculative behavior not present in the specification.

Small local duplication is not automatically a problem. Prefer duplication over a speculative shared abstraction when the commonality is not demonstrated.

## Verification simplification review

Verification strategy is an independent complexity surface. Review materially changed verification assets against the plan's `## Verification Complexity Budget` and `## Verification Justification`, current requirements, and actual existing/planned lower-level proof. Test count alone is not complexity: many cheap deterministic tests may be preferable to a few expensive browser/E2E tests.

For every required claim, MUST use the lowest-cost deterministic verification layer that can conclusively prove it: **unit → integration → real browser / E2E → human acceptance**. Higher does not mean automatically better; a higher layer MUST add a specific new proof obligation.

Browser/E2E is justified only when the real browser/runtime materially participates in the claim, such as actual Chrome native context-menu routing, MV3 worker lifecycle, permission behavior, Side Panel behavior, or integration with the real target-page DOM. An internal state-machine invariant is not automatically a browser claim merely because it is security-sensitive. Human acceptance is justified only for human-observed interaction, comprehension, perception, accessibility use, or another property that machine evidence cannot conclusively establish.

For each materially changed verification asset, ask:

1. What exact claim does this prove, and what current requirement/source requires it?
2. What is the lowest sufficient layer?
3. Is the claim already conclusively covered below?
4. What does this environment add? What additional claim becomes proven at this higher layer that is not already conclusively proven below?
5. Does the test require artificial fault injection or test-only machinery?
6. Can multiple real-browser/E2E scenarios become one representative case plus lower-level exhaustive coverage?
7. Would removing or down-leveling this proof weaken requirement coverage, or only change the proof method?

Look specifically for:

- higher-level tests duplicating conclusive lower-level proof;
- browser/E2E tests with no browser-specific evidentiary value;
- acceptance scenarios requiring artificial delay, replay, synthetic ambiguity, direct internal-state construction, or comparable fault injection, unless the external runtime behavior itself is the subject of the claim;
- exhaustive real-runtime matrices or multiple expensive variants of one invariant where representative real-runtime coverage plus exhaustive deterministic coverage is sufficient;
- test-only infrastructure created solely for over-elevated verification;
- unnecessary acceptance diagnostics, including internal traces, IDs, identities, timestamps, or timing evidence beyond what establishes the assigned external claim;
- environment permutations without a current environment-specific requirement or risk;
- deviations from the verification budget without current justification.

“The same invariant is also exercised in a real browser” is insufficient justification by itself. Without material incremental evidence, require **DOWNLEVEL**, **MERGE**, or **REMOVE** of unnecessary proof; **SIMPLIFY** evidence collection where the runtime claim itself is justified. Preserve conclusive requirement coverage and **KEEP** justified real-runtime boundaries. Consolidate overlapping findings for the same obligation. Explicit plan approval alone does not establish incremental evidence.

## Severity and blocking

- **CRITICAL** — implementation violates constitution or implements deferred/unsupported scope in a way that materially changes architecture or risk.
- **HIGH** — removable architectural layer/framework/infrastructure or speculative flexibility with material maintenance/state-space cost.
- **MEDIUM** — localized unnecessary abstraction/configuration/fallback/state.
- **LOW** — minor indirection or cleanup opportunity.

Return `BLOCK` when there is at least one CRITICAL or HIGH simplification finding. MEDIUM/LOW findings do not block completion.

Apply the same severity semantics to verification complexity. Materially expensive or architecture-affecting violations are **HIGH** and MUST block, including artificial browser fault/state construction, unnecessary test-only infrastructure, and exhaustive high-cost matrices without incremental evidence. Limited local verification overhead may be MEDIUM/LOW; do not downgrade a material violation because its invariant is safety-critical. Loss of required safety proof remains a CRITICAL safety/integrity regression.

## Required output

```text
## MVP Post-Implementation Simplification Review

| ID | Severity | Location | Unnecessary complexity | Why it is not currently required | Behavior-preserving simplification |
|----|----------|----------|------------------------|----------------------------------|------------------------------------|
| S-01 | HIGH | src/... | ... | ... | ... |

Protected behavior checked:
- ...

Result: MVP_COMPLEXITY_GUARD: PASS | BLOCK
```

For every HIGH/CRITICAL finding, describe the smallest behavior-preserving simplification and the validation/tests that must be rerun after applying it.

When `BLOCK`, explicitly state:

> Mandatory `after_implement` gate failed. Do not report the feature complete until the blocking accidental complexity is simplified or explicitly justified in the plan and the gate is rerun.

When there are no findings, report PASS explicitly. Do not invent cleanup work.
