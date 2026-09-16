#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
DOCS = ROOT / "Docs" / "Production"
SCRIPT = ROOT / "tools" / "havenline" / "task11" / "prepare_activation.py"
CHECKLIST = DOCS / "T11" / "ACTIVATION_CHECKLIST.json"
PREBUILD = DOCS / "T11" / "PREBUILD_CONTRACT.json"
DEFECTS = DOCS / "T11" / "defect-ledger.json"
T10_CHECKLIST = DOCS / "T10" / "ACTIVATION_CHECKLIST.json"
GRAPH = DOCS / "DEPENDENCY_GRAPH.json"
CRITICS = DOCS / "CRITIC_MATRIX.json"
OWNERSHIP = DOCS / "PATH_OWNERSHIP.json"


def load(path: pathlib.Path):
    return json.loads(path.read_text())


def run(*args: str):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class T11PreparationTests(unittest.TestCase):
    def test_default_build_pending_preparation_validation_passes(self):
        proc = run()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["passed"])
        self.assertTrue(payload["isolated_build_allowed"])
        self.assertEqual(payload["maximum_pre_dependency_state"], "BUILT_PENDING_DEPENDENCY")
        self.assertFalse(payload["final_integration_allowed"])
        self.assertEqual(payload["required_critics"], ["C2", "C3", "C4", "C6"])

    def test_final_promotion_fails_closed_while_t10_unapproved(self):
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        proc = run("--activate", "--base", head)
        self.assertNotEqual(proc.returncode, 0, "T11 final promotion unexpectedly passed before T10 approval")
        payload = json.loads(proc.stdout)
        self.assertFalse(payload["passed"])
        joined = "\n".join(payload["errors"])
        self.assertIn("T10", joined)
        self.assertTrue(
            "not APPROVED" in joined or "completed_task_records" in joined or "active owner" in joined,
            joined,
        )

    def test_machine_readable_contract_is_bound_to_authoritative_sources(self):
        contract = load(PREBUILD)
        checklist = load(CHECKLIST)
        graph = load(GRAPH)
        critics = load(CRITICS)

        self.assertEqual(contract["task_id"], "T11")
        gate = contract["dependency_gate"]
        self.assertEqual(gate["required_approved_for_final_integration"], ["T05", "T10"])
        self.assertTrue(gate["isolated_build_allowed_before_t10_approval"])
        self.assertEqual(gate["maximum_state_before_t10_approval"], "BUILT_PENDING_DEPENDENCY")
        self.assertFalse(gate["final_integration_allowed_before_gate"])
        self.assertTrue(gate["reconcile_to_exact_t10_before_integration_ready"])
        self.assertTrue(checklist["build_pending_policy"]["isolated_build_allowed_before_t10_approval"])
        self.assertEqual(checklist["build_pending_policy"]["maximum_state_before_t10_approval"], "BUILT_PENDING_DEPENDENCY")
        self.assertFalse(checklist["build_pending_policy"]["may_claim_integration_ready"])
        self.assertEqual(
            contract["authoritative_sources"]["reference_b_sha256"],
            "4c9051cbea6df0efa3e7288b13b6d17da46e857274869b0b43d2f96ff6cc79d2",
        )
        self.assertEqual(
            contract["authoritative_sources"]["t05_accepted_source"],
            "fa6fa70f154f3757d22303522ca3f6de2c3d391f",
        )
        self.assertEqual(contract["critic_contract"]["required"], checklist["required_critics"])
        self.assertEqual(graph["tasks"]["T11"]["critics"], checklist["required_critics"])
        self.assertEqual(critics["task_applicability"]["T11"], checklist["required_critics"])
        self.assertGreaterEqual(len(contract["reference_acceptance_moments"]), 4)
        self.assertGreaterEqual(len(contract["required_content_roles"]), 6)
        self.assertGreaterEqual(len(contract["required_capture_groups"]), 4)

    def test_shipping_price_provenance_rule_is_fail_closed(self):
        contract = load(PREBUILD)
        rule = contract["camp_recipe_schema"]["shipping_price_rule"]
        self.assertIn("price_source", rule)
        self.assertIn("tuning_record", rule)
        self.assertIn("may not be generalized", rule)
        self.assertIn("shipping prices", contract["explicitly_not_implemented_during_prep"])
        blocked = contract["build_pending_contract"]["blocked_until_t10_accepted"]
        self.assertIn("shipping prices without authoritative provenance", blocked)

    def test_t11_planned_paths_do_not_overlap_t10_or_integration_only(self):
        t11 = load(CHECKLIST)
        t10 = load(T10_CHECKLIST)
        ownership = load(OWNERSHIP)
        t11_paths = set(t11["planned_owned_paths"])
        t10_paths = set(t10["planned_owned_paths"])
        protected = set(ownership.get("aliases", {}).get("@integration-only", []))
        self.assertFalse(t11_paths & t10_paths, sorted(t11_paths & t10_paths))
        self.assertFalse(t11_paths & protected, sorted(t11_paths & protected))
        self.assertNotIn("HavenlineGodot/scripts/main.gd", t11_paths)
        self.assertNotIn("HavenlineGodot/scripts/simulation.gd", t11_paths)

    def test_prep_branch_has_no_runtime_changes(self):
        checklist = load(CHECKLIST)
        base = checklist["prepared_from_commit"]
        changed = subprocess.check_output(
            ["git", "diff", "--name-only", f"{base}..HEAD"], cwd=ROOT, text=True
        ).splitlines()
        runtime = [path for path in changed if path.startswith("HavenlineGodot/")]
        self.assertEqual(runtime, [], runtime)

    def test_defect_ledger_is_truthful_about_dependency_blocker(self):
        ledger = load(DEFECTS)
        self.assertFalse(ledger["internal_review"]["task_approval_claimed"])
        self.assertEqual(ledger["mandatory_prep_defects"], [])
        blockers = ledger["runtime_blockers"]
        self.assertEqual(len(blockers), 1)
        self.assertIn("T10", blockers[0]["blocker"])
        self.assertIn("Does not block isolated T11 build/test", blockers[0]["effect"])
        self.assertIn("BUILT_PENDING_DEPENDENCY", blockers[0]["effect"])


if __name__ == "__main__":
    unittest.main()
