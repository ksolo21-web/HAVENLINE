from __future__ import annotations

import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
MODULE_PATH = ROOT / "tools" / "havenline" / "production" / "forward_execution.py"
spec = importlib.util.spec_from_file_location("forward_execution", MODULE_PATH)
forward_execution = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(forward_execution)


class ForwardExecutionTests(unittest.TestCase):
    def plan(self, task_id: str) -> dict:
        return forward_execution.resolve_task(task_id)

    def test_all_61_forward_tasks_validate(self):
        result = forward_execution.validate_all()
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["task_count"], 61)
        self.assertEqual(result["expected_task_count"], 61)

    def test_t10_world_transform_is_fail_fast_build(self):
        plan = self.plan("T10")
        self.assertEqual(plan["execution_mode"], "build")
        gates = plan["ordered_gates"]
        for gate in ("reference_lock", "progression_sim", "performance", "visual_evidence", "integration", "post_integration_regression"):
            self.assertIn(gate, gates)
        self.assertLess(gates.index("task_sentinel"), gates.index("performance"))
        self.assertLess(gates.index("task_sentinel"), gates.index("visual_evidence"))

    def test_t14_persistence_runs_security_and_save_proof(self):
        plan = self.plan("T14")
        self.assertEqual(plan["archetype"], "persistence_security")
        self.assertIn("save_matrix", plan["ordered_gates"])
        self.assertIn("security_attack", plan["ordered_gates"])
        self.assertNotIn("motion_preflight", plan["ordered_gates"])

    def test_t24_animal_requires_reference_motion_and_performance(self):
        plan = self.plan("T24")
        gates = set(plan["ordered_gates"])
        self.assertTrue({"reference_lock", "motion_preflight", "performance", "visual_evidence"} <= gates)

    def test_t33_economy_gets_progression_economy_security(self):
        plan = self.plan("T33")
        gates = set(plan["ordered_gates"])
        self.assertTrue({"progression_sim", "economy_sim", "security_attack"} <= gates)

    def test_t37_liveops_gets_liveops_and_economy_security(self):
        plan = self.plan("T37")
        gates = set(plan["ordered_gates"])
        self.assertTrue({"progression_sim", "economy_sim", "security_attack", "liveops_sim"} <= gates)

    def test_t58_validation_cannot_integrate_runtime(self):
        plan = self.plan("T58")
        self.assertEqual(plan["execution_mode"], "validation_only")
        gates = set(plan["ordered_gates"])
        self.assertTrue({"save_matrix", "device_matrix", "performance", "impacted_regression"} <= gates)
        self.assertNotIn("integration", gates)
        self.assertNotIn("post_integration_regression", gates)
        self.assertIn("may not repair runtime", plan["failure_disposition"])

    def test_t62_whole_progression_acceptance_is_validation_only(self):
        plan = self.plan("T62")
        self.assertEqual(plan["execution_mode"], "validation_only")
        gates = set(plan["ordered_gates"])
        self.assertTrue({"progression_sim", "economy_sim", "save_matrix", "device_matrix", "security_attack", "liveops_sim", "motion_preflight", "performance", "visual_evidence"} <= gates)
        self.assertNotIn("integration", gates)

    def test_t68_physical_cert_cannot_use_runtime_integration(self):
        plan = self.plan("T68")
        self.assertEqual(plan["execution_mode"], "certification_only")
        self.assertIn("physical_device", plan["ordered_gates"])
        self.assertNotIn("integration", plan["ordered_gates"])

    def test_t70_release_only_requires_manifest_and_full_closure(self):
        plan = self.plan("T70")
        self.assertEqual(plan["execution_mode"], "release_only")
        gates = set(plan["ordered_gates"])
        self.assertTrue({"release_manifest", "physical_device", "security_attack", "liveops_sim", "performance", "visual_evidence"} <= gates)
        self.assertNotIn("integration", gates)


if __name__ == "__main__":
    unittest.main()
