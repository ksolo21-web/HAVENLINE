from __future__ import annotations

import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve()
PRODUCTION = HERE.parents[1]
sys.path.insert(0, str(PRODUCTION))

from validate_migration_scope import classify_changed_files, governance_patterns_from_base


class MigrationScopeTests(unittest.TestCase):
    def ownership(self, extra=None):
        patterns = [
            "Docs/Production/**",
            "tools/havenline/production/**",
            ".github/workflows/havenline-production-governance.yml",
            ".github/workflows/havenline-critic-safeguards.yml",
            ".github/workflows/havenline-c0-root-cause.yml",
            "AGENTS.md",
        ]
        if extra:
            patterns.extend(extra)
        return {"aliases": {"@ownership:QA-GOV": patterns}}

    def test_preowned_qa_workflow_is_allowed(self):
        r = classify_changed_files([".github/workflows/havenline-critic-safeguards.yml"], self.ownership())
        self.assertTrue(r["passed"])
        self.assertEqual(r["rejected_files"], [])

    def test_game_runtime_is_rejected_even_if_qa_alias_claims_it(self):
        r = classify_changed_files(["HavenlineGodot/scripts/main.gd"], self.ownership(["HavenlineGodot/**"]))
        self.assertFalse(r["passed"])
        self.assertEqual(r["rejected_files"], ["HavenlineGodot/scripts/main.gd"])
        self.assertTrue(r["runtime_ownership_filtered"])

    def test_unknown_task_workflow_is_rejected(self):
        r = classify_changed_files([".github/workflows/havenline-task10-world.yml"], self.ownership())
        self.assertFalse(r["passed"])

    def test_explicit_qa_capture_harness_remains_allowed(self):
        for path in (
            "HavenlineGodot/tests/production_capture_harness.gd",
            "HavenlineGodot/tests/production_motion_capture.gd",
        ):
            with self.subTest(path=path):
                r = classify_changed_files([path], self.ownership())
                self.assertTrue(r["passed"])

    def test_missing_base_governance_alias_fails_closed(self):
        with self.assertRaises(ValueError):
            governance_patterns_from_base({"aliases": {}})

    def test_candidate_added_ownership_cannot_change_base_decision(self):
        # The classifier consumes only the supplied base ownership. A candidate
        # could add this path to its own PATH_OWNERSHIP.json, but that newer
        # ownership object is intentionally irrelevant to this decision.
        base = self.ownership()
        r = classify_changed_files([".github/workflows/new-self-authorized.yml"], base)
        self.assertFalse(r["passed"])
        self.assertTrue(r["candidate_cannot_self_authorize"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
