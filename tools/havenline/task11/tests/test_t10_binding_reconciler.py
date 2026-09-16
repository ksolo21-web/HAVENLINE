#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "tools" / "havenline" / "task11" / "reconcile_t10_binding.py"
T11_CATALOG = ROOT / "HavenlineGodot" / "data" / "camp_upgrade_recipes.json"

spec = importlib.util.spec_from_file_location("t11_reconcile_t10", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

T10_SCRIPT = """
func preview_transform(recipe_id, target_id, inventory, prerequisites=[]):
    pass
func commit_transform(transaction_id, recipe_id, target_id, inventory, prerequisites=[]):
    pass
func accept_authoritative_receipt(receipt):
    pass
"""


def t10_catalog() -> dict:
    return {
        "schema_version": 1,
        "authority_id": "T10-world-transform-recipes-v1",
        "prebuild_fixtures": True,
        "shipping_binding_required_after_t09": True,
        "recipes": [
            {
                "recipe_id": "framework_anchor_seed_to_foundation",
                "source_state": "seed",
                "target_state": "foundation",
                "costs": [
                    {"resource_id": "wood", "quantity": 8},
                    {"resource_id": "stone", "quantity": 4},
                ],
                "prerequisites": [],
                "progression_tags": ["opening_transform"],
                "presentation_key": "framework_foundation",
                "reversible": False,
            },
            {
                "recipe_id": "framework_anchor_foundation_to_reinforced",
                "source_state": "foundation",
                "target_state": "reinforced",
                "costs": [
                    {"resource_id": "wood", "quantity": 12},
                    {"resource_id": "stone", "quantity": 8},
                    {"resource_id": "metal", "quantity": 2},
                ],
                "prerequisites": ["harvesting_online"],
                "progression_tags": ["opening_transform", "reinforcement"],
                "presentation_key": "framework_reinforced",
                "reversible": False,
            },
        ],
    }


class T10BindingReconcilerTests(unittest.TestCase):
    def setUp(self):
        self.t11 = json.loads(T11_CATALOG.read_text())
        self.t10 = t10_catalog()

    def test_current_observed_t10_semantics_are_compatible(self):
        report = module.reconcile(
            self.t11,
            self.t10,
            T10_SCRIPT,
            mode="semantic",
            expected_t10_source="9ad946c226132ebedd34ff1d9298e192fa3f2990",
        )
        self.assertTrue(report["passed"], report["errors"])
        self.assertTrue(report["semantic_compatible"])
        self.assertEqual(report["binding_count"], 2)
        self.assertFalse(report["t11_local_cost_authority"])
        self.assertFalse(report["task_approved"])
        self.assertTrue(all(row["source_match"] and row["target_match"] for row in report["bindings"]))
        self.assertTrue(all(row["t10_costs_present_authority_owned"] for row in report["bindings"]))
        self.assertIn("T10 catalog still declares prebuild_fixtures=true", report["warnings"])

    def test_missing_t10_recipe_fails_closed(self):
        drifted = copy.deepcopy(self.t10)
        drifted["recipes"] = drifted["recipes"][:1]
        report = module.reconcile(self.t11, drifted, T10_SCRIPT)
        self.assertFalse(report["passed"])
        self.assertTrue(any("missing T10 recipe" in value for value in report["errors"]))

    def test_source_or_target_state_drift_fails_closed(self):
        drifted = copy.deepcopy(self.t10)
        drifted["recipes"][0]["source_state"] = "different_seed"
        drifted["recipes"][1]["target_state"] = "different_reinforced"
        report = module.reconcile(self.t11, drifted, T10_SCRIPT)
        self.assertFalse(report["passed"])
        joined = "\n".join(report["errors"])
        self.assertIn("source-state drift", joined)
        self.assertIn("target-state drift", joined)

    def test_missing_required_t10_method_fails_closed(self):
        report = module.reconcile(
            self.t11,
            self.t10,
            "func preview_transform():\n    pass\nfunc commit_transform():\n    pass\n",
        )
        self.assertFalse(report["passed"])
        self.assertTrue(any("accept_authoritative_receipt" in value for value in report["errors"]))

    def test_t11_may_not_duplicate_t10_cost_authority(self):
        drifted_t11 = copy.deepcopy(self.t11)
        drifted_t11["recipes"][0]["costs"] = [{"resource_id": "wood", "quantity": 1}]
        report = module.reconcile(drifted_t11, self.t10, T10_SCRIPT)
        self.assertFalse(report["passed"])
        self.assertTrue(any("duplicates T10 cost/debit authority" in value for value in report["errors"]))

    def test_final_mode_rejects_unapproved_prebuild_bindings(self):
        report = module.reconcile(self.t11, self.t10, T10_SCRIPT, mode="final")
        self.assertFalse(report["passed"])
        joined = "\n".join(report["errors"])
        self.assertIn("prebuild_fixtures=true", joined)
        self.assertIn("final_t10_reconciliation_required", joined)
        self.assertIn("unapproved prebuild binding status", joined)
        self.assertFalse(report["final_reconciliation_passed"])

    def test_final_mode_can_pass_after_explicit_accepted_reconciliation(self):
        accepted_t10 = copy.deepcopy(self.t10)
        accepted_t10["prebuild_fixtures"] = False
        accepted_t10["shipping_binding_required_after_t09"] = False
        reconciled_t11 = copy.deepcopy(self.t11)
        reconciled_t11["final_t10_reconciliation_required"] = False
        for row in reconciled_t11["recipes"]:
            row["binding_status"] = "t10_accepted_reconciled"
        report = module.reconcile(reconciled_t11, accepted_t10, T10_SCRIPT, mode="final")
        self.assertTrue(report["passed"], report["errors"])
        self.assertTrue(report["semantic_compatible"])
        self.assertTrue(report["final_reconciliation_passed"])
        self.assertFalse(report["task_approved"])


if __name__ == "__main__":
    unittest.main()
