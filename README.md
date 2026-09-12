# Greenfield MVP Governance for Spec Kit

Two deliberately small components:

- `preset/` — **greenfield-mvp-simplicity**: augments the core Spec Kit workflow so edge cases are classified before design and architecture must stay evidence-driven.
- `extension/` — **mvp-complexity-guard**: mandatory semantic gates immediately before and after implementation.

## What the preset changes

It composes with the existing Spec Kit commands instead of copying/replacing them:

- `speckit.specify` — adds Supported / Handled Failures / Explicitly Unsupported / Deferred and Handle / Reject / Defer disposition.
- `speckit.clarify` — asks whether an edge case belongs to the MVP before asking how to support it.
- `speckit.plan` — adds Complexity Budget and Architecture Justification.
- `speckit.tasks` — requires current evidence for tasks and prevents deferred scenarios from becoming implementation work.
- `constitution-template` — appends MVP simplicity and evidence-driven architecture principles when the constitution template is resolved.

The preset uses `strategy: append`, so upstream core command updates remain intact.

## What the extension changes

Two mandatory hooks:

- `before_implement` -> `speckit.mvp-complexity-guard.preflight`
- `after_implement` -> `speckit.mvp-complexity-guard.simplify`

Both reviews are read-only. A CRITICAL/HIGH finding returns `MVP_COMPLEXITY_GUARD: BLOCK`.

Two command entrypoints are used intentionally. Current Spec Kit hook manifests reference a command identifier; they do not provide a hook-command argument slot for a `mode=pre|post` parameter. Separate entrypoints make hook behavior deterministic while keeping one extension and one policy.

## Local installation

Run from an already initialized Spec Kit project:

```bash
specify preset add --dev /absolute/path/to/greenfield-mvp-governance/preset --priority 10
specify extension add --dev /absolute/path/to/greenfield-mvp-governance/extension --priority 10
```

Verify:

```bash
specify preset list
specify preset info greenfield-mvp-simplicity
specify extension list
```

For preset resolution debugging:

```bash
specify preset resolve constitution-template
```

## Recommended greenfield workflow

```text
/speckit.constitution
/speckit.specify
/speckit.clarify
/speckit.plan
/speckit.checklist
/speckit.tasks
/speckit.analyze
/speckit.implement
/speckit.converge
```

The preflight guard is invoked automatically by `speckit.implement` before code execution. The simplification guard is invoked automatically after implementation and before completion reporting.

## Existing constitution caveat

Spec Kit preserves an already-authored live constitution. Installing a preset does not silently rewrite authored constitutional policy. For an existing project, run `/speckit.constitution` and merge the `MVP Simplicity and Evidence-Driven Architecture` principle deliberately, or keep the policy enforced at the command/guard level only.

For a new greenfield project, install the preset before creating/finalizing the constitution so the composed constitution template contains the addendum.

## Publishing metadata

The manifests intentionally use placeholder repository URLs under `github.com/example/...` because a valid URL field is required by the manifest schema. Replace `author` and `repository` with your real values before publishing. Local `--dev` installation does not require the placeholder repository to exist.

## Design constraints

This package deliberately does **not** add:

- another orchestration framework;
- an automatic code-rewriter;
- language-specific complexity thresholds;
- extra hooks for every Spec Kit phase;
- speculative architecture scoring.

The preset constrains decisions before code. The extension performs semantic gates around implementation. Deterministic lint/type/test/architecture checks should remain in your normal `make check` / CI workflow.

---

## Automatic GitHub-backed installation for every new repository

Version 1.1.0 adds the same global-bootstrap pattern used by the Feature Governance setup. You configure the GitHub source once; afterwards use `specify-mvp init` instead of bare `specify init` for greenfield MVP repositories.

### One-time machine setup

After this package has been pushed to your GitHub repository:

```bash
cd /path/to/your/clone
python3 bootstrap/specify-mvp.py install-global \
  --repo https://github.com/<YOUR_GITHUB>/<YOUR_REPO>.git \
  --ref main
```

This creates:

```text
~/.config/speckit-greenfield-mvp-governance/
├── config.json
└── source/          # managed Git checkout of your GitHub repository

~/.local/bin/specify-mvp
```

The source checkout is a machine-managed cache. `specify-mvp init` runs `git fetch` and resets it to the configured Git ref before initializing a project, so new repositories automatically receive the current governance package from GitHub.

### Initialize a new greenfield MVP repository

Instead of:

```bash
specify init --here --integration codex
```

use:

```bash
specify-mvp init --here --integration codex
```

For an existing non-empty repository:

```bash
specify-mvp init --here --force --integration codex
```

Or create a new directory:

```bash
specify-mvp init my-new-mvp --integration codex
```

The wrapper performs this sequence automatically:

```text
GitHub repository
      ↓ sync
~/.config/speckit-greenfield-mvp-governance/source
      ↓
specify init
      ├─ installs mvp-complexity-guard during init when supported
      └─ initializes normal Spec Kit project
      ↓
installs greenfield-mvp-simplicity preset
      ↓
verifies fresh-project constitution contains MVP simplicity policy
      ↓
verifies preset + extension are enabled
```

Spec Kit 0.16.2 already supports repeatable `--extension` during `specify init` for bundled names, catalog IDs, local directories, and HTTPS URLs. The preset init option accepts a preset ID rather than a local directory, so the bootstrap installs the locally synced preset immediately after init. For a freshly created project it then verifies the generated constitution and adds the MVP addendum only if Spec Kit has not already reconciled it.

### Commands

```bash
# Check the machine/global setup
specify-mvp doctor

# Pull the configured GitHub ref now
specify-mvp sync

# Add/verify governance in an already initialized Spec Kit project
specify-mvp ensure-project .

# Initialize a new governed project
specify-mvp init --here --force --integration codex
```

`ensure-project` does not rewrite an existing project's constitution. It installs missing components and fails verification if the project constitution does not contain the MVP policy; this keeps automatic mutation limited to genuinely fresh initialization.

### Updating all future projects

Push changes to the configured GitHub branch/ref. The next:

```bash
specify-mvp init ...
```

will sync that ref before project initialization. No manual preset/extension installation is required in the new repository.

If you intentionally pin the bootstrap to a release/tag instead of `main`, change the machine configuration by rerunning:

```bash
python3 bootstrap/specify-mvp.py install-global \
  --repo https://github.com/<YOUR_GITHUB>/<YOUR_REPO>.git \
  --ref v1.1.0
```
