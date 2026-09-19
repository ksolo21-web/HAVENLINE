#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SCALAR_STRATEGIES = {"SCALAR_TUNING", "CONFIGURATION_TUNING", "CONSTANT_ADJUSTMENT"}
CAUSAL_STRATEGIES = {"ALGORITHM", "ARCHITECTURE", "CONTRACT", "PRODUCT_LOGIC", "TOOLING", "GOVERNANCE"} | SCALAR_STRATEGIES
NON_PRODUCT_STRATEGIES = {"EVIDENCE_ONLY", "TEST_ONLY", "DIAGNOSTIC_ONLY"}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def review(c0: dict, plan: dict) -> dict:
    reject: list[str] = []
    evidence_gaps: list[str] = []
    risk_codes: list[str] = []

    c0_ready = (
        c0.get("critic_id") == "C0"
        and c0.get("non_voting") is True
        and c0.get("validated") is True
        and c0.get("diagnosis_status") == "DIAGNOSIS_COMPLETE"
        and c0.get("complete_known_blocker_set") is True
        and c0.get("builder_action") in {"REPAIR", "FREEZE_AND_VALIDATE"}
    )
    if not c0_ready:
        evidence_gaps.append("C0_COMPLETE_DIAGNOSIS_REQUIRED")

    task = c0.get("task_id")
    if plan.get("schema_version") != 1 or plan.get("task_id") != task:
        reject.append("REPAIR_PLAN_TASK_BINDING_INVALID")
    if plan.get("failed_candidate") != c0.get("failed_candidate"):
        reject.append("REPAIR_PLAN_FAILED_CANDIDATE_MISMATCH")
    if plan.get("diagnosis_id") != c0.get("diagnosis_id"):
        reject.append("REPAIR_PLAN_DIAGNOSIS_MISMATCH")

    suff = _dict(plan.get("repair_sufficiency"))
    if not suff:
        reject.append("REPAIR_SUFFICIENCY_SECTION_REQUIRED")
        suff = {}

    family = _dict(suff.get("failure_family"))
    strategy = _text(suff.get("strategy_kind")).upper()
    same_family_attempt_count = suff.get("same_family_attempt_count")
    prior_attempts = _list(suff.get("prior_attempts"))
    blocker_coverage = _list(suff.get("blocker_coverage"))
    domain = _dict(suff.get("full_domain_proof"))
    preflights = _list(suff.get("cheap_disproof_preflight"))
    counterexamples = _list(suff.get("counterexamples_considered"))
    blast = _list(suff.get("blast_radius_hypotheses"))
    residual_unknowns = _list(suff.get("residual_unknowns"))
    threshold_changes = _list(suff.get("threshold_changes"))

    for field in ("id", "invariant"):
        if not _text(family.get(field)):
            reject.append(f"FAILURE_FAMILY_{field.upper()}_REQUIRED")
    dimensions = _list(family.get("scope_dimensions"))
    if not dimensions or any(not _text(x) for x in dimensions):
        reject.append("FAILURE_FAMILY_SCOPE_DIMENSIONS_REQUIRED")
    known_failed = _list(family.get("known_failed_cases"))
    if not known_failed:
        reject.append("KNOWN_FAILED_CASES_REQUIRED")
    unknown = _list(family.get("unexecuted_or_unknown_cases"))

    if strategy not in CAUSAL_STRATEGIES | NON_PRODUCT_STRATEGIES:
        reject.append("STRATEGY_KIND_INVALID")
    if not _text(suff.get("causal_mechanism")):
        reject.append("CAUSAL_MECHANISM_REQUIRED")
    if not _text(suff.get("why_this_fixes_cause")):
        reject.append("WHY_THIS_FIXES_CAUSE_REQUIRED")
    if not _text(suff.get("why_materially_different")):
        reject.append("WHY_MATERIALLY_DIFFERENT_REQUIRED")

    if not isinstance(same_family_attempt_count, int) or same_family_attempt_count < 0:
        reject.append("SAME_FAMILY_ATTEMPT_COUNT_INVALID")
        same_family_attempt_count = 0
    recorded_same_family = sum(1 for row in prior_attempts if isinstance(row, dict) and row.get("same_family") is True)
    if recorded_same_family > same_family_attempt_count:
        reject.append("PRIOR_ATTEMPTS_EXCEED_DECLARED_COUNT")
    if same_family_attempt_count > 0 and not prior_attempts:
        reject.append("PRIOR_ATTEMPTS_REQUIRED")
    if same_family_attempt_count >= 2:
        risk_codes.append("REPEATED_FAILURE_FAMILY")
        if len(_text(suff.get("why_materially_different"))) < 24:
            reject.append("MATERIAL_DIFFERENCE_NOT_JUSTIFIED")

    product_blockers = {
        str(row.get("id"))
        for row in _list(c0.get("blockers"))
        if isinstance(row, dict) and row.get("classification") == "PRODUCT_DEFECT"
    }
    if product_blockers and strategy in NON_PRODUCT_STRATEGIES:
        reject.append("PRODUCT_DEFECT_REQUIRES_CAUSAL_PRODUCT_STRATEGY")

    blocker_ids = {str(row.get("id")) for row in _list(c0.get("blockers")) if isinstance(row, dict) and row.get("id")}
    covered = {str(row.get("blocker_id")) for row in blocker_coverage if isinstance(row, dict) and row.get("blocker_id")}
    if blocker_ids != covered:
        reject.append("EVERY_C0_BLOCKER_REQUIRES_SUFFICIENCY_COVERAGE")
    for row in blocker_coverage:
        if not isinstance(row, dict):
            reject.append("BLOCKER_COVERAGE_ENTRY_INVALID")
            continue
        bid = _text(row.get("blocker_id")) or "<missing>"
        for key in ("why_fix_changes_cause", "expected_result", "failure_if_wrong", "cheap_disproof"):
            if not _text(row.get(key)):
                reject.append(f"{bid}:{key.upper()}_REQUIRED")

    exhaustive_required = family.get("observable_exhaustive_collection_required") is True
    complete_observable = family.get("complete_observable_set_collected") is True
    if exhaustive_required and not complete_observable:
        evidence_gaps.append("OBSERVABLE_FAILURE_FAMILY_NOT_EXHAUSTIVELY_COLLECTED")
    if family.get("full_failure_family_closed_by_design") is True and unknown:
        reject.append("OVERCLAIMED_FAILURE_FAMILY_CLOSURE")

    domain_required = domain.get("required") is True
    domain_provided = domain.get("provided") is True
    expected_cases = domain.get("expected_cases")
    covered_cases = domain.get("covered_cases")
    if domain_required and not domain_provided:
        reject.append("FULL_DOMAIN_PROOF_REQUIRED")
    if domain_provided:
        if not _text(domain.get("method")):
            reject.append("FULL_DOMAIN_PROOF_METHOD_REQUIRED")
        if isinstance(expected_cases, int) and expected_cases > 0:
            if covered_cases != expected_cases:
                reject.append("FULL_DOMAIN_PROOF_CASE_COUNT_MISMATCH")

    if same_family_attempt_count >= 2 and strategy in SCALAR_STRATEGIES:
        risk_codes.append("SERIAL_SCALAR_PATCH_RISK")
        if not domain_provided:
            reject.append("REPEATED_SCALAR_FIX_REQUIRES_FULL_DOMAIN_PROOF")

    if same_family_attempt_count >= 1 and not counterexamples:
        reject.append("COUNTEREXAMPLES_REQUIRED_AFTER_PRIOR_FAILURE")
    for row in counterexamples:
        if not isinstance(row, dict) or not _text(row.get("case")) or not _text(row.get("why_covered")):
            reject.append("COUNTEREXAMPLE_ENTRY_INVALID")

    if not preflights:
        reject.append("CHEAP_DISPROOF_PREFLIGHT_REQUIRED")
    for row in preflights:
        if not isinstance(row, dict):
            reject.append("CHEAP_DISPROOF_PREFLIGHT_ENTRY_INVALID")
            continue
        for key in ("name", "command", "falsifies"):
            if not _text(row.get(key)):
                reject.append(f"PREFLIGHT_{key.upper()}_REQUIRED")

    if not blast:
        reject.append("BLAST_RADIUS_HYPOTHESES_REQUIRED")
    if threshold_changes:
        reject.append("CRITIC_OR_QUALITY_THRESHOLD_CHANGE_FORBIDDEN")

    if suff.get("loop_risk_acknowledged") is not True:
        reject.append("LOOP_RISK_ACKNOWLEDGEMENT_REQUIRED")

    if c0_ready and reject:
        outcome = "REPAIR_PLAN_REJECTED"
        builder_action = "REVISE_REPAIR_PLAN"
    elif evidence_gaps:
        outcome = "INSUFFICIENT_EVIDENCE"
        builder_action = "COLLECT_NAMED_EVIDENCE"
    else:
        outcome = "REPAIR_PLAN_ACCEPTED"
        builder_action = "BUILD_BOUNDED_REPAIR"

    risk_rank = 0
    if same_family_attempt_count >= 1:
        risk_rank = 1
    if same_family_attempt_count >= 2 or "SERIAL_SCALAR_PATCH_RISK" in risk_codes:
        risk_rank = 2
    if reject:
        risk_rank = max(risk_rank, 2)
    loop_risk = ["LOW", "MEDIUM", "HIGH"][risk_rank]

    return {
        "schema_version": 1,
        "critic_id": "C0R",
        "name": "Repair Sufficiency Critic",
        "non_voting": True,
        "approval_critic": False,
        "read_only": True,
        "task_id": task,
        "diagnosis_id": c0.get("diagnosis_id"),
        "failed_candidate": c0.get("failed_candidate"),
        "outcome": outcome,
        "builder_action": builder_action,
        "loop_risk": loop_risk,
        "risk_codes": sorted(set(risk_codes)),
        "rejections": sorted(set(reject)),
        "evidence_gaps": sorted(set(evidence_gaps)),
        "full_blocker_coverage": blocker_ids == covered and bool(blocker_ids),
        "same_family_attempt_count": same_family_attempt_count,
        "thresholds_unchanged": not threshold_changes,
        "may_approve_task": False,
        "may_score_gameplay": False,
        "may_lower_C1_C11_thresholds": False,
        "passed": outcome == "REPAIR_PLAN_ACCEPTED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Non-voting C0R repair-sufficiency and anti-loop critic")
    parser.add_argument("--c0", required=True)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    c0_path = Path(args.c0)
    plan_path = Path(args.plan)
    c0 = json.loads(c0_path.read_text())
    plan = json.loads(plan_path.read_text())
    report = review(c0, plan)
    report["input_bindings"] = {
        "c0_path": str(c0_path),
        "c0_sha256": _digest(c0_path),
        "plan_path": str(plan_path),
        "plan_sha256": _digest(plan_path),
    }
    rendered = json.dumps(report, indent=2) + "\n"
    print(rendered, end="")
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered)
    return 0 if report["passed"] else (3 if report["outcome"] == "INSUFFICIENT_EVIDENCE" else 2)


if __name__ == "__main__":
    raise SystemExit(main())
