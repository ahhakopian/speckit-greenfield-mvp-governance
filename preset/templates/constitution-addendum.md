
## MVP Simplicity and Evidence-Driven Architecture

For greenfield MVP work, simplicity is a governing constraint rather than a stylistic preference.

1. **Current evidence only**. Architecture and implementation MUST be justified by a current requirement, a current technical constraint, or a mandatory safety/integrity concern. Hypothetical future requirements MUST NOT justify present complexity.
2. **Supported scope is explicit**. The specification MUST distinguish supported behavior, handled failures, explicitly unsupported behavior, and deferred behavior. Discovering an edge case does not automatically make it supported scope.
3. **Disposition before design**. Edge cases MUST be classified as **Handle**, **Reject**, or **Defer** before implementation behavior is designed. Security, privacy, data-loss, irreversible-action, and state-corruption risks MUST be handled even when rare.
4. **Prefer rejection to generalization**. For non-critical behavior outside MVP scope, explicit validation and an actionable failure are preferred to generic accommodation, heuristic recovery, compatibility machinery, or fallback trees.
5. **No speculative abstractions**. An abstraction, extension point, interface, factory, registry, strategy, plugin system, generic framework, compatibility layer, configuration surface, background worker, cache, queue, retry system, or additional persistent state MUST have a current consumer and current evidence that a simpler direct design is insufficient.
6. **Duplication can be cheaper than a wrong abstraction**. Small local duplication MAY be retained when the common abstraction is not yet demonstrated by multiple real cases.
7. **Minimize state space and indirection**. Prefer fewer states, fewer layers, fewer configuration knobs, and direct control flow. Reversible internal decisions SHOULD optimize for simplicity; hard-to-reverse external contracts, persistent data formats, security boundaries, and public APIs SHOULD optimize for correctness.
8. **Simplify after implementation**. Completed implementation MUST be reviewed for accidental complexity. Behavior required by the specification, safety constraints, and data-integrity guarantees MUST NOT be removed merely to reduce code size.

When a simplicity rule conflicts with an explicit current requirement or mandatory safety requirement, the requirement wins, but the exception MUST be documented with its evidence.
