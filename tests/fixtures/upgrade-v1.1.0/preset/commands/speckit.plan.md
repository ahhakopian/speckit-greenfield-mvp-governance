
## Mandatory Greenfield MVP Planning Addendum

The implementation plan MUST optimize for the smallest architecture that satisfies the current specification and constitution.

### 1. Add a Complexity Budget

Ensure `plan.md` contains `## Complexity Budget` and explicitly state the allowed/required complexity for this feature. Use the following defaults unless current evidence requires otherwise:

| Complexity surface | MVP default |
|---|---|
| New architectural layers | 0 unless a current boundary requires one |
| Generic frameworks / internal platforms | 0 |
| Future extensibility points | 0 unless a known current variability point exists |
| New configuration options | 0 unless a current user/product/ops requirement consumes them |
| Fallback trees | 0; prefer one explicit failure path over multi-step recovery |
| Background workers / queues | 0 unless required by current behavior or load constraint |
| New persistent state | Only what current requirements require |
| Compatibility / migration layers | 0 in greenfield unless an external contract requires compatibility |
| Caching / retry / circuit breaking | Only when a current failure/performance requirement demonstrates need |
| Additional concurrency mechanisms | Only when current behavior requires concurrency |

A non-zero entry MUST be justified in the Architecture Justification table.

### 2. Add Architecture Justification

Ensure `plan.md` contains `## Architecture Justification`:

| Element | Current requirement / constraint | Current consumer | Why the simpler direct design is insufficient |
|---|---|---|---|
| ... | FR-### / SC-### / SECURITY / external constraint | ... | ... |

Apply the following rules:

- Every non-trivial abstraction or infrastructure component needs current evidence.
- One concrete implementation does not, by itself, justify an interface/factory/registry/strategy hierarchy.
- A second hypothetical implementation is not a current consumer.
- Small local duplication is acceptable when the common abstraction is not proven.
- Prefer strict validation + explicit rejection to accommodation of unsupported variants.
- Minimize state count, indirection, configuration, and fallback branches.
- Do not design implementation paths for `Deferred` scenarios.
- For `Explicitly Unsupported` scenarios, plan only the smallest safe detection/rejection behavior.
- Do not introduce scale infrastructure without a measurable current scale/performance requirement.

### 3. Reversible vs. hard-to-reverse decisions

For reversible internal decisions, prefer the simplest concrete implementation. Spend additional design effort on hard-to-reverse decisions such as public APIs, persistent schemas/formats, external contracts, security boundaries, and irreversible workflows.
