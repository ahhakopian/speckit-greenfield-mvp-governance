
## Mandatory Greenfield MVP Clarification Addendum

When an ambiguity or edge case is discovered, do **not** begin by asking how the system should support it. First determine whether the scenario belongs to the supported MVP domain.

Use this order for each material ambiguity:

1. Is it security-, privacy-, data-loss-, money-, irreversible-action-, or state-corruption-critical? If yes, clarify the safe behavior and mark **Handle**.
2. Is it reasonably expected in normal MVP usage? If yes, clarify the minimum acceptable behavior and mark **Handle**.
3. Can it be detected and rejected safely? If yes, prefer **Reject** to adding a generalized architecture.
4. Otherwise, if no current requirement demands it, mark **Defer**.

Update `## MVP Behavior Boundary` and `## Edge Case Disposition` in `spec.md` when clarification changes scope.

Clarification MUST NOT expand the feature merely because a possible scenario exists. If the user has not requested a future variant, do not create one on their behalf.

When choosing among equally valid clarifications, prefer the option with the smaller supported state space and fewer new architectural obligations, unless that would weaken a current acceptance criterion or safety requirement.
