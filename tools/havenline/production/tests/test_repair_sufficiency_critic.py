from __future__ import annotations

import copy
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

from repair_sufficiency_critic import review


def c0(product=True, two_blockers=False):
    classification = "PRODUCT_DEFECT" if product else "TOOLING_DEFECT"
    blockers = [{
        "id": "C0-T10-B053",
        "classification": classification,
        "root_cause": "fallback placement accepts an infeasible terminal lane",
    }]
    if two_blockers:
        blockers.append({
            "id": "C0-T10-B060",
            "classification": "TOOLING_DEFECT",
            "root_cause": "diagnostic projection can omit the terminal artifact excerpt",
        })
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
        "blockers": blockers,
    }


def layout_group():
    return {
        "group_id": "layout-feasibility",
        "blocker_ids": ["C0-T10-B053"],
        "failure_family": {
            "id": "projected-label-feasibility",
            "invariant": "every mandatory state/camera/device projection has a contained readable label with required clearance",
            "scope_dimensions": ["device", "lifecycle_state", "camera_angle"],
            "known_failed_cases": ["phone_16_9/blocked/overhead"],
            "unexecuted_or_unknown_cases": [],
            "observable_exhaustive_collection_required": True,
            "complete_observable_set_collected": True,
            "full_failure_family_closed_by_design": True,
            "collection_evidence": ["run 35402388836 retained device-layout projection records"],
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
            "diagnosed_root_cause": "fallback placement accepts an infeasible terminal lane",
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
    }


def tooling_group():
    return {
        "group_id": "terminal-evidence-priority",
        "blocker_ids": ["C0-T10-B060"],
        "failure_family": {
            "id": "diagnostic-terminal-evidence-loss",
            "invariant": "terminal failure evidence must survive bounded projection before generic successful evidence",
            "scope_dimensions": ["artifact", "diagnostic-priority"],
            "known_failed_cases": ["device-layout terminal capture log omitted from C0 model projection"],
            "unexecuted_or_unknown_cases": [],
            "observable_exhaustive_collection_required": False,
            "complete_observable_set_collected": True,
            "full_failure_family_closed_by_design": True,
        },
        "strategy_kind": "TOOLING",
        "causal_mechanism": "rank terminal failing source excerpts ahead of generic successful artifact excerpts",
        "why_this_fixes_cause": "the terminal artifact is retained but currently loses the shared excerpt budget before model projection",
        "why_materially_different": "changes evidence selection priority rather than expanding budget or weakening grounding",
        "same_family_attempt_count": 1,
        "prior_attempts": [{"strategy": "bounded artifact diagnostics", "outcome": "PARTIAL", "same_family": True, "lesson": "collection succeeded but projection priority still dropped terminal evidence"}],
        "blocker_coverage": [{
            "blocker_id": "C0-T10-B060",
            "diagnosed_root_cause": "diagnostic projection can omit the terminal artifact excerpt",
            "why_fix_changes_cause": "makes the exact terminal record consume projection budget first",
            "expected_result": "C0 sees the terminal failed assertion before secondary evidence",
            "failure_if_wrong": "terminal artifact remains absent from model projection",
            "cheap_disproof": "replay the retained failed packet and inspect source-bound projection ordering",
        }],
        "full_domain_proof": {"required": False, "provided": False, "method": "", "expected_cases": 0, "covered_cases": 0},
        "cheap_disproof_preflight": [{
            "name": "packet-replay",
            "command": "python3 tools/havenline/production/c0_root_cause_advisor.py --packet fixture.json --out out",
            "falsifies": "terminal artifact excerpt is absent or loses source binding",
        }],
        "counterexamples_considered": [{"case": "large successful domain log sorts before terminal device log", "why_covered": "terminal disposition/path priority is explicit"}],
        "blast_radius_hypotheses": ["secondary context may shrink but cannot displace terminal evidence"],
        "residual_unknowns": [],
    }


def accepted_plan(two_groups=False):
    groups = [layout_group()]
    if two_groups:
        groups.append(tooling_group())
    return {
        "schema_version": 1,
        "task_id": "T10",
        "failed_candidate": "a" * 40,
        "diagnosis_id": "C0-T10-123",
        "c0_report_path": "Docs/Production/T10/C0_ROOT_CAUSE.json",
        "c0_report_sha256": "d" * 64,
        "repair_sufficiency": {
            "repair_groups": groups,
            "evidence_frontier": {
                "complete": True,
                "diagnosed_through_candidate": "a" * 40,
                "latest_observed_failed_candidate": "a" * 40,
                "observations": [],
                "unclassified_failures": [],
            },
            "cross_group_interactions": ["layout exhaustiveness feeds better terminal diagnostics; neither group lowers task quality gates"],
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

    def test_mixed_plan_supports_distinct_failure_families_and_strategies(self):
        report = review(c0(two_blockers=True), accepted_plan(two_groups=True))
        self.assertTrue(report["passed"], report)
        self.assertEqual(2, report["group_count"])
        self.assertTrue(report["full_blocker_coverage"])

    def test_post_diagnosis_failure_can_bind_to_existing_group(self):
        plan = accepted_plan()
        newer = "b" * 40
        plan["repair_sufficiency"]["evidence_frontier"]["latest_observed_failed_candidate"] = newer
        plan["repair_sufficiency"]["evidence_frontier"]["observations"] = [{
            "run_id": 12345,
            "candidate": newer,
            "disposition": "BOUND_TO_EXISTING_GROUP",
            "group_id": "layout-feasibility",
            "evidence": ["new blocked/overhead projection violates the same containment invariant"],
            "reason": "same invariant and same affected placement algorithm",
        }]
        report = review(c0(), plan)
        self.assertTrue(report["passed"], report)
        self.assertIn("POST_DIAGNOSIS_FAILURES_PRESENT", report["risk_codes"])

    def test_unclassified_post_diagnosis_failure_blocks_build(self):
        plan = accepted_plan()
        newer = "b" * 40
        frontier = plan["repair_sufficiency"]["evidence_frontier"]
        frontier["latest_observed_failed_candidate"] = newer
        frontier["unclassified_failures"] = [{"run_id": 12345, "candidate": newer}]
        report = review(c0(), plan)
        self.assertEqual("INSUFFICIENT_EVIDENCE", report["outcome"])
        self.assertIn("POST_DIAGNOSIS_FAILURES_UNCLASSIFIED", report["evidence_gaps"])

    def test_new_failure_requiring_c0_blocks_build(self):
        plan = accepted_plan()
        newer = "b" * 40
        frontier = plan["repair_sufficiency"]["evidence_frontier"]
        frontier["latest_observed_failed_candidate"] = newer
        frontier["observations"] = [{
            "run_id": 12345,
            "candidate": newer,
            "disposition": "NEW_FAILURE_REQUIRES_C0",
            "evidence": ["new causal surface not represented by the diagnosed blocker set"],
            "reason": "cannot bind to an existing failure family",
        }]
        report = review(c0(), plan)
        self.assertEqual("INSUFFICIENT_EVIDENCE", report["outcome"])
        self.assertTrue(any("NEW_FAILURE_REQUIRES_C0" in x for x in report["evidence_gaps"]))

    def test_frontier_must_bind_to_c0_diagnosis_boundary(self):
        root = c0()
        root["latest_failed_candidate"] = "c" * 40
        report = review(root, accepted_plan())
        self.assertFalse(report["passed"])
        self.assertIn("EVIDENCE_FRONTIER_DIAGNOSIS_BOUNDARY_MISMATCH", report["rejections"])

    def test_exact_c0_hash_binding_rejects_substituted_diagnosis_bytes(self):
        report = review(c0(), accepted_plan(), "e" * 64)
        self.assertFalse(report["passed"])
        self.assertIn("C0_REPORT_HASH_MISMATCH", report["rejections"])
        self.assertTrue(review(c0(), accepted_plan(), "d" * 64)["passed"])

    def test_root_cause_binding_is_exact(self):
        plan = accepted_plan()
        plan["repair_sufficiency"]["repair_groups"][0]["blocker_coverage"][0]["diagnosed_root_cause"] = "generic label problem"
        report = review(c0(), plan)
        self.assertTrue(any("ROOT_CAUSE_BINDING_MISMATCH" in x for x in report["rejections"]))

    def test_exhaustive_claim_requires_collection_evidence(self):
        plan = accepted_plan()
        plan["repair_sufficiency"]["repair_groups"][0]["failure_family"]["collection_evidence"] = []
        report = review(c0(), plan)
        self.assertTrue(any("EXHAUSTIVE_COLLECTION_EVIDENCE_REQUIRED" in x for x in report["rejections"]))

    def test_current_style_scalar_patch_after_two_attempts_is_rejected(self):
        plan = accepted_plan()
        group = plan["repair_sufficiency"]["repair_groups"][0]
        group["strategy_kind"] = "SCALAR_TUNING"
        group["why_materially_different"] = "smaller pixel size"
        group["full_domain_proof"]["provided"] = False
        group["full_domain_proof"]["covered_cases"] = 1
        report = review(c0(), plan)
        self.assertFalse(report["passed"])
        self.assertEqual("REPAIR_PLAN_REJECTED", report["outcome"])
        self.assertIn("SERIAL_SCALAR_PATCH_RISK", report["risk_codes"])
        self.assertTrue(any("REPEATED_SCALAR_FIX_REQUIRES_FULL_DOMAIN_PROOF" in x for x in report["rejections"]))

    def test_missing_exhaustive_observable_set_returns_insufficient_evidence(self):
        plan = accepted_plan()
        plan["repair_sufficiency"]["repair_groups"][0]["failure_family"]["complete_observable_set_collected"] = False
        report = review(c0(), plan)
        self.assertFalse(report["passed"])
        self.assertEqual("INSUFFICIENT_EVIDENCE", report["outcome"])
        self.assertTrue(any("OBSERVABLE_FAILURE_FAMILY_NOT_EXHAUSTIVELY_COLLECTED" in x for x in report["evidence_gaps"]))

    def test_unknown_cases_cannot_be_called_fully_closed(self):
        plan = accepted_plan()
        plan["repair_sufficiency"]["repair_groups"][0]["failure_family"]["unexecuted_or_unknown_cases"] = ["phone_20_9/blocked/overhead"]
        report = review(c0(), plan)
        self.assertEqual("REPAIR_PLAN_REJECTED", report["outcome"])
        self.assertTrue(any("OVERCLAIMED_FAILURE_FAMILY_CLOSURE" in x for x in report["rejections"]))

    def test_every_c0_blocker_is_assigned_exactly_once_across_groups(self):
        root = c0(two_blockers=True)
        report = review(root, accepted_plan(two_groups=False))
        self.assertIn("REPAIR_GROUPS_MUST_COVER_EVERY_C0_BLOCKER_EXACTLY_ONCE", report["rejections"])
        plan = accepted_plan(two_groups=True)
        plan["repair_sufficiency"]["repair_groups"][1]["blocker_ids"] = ["C0-T10-B053", "C0-T10-B060"]
        report = review(root, plan)
        self.assertIn("C0_BLOCKER_ASSIGNED_TO_MULTIPLE_REPAIR_GROUPS", report["rejections"])

    def test_threshold_weakening_is_never_an_accepted_repair(self):
        plan = accepted_plan()
        plan["repair_sufficiency"]["threshold_changes"] = ["C3 >9.0 becomes >=8.0"]
        report = review(c0(), plan)
        self.assertFalse(report["passed"])
        self.assertIn("CRITIC_OR_QUALITY_THRESHOLD_CHANGE_FORBIDDEN", report["rejections"])
        self.assertFalse(report["thresholds_unchanged"])

    def test_product_defect_cannot_be_closed_by_evidence_only_strategy(self):
        plan = accepted_plan()
        plan["repair_sufficiency"]["repair_groups"][0]["strategy_kind"] = "EVIDENCE_ONLY"
        report = review(c0(product=True), plan)
        self.assertTrue(any("PRODUCT_DEFECT_REQUIRES_CAUSAL_PRODUCT_STRATEGY" in x for x in report["rejections"]))

    def test_incomplete_c0_never_authorizes_build(self):
        root = c0()
        root["validated"] = False
        report = review(root, accepted_plan())
        self.assertFalse(report["passed"])
        self.assertEqual("INSUFFICIENT_EVIDENCE", report["outcome"])
        self.assertEqual("COLLECT_NAMED_EVIDENCE", report["builder_action"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
