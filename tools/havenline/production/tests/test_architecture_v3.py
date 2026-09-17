from __future__ import annotations

import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve()
PROD = HERE.parents[1]
sys.path.insert(0, str(PROD))

from architecture_v3 import task_readiness, validate as validate_v3
from contract_compatibility import evaluate_change, validate_registry
from critical_path_scheduler import schedule, validate as validate_scheduler
from failure_intelligence import query, validate as validate_failure_intelligence
from gate_fingerprint import validate_policy
from preactivation_feasibility import resolve_capabilities, validate_all as validate_feasibility
from synthetic_merge_forecast import forecast


class ArchitectureV3Tests(unittest.TestCase):
    def test_all_61_tasks_resolve_v3_readiness(self):
        reports = [task_readiness(f"T{i:02d}") for i in range(10, 71)]
        self.assertEqual(len(reports), 61)
        self.assertEqual({r["task_id"] for r in reports}, {f"T{i:02d}" for i in range(10, 71)})

    def test_external_capability_is_never_assumed_ready(self):
        t35 = resolve_capabilities("T35")
        self.assertIn("google_play_billing_sandbox", t35["required_capabilities"])
        self.assertIn("google_play_billing_sandbox", t35["capability_blockers"])
        self.assertEqual(t35["capabilities"]["google_play_billing_sandbox"]["state"], "UNVERIFIED")

    def test_physical_certification_requires_real_hardware_capability(self):
        t68 = resolve_capabilities("T68")
        self.assertIn("physical_phone_4k60", t68["required_capabilities"])
        self.assertEqual(t68["capabilities"]["physical_phone_4k60"]["state"], "UNVERIFIED")
        self.assertFalse(t68["runtime_activation_allowed"])

    def test_scheduler_is_advisory_unique_and_preserves_single_integration_owner(self):
        report = schedule()
        ids = [r["task_id"] for r in report["all_unapproved"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(report["scheduler_is_advisory"])
        self.assertEqual(report["integration_owner_slots"], 1)

    def test_gate_fingerprint_policy_keeps_fresh_only_gates_exact_source(self):
        report = validate_policy()
        self.assertTrue(report["passed"], report["errors"])

    def test_contract_registry_and_breaking_change_rules(self):
        self.assertTrue(validate_registry()["passed"])
        bad = evaluate_change({"contract_id": "persistence_schema", "from_version": 1, "to_version": 2, "change_kind": "breaking", "consumer_revalidation": []})
        self.assertFalse(bad["passed"])
        self.assertTrue(any("migration_plan" in e for e in bad["errors"]))
        good = evaluate_change({"contract_id": "persistence_schema", "from_version": 1, "to_version": 2, "change_kind": "breaking", "migration_plan": "Migrate v1 saves to v2 before load; preserve rollback reader.", "consumer_revalidation": []})
        self.assertTrue(good["passed"], good["errors"])

    def test_failure_intelligence_matches_t09_pose_tooling_without_auto_repair(self):
        result = query("T24", "C5", "C5 t=0 pose identity failed after pixel RMSE changed even though skeleton pose looked stable")
        self.assertTrue(result["matches"])
        self.assertEqual(result["matches"][0]["id"], "FI-T09-001")
        self.assertTrue(result["matches"][0]["advisory_only"])

    def test_failure_intelligence_schema_is_valid(self):
        self.assertTrue(validate_failure_intelligence()["passed"])

    def test_feasibility_schema_is_valid_for_all_tasks(self):
        report = validate_feasibility()
        self.assertTrue(report["passed"], report["errors"])
        self.assertEqual(report["task_count"], 61)

    def test_scheduler_policy_validates(self):
        report = validate_scheduler()
        self.assertTrue(report["passed"], report["errors"])

    def test_same_head_merge_forecast_is_clean_and_non_mutating(self):
        report = forecast("HEAD", "HEAD")
        self.assertEqual(report["risk"], "NO_DRIFT")
        self.assertFalse(report["requires_reconcile"])
        self.assertEqual(report["candidate"], report["integration_head"])

    def test_combined_v3_validation_passes(self):
        report = validate_v3()
        self.assertTrue(report["passed"], report["errors"])
        self.assertEqual(report["task_count"], 61)


if __name__ == "__main__":
    unittest.main(verbosity=2)
