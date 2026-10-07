"""Attributable in-place updates for this package's existing Spec Kit installation.

No Spec Kit installer/resolver is called. YAML source marks let us edit individual
registry/hook values without serializing other entries or changing hook order.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


class UpgradeConflict(ValueError):
    pass


def upgrade_project(project: Path, source: Path, codex: bool = True) -> list[Path]:
    try:
        import yaml
    except ImportError as exc:
        raise UpgradeConflict("safe upgrade requires PyYAML; use a Python environment with Spec Kit's dependencies") from exc

    writes: dict[Path, str] = {}
    originals: dict[Path, str | None] = {}

    def guard(path: Path) -> None:
        # Never follow project symlinks (including symlinked parent directories).
        for parent in (path, *path.parents):
            if parent == project.parent:
                break
            if parent.is_symlink():
                raise UpgradeConflict(f"symlink prevents attributable upgrade: {path}")

    def read(path: Path) -> str:
        guard(path)
        text = path.read_bytes().decode("utf-8")
        # Keep the first snapshot used to derive or validate a replacement.
        originals.setdefault(path, text)
        return text

    def stage(path: Path, text: str) -> None:
        guard(path)
        if path not in originals:
            originals[path] = read(path) if path.exists() else None
        before = originals[path]
        if text != before:
            writes[path] = text

    def document(text: str):
        try:
            if any(isinstance(token, (yaml.AliasToken, yaml.AnchorToken)) for token in yaml.scan(text)):
                raise UpgradeConflict("YAML aliases/anchors make surgical ownership ambiguous")
            node = yaml.compose(text)
        except yaml.YAMLError as exc:
            raise UpgradeConflict(f"invalid YAML ownership metadata: {exc}") from exc

        def validate(n):
            if isinstance(n, yaml.MappingNode):
                keys = [k.value for k, _ in n.value]
                if len(keys) != len(set(keys)):
                    raise UpgradeConflict("duplicate mapping keys make ownership ambiguous")
                for _, v in n.value:
                    validate(v)
            elif isinstance(n, yaml.SequenceNode):
                for v in n.value:
                    validate(v)
        validate(node)
        return node

    def load(text):
        document(text)
        try:
            return yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise UpgradeConflict(f"invalid YAML ownership metadata: {exc}") from exc

    def child(node, key):
        if not isinstance(node, yaml.MappingNode):
            raise UpgradeConflict(f"expected mapping containing {key}")
        matches = [v for k, v in node.value if k.value == key]
        if len(matches) != 1:
            raise UpgradeConflict(f"missing or ambiguous ownership field: {key}")
        return matches[0]

    def patch_scalars(text, edits):
        for node, value in sorted(edits, key=lambda item: item[0].start_mark.index, reverse=True):
            if not isinstance(node, yaml.ScalarNode):
                raise UpgradeConflict("expected scalar metadata value")
            text = text[:node.start_mark.index] + json.dumps(value, ensure_ascii=False) + text[node.end_mark.index:]
        return text

    def body(text):
        if text.startswith("---\n"):
            end = re.search(r"^---\s*$", text[4:], re.MULTILINE)
            if not end:
                raise UpgradeConflict("unclosed command frontmatter")
            return text[4 + end.end():].strip()
        return text.strip()

    contributions = []
    registered_names = set()
    manifests = {}
    for kind, component in (("preset", "greenfield-mvp-simplicity"), ("extension", "mvp-complexity-guard")):
        plural = kind + "s"
        installed = project / ".specify" / plural / component
        manifest = f"{kind}.yml"
        old_text = read(installed / manifest)
        new_text = (source / kind / manifest).read_text(encoding="utf-8")
        old = load(old_text)
        new = load(new_text)
        if old[kind]["id"] != component or new[kind]["id"] != component:
            raise UpgradeConflict(f"unexpected {kind} identity")
        registry = project / ".specify" / plural / ".registry"
        registry_text = read(registry)
        entry_node = child(child(document(registry_text), plural), component)
        entry = json.loads(registry_text)[plural][component]
        if entry["version"] != old[kind]["version"] or entry["manifest_hash"] != "sha256:" + hashlib.sha256(old_text.encode()).hexdigest():
            raise UpgradeConflict(f"installed manifest does not match registry: {component}")
        for field in ("registered_commands", "registered_skills"):
            registrations = entry.get(field, {})
            if isinstance(registrations, dict) and any(agent != "codex" and names for agent, names in registrations.items()):
                raise UpgradeConflict("safe upgrade currently supports Codex outputs only; other registered integrations require reconciliation")
            names = registrations.get("codex", []) if isinstance(registrations, dict) else registrations
            if not isinstance(names, list) or any(not isinstance(name, str) for name in names):
                raise UpgradeConflict(f"invalid {field} ownership metadata: {component}")
            registered_names.update(names)
        # This updater supports the existing append preset and two guard commands.
        # A future change in composition topology needs explicit migration support.
        old_provides = old["provides"]
        if old_provides != new["provides"]:
            raise UpgradeConflict(f"changed contribution topology is unsupported: {component}")
        records = old_provides["templates" if kind == "preset" else "commands"]
        files = [manifest]
        for record in records:
            relative = record["file"]
            if Path(relative).is_absolute() or ".." in Path(relative).parts:
                raise UpgradeConflict(f"unsafe contribution path: {relative}")
            files.append(relative)
            old_content = read(installed / relative)
            new_content = (source / kind / relative).read_text(encoding="utf-8")
            if kind == "preset" and record.get("strategy") != "append":
                raise UpgradeConflict("only attributable append contributions are supported")
            old_body, new_body = body(old_content), body(new_content)
            if not old_body or not new_body:
                raise UpgradeConflict(f"empty contribution: {relative}")
            contributions.append((record["name"], old_body, new_body))
        for relative in files:
            stage(installed / relative, (source / kind / relative).read_text(encoding="utf-8"))
        stage(registry, patch_scalars(registry_text, [
            (child(entry_node, "version"), new[kind]["version"]),
            (child(entry_node, "manifest_hash"), "sha256:" + hashlib.sha256(new_text.encode()).hexdigest()),
        ]))
        manifests[kind] = (old, new, installed)

    # Restrict discovery to generated command/skill/cache surfaces, never workflow,
    # memory, project artifacts, implementation files, or arbitrary Markdown.
    candidates = set()
    for root in (project / ".codex/prompts", project / ".codex/skills", project / ".agents/skills"):
        if root.exists():
            candidates.update(root.rglob("*.md"))
    for cache in (project / ".specify/presets").glob("**/.composed"):
        candidates.update(cache.glob("*.md"))
    templates = project / ".specify/templates/constitution-template.md"
    if templates.exists():
        candidates.add(templates)
    seen = set()
    found_names = set()
    for path in sorted(candidates):
        text = read(path)
        updated = text
        for name, old_body, new_body in contributions:
            marker = old_body.splitlines()[0]
            expected_name = name.replace(".", "-")
            named = name.startswith("speckit.") and (path.stem in {name, name + ".prompt"} or (path.name == "SKILL.md" and path.parent.name in {name, expected_name}))
            if marker not in updated and not named:
                continue
            if updated.count(marker) != 1 or updated.count(old_body) != 1:
                raise UpgradeConflict(f"missing, modified, or duplicate {name} contribution in {path}")
            updated = updated.replace(old_body, new_body, 1)
            seen.add(name)
            found_names.add(name)
            if named:
                found_names.add(path.parent.name if path.name == "SKILL.md" else path.stem)
        stage(path, updated)
    if registered_names - found_names:
        raise UpgradeConflict(f"registered outputs missing: {sorted(registered_names - found_names)}")
    for name, _, _ in contributions:
        if name.startswith("speckit.") and name not in seen:
            raise UpgradeConflict(f"no attributable generated output found for {name}")

    # Patch only changed manifest-owned fields in this extension's hook entries.
    # Preserve enabled flags, local configuration, comments, and list ordering.
    old, new, installed = manifests["extension"]
    hooks_path = project / ".specify/extensions.yml"
    hooks_text = read(hooks_path)
    hooks_node = child(document(hooks_text), "hooks")
    hook_data = load(hooks_text)["hooks"]
    if old["hooks"].keys() != new["hooks"].keys():
        raise UpgradeConflict("hook event topology changed; explicit migration required")
    edits = []
    for event, old_hook in old["hooks"].items():
        sequence = child(hooks_node, event)
        if not isinstance(sequence, yaml.SequenceNode):
            raise UpgradeConflict(f"ambiguous hook list: {event}")
        matches = [(i, h) for i, h in enumerate(hook_data[event]) if isinstance(h, dict) and h.get("extension") == "mvp-complexity-guard"]
        if len(matches) != 1 or matches[0][1].get("command") != old_hook["command"]:
            raise UpgradeConflict(f"missing or ambiguous MVP hook: {event}")
        index, existing = matches[0]
        new_hook = new["hooks"][event]
        if old_hook.keys() != new_hook.keys():
            raise UpgradeConflict(f"hook field topology changed: {event}")
        for key, value in new_hook.items():
            if old_hook[key] != value:
                if existing.get(key) != old_hook[key]:
                    raise UpgradeConflict(f"locally modified MVP hook field: {event}.{key}")
                edits.append((child(sequence.value[index], key), value))
    stage(hooks_path, patch_scalars(hooks_text, edits))

    if codex:
        for agent in (source / "extension/agents").glob("*.toml"):
            target = project / ".codex/agents" / agent.name
            old_agent = installed / "agents" / agent.name
            new_agent = agent.read_text(encoding="utf-8")
            if target.exists() and read(target) != new_agent:
                if not old_agent.exists() or read(target) != read(old_agent):
                    raise UpgradeConflict(f"locally modified or unattributed Codex agent: {target}")
            stage(target, new_agent)
            stage(old_agent, new_agent)

    # All ownership/content checks finish before the first write. Check for races,
    # and roll back our writes if an I/O failure interrupts the commit.
    for path, before in originals.items():
        if (read(path) if path.exists() else None) != before:
            raise UpgradeConflict(f"file changed during upgrade: {path}")
    committed = []
    try:
        for path, text in writes.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            committed.append(path)
            path.write_bytes(text.encode("utf-8"))
    except OSError as commit_error:
        restoration_failures = []
        for path in reversed(committed):
            before = originals[path]
            try:
                if before is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_bytes(before.encode("utf-8"))
            except OSError as exc:
                restoration_failures.append(f"{path}: {exc}")
        if restoration_failures:
            raise UpgradeConflict(
                f"upgrade commit failed: {commit_error}; restoration failed for: "
                + "; ".join(restoration_failures)
            ) from commit_error
        raise
    return list(writes)
