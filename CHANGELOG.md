# Changelog

## 1.2.0 — 2026-10-07

- Added verification strategy as an independent MVP complexity surface, with lowest sufficient layer and incremental evidentiary value rules.
- Added a planning Verification Complexity Budget and compact Verification Justification; verification tasks follow the justified layer without duplicating expensive edge-case acceptance.
- Extended the existing mandatory preflight/simplify gates to block materially expensive or architecture-affecting verification complexity while preserving conclusive safety coverage.
- Clarified that acceptance criteria define required claims rather than the highest proof layer.
- Added verification regression fixtures and dependency-free governance contract checks; extension hooks and the existing Spec Kit compatibility range remain unchanged.

## 1.1.0 — 2026-09-12

- Added GitHub-backed global bootstrap at `bootstrap/specify-mvp.py`.
- Added one-time `install-global` setup that stores repository/ref under `~/.config/speckit-greenfield-mvp-governance/` and installs a `~/.local/bin/specify-mvp` launcher.
- Added `specify-mvp init`, which syncs governance from GitHub and automatically provisions the preset and extension into every new Spec Kit project.
- Uses native `specify init --extension <local-path>` when supported, with a post-init fallback for older compatible CLI releases.
- Guarantees the MVP simplicity constitution addendum for freshly initialized projects without rewriting constitutions in existing projects.
- Added `sync`, `doctor`, and `ensure-project` commands.

## 1.0.0 — 2026-09-12

- Initial `greenfield-mvp-simplicity` preset.
- Initial `mvp-complexity-guard` extension.
- Mandatory `before_implement` and `after_implement` semantic gates.
