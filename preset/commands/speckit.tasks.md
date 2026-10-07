
## Mandatory Greenfield MVP Task-Generation Addendum

Generate only tasks that can be traced to current requirements, current plan decisions, or mandatory engineering/safety constraints.

### 1. Task source requirement

Each implementation task MUST include a concise source annotation in its normal task text, for example:

`(source: FR-004)`
`(source: ARCH: direct OpenAI integration)`
`(source: SECURITY)`

Do not change the core Spec Kit checkbox/ID/[P]/[US] task syntax; add the source annotation inside the task description.

### 2. Prohibited speculative tasks

Do NOT create implementation tasks for:

- scenarios listed as `Deferred`;
- generalized support for `Explicitly Unsupported` scenarios;
- future providers, future storage engines, future user types, future scale, or hypothetical integrations;
- factories, registries, strategies, plugin systems, adapters, compatibility layers, generic frameworks, configuration surfaces, caches, queues, retries, or additional state unless `plan.md` provides current evidence for them.

An explicitly unsupported scenario MAY create a task only for the smallest validation/error behavior needed to reject it safely.

### 3. Task-to-plan consistency

If a task introduces a new architectural element that is absent from `## Architecture Justification`, do not emit the task. Report the mismatch and require the plan to justify the element first.

If a task cannot cite a current requirement, acceptance criterion, architecture decision, or mandatory safety/technical constraint, omit it.

### 4. Verification-to-plan consistency

Verification tasks MUST respect the verification layer justified in `plan.md` under `## Verification Complexity Budget` and `## Verification Justification`. Keep the existing task syntax and source annotations for verification/acceptance tasks too.

Do not promote an integration-level claim into browser/E2E acceptance unless the plan contains an explicit incremental-evidence justification: what additional claim is proven at that higher layer that is not already conclusively proven below? Safety sensitivity alone and “the same invariant is also exercised in a real browser” are insufficient.

Do not automatically emit separate high-cost acceptance tasks for every edge-case variant of the same invariant. Exhaustive variants normally remain in deterministic lower-level coverage when one representative higher-level case is sufficient. Do not add artificial fault/state construction, test-only hooks, environment permutations, or internal acceptance diagnostics to support an unnecessarily elevated layer.

If a proposed verification task exceeds the plan's justified layer or budget, do not emit it; report the mismatch and require current incremental evidence in the plan first. A plan entry does not exempt a task from the preflight verification rules. Ordinary unit/integration tasks with an obvious appropriate layer need no verbose justification entry.

### 5. Final simplification pass

Before completing `tasks.md`, scan the generated task list and ask for each task: **"What current evidence makes this necessary for the MVP?"** Remove tasks whose only answer is future flexibility, generic robustness, elegance, or possible future reuse.

For verification tasks, also ask whether the assigned layer adds material evidence beyond existing/planned lower-level proof. **DOWNLEVEL**, **MERGE**, or **REMOVE** unnecessary proof methods while retaining conclusive coverage of the required claims.
