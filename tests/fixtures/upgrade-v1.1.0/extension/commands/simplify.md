---
description: "Read-only post-implementation gate that finds removable accidental complexity without weakening required behavior."
---

# MVP Complexity Guard — Simplification Review

## Purpose

Run a mandatory, **read-only** review after implementation and before the parent implementation workflow reports completion.

The question is deliberately narrow:

> What implementation complexity exists that is not demanded by the current specification, plan, tasks, constitution, or mandatory safety/integrity constraints?

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

Then inspect the implementation changed for the feature:

1. Prefer current VCS status/diff to identify touched implementation files.
2. If the diff is empty or unavailable, inspect implementation paths referenced by completed tasks and the plan.
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

## Severity and blocking

- **CRITICAL** — implementation violates constitution or implements deferred/unsupported scope in a way that materially changes architecture or risk.
- **HIGH** — removable architectural layer/framework/infrastructure or speculative flexibility with material maintenance/state-space cost.
- **MEDIUM** — localized unnecessary abstraction/configuration/fallback/state.
- **LOW** — minor indirection or cleanup opportunity.

Return `BLOCK` when there is at least one CRITICAL or HIGH simplification finding. MEDIUM/LOW findings do not block completion.

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
