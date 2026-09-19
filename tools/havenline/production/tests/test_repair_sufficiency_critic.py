from __future__ import annotations

import copy
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

from repair_sufficiency_critic import review


def c0(product=True):
    classification = "PRODUCT_DEFECT" if product else "TOOLING_DEFECT"
    return {
        "schema_version": 1,
        "critic_id": "C0",
        "non_voting": True,
        "validated": True,
        "diagnosis_status": "DIAGNOSIS_COMPLETE",
        "complete_known_blocker_set": True,
        "builder_action": "REPAIR",
        "diagnosis_id": "C0-T10-123",
        "task_id": "T10",
        "failed_candidate": "a" * 40,
        "blockers": [{
            "id": "C0-T10-B053",
            "classification": classification,
            "root_cause": "fallback placement accepts an infeasible terminal lane",
        }],
    }


def accepted_plan():
    return {
        "schema_version": 1,
        "task_id": "T10",
        "failed_candidate": "a" * 40,
        "diagnosis_id": "C0-T10-123",
        "repair_sufficiency": {
            "failure_family": {
                "id": "projected-label-feasibility",
                "invariant": "every mandatory state/camera/device projection has a contained readable label with required clearance",
                "scope_dimensions": ["device", "lifecycle_state", "camera_angle"],
                "known_failed_cases": ["phone_16_9/blocked/overhead"],
                "unexecuted_or_unknown_cases": [],
                "observable_exhaustive_collection_required": True,
                "complete_observable_set_collected": True,
                "full_failure_family_closed_by_design": True,
            },
            "strategy_kind": "ALGORITHM",
            "causal_mechanism": "enumerate legal screen regions, measure reflowed candidates, and accept only a proven feasible placement",
            "why_this_fixes_cause": "the failed code accepted the last fallback without proving containment; the new solver validates containment before selection",
            "why_materially_different": "replaces scalar symptom tuning with a constrained feasibility algorithm over the whole mandatory projection domain",
            "same_family_attempt_count": 2,
            "prior_attempts": [
                {"strategy": "width 1000 to 960", "outcome": "FAILED", "same_family": True, "lesson": "natural measured width was unchanged"},
                {"strategy": "pixel_size 0.006 to 0.0057", "outcome": "PARTIAL", "same_family": True, "lesson": "one state improved while blocked overhead remained infeasible"},
            ],
            "blocker_coverage": [{
                "blocker_id": "C0-T10-B053",
                "why_fix_changes_cause": "removes unconditional infeasible fallback acceptance",
                "expected_result": "all mandatory projections either select a legal placement or fail deterministically",
                "failure_if_wrong": "any mandatory projection has no legal candidate or escapes the safe frame",
                "cheap_disproof": "run the complete deterministic projection feasibility matrix before render/critic jobs",
            }],
            "full_domain_proof": {
                "required": True,
                "provided": True,
                "method": "216-case device/state/angle projection sweep",
                "expected_cases": 216,
                "covered_cases": 216,
            },
            "cheap_disproof_preflight": [{
                "name": "projection-matrix",
                "command": "python3 tools/havenline/task10/validate_projection_matrix.py",
                "falsifies": "any required state/device/angle lacks a feasible placement",
            }],
            "counterexamples_considered": [{
                "case": "long blocked label at phone overhead",
                "why_covered": "solver measures wrapped label against actual left/right/top/bottom available regions",
            }],
            "blast_radius_hypotheses": ["readability can regress if reflow chooses too narrow a lane"],
            "residual_unknowns": [],
            "threshold_changes": [],
            "loop_risk_acknowledged": True,
        },
    }


class RepairSufficiencyCriticTests(unittest.TestCase):
    def test_algorithmic_full_domain_plan_is_accepted(self):
        report = review(c0(), accepted_plan())
        self.assertTrue(report["passed"], report)
        self.assertEqual("REPAIR_PLAN_ACCEPTED", report["outcome"])
        self.assertEqual("C0R", report["critic_id"])
        self.assertFalse(report["may_approve_task"])

    def test_current_style_scalar_patch_after_two_attempts_is_rejected(self):
        plan = accepted_plan()
        s = plan["repair_sufficiency"]
        s["strategy_kind"] = "SCALAR_TUNING"
        s["why_materially_different"] = "smaller pixel size"
        s["full_domain_proof"]["provided"] = False
        s["full_domain_proof"]["covered_cases"] = 1
        report = review(c0(), plan)
        self.assertFalse(report["passed"])
        self.assertEqual("REPAIR_PLAN_REJECTED", report["outcome"])
        self.assertIn("SERIAL_SCALAR_PATCH_RISK", report["risk_codes"])
        self.assertIn("REPEATED_SCALAR_FIX_REQUIRES_FULL_DOMAIN_PROOF", report["rejections"])

    def test_missing_exhaustive_observable_set_returns_insufficient_evidence(self):
        plan = accepted_plan()
        plan["repair_sufficiency"]["failure_family"]["complete_observable_set_collected"] = False
        report = review(c0(), plan)
        self.assertFalse(report["passed"])
        self.assertEqual("INSUFFICIENT_EVIDENCE", report["outcome"])
        self.assertIn("OBSERVABLE_FAILURE_FAMILY_NOT_EXHAUSTIVELY_COLLECTED", report["evidence_gaps"])

    def test_unknown_cases_cannot_be_called_fully_closed(self):
        plan = accepted_plan()
        plan["repair_sufficiency"]["failure_family"]["unexecuted_or_unknown_cases"] = ["phone_20_9/blocked/overhead"]
        report = review(c0(), plan)
        self.assertEqual("REPAIR_PLAN_REJECTED", report["outcome"])
        self.assertIn("OVERCLAIMED_FAILURE_FAMILY_CLOSURE", report["rejections"])

    def test_every_c0_blocker_requires_explicit_causal_sufficiency_coverage(self):
        base = c0()
        second = copy.deepcopy(base["blockers"][0])
        second["id"] = "C0-T10-B055"
        base["blockers"].append(second)
        report = review(base, accepted_plan())
        self.assertIn("EVERY_C0_BLOCKER_REQUIRES_SUFFICIENCY_COVERAGE", report["rejections"])

    def test_threshold_weakening_is_never_an_accepted_repair(self):
        plan = accepted_plan()
        plan["repair_sufficiency"]["threshold_changes"] = ["C3 >9.0 becomes >=8.0"]
        report = review(c0(), plan)
        self.assertFalse(report["passed"])
        self.assertIn("CRITIC_OR_QUALITY_THRESHOLD_CHANGE_FORBIDDEN", report["rejections"])
        self.assertFalse(report["thresholds_unchanged"])

    def test_product_defect_cannot_be_closed_by_evidence_only_strategy(self):
        plan = accepted_plan()
        plan["repair_sufficiency"]["strategy_kind"] = "EVIDENCE_ONLY"
        report = review(c0(product=True), plan)
        self.assertIn("PRODUCT_DEFECT_REQUIRES_CAUSAL_PRODUCT_STRATEGY", report["rejections"])

    def test_incomplete_c0_never_authorizes_build(self):
        root = c0()
        root["validated"] = False
        report = review(root, accepted_plan())
        self.assertFalse(report["passed"])
        self.assertEqual("INSUFFICIENT_EVIDENCE", report["outcome"])
        self.assertEqual("COLLECT_NAMED_EVIDENCE", report["builder_action"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
