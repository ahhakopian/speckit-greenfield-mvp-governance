"""Artifact contracts for the existing semantic gates; no semantic classifier."""

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def section(document, heading):
    match = re.search(
        rf"^{re.escape(heading)}\n(.*?)(?=^#{{1,{len(heading.split()[0])}}} |\Z)",
        document,
        re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"Missing section: {heading}")
    return match.group(1)


def table_rows(document):
    return [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in document.splitlines()
        if line.startswith("|") and not re.fullmatch(r"[| :\-]+", line)
    ]


class GovernanceContractTests(unittest.TestCase):
    def test_extension_preserves_mandatory_entrypoints_and_compatibility(self):
        manifest = read("extension/extension.yml")
        self.assertIn('  version: "1.2.1"', manifest)
        self.assertIn('  speckit_version: ">=0.16.0,<2.0.0"', manifest)
        commands = re.findall(
            r'    - name: "([^"]+)"\n      file: "([^"]+)"', manifest
        )
        expected = {
            "speckit.mvp-complexity-guard.preflight": "commands/preflight.md",
            "speckit.mvp-complexity-guard.simplify": "commands/simplify.md",
        }
        self.assertEqual(dict(commands), expected)
        self.assertEqual(len(commands), 2)
        hooks = re.search(r"^hooks:\n(.*?)(?=^\w|\Z)", manifest, re.MULTILINE | re.DOTALL).group(1)
        self.assertEqual(re.findall(r"^  (\w+):", hooks, re.MULTILINE), ["before_implement", "after_implement"])
        for hook, command in zip(("before_implement", "after_implement"), expected):
            with self.subTest(hook=hook):
                block = re.search(
                    rf"^  {hook}:\n(.*?)(?=^  \w+:|^\w|\Z)",
                    manifest,
                    re.MULTILINE | re.DOTALL,
                ).group(1)
                self.assertIn(f'    command: "{command}"', block)
                self.assertIn("    optional: false", block)
                self.assertIn("    priority: 10", block)
                artifact = read(f"extension/{expected[command]}")
                self.assertIn("**read-only**", artifact)
                self.assertIn(f"Mandatory `{hook}` gate failed.", artifact)

    def test_updated_addenda_still_append_to_existing_speckit_commands(self):
        manifest = read("preset/preset.yml")
        for command in ("specify", "plan", "tasks"):
            with self.subTest(command=command):
                block = re.search(
                    rf'      name: "speckit\.{command}"\n(.*?)(?=^    - |^tags:|\Z)',
                    manifest,
                    re.MULTILINE | re.DOTALL,
                ).group(1)
                self.assertIn(f'      file: "commands/speckit.{command}.md"', block)
                self.assertIn('      strategy: "append"', block)
                self.assertTrue((ROOT / f"preset/commands/speckit.{command}.md").is_file())
        tasks = read("preset/commands/speckit.tasks.md")
        self.assertIn("(source: FR-004)", tasks)
        self.assertIn("Do not change the core Spec Kit checkbox/ID/[P]/[US] task syntax", tasks)
        for heading in ("Verification Complexity Budget", "Verification Justification"):
            self.assertIn(f"`## {heading}`", tasks)

    def test_plan_budget_and_justification_are_consumed_by_both_gates(self):
        plan = read("preset/commands/speckit.plan.md")
        budget = table_rows(section(plan, "### 3. Add a Verification Complexity Budget"))
        self.assertEqual(
            [row[0] for row in budget[1:]],
            [
                "Verification layer", "Real-browser/E2E coverage",
                "Exhaustive edge-case matrices", "Browser/E2E fault injection",
                "Test-only hooks", "Duplicate proof across layers",
                "Environment permutations", "Internal diagnostic evidence in acceptance",
            ],
        )
        justification = table_rows(section(plan, "### 4. Add compact Verification Justification"))
        self.assertEqual(justification[0], [
            "Claim", "Requirement / source", "Lowest sufficient layer",
            "Higher layer required?", "Incremental evidence provided by higher layer",
        ])
        for command in ("preflight", "simplify"):
            guard = read(f"extension/commands/{command}.md")
            for heading in ("Verification Complexity Budget", "Verification Justification"):
                self.assertIn(f"`## {heading}`", guard)
        self.assertIn("Do not require verbose entries for ordinary unit/integration tests", plan)

    def test_expensive_verification_blocks_without_removing_safety_proof(self):
        hierarchy = "unit → integration → real browser / E2E → human acceptance"
        for relative in (
            "extension/commands/preflight.md", "extension/commands/simplify.md",
            "preset/commands/speckit.plan.md",
        ):
            with self.subTest(artifact=relative):
                document = read(relative)
                self.assertIn(hierarchy, document)
                self.assertIn("lowest-cost deterministic verification layer", document)
                for disposition in ("DOWNLEVEL", "MERGE", "REMOVE"):
                    self.assertIn(f"**{disposition}**", document)
                self.assertIn("Test count alone is not complexity", document)
        for command in ("preflight", "simplify"):
            document = read(f"extension/commands/{command}.md")
            severity = section(document, "## Severity and blocking")
            self.assertIn("Materially expensive or architecture-affecting violations are **HIGH** and MUST block", severity)
            self.assertIn("Loss of required safety proof remains a CRITICAL", severity)
            self.assertIn("provided the underlying requirement remains conclusively verified", document)
            self.assertIn("A particular verification method is not protected merely because", document)

    def test_semantic_fixture_oracles_reference_current_rules_and_preserve_boundaries(self):
        fixture = json.loads(read("tests/fixtures/verification-complexity.json"))
        rules = set(re.findall(r"\*\*(V-\d{2})\*\*", read("extension/commands/preflight.md")))
        self.assertEqual(rules, {f"V-{i:02}" for i in range(1, 9)})
        cases = fixture["cases"]
        self.assertEqual([case["id"] for case in cases], [
            "native-context-menu", "mv3-worker-restart", "consumed-capture-replay",
            "callback-ordering", "stale-target-variants", "permission-evidence",
            "t012-over-specified",
        ])
        for case in cases:
            with self.subTest(case=case["id"]):
                for artifact in ("spec.md", "plan.md", "tasks.md", "implemented_verification"):
                    self.assertTrue(case[artifact])
                self.assertRegex(case["tasks.md"], r"- \[ \] T\d{3} .*\(source: FR-\d{3}")
                expected = case["expected"]
                self.assertTrue(set(expected["rules"]) <= rules)
                self.assertTrue(set(expected.get("additional_simplify_rules", [])) <= rules)
                self.assertEqual(expected["preflight"], expected["simplify"])
                if expected["rules"]:
                    self.assertEqual(expected["severity"], "HIGH")
                    self.assertEqual(expected["preflight"], "BLOCK")
                else:
                    self.assertEqual(expected["disposition"], "KEEP")
                    self.assertEqual(expected["preflight"], "PASS")
                self.assertTrue(expected["reason"])
        self.assertEqual(set(cases[-1]["expected"]["rules"]), rules)


if __name__ == "__main__":
    unittest.main()
