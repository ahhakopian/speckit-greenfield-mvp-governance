# Verification governance regression checks

Run the dependency-free artifact contract checks from the repository root:

```bash
python3 -m unittest discover -s tests -v
```

These checks validate command/hook wiring, append composition, planning structures,
blocking-policy consistency, fixture references, the single read-only Codex role,
independent dispatch/return/remediation contracts, and bootstrap provisioning.
They do not implement a second
semantic guard or claim to execute an LLM review.

`fixtures/verification-complexity.json` contains seven independent semantic cases.
For each case, append its spec/plan/tasks text to the common artifacts and apply the
existing preflight command through `mvp-simplicity-controller`. For simplify,
use the same controller role, mark the task complete, and use its
`implemented_verification` description as the changed verification asset. These
descriptions stand in for implementation diffs; no browser or feature repository
is needed to evaluate governance proportionality. Compare the review with
`expected`, including the protected claim, disposition, rule IDs, severity, and gate
result. `rules` applies to both gates; `additional_simplify_rules`, when present,
captures a distinction between planned and already implemented lower proof. Treat
expected answers as the review oracle, not justification input.

Both gates should KEEP native context-menu and actual MV3 restart proof; DOWNLEVEL
consumed replay and callback ordering; MERGE expensive stale-target variants into
one representative browser case plus exhaustive deterministic proof; and SIMPLIFY
permission evidence while retaining its real-browser boundary. The composite
T012-style pattern must BLOCK with HIGH findings. A semantic fixture review checks
the reasoning, while the automated checks guard the artifact contracts; neither
establishes consistency across all future model executions.
