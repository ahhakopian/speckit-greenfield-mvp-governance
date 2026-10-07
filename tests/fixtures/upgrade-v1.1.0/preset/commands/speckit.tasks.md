
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

### 4. Final simplification pass

Before completing `tasks.md`, scan the generated task list and ask for each task: **"What current evidence makes this necessary for the MVP?"** Remove tasks whose only answer is future flexibility, generic robustness, elegance, or possible future reuse.
