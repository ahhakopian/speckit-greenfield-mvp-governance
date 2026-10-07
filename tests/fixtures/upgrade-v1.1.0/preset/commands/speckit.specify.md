
## Mandatory Greenfield MVP Simplicity Addendum

Apply these instructions throughout specification work. They narrow generic "be comprehensive" behavior when comprehensiveness would expand MVP scope.

### 1. Define the MVP behavior boundary

Ensure `spec.md` contains a section named `## MVP Behavior Boundary` with these subsections:

- `### Supported` — behavior that the MVP intentionally promises.
- `### Handled Failures` — failures that remain inside the supported domain and require safe/minimal handling.
- `### Explicitly Unsupported` — inputs or scenarios the MVP intentionally rejects with a clear error or boundary message.
- `### Deferred` — scenarios acknowledged but intentionally not implemented in this feature/MVP.

Do not turn `Explicitly Unsupported` or `Deferred` scenarios into implementation requirements except for the minimal validation/error behavior needed to reject an unsupported scenario safely.

### 2. Classify edge cases before specifying solutions

For material edge cases, add or update an `## Edge Case Disposition` table:

| Edge case | Impact | Likelihood | Disposition | Evidence / rationale |
|---|---|---|---|---|
| ... | ... | ... | Handle / Reject / Defer | ... |

Use this decision order:

1. Security, privacy, data loss, irreversible action, money movement, or state corruption risk -> **Handle**.
2. Expected during normal MVP use -> **Handle**, using the smallest behavior that satisfies the requirement.
3. Non-critical and outside normal MVP use, but detectable -> **Reject** explicitly.
4. Non-critical, rare, and not required by current acceptance criteria -> **Defer**.

### 3. Do not create future requirements

Do not add requirements whose sole justification is language such as "might", "could", "future", "eventually", "for extensibility", "future-proof", or "in case we later...".

A discovered possibility is not a requirement. Record it under `Deferred` when it is useful to preserve the decision.

### 4. Keep acceptance criteria aligned with scope

Acceptance criteria MUST test the supported path, critical/safety failure behavior, and explicit rejection boundaries. They MUST NOT silently require generalized support for deferred scenarios.
