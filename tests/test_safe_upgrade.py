"""Closed-scope regression for the actual v1.1.0 -> current contribution delta."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "tests/fixtures/upgrade-v1.1.0"


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "bootstrap" / filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


UPGRADE = module("safe_upgrade", "safe_upgrade.py")
BOOTSTRAP = module("specify_mvp", "specify-mvp.py")


def snapshot(project):
    return {str(p.relative_to(project)): p.read_bytes() for p in project.rglob("*") if p.is_file()}


def put(project, name, text):
    path = project / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def body(text):
    if text.startswith("---\n"):
        return text.split("---", 2)[2].strip()
    return text.strip()


class SafeUpgradeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        p = self.project
        self.contributions = {}
        self.unrelated_registry = '"other-overlay": {"version":"9", "local": [3, 1, 2]}'
        for kind, component in (("preset", BOOTSTRAP.PRESET_ID), ("extension", BOOTSTRAP.EXTENSION_ID)):
            plural = kind + "s"
            target = p / ".specify" / plural / component
            shutil.copytree(OLD / kind, target)
            manifest_path = OLD / kind / f"{kind}.yml"
            manifest = yaml.safe_load(manifest_path.read_text())
            records = manifest["provides"]["templates" if kind == "preset" else "commands"]
            names = []
            for record in records:
                name = record["name"]
                text = body((OLD / kind / record["file"]).read_text())
                self.contributions[name] = (kind, record["file"], text)
                if not name.startswith("speckit."):
                    continue
                names.append(name)
                # A foreign overlay owns the composed cache; its surrounding
                # contributions and locally changed shared content must survive.
                composed = "---\ndescription: Local description\n---\n\n# Core locally edited\n\n" + text + "\n\n# Other overlay\nkeep exact spaces  \n"
                put(p, f".specify/presets/other-overlay/.composed/{name}.md", composed)
                put(p, f".codex/prompts/{name}.md", composed)
                put(p, f".agents/skills/{name.replace('.', '-')}/SKILL.md", "---\nname: local\nmetadata:\n  source: preset:other-overlay\n---\n\n# Skill\n\n" + composed)
            entry = {"version": "1.1.0", "manifest_hash": "sha256:" + hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                     "priority": 17, "enabled": True, "installed_at": "keep", "registered_commands": {"codex": names}, "registered_skills": {"codex": [n.replace('.', '-') for n in names]}}
            put(p, f".specify/{plural}/.registry", '{\n "schema_version": "1.0", "' + plural + '": {\n  ' + self.unrelated_registry + ',\n  "' + component + '": ' + json.dumps(entry) + '\n }\n}\n')
        hooks = yaml.safe_load((OLD / "extension/extension.yml").read_text())["hooks"]
        config = "# retain this comment and list order\ninstalled: [other-overlay, mvp-complexity-guard]\nhooks:\n"
        for event, hook in hooks.items():
            entries = [{"extension": "other-overlay", "command": "first", "enabled": False},
                       {"extension": BOOTSTRAP.EXTENSION_ID, "enabled": False, **hook},
                       {"extension": "another-overlay", "command": "last", "custom": "keep"}]
            config += yaml.safe_dump({event: entries}, sort_keys=False).replace('\n', '\n  ').join(['  ', '']).rstrip() + '\n'
        put(p, ".specify/extensions.yml", config)
        put(p, ".specify/init-options.json", '{"ai":"codex"}')
        for name in (".specify/memory/constitution.md", ".specify/workflow/runs/run.json", "specs/001/spec.md", "src/main.py", "approvals/approved.json", ".codex/config.toml", ".codex/agents/other.toml", ".agents/skills/unrelated/SKILL.md", ".specify/extensions/other-overlay/local-config.yml", ".specify/presets/greenfield-mvp-simplicity/local-notes.md"):
            put(p, name, "existing local/project state  \n" + name + "\n")
        self.before = snapshot(p)

    def test_upgrade_preserves_everything_except_attributable_delta(self):
        changed = UPGRADE.upgrade_project(self.project, ROOT)
        after = snapshot(self.project)
        self.assertTrue(changed)
        for relative, before in self.before.items():
            path = self.project / relative
            if "/.composed/" in relative or relative.startswith((".codex/prompts/", ".agents/skills/speckit-")):
                expected = before.decode()
                for name, (kind, filename, old) in self.contributions.items():
                    new = body((ROOT / kind / filename).read_text())
                    expected = expected.replace(old, new)
                self.assertEqual(after[relative], expected.encode(), relative)
            elif relative.endswith("/.registry"):
                text = after[relative].decode()
                self.assertIn(self.unrelated_registry, text)
                plural = "presets" if "/presets/" in relative else "extensions"
                component = BOOTSTRAP.PRESET_ID if plural == "presets" else BOOTSTRAP.EXTENSION_ID
                kind = plural[:-1]
                original = json.loads(before)[plural][component]
                actual = json.loads(text)[plural][component]
                expected = dict(original, version=yaml.safe_load((ROOT / kind / f"{kind}.yml").read_text())[kind]["version"], manifest_hash="sha256:" + hashlib.sha256((ROOT / kind / f"{kind}.yml").read_bytes()).hexdigest())
                self.assertEqual(actual, expected)
            elif relative == ".specify/extensions.yml":
                previous = yaml.safe_load(before)
                current = yaml.safe_load(after[relative])
                self.assertTrue(after[relative].startswith(b"# retain this comment"))
                new_hooks = yaml.safe_load((ROOT / "extension/extension.yml").read_text())["hooks"]
                for event, entries in current["hooks"].items():
                    self.assertEqual(entries[0], previous["hooks"][event][0])
                    self.assertEqual(entries[2], previous["hooks"][event][2])
                    self.assertFalse(entries[1]["enabled"])
                    self.assertEqual(entries[1]["description"], new_hooks[event]["description"])
            else:
                source = None
                for kind, component in (("preset", BOOTSTRAP.PRESET_ID), ("extension", BOOTSTRAP.EXTENSION_ID)):
                    prefix = f".specify/{kind}s/{component}/"
                    if relative.startswith(prefix) and (ROOT / kind / relative[len(prefix):]).is_file():
                        source = ROOT / kind / relative[len(prefix):]
                self.assertEqual(after[relative], source.read_bytes() if source else before, relative)
        agent = "extension/agents/mvp-simplicity-controller.toml"
        self.assertEqual(after[".codex/agents/mvp-simplicity-controller.toml"], (ROOT / agent).read_bytes())
        self.assertEqual(UPGRADE.upgrade_project(self.project, ROOT), [])
        self.assertEqual(snapshot(self.project), after)

    def test_codex_skill_only_registration_layout(self):
        # Spec Kit 0.16.2 records dotted guard command IDs while writing
        # hyphenated Codex skill directories, without a prompt mirror.
        shutil.rmtree(self.project / ".codex/prompts")
        cache = self.project / ".specify/presets/other-overlay/.composed"
        for path in cache.glob("speckit.mvp-complexity-guard.*.md"):
            path.unlink()
        registry = self.project / ".specify/extensions/.registry"
        data = json.loads(registry.read_text())
        data["extensions"][BOOTSTRAP.EXTENSION_ID]["registered_skills"] = []
        registry.write_text(json.dumps(data))
        put(self.project, ".specify/templates/constitution-template.md", "# Uncomposed core template\n")
        UPGRADE.upgrade_project(self.project, ROOT)
        self.assertIn("## Independent execution", (self.project / ".agents/skills/speckit-mvp-complexity-guard-preflight/SKILL.md").read_text())
        self.assertEqual((self.project / ".specify/templates/constitution-template.md").read_text(), "# Uncomposed core template\n")

    def test_shared_conflicts_stop_before_any_write(self):
        name = "speckit.plan"
        path = self.project / f".agents/skills/{name.replace('.', '-')}/SKILL.md"
        original = path.read_text()
        old = self.contributions[name][2]
        for conflicting in (original.replace("### 1. Add a Complexity Budget", "### 1. Local edits"), original + '\n' + old):
            with self.subTest(conflicting=conflicting[-50:]):
                path.write_text(conflicting)
                before = snapshot(self.project)
                with self.assertRaisesRegex(UPGRADE.UpgradeConflict, "modified, or duplicate"):
                    UPGRADE.upgrade_project(self.project, ROOT)
                self.assertEqual(snapshot(self.project), before)
        path.write_text(original)

    def test_registry_mismatch_stops_before_any_write(self):
        path = self.project / ".specify/extensions/.registry"
        path.write_text(path.read_text().replace('"version": "1.1.0"', '"version": "0.0.0"'))
        before = snapshot(self.project)
        with self.assertRaisesRegex(UPGRADE.UpgradeConflict, "does not match registry"):
            UPGRADE.upgrade_project(self.project, ROOT)
        self.assertEqual(snapshot(self.project), before)

    def test_rollback_continues_after_restoration_failure(self):
        first = self.project / ".specify/presets/greenfield-mvp-simplicity/preset.yml"
        second = self.project / ".specify/presets/greenfield-mvp-simplicity/commands/speckit.specify.md"
        write_bytes = Path.write_bytes
        for fail_first_restore in (False, True):
            with self.subTest(fail_first_restore=fail_first_restore):
                for relative, content in self.before.items():
                    write_bytes(self.project / relative, content)
                attempts = []

                def failing_write(path, content):
                    attempts.append(path)
                    if path == second:
                        write_bytes(path, content[:20])
                        raise PermissionError("second file remains unwritable")
                    if path == first and fail_first_restore and attempts.count(first) > 1:
                        raise PermissionError("first file cannot be restored")
                    return write_bytes(path, content)

                with patch.object(Path, "write_bytes", failing_write):
                    with self.assertRaisesRegex(UPGRADE.UpgradeConflict, "restoration failed for") as raised:
                        UPGRADE.upgrade_project(self.project, ROOT)
                self.assertEqual(attempts, [first, second, second, first])
                self.assertIn(str(second), str(raised.exception))
                self.assertIsInstance(raised.exception.__cause__, PermissionError)
                if fail_first_restore:
                    self.assertIn(str(first), str(raised.exception))
                else:
                    expected = dict(self.before)
                    relative = str(second.relative_to(self.project))
                    expected[relative] = self.before[relative][:20]
                    self.assertEqual(snapshot(self.project), expected)

    def test_intervening_shared_edit_stops_before_any_write(self):
        path = self.project / ".codex/prompts/speckit.plan.md"
        relative = str(path.relative_to(self.project))
        edited = self.before[relative] + b"\n# Unrelated concurrent local edit\n"
        read_bytes, write_bytes = Path.read_bytes, Path.write_bytes
        injected = False

        def concurrent_read(candidate):
            nonlocal injected
            content = read_bytes(candidate)
            if candidate == path and not injected:
                # The replacement derives from content returned before this edit.
                write_bytes(path, edited)
                injected = True
            return content

        with patch.object(Path, "read_bytes", concurrent_read), patch.object(Path, "write_bytes") as writes:
            with self.assertRaisesRegex(UPGRADE.UpgradeConflict, "file changed during upgrade"):
                UPGRADE.upgrade_project(self.project, ROOT)
            writes.assert_not_called()
        self.assertTrue(injected)
        expected = dict(self.before)
        expected[relative] = edited
        self.assertEqual(snapshot(self.project), expected)

    def test_unrelated_filename_cannot_mask_missing_registered_skill(self):
        (self.project / ".agents/skills/speckit-plan/SKILL.md").unlink()
        put(self.project, ".agents/skills/unrelated/speckit-plan.md", "# Unrelated local notes\n")
        before = snapshot(self.project)
        with patch.object(Path, "write_bytes") as writes:
            with self.assertRaisesRegex(UPGRADE.UpgradeConflict, "registered outputs missing:.*speckit-plan"):
                UPGRADE.upgrade_project(self.project, ROOT)
            writes.assert_not_called()
        self.assertEqual(snapshot(self.project), before)

    def test_owned_controller_updates_but_local_controller_conflicts(self):
        installed = ".specify/extensions/mvp-complexity-guard/agents/mvp-simplicity-controller.toml"
        target = ".codex/agents/mvp-simplicity-controller.toml"
        put(self.project, installed, 'name = "mvp-simplicity-controller"\n# older definition\n')
        put(self.project, target, 'name = "mvp-simplicity-controller"\n# local definition\n')
        before = snapshot(self.project)
        with self.assertRaisesRegex(UPGRADE.UpgradeConflict, "unattributed Codex agent"):
            UPGRADE.upgrade_project(self.project, ROOT)
        self.assertEqual(snapshot(self.project), before)
        (self.project / target).write_bytes((self.project / installed).read_bytes())
        UPGRADE.upgrade_project(self.project, ROOT)
        self.assertEqual((self.project / target).read_bytes(), (ROOT / "extension/agents/mvp-simplicity-controller.toml").read_bytes())

    def test_local_command_line_never_calls_installer(self):
        with patch.object(BOOTSTRAP, "run", side_effect=AssertionError("no reinstall")), patch.object(BOOTSTRAP, "sync_source", side_effect=AssertionError("no sync")):
            BOOTSTRAP.cmd_upgrade_project([str(self.project), "--source", str(ROOT)])
        self.assertEqual(json.loads((self.project / ".specify/presets/.registry").read_text())["presets"][BOOTSTRAP.PRESET_ID]["version"], "1.2.1")

    def test_ensure_routes_installed_project_to_safe_upgrade(self):
        with patch.object(BOOTSTRAP, "require_tool"), patch.object(BOOTSTRAP, "load_config", return_value={}), patch.object(BOOTSTRAP, "validate_source"), patch.object(BOOTSTRAP, "safe_upgrade") as upgrade, patch.object(BOOTSTRAP, "verify_project"), patch.object(BOOTSTRAP, "install_missing_components", side_effect=AssertionError("no reinstall")):
            BOOTSTRAP.cmd_ensure_project([str(self.project), "--no-sync"])
            upgrade.assert_called_once_with(self.project, BOOTSTRAP.SOURCE_DIR)

    def test_partial_registry_installation_cannot_fall_back_to_install(self):
        shutil.rmtree(self.project / ".specify/presets/greenfield-mvp-simplicity")
        shutil.rmtree(self.project / ".specify/extensions/mvp-complexity-guard")
        with patch.object(BOOTSTRAP, "require_tool"), patch.object(BOOTSTRAP, "load_config", return_value={}), patch.object(BOOTSTRAP, "validate_source"), patch.object(BOOTSTRAP, "safe_upgrade") as upgrade, patch.object(BOOTSTRAP, "verify_project"), patch.object(BOOTSTRAP, "install_missing_components", side_effect=AssertionError("no reinstall")):
            BOOTSTRAP.cmd_ensure_project([str(self.project), "--no-sync"])
            upgrade.assert_called_once()

    def test_first_installation_keeps_normal_installer(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / ".specify").mkdir()
            with patch.object(BOOTSTRAP, "require_tool"), patch.object(BOOTSTRAP, "load_config", return_value={}), patch.object(BOOTSTRAP, "validate_source"), patch.object(BOOTSTRAP, "safe_upgrade", side_effect=AssertionError("no upgrade")), patch.object(BOOTSTRAP, "verify_project"), patch.object(BOOTSTRAP, "install_missing_components") as install:
                BOOTSTRAP.cmd_ensure_project([str(project), "--no-sync"])
                install.assert_called_once_with(project, BOOTSTRAP.DEFAULT_PRIORITY, False)

    def test_init_refuses_to_reinitialize_composed_project(self):
        with patch.object(BOOTSTRAP, "require_tool"), patch.object(BOOTSTRAP, "load_config", return_value={}), patch.object(BOOTSTRAP, "sync_source"), patch.object(BOOTSTRAP, "infer_project_root", return_value=self.project), patch.object(BOOTSTRAP, "run", side_effect=AssertionError("no reinitialization")):
            with self.assertRaises(SystemExit):
                BOOTSTRAP.cmd_init(["--here", "--force"])


if __name__ == "__main__":
    unittest.main()
