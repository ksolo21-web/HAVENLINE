from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

from repair_sufficiency_critic import ROOT, _stable_digest, canonical_threshold_snapshot, review as _review


def review(root, plan, c0_sha256=None, threshold_snapshot=None, expected_repair_intelligence_sha256=None):
    expected = expected_repair_intelligence_sha256 or _stable_digest({
        key: root.get(key) for key in ("failure_family_history", "full_domain_proofs", "failure_frontier")
    })
    return _review(root, plan, c0_sha256, threshold_snapshot, expected)


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
    frontier = {
        "complete": True,
        "diagnosed_through_candidate": "a" * 40,
        "latest_observed_failed_candidate": "a" * 40,
        "observations": [],
        "unclassified_failures": [],
    }
    history = [{
        "failure_family_id": "projected-label-feasibility",
        "blocker_ids": ["C0-T10-B053"],
        "prior_attempts": copy.deepcopy(layout_group()["prior_attempts"]),
    }]
    if two_blockers:
        history.append({
            "failure_family_id": "diagnostic-terminal-evidence-loss",
            "blocker_ids": ["C0-T10-B060"],
            "prior_attempts": copy.deepcopy(tooling_group()["prior_attempts"]),
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
        "failure_frontier": frontier,
        "failure_family_history": history,
        "full_domain_proofs": [{
            "failure_family_id": "projected-label-feasibility",
            "proof": copy.deepcopy(layout_group()["full_domain_proof"]),
        }],
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
        "causal_mechanism": "ALGORITHM_REPLACEMENT[_label_candidate,placement_found]",
        "why_this_fixes_cause": "the failed code accepted the last fallback without proving containment; the new solver validates containment before selection",
        "why_materially_different": "replaces scalar symptom tuning with a constrained feasibility algorithm over the whole mandatory projection domain",
        "same_family_attempt_count": 2,
        "operation_contract_version": 2,
        "prior_attempts": [
            {"strategy": "width 1000 to 960", "outcome": "FAILED", "same_family": True, "candidate": "1" * 40, "lesson": "natural measured width was unchanged"},
            {"strategy": "pixel_size 0.006 to 0.0057", "outcome": "PARTIAL", "same_family": True, "candidate": "2" * 40, "lesson": "one state improved while blocked overhead remained infeasible"},
        ],
        "architectural_escalation": {
            "required": True,
            "provided": True,
            "kind": "PLACEMENT_ALGORITHM",
            "reason": "two scalar attempts failed, so the repair replaces terminal fallback with a complete feasibility algorithm",
        },
        "repair_operations": [{
            "operation_kind": "ALGORITHM_REPLACEMENT",
            "target": "terminal fallback",
            "target_symbols": ["_label_candidate", "placement_found"],
            "replaces": "unconditional last-lane acceptance",
            "with": "IMPLEMENT_SYMBOLS[_label_candidate,placement_found]",
            "invariant_enforced": "accepted placements are contained and readable",
        }],
        "scalar_parameters_changed": [],
        "implementation_diff_contract": {
            "comparison_base": "2" * 40,
            "causal_files": ["HavenlineGodot/scripts/world_transform_view.gd"],
            "required_added_markers": [
                {"kind": "FUNCTION_DEFINITION", "value": "_label_candidate"},
                {"kind": "CODE_IDENTIFIER", "value": "placement_found"},
            ],
        },
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
            "dimensions": {"device": 6, "lifecycle_state": 6, "camera_angle": 6},
            "artifact_id": 10584940146,
            "artifact_sha256": "f" * 64,
            "verifier": "verify the source-addressed summary has 216 projections and zero failures",
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
            "collection_evidence": ["source-addressed packet replay covers the retained terminal artifact"],
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
            "evidence_frontier": copy.deepcopy(c0()["failure_frontier"]),
            "cross_group_interactions": ["layout exhaustiveness feeds better terminal diagnostics; neither group lowers task quality gates"],
            "threshold_changes": [],
            "loop_risk_acknowledged": True,
        },
    }


class RepairSufficiencyCriticTests(unittest.TestCase):
    def test_canonical_plan_cannot_redefine_locked_proof_exclusions(self):
        root = json.loads((ROOT / "Docs/Production/T10/C0_ROOT_CAUSE.json").read_text())
        plan = json.loads((ROOT / "Docs/Production/T10/REPAIR_PLAN.json").read_text())
        group = next(row for row in plan["repair_sufficiency"]["repair_groups"] if row["group_id"] == "layout-feasibility")
        contract = group["implementation_diff_contract"]
        contract["proof_irrelevant_exact_lines"] = ['\treturn "READY".repeat(100)']
        contract["proof_relevant_sha256"] = "0" * 64
        c0_sha = hashlib.sha256((ROOT / "Docs/Production/T10/C0_ROOT_CAUSE.json").read_bytes()).hexdigest()
        report = review(root, plan, c0_sha)
        self.assertFalse(report["passed"])
        self.assertTrue(any("PROOF_RELEVANT_SOURCE_BINDING_INVALID" in row for row in report["rejections"]), report)

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
        root = c0()
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
        root["failure_frontier"] = copy.deepcopy(plan["repair_sufficiency"]["evidence_frontier"])
        report = review(root, plan)
        self.assertTrue(report["passed"], report)
        self.assertIn("POST_DIAGNOSIS_FAILURES_PRESENT", report["risk_codes"])

    def test_unclassified_post_diagnosis_failure_blocks_build(self):
        plan = accepted_plan()
        root = c0()
        newer = "b" * 40
        frontier = plan["repair_sufficiency"]["evidence_frontier"]
        frontier["latest_observed_failed_candidate"] = newer
        frontier["unclassified_failures"] = [{"run_id": 12345, "candidate": newer}]
        root["failure_frontier"] = copy.deepcopy(frontier)
        report = review(root, plan)
        self.assertEqual("INSUFFICIENT_EVIDENCE", report["outcome"])
        self.assertIn("POST_DIAGNOSIS_FAILURES_UNCLASSIFIED", report["evidence_gaps"])

    def test_new_failure_requiring_c0_blocks_build(self):
        plan = accepted_plan()
        root = c0()
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
        root["failure_frontier"] = copy.deepcopy(frontier)
        report = review(root, plan)
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

    def test_validated_machine_identifiers_are_not_scalar_prose(self):
        def fixture():
            plan = accepted_plan()
            group = plan["repair_sufficiency"]["repair_groups"][0]
            symbols = ["decoded_failure_logs", "structured_grounding_fragments", "compact_model_projection"]
            group["repair_operations"][0].update(operation_kind="EVIDENCE_ARCHITECTURE_CHANGE", target_symbols=symbols)
            group["repair_operations"][0]["with"] = "IMPLEMENT_SYMBOLS[" + ",".join(symbols) + "]"
            group["causal_mechanism"] = "EVIDENCE_ARCHITECTURE_CHANGE[" + ",".join(symbols) + "]"
            group["implementation_diff_contract"]["required_added_markers"] = [
                {"kind": "FUNCTION_DEFINITION", "value": symbol} for symbol in symbols]
            return plan, group
        plan, group = fixture()
        result = review(c0(), plan)
        self.assertTrue(result["passed"], result["rejections"])
        self.assertNotIn("SERIAL_SCALAR_PATCH_RISK", result["risk_codes"])
        for mutation in ("empty", "invalid_kind", "missing_target", "invalid_symbol", "appended", "near_match", "why", "strategy", "with", "target", "invariant_enforced", "difference", "escalation"):
            plan, group = fixture()
            if mutation == "empty": group["repair_operations"] = []
            elif mutation == "invalid_kind": group["repair_operations"][0]["operation_kind"] = "UNSUPPORTED"
            elif mutation == "missing_target": group["repair_operations"][0].pop("target")
            elif mutation == "invalid_symbol": group["repair_operations"][0]["target_symbols"] = ["compact-model-projection"]
            elif mutation == "appended": group["causal_mechanism"] += "; reduce projection scale to 0.95"
            elif mutation == "near_match": group["causal_mechanism"] = group["causal_mechanism"].replace("[", "[ ")
            elif mutation == "why": group["why_this_fixes_cause"] = "reduce projection scale to 0.95"
            elif mutation == "strategy": group["strategy_kind"] = "SCALAR_TUNING"
            elif mutation in {"with", "target", "invariant_enforced"}:
                group["repair_operations"][0][mutation] = "set timeout limit to 2000 and shrink projection scale to 0.95"
            elif mutation == "difference": group["why_materially_different"] = "set timeout limit to 2000 and shrink projection scale to 0.95"
            elif mutation == "escalation": group["architectural_escalation"]["reason"] = "set timeout limit to 2000 and shrink projection scale to 0.95"
            with self.subTest(mutation=mutation):
                result = review(c0(), plan)
                self.assertFalse(result["passed"])
                self.assertIn("SERIAL_SCALAR_PATCH_RISK", result["risk_codes"])

    def test_prose_fields_do_not_form_a_synthetic_scalar_sentence(self):
        plan = accepted_plan(); group = plan["repair_sufficiency"]["repair_groups"][0]
        group["why_this_fixes_cause"] = "The geometry proof remains authoritative."
        group["why_materially_different"] = "Repair the missing caller-to-callee authority contract."
        self.assertTrue(review(c0(), plan)["passed"])

    def test_repeated_replacement_is_typed_not_quantity_prose(self):
        bad = ["cap watchdog duration at 2000 seconds", "prefer a 2000-second deadline",
               "replace the prior sizing number with 54 ten-thousandths",
               "cap watchdog duration at two thousand seconds", "prefer a ２０００-second deadline",
               "IMPLEMENT_SYMBOLS[_label_candidate,placement_found]; cap duration at 2000",
               " IMPLEMENT_SYMBOLS[_label_candidate,placement_found]",
               "IMPLEMENT_SYMBOLS[placement_found,_label_candidate]",
               "IMPLEMENT_SYMBOLS[_label_candidate,placement_found,extra]",
               "IMPLEMENT_SYMBOLS[_label_candidate, placement_found]"]
        for replacement in bad:
            plan = accepted_plan()
            group = plan["repair_sufficiency"]["repair_groups"][0]
            group["repair_operations"][0]["with"] = replacement
            with self.subTest(replacement=replacement):
                result = review(c0(), plan)
                self.assertFalse(result["passed"])
                self.assertIn("layout-feasibility:REPEATED_REPAIR_REPLACEMENT_MUST_BE_MACHINE_STRUCTURED", result["rejections"])
                self.assertIn("SERIAL_SCALAR_PATCH_RISK", result["risk_codes"])
        for mutation in ("duplicate", "symbol_whitespace", "old_version", "missing_version"):
            plan = accepted_plan(); group = plan["repair_sufficiency"]["repair_groups"][0]
            operation = group["repair_operations"][0]
            if mutation == "duplicate": operation["target_symbols"].append("placement_found")
            elif mutation == "symbol_whitespace": operation["target_symbols"][0] += " "
            elif mutation == "old_version": group["operation_contract_version"] = 1
            else: group.pop("operation_contract_version")
            operation["with"] = "IMPLEMENT_SYMBOLS[" + ",".join(operation["target_symbols"]) + "]"
            with self.subTest(mutation=mutation):
                self.assertFalse(review(c0(), plan)["passed"])

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
        self.assertTrue(any("REPEATED_SCALAR_FIX_REQUIRES_ARCHITECTURAL_REPAIR" in x for x in report["rejections"]))

    def test_scalar_patch_cannot_hide_behind_tooling_label(self):
        plan = accepted_plan()
        group = plan["repair_sufficiency"]["repair_groups"][0]
        group["strategy_kind"] = "TOOLING"
        group["causal_mechanism"] = "reduce pixel_size from 0.0057 to 0.0054 until the observed rectangle fits"
        report = review(c0(), plan)
        self.assertFalse(report["passed"])
        self.assertIn("SERIAL_SCALAR_PATCH_RISK", report["risk_codes"])
        self.assertTrue(any("REPEATED_SCALAR_FIX_REQUIRES_ARCHITECTURAL_REPAIR" in x for x in report["rejections"]))

    def test_attempt_count_and_history_are_derived_from_c0(self):
        for mutation in ("count", "erase", "rewrite"):
            plan = accepted_plan()
            group = plan["repair_sufficiency"]["repair_groups"][0]
            if mutation == "count":
                group["same_family_attempt_count"] = 0
            elif mutation == "erase":
                group["prior_attempts"] = []
            else:
                group["prior_attempts"][0]["outcome"] = "SUCCESS"
            report = review(c0(), plan)
            with self.subTest(mutation=mutation):
                self.assertTrue(any("C0_ATTEMPT_HISTORY_BINDING_MISMATCH" in x for x in report["rejections"]))

    def test_plan_cannot_erase_c0_failure_frontier(self):
        root = c0()
        root["failure_frontier"]["latest_observed_failed_candidate"] = "b" * 40
        root["failure_frontier"]["unclassified_failures"] = [{"run_id": 123, "candidate": "b" * 40}]
        report = review(root, accepted_plan())
        self.assertFalse(report["passed"])
        self.assertIn("C0_FAILURE_FRONTIER_BINDING_MISMATCH", report["rejections"])

    def test_c0_and_plan_cannot_jointly_erase_locked_frontier_or_attempts(self):
        for mutation in ("frontier", "attempts"):
            root = c0()
            plan = accepted_plan()
            if mutation == "frontier":
                root["failure_frontier"] = {
                    "complete": True,
                    "diagnosed_through_candidate": "b" * 40,
                    "latest_observed_failed_candidate": "b" * 40,
                    "observations": [{"run_id": 123, "candidate": "b" * 40}],
                    "unclassified_failures": [],
                }
                plan["repair_sufficiency"]["evidence_frontier"] = copy.deepcopy(root["failure_frontier"])
            expected = _stable_digest({key: root.get(key) for key in ("failure_family_history", "full_domain_proofs", "failure_frontier")})
            if mutation == "frontier":
                root["failure_frontier"] = {
                    "complete": True, "diagnosed_through_candidate": "a" * 40,
                    "latest_observed_failed_candidate": "a" * 40, "observations": [], "unclassified_failures": [],
                }
                plan["repair_sufficiency"]["evidence_frontier"] = copy.deepcopy(root["failure_frontier"])
            else:
                root["failure_family_history"] = []
                group = plan["repair_sufficiency"]["repair_groups"][0]
                group["same_family_attempt_count"] = 0
                group["prior_attempts"] = []
                group.pop("architectural_escalation")
                group.pop("repair_operations")
                group.pop("scalar_parameters_changed")
                group.pop("implementation_diff_contract")
            report = review(root, plan, expected_repair_intelligence_sha256=expected)
            with self.subTest(mutation=mutation):
                self.assertIn("C0_REPAIR_INTELLIGENCE_DIGEST_MISMATCH", report["rejections"])

    def test_full_domain_proof_requires_source_addressed_provenance(self):
        for key in ("dimensions", "artifact_id", "artifact_sha256", "verifier"):
            plan = accepted_plan()
            plan["repair_sufficiency"]["repair_groups"][0]["full_domain_proof"].pop(key)
            report = review(c0(), plan)
            with self.subTest(key=key):
                self.assertTrue(any("FULL_DOMAIN_PROOF_" in x for x in report["rejections"]))

    def test_full_domain_proof_cannot_substitute_a_fake_artifact(self):
        plan = accepted_plan()
        plan["repair_sufficiency"]["repair_groups"][0]["full_domain_proof"]["artifact_sha256"] = "0" * 64
        report = review(c0(), plan)
        self.assertFalse(report["passed"])
        self.assertTrue(any("C0_FULL_DOMAIN_PROOF_BINDING_MISMATCH" in x for x in report["rejections"]))

    def test_c0_and_plan_cannot_jointly_substitute_a_fake_artifact(self):
        root = c0()
        plan = accepted_plan()
        expected = _stable_digest({key: root.get(key) for key in ("failure_family_history", "full_domain_proofs", "failure_frontier")})
        for holder in (root["full_domain_proofs"][0]["proof"], plan["repair_sufficiency"]["repair_groups"][0]["full_domain_proof"]):
            holder["artifact_id"] = 1
            holder["artifact_sha256"] = "z" * 64
            holder["verifier"] = "trust this text"
        report = review(root, plan, expected_repair_intelligence_sha256=expected)
        self.assertFalse(report["passed"])
        self.assertIn("C0_REPAIR_INTELLIGENCE_DIGEST_MISMATCH", report["rejections"])

    def test_scalar_synonym_cannot_hide_behind_architectural_label(self):
        for proposal in (
            "multiply the projection factor by 0.95 for every label",
            "apply a coefficient of 0.95 to glyph dimensions",
            "shrink glyph geometry by five percent",
            "use nine tenths of the current glyph footprint",
            "make every glyph 95% of its former dimensions",
            "render each glyph at nineteen twentieths of its former dimensions",
            "compress each label geometry by one twentieth",
            "cap each caption at 95% of its former extent",
            "give every caption nineteen parts of the former twenty",
            "trim each caption by one part in twenty",
        ):
            plan = accepted_plan()
            group = plan["repair_sufficiency"]["repair_groups"][0]
            group["causal_mechanism"] = proposal
            report = review(c0(), plan)
            with self.subTest(proposal=proposal):
                self.assertFalse(report["passed"])
                self.assertIn("SERIAL_SCALAR_PATCH_RISK", report["risk_codes"])

    def test_repeated_family_requires_structured_non_scalar_operations(self):
        for mutation in ("missing", "scalar", "symbols", "unbound_marker"):
            plan = accepted_plan()
            group = plan["repair_sufficiency"]["repair_groups"][0]
            if mutation == "missing":
                group.pop("repair_operations")
            elif mutation == "scalar":
                group["scalar_parameters_changed"] = [{"target": "projection factor", "after": 0.95}]
            elif mutation == "symbols":
                group["repair_operations"][0].pop("target_symbols")
            else:
                group["implementation_diff_contract"]["required_added_markers"][0]["value"] = "unbound_symbol"
            report = review(c0(), plan)
            with self.subTest(mutation=mutation):
                self.assertFalse(report["passed"])

    def test_canonical_threshold_registry_is_independently_verified(self):
        snapshot = canonical_threshold_snapshot()
        snapshot["critic_matrix"] = dict(snapshot["critic_matrix"], threshold=8.0)
        report = review(c0(), accepted_plan(), threshold_snapshot=snapshot)
        self.assertFalse(report["passed"])
        self.assertIn("CANONICAL_THRESHOLD_POLICY_WEAKENED", report["rejections"])
        self.assertFalse(report["thresholds_unchanged"])
        snapshot = canonical_threshold_snapshot()
        snapshot["critic_matrix_sha256"] = "0" * 64
        report = review(c0(), accepted_plan(), threshold_snapshot=snapshot)
        self.assertIn("CANONICAL_THRESHOLD_POLICY_WEAKENED", report["rejections"])

    def test_full_family_closure_requires_complete_collected_evidence(self):
        plan = accepted_plan()
        family = plan["repair_sufficiency"]["repair_groups"][0]["failure_family"]
        family["complete_observable_set_collected"] = False
        family["observable_exhaustive_collection_required"] = False
        report = review(c0(), plan)
        self.assertTrue(any("FULL_FAMILY_CLOSURE_REQUIRES_COMPLETE_COLLECTION" in x for x in report["rejections"]))

    def test_missing_exhaustive_observable_set_returns_insufficient_evidence(self):
        plan = accepted_plan()
        plan["repair_sufficiency"]["repair_groups"][0]["failure_family"]["complete_observable_set_collected"] = False
        report = review(c0(), plan)
        self.assertFalse(report["passed"])
        self.assertEqual("REPAIR_PLAN_REJECTED", report["outcome"])
        self.assertTrue(any("OBSERVABLE_FAILURE_FAMILY_NOT_EXHAUSTIVELY_COLLECTED" in x for x in report["evidence_gaps"]))
        self.assertTrue(any("FULL_FAMILY_CLOSURE_REQUIRES_COMPLETE_COLLECTION" in x for x in report["rejections"]))

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
