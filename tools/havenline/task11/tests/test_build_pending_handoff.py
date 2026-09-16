#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "tools" / "havenline" / "task11" / "prepare_activation.py"
CHECKPOINT = ROOT / "Docs" / "Production" / "T11" / "BUILD_PENDING_CANDIDATE.json"
CRITIC_READINESS = ROOT / "Docs" / "Production" / "T11" / "critic-input-readiness.json"
CRITIC_MATRIX = ROOT / "Docs" / "Production" / "CRITIC_MATRIX.json"

spec = importlib.util.spec_from_file_location("t11_prepare_activation", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class T11BuildPendingHandoffTests(unittest.TestCase):
    def test_checkpoint_is_valid_and_source_bound(self):
        errors: list[str] = []
        checkpoint = module.validate_build_pending_checkpoint(errors)
        self.assertEqual(errors, [], "\n".join(errors))
        self.assertEqual(checkpoint["state"], "BUILT_PENDING_DEPENDENCY")
        self.assertFalse(checkpoint["final_integration_ready"])
        self.assertFalse(checkpoint["task_approved"])
        self.assertEqual(checkpoint["unresolved_mandatory_build_defects"], [])

        source = module.checkpoint_source(checkpoint)
        run = checkpoint["build_pending_test_run"]
        tests = checkpoint["build_pending_tests"]
        evidence = checkpoint["rendered_evidence"]
        self.assertEqual(len(source), 40)
        self.assertEqual(run["source"], source)
        self.assertEqual(run["conclusion"], "success")
        self.assertGreater(run["workflow_run"], 0)
        self.assertGreater(run["artifact_id"], 0)
        self.assertEqual(len(run["artifact_sha256"]), 64)
        self.assertTrue(tests["all_passed"])
        self.assertGreaterEqual(tests["suite_count"], 16)
        self.assertGreaterEqual(tests["check_count"], 1121)
        self.assertEqual(tests["rendered_evidence_gate"], "PASS")
        self.assertEqual(evidence["standard_frame_count"], 16)
        self.assertEqual(evidence["native_4k_frame_count"], 3)
        self.assertTrue(evidence["approved_t03_boundary_rendered"])
        self.assertTrue(evidence["lifecycle_beacon_readable_at_gameplay_scale"])
        self.assertFalse(evidence["final_visual_critic_evidence"])
        self.assertFalse(evidence["physical_4k60_verified"])

    def test_critic_readiness_is_bound_to_checkpoint_and_matrix(self):
        checkpoint = json.loads(CHECKPOINT.read_text())
        critic = json.loads(CRITIC_READINESS.read_text())
        matrix = json.loads(CRITIC_MATRIX.read_text())
        source = module.checkpoint_source(checkpoint)
        run = checkpoint["build_pending_test_run"]

        required = ["C2", "C3", "C4", "C6"]
        self.assertEqual(matrix["task_applicability"]["T11"], required)
        self.assertEqual(critic["required_critics"], required)
        self.assertEqual(set(critic["coverage"]), set(required))
        self.assertTrue(all(critic["coverage"][critic_id]["input_ready"] for critic_id in required))

        self.assertEqual(critic["state"], "BUILT_PENDING_DEPENDENCY")
        self.assertEqual(critic["candidate"], source)
        self.assertEqual(critic["runtime_and_evidence_source"], source)
        self.assertEqual(critic["isolated_workflow_run"], run["workflow_run"])
        self.assertEqual(critic["evidence_artifact"], run["artifact_id"])
        self.assertEqual(critic["evidence_artifact_sha256"], run["artifact_sha256"])
        self.assertTrue(critic["isolated_critic_input_ready"])
        self.assertFalse(critic["production_critic_execution_allowed"])
        self.assertFalse(critic["critic_scores_recorded"])
        self.assertFalse(critic["integration_allowed"])
        self.assertFalse(critic["task_approved"])
        self.assertFalse(critic["final_t10_compatibility_claimed"])
        self.assertFalse(critic["evidence_summary"]["physical_4k60_verified"])
        self.assertTrue(critic["remaining_integration_blockers"])
        self.assertTrue(any("not a critic result" in note for note in critic["notes"]))

    def test_activation_still_fails_closed_until_t10_is_approved(self):
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        result = module.validate_activation(head)
        self.assertFalse(result["passed"])
        self.assertEqual(result["build_pending_candidate_source"], module.checkpoint_source(json.loads(CHECKPOINT.read_text())))
        self.assertTrue(result["fresh_reconciliation_required"])
        joined = "\n".join(result["errors"])
        self.assertIn("T10", joined)
        self.assertTrue(
            "not APPROVED" in joined or "completed_task_records" in joined or "active owner" in joined,
            joined,
        )

    def test_promotion_code_preserves_tested_candidate_identity(self):
        source = SCRIPT.read_text()
        required = [
            '"candidate_commit": candidate_source',
            '"candidate_hash_or_artifact": artifact_identity',
            'gates["active_candidate_source"] = candidate_source',
            'gates["active_candidate_run"] = run.get("workflow_run")',
            'gates["active_tests"] = tests',
            '"fresh_reconciliation_required": True',
            'PENDING_EXACT_T10_RECONCILIATION_AND_INDEPENDENT_REVIEW',
        ]
        for marker in required:
            self.assertIn(marker, source, marker)


if __name__ == "__main__":
    unittest.main()
