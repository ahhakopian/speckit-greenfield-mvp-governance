"""Native agent and dispatch contracts; these do not execute an LLM review."""

import importlib.util
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from test_governance_contract import ROOT, read, section, table_rows


ROLE = "mvp-simplicity-controller"
AGENT = f"extension/agents/{ROLE}.toml"


class IndependentControllerContractTests(unittest.TestCase):
    def test_one_read_only_controller_reuses_the_existing_guard(self):
        self.assertEqual(list((ROOT / "extension/agents").glob("*.toml")), [ROOT / AGENT])
        agent = tomllib.loads(read(AGENT))
        self.assertEqual(agent["name"], ROLE)
        self.assertEqual(agent["sandbox_mode"], "read-only")
        self.assertTrue(agent["description"])
        instructions = agent["developer_instructions"]
        for command in ("preflight", "simplify"):
            self.assertIn(f"speckit.mvp-complexity-guard.{command}", instructions)
            self.assertIn(f".specify/extensions/mvp-complexity-guard/commands/{command}.md", instructions)
        self.assertIn("separate agent execution", instructions)
        self.assertIn("starting at Purpose", instructions)
        self.assertIn("Do not edit project artifacts, implement fixes, expand", instructions)
        self.assertIn("Remediation belongs to the original", instructions)
        self.assertIn("author/executor", instructions)
        self.assertIn("reread the", instructions)
        self.assertNotIn("V-01", instructions)
        self.assertNotIn("## Severity and blocking", instructions)

    def test_both_existing_commands_require_independent_dispatch_and_return(self):
        for command in ("preflight", "simplify"):
            with self.subTest(command=command):
                routing = section(read(f"extension/commands/{command}.md"), "## Independent execution")
                self.assertIn(f"`agent_type: {ROLE}`", routing)
                self.assertIn(f"`speckit.mvp-complexity-guard.{command}`", routing)
                self.assertIn("author/executor must not review its own output", routing)
                self.assertIn("do not perform the review below in the", routing)
                self.assertIn("Wait for the controller", routing)
                self.assertIn("complete output unchanged to the parent", routing)
                self.assertIn("remediation remains with the original", routing)
                self.assertIn("controller must not modify the reviewed artifacts", routing)
                self.assertIn("rerun this command through the same", routing)
                self.assertIn("never fall back to self-review", routing)
                for result in ("PASS", "BLOCK"):
                    self.assertIn(f"MVP_COMPLEXITY_GUARD: {result}", routing)

    def test_review_output_and_blocking_semantics_are_preserved(self):
        headers = {
            "preflight": ["ID", "Severity", "Location", "Complexity", "Current evidence", "Simpler alternative", "Disposition"],
            "simplify": ["ID", "Severity", "Location", "Unnecessary complexity", "Why it is not currently required", "Behavior-preserving simplification"],
        }
        for command, header in headers.items():
            with self.subTest(command=command):
                guard = read(f"extension/commands/{command}.md")
                output = guard.split("## Required output\n", 1)[1]
                self.assertEqual(table_rows(output)[0], header)
                self.assertIn("Result: MVP_COMPLEXITY_GUARD: PASS | BLOCK", output)
                severity = section(guard, "## Severity and blocking")
                self.assertRegex(severity, r"Return `BLOCK` when .*CRITICAL or HIGH")
                self.assertIn("MEDIUM/LOW findings", severity)

    def test_bootstrap_provisions_and_verifies_the_native_codex_role(self):
        spec = importlib.util.spec_from_file_location("specify_mvp", ROOT / "bootstrap/specify-mvp.py")
        bootstrap = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bootstrap)
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / ".specify/memory").mkdir(parents=True)
            (project / ".specify/init-options.json").write_text('{"ai": "codex"}', encoding="utf-8")
            (project / ".specify/memory/constitution.md").write_text(
                "## MVP Simplicity and Evidence-Driven Architecture\n", encoding="utf-8"
            )
            with patch.object(bootstrap, "SOURCE_DIR", ROOT), patch.object(
                bootstrap, "project_has_component", return_value=True
            ):
                bootstrap.install_missing_components(project, 10, False)
                target = project / f".codex/agents/{ROLE}.toml"
                self.assertEqual(target.read_text(encoding="utf-8"), read(AGENT))
                bootstrap.verify_project(project)
                bootstrap.install_missing_components(project, 10, False)
                self.assertEqual(target.read_text(encoding="utf-8"), read(AGENT))
                self.assertEqual(list((project / ".codex").iterdir()), [target.parent])


if __name__ == "__main__":
    unittest.main()
