
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

### 3. Add a Verification Complexity Budget

Verification strategy is an independent complexity surface. Required behavior and safety invariants remain protected, but their proof method is not automatically protected.

For every required claim, MUST use the lowest-cost deterministic verification layer that can conclusively prove it: **unit → integration → real browser / E2E → human acceptance**. Higher does not mean automatically better; a higher layer MUST add a specific new proof obligation.

Escalate to browser/E2E only when the real browser/runtime materially participates in the behavior being proved, such as actual Chrome native context-menu routing, MV3 worker lifecycle, permission behavior, Side Panel behavior, or integration with the real target-page DOM. An internal state-machine invariant is not automatically a browser claim merely because it is security-sensitive.

Escalate to human acceptance only for human-observed interaction, comprehension, perception, accessibility use, or another property that machine evidence cannot conclusively establish.

Ensure `plan.md` contains `## Verification Complexity Budget`, using these defaults:

| Verification surface | MVP default |
|---|---|
| Verification layer | Lowest sufficient deterministic layer |
| Real-browser/E2E coverage | Smallest representative set proving real-runtime boundaries |
| Exhaustive edge-case matrices | Lower-level deterministic tests by default |
| Browser/E2E fault injection | 0 unless the external runtime itself is the failure source being validated |
| Test-only hooks | 0 unless lower-level proof cannot establish the required claim |
| Duplicate proof across layers | 0 unless the higher layer adds explicit incremental evidence |
| Environment permutations | Only variants with a current environment-specific risk |
| Internal diagnostic evidence in acceptance | Only what is necessary to establish the assigned external claim |

Every non-default choice MUST be justified with current evidence in Verification Justification. Test count alone is not complexity: many cheap deterministic tests may be preferable to a few expensive browser/E2E tests. Do not require artificial delay/replay/synthetic ambiguity/internal-state manipulation or test-only machinery merely to make an unnecessarily elevated scenario possible.

### 4. Add compact Verification Justification

Ensure `plan.md` contains `## Verification Justification`. For expensive or elevated verification claims, capture:

| Claim | Requirement / source | Lowest sufficient layer | Higher layer required? | Incremental evidence provided by higher layer |
|---|---|---|---|---|
| ... | FR-### / SC-### / SECURITY / current constraint | unit / integration / real browser / human | No / Yes: layer and reason | Specific additional claim, or none |

Do not require verbose entries for ordinary unit/integration tests where the appropriate layer is obvious. Cite existing or planned lower-level proof when assessing overlap; a compact reference is enough. For a non-default budget choice, include its current justification in the relevant row.

For any verification above the lowest sufficient layer, explicitly answer:

> What additional claim becomes proven at this higher layer that is not already conclusively proven below?

“The same invariant is also exercised in a real browser” is insufficient by itself. Without material incremental evidence, **DOWNLEVEL**, **MERGE**, or **REMOVE** the unnecessary proof without weakening the underlying requirement. Keep exhaustive deterministic coverage and only the representative real-runtime cases that prove distinct runtime boundaries. Security, authorization, privacy, data-integrity, and state-corruption requirements remain conclusively verified even when the proof method changes.

### 5. Reversible vs. hard-to-reverse decisions

For reversible internal decisions, prefer the simplest concrete implementation. Spend additional design effort on hard-to-reverse decisions such as public APIs, persistent schemas/formats, external contracts, security boundaries, and irreversible workflows.
