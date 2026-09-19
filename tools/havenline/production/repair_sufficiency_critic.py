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


def _group_review(group: dict, c0_blockers: dict[str, dict]) -> tuple[list[str], list[str], list[str]]:
    reject: list[str] = []
    evidence_gaps: list[str] = []
    risk_codes: list[str] = []

    group_id = _text(group.get("group_id")) or "<missing-group>"
    group_blockers = [str(x) for x in _list(group.get("blocker_ids")) if _text(x)]
    family = _dict(group.get("failure_family"))
    strategy = _text(group.get("strategy_kind")).upper()
    same_family_attempt_count = group.get("same_family_attempt_count")
    prior_attempts = _list(group.get("prior_attempts"))
    blocker_coverage = _list(group.get("blocker_coverage"))
    domain = _dict(group.get("full_domain_proof"))
    preflights = _list(group.get("cheap_disproof_preflight"))
    counterexamples = _list(group.get("counterexamples_considered"))
    blast = _list(group.get("blast_radius_hypotheses"))
    residual_unknowns = _list(group.get("residual_unknowns"))

    if group_id == "<missing-group>":
        reject.append("GROUP_ID_REQUIRED")
    if not group_blockers:
        reject.append(f"{group_id}:BLOCKER_IDS_REQUIRED")
    unknown_blocker_ids = sorted(set(group_blockers) - set(c0_blockers))
    if unknown_blocker_ids:
        reject.append(f"{group_id}:UNKNOWN_C0_BLOCKERS:{','.join(unknown_blocker_ids)}")

    for field in ("id", "invariant"):
        if not _text(family.get(field)):
            reject.append(f"{group_id}:FAILURE_FAMILY_{field.upper()}_REQUIRED")
    dimensions = _list(family.get("scope_dimensions"))
    if not dimensions or any(not _text(x) for x in dimensions):
        reject.append(f"{group_id}:FAILURE_FAMILY_SCOPE_DIMENSIONS_REQUIRED")
    if not _list(family.get("known_failed_cases")):
        reject.append(f"{group_id}:KNOWN_FAILED_CASES_REQUIRED")
    unknown_cases = _list(family.get("unexecuted_or_unknown_cases"))

    if strategy not in CAUSAL_STRATEGIES | NON_PRODUCT_STRATEGIES:
        reject.append(f"{group_id}:STRATEGY_KIND_INVALID")
    for key in ("causal_mechanism", "why_this_fixes_cause", "why_materially_different"):
        if not _text(group.get(key)):
            reject.append(f"{group_id}:{key.upper()}_REQUIRED")

    if not isinstance(same_family_attempt_count, int) or same_family_attempt_count < 0:
        reject.append(f"{group_id}:SAME_FAMILY_ATTEMPT_COUNT_INVALID")
        same_family_attempt_count = 0
    recorded_same_family = sum(1 for row in prior_attempts if isinstance(row, dict) and row.get("same_family") is True)
    if recorded_same_family > same_family_attempt_count:
        reject.append(f"{group_id}:PRIOR_ATTEMPTS_EXCEED_DECLARED_COUNT")
    if same_family_attempt_count > 0 and not prior_attempts:
        reject.append(f"{group_id}:PRIOR_ATTEMPTS_REQUIRED")
    if same_family_attempt_count >= 2:
        risk_codes.append("REPEATED_FAILURE_FAMILY")
        if len(_text(group.get("why_materially_different"))) < 24:
            reject.append(f"{group_id}:MATERIAL_DIFFERENCE_NOT_JUSTIFIED")

    product_blockers = {
        bid for bid in group_blockers
        if c0_blockers.get(bid, {}).get("classification") == "PRODUCT_DEFECT"
    }
    if product_blockers and strategy in NON_PRODUCT_STRATEGIES:
        reject.append(f"{group_id}:PRODUCT_DEFECT_REQUIRES_CAUSAL_PRODUCT_STRATEGY")

    covered = [str(row.get("blocker_id")) for row in blocker_coverage if isinstance(row, dict) and row.get("blocker_id")]
    if set(group_blockers) != set(covered) or len(covered) != len(set(covered)):
        reject.append(f"{group_id}:GROUP_BLOCKERS_REQUIRE_EXACT_SUFFICIENCY_COVERAGE")
    for row in blocker_coverage:
        if not isinstance(row, dict):
            reject.append(f"{group_id}:BLOCKER_COVERAGE_ENTRY_INVALID")
            continue
        bid = _text(row.get("blocker_id")) or "<missing>"
        diagnosed = _text(row.get("diagnosed_root_cause"))
        expected_root = _text(c0_blockers.get(bid, {}).get("root_cause"))
        if not diagnosed:
            reject.append(f"{group_id}:{bid}:DIAGNOSED_ROOT_CAUSE_REQUIRED")
        elif diagnosed != expected_root:
            reject.append(f"{group_id}:{bid}:ROOT_CAUSE_BINDING_MISMATCH")
        for key in ("why_fix_changes_cause", "expected_result", "failure_if_wrong", "cheap_disproof"):
            if not _text(row.get(key)):
                reject.append(f"{group_id}:{bid}:{key.upper()}_REQUIRED")

    exhaustive_required = family.get("observable_exhaustive_collection_required") is True
    complete_observable = family.get("complete_observable_set_collected") is True
    if exhaustive_required and not complete_observable:
        evidence_gaps.append(f"{group_id}:OBSERVABLE_FAILURE_FAMILY_NOT_EXHAUSTIVELY_COLLECTED")
    if exhaustive_required and complete_observable and not _list(family.get("collection_evidence")):
        reject.append(f"{group_id}:EXHAUSTIVE_COLLECTION_EVIDENCE_REQUIRED")
    if family.get("full_failure_family_closed_by_design") is True and (unknown_cases or residual_unknowns):
        reject.append(f"{group_id}:OVERCLAIMED_FAILURE_FAMILY_CLOSURE")

    domain_required = domain.get("required") is True
    domain_provided = domain.get("provided") is True
    expected_cases = domain.get("expected_cases")
    covered_cases = domain.get("covered_cases")
    if domain_required and not domain_provided:
        reject.append(f"{group_id}:FULL_DOMAIN_PROOF_REQUIRED")
    if domain_provided:
        if not _text(domain.get("method")):
            reject.append(f"{group_id}:FULL_DOMAIN_PROOF_METHOD_REQUIRED")
        if isinstance(expected_cases, int) and expected_cases > 0 and covered_cases != expected_cases:
            reject.append(f"{group_id}:FULL_DOMAIN_PROOF_CASE_COUNT_MISMATCH")

    if same_family_attempt_count >= 2 and strategy in SCALAR_STRATEGIES:
        risk_codes.append("SERIAL_SCALAR_PATCH_RISK")
        if not domain_provided:
            reject.append(f"{group_id}:REPEATED_SCALAR_FIX_REQUIRES_FULL_DOMAIN_PROOF")

    if same_family_attempt_count >= 1 and not counterexamples:
        reject.append(f"{group_id}:COUNTEREXAMPLES_REQUIRED_AFTER_PRIOR_FAILURE")
    for row in counterexamples:
        if not isinstance(row, dict) or not _text(row.get("case")) or not _text(row.get("why_covered")):
            reject.append(f"{group_id}:COUNTEREXAMPLE_ENTRY_INVALID")

    if not preflights:
        reject.append(f"{group_id}:CHEAP_DISPROOF_PREFLIGHT_REQUIRED")
    for row in preflights:
        if not isinstance(row, dict):
            reject.append(f"{group_id}:CHEAP_DISPROOF_PREFLIGHT_ENTRY_INVALID")
            continue
        for key in ("name", "command", "falsifies"):
            if not _text(row.get(key)):
                reject.append(f"{group_id}:PREFLIGHT_{key.upper()}_REQUIRED")

    if not blast:
        reject.append(f"{group_id}:BLAST_RADIUS_HYPOTHESES_REQUIRED")

    return reject, evidence_gaps, risk_codes


def review(c0: dict, plan: dict, c0_sha256: str | None = None) -> dict:
    reject: list[str] = []
    evidence_gaps: list[str] = []
    risk_codes: set[str] = set()
    group_reports: list[dict] = []

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
    canonical_c0 = f"Docs/Production/{task}/C0_ROOT_CAUSE.json"
    if plan.get("c0_report_path") != canonical_c0:
        reject.append("CANONICAL_C0_REPORT_PATH_REQUIRED")
    declared_c0_hash = _text(plan.get("c0_report_sha256"))
    if c0_sha256 is not None:
        if len(c0_sha256) != 64 or declared_c0_hash != c0_sha256:
            reject.append("C0_REPORT_HASH_MISMATCH")
    elif declared_c0_hash and len(declared_c0_hash) != 64:
        reject.append("C0_REPORT_HASH_INVALID")

    c0_blockers = {
        str(row.get("id")): row
        for row in _list(c0.get("blockers"))
        if isinstance(row, dict) and row.get("id")
    }
    if c0_ready and not c0_blockers:
        reject.append("COMPLETE_FAILED_C0_REQUIRES_BLOCKERS")

    suff = _dict(plan.get("repair_sufficiency"))
    if not suff:
        reject.append("REPAIR_SUFFICIENCY_SECTION_REQUIRED")
    groups = _list(suff.get("repair_groups"))
    if not groups:
        reject.append("REPAIR_GROUPS_REQUIRED")

    assigned: list[str] = []
    group_ids: list[str] = []
    for raw_group in groups:
        if not isinstance(raw_group, dict):
            reject.append("REPAIR_GROUP_ENTRY_INVALID")
            continue
        group_id = _text(raw_group.get("group_id")) or "<missing-group>"
        group_ids.append(group_id)
        assigned.extend(str(x) for x in _list(raw_group.get("blocker_ids")) if _text(x))
        group_reject, group_gaps, group_risks = _group_review(raw_group, c0_blockers)
        reject.extend(group_reject)
        evidence_gaps.extend(group_gaps)
        risk_codes.update(group_risks)
        group_reports.append({
            "group_id": group_id,
            "blocker_ids": [str(x) for x in _list(raw_group.get("blocker_ids")) if _text(x)],
            "strategy_kind": _text(raw_group.get("strategy_kind")).upper(),
            "same_family_attempt_count": raw_group.get("same_family_attempt_count"),
            "rejections": sorted(set(group_reject)),
            "evidence_gaps": sorted(set(group_gaps)),
            "risk_codes": sorted(set(group_risks)),
            "passed": not group_reject and not group_gaps,
        })

    if len(group_ids) != len(set(group_ids)):
        reject.append("REPAIR_GROUP_IDS_MUST_BE_UNIQUE")
    if len(assigned) != len(set(assigned)):
        reject.append("C0_BLOCKER_ASSIGNED_TO_MULTIPLE_REPAIR_GROUPS")
    if set(assigned) != set(c0_blockers):
        reject.append("REPAIR_GROUPS_MUST_COVER_EVERY_C0_BLOCKER_EXACTLY_ONCE")

    frontier = _dict(suff.get("evidence_frontier"))
    if not frontier:
        reject.append("EVIDENCE_FRONTIER_REQUIRED")
        frontier = {}
    expected_diagnosed_through = _text(c0.get("latest_failed_candidate")) or _text(c0.get("failed_candidate"))
    diagnosed_through = _text(frontier.get("diagnosed_through_candidate"))
    if diagnosed_through != expected_diagnosed_through:
        reject.append("EVIDENCE_FRONTIER_DIAGNOSIS_BOUNDARY_MISMATCH")
    latest_observed = _text(frontier.get("latest_observed_failed_candidate"))
    if not latest_observed or len(latest_observed) != 40:
        reject.append("LATEST_OBSERVED_FAILED_CANDIDATE_REQUIRED")
    if frontier.get("complete") is not True:
        evidence_gaps.append("EVIDENCE_FRONTIER_INCOMPLETE")

    observations = _list(frontier.get("observations"))
    unclassified = _list(frontier.get("unclassified_failures"))
    if unclassified:
        evidence_gaps.append("POST_DIAGNOSIS_FAILURES_UNCLASSIFIED")

    allowed_frontier_dispositions = {
        "BOUND_TO_EXISTING_GROUP",
        "SUPERSEDED",
        "INFRASTRUCTURE_ONLY",
        "NEW_FAILURE_REQUIRES_C0",
    }
    observation_candidates: set[str] = set()
    for index, row in enumerate(observations):
        prefix = f"FRONTIER[{index}]"
        if not isinstance(row, dict):
            reject.append(prefix + ":ENTRY_INVALID")
            continue
        candidate = _text(row.get("candidate"))
        if len(candidate) != 40:
            reject.append(prefix + ":CANDIDATE_INVALID")
        else:
            observation_candidates.add(candidate)
        run_id = row.get("run_id")
        if not isinstance(run_id, int) or run_id <= 0:
            reject.append(prefix + ":RUN_ID_INVALID")
        disposition = _text(row.get("disposition")).upper()
        if disposition not in allowed_frontier_dispositions:
            reject.append(prefix + ":DISPOSITION_INVALID")
        if not _list(row.get("evidence")):
            reject.append(prefix + ":EVIDENCE_REQUIRED")
        if not _text(row.get("reason")):
            reject.append(prefix + ":REASON_REQUIRED")
        if disposition == "BOUND_TO_EXISTING_GROUP":
            group_id = _text(row.get("group_id"))
            if group_id not in set(group_ids):
                reject.append(prefix + ":BOUND_GROUP_UNKNOWN")
        elif disposition == "NEW_FAILURE_REQUIRES_C0":
            evidence_gaps.append(prefix + ":NEW_FAILURE_REQUIRES_C0")
    if latest_observed and latest_observed != diagnosed_through and latest_observed not in observation_candidates:
        reject.append("LATEST_POST_DIAGNOSIS_FAILURE_NOT_REPRESENTED")
    if observations:
        risk_codes.add("POST_DIAGNOSIS_FAILURES_PRESENT")

    raw_threshold_changes = suff.get("threshold_changes")
    if not isinstance(raw_threshold_changes, list):
        reject.append("THRESHOLD_CHANGES_MUST_BE_EXPLICIT_LIST")
        threshold_changes = []
    else:
        threshold_changes = raw_threshold_changes
    if threshold_changes:
        reject.append("CRITIC_OR_QUALITY_THRESHOLD_CHANGE_FORBIDDEN")
    if suff.get("loop_risk_acknowledged") is not True:
        reject.append("LOOP_RISK_ACKNOWLEDGEMENT_REQUIRED")
    interactions = suff.get("cross_group_interactions")
    if not isinstance(interactions, list) or not interactions or any(not _text(x) for x in interactions):
        reject.append("CROSS_GROUP_INTERACTIONS_REQUIRED")

    if c0_ready and reject:
        outcome = "REPAIR_PLAN_REJECTED"
        builder_action = "REVISE_REPAIR_PLAN"
    elif evidence_gaps:
        outcome = "INSUFFICIENT_EVIDENCE"
        builder_action = "COLLECT_NAMED_EVIDENCE"
    else:
        outcome = "REPAIR_PLAN_ACCEPTED"
        builder_action = "BUILD_BOUNDED_REPAIR"

    max_attempts = max(
        [g.get("same_family_attempt_count") for g in groups if isinstance(g, dict) and isinstance(g.get("same_family_attempt_count"), int)]
        or [0]
    )
    risk_rank = 0 if max_attempts == 0 else 1
    if max_attempts >= 2 or "SERIAL_SCALAR_PATCH_RISK" in risk_codes or reject:
        risk_rank = 2

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
        "loop_risk": ["LOW", "MEDIUM", "HIGH"][risk_rank],
        "risk_codes": sorted(risk_codes),
        "rejections": sorted(set(reject)),
        "evidence_gaps": sorted(set(evidence_gaps)),
        "group_reports": group_reports,
        "group_count": len(group_reports),
        "full_blocker_coverage": set(assigned) == set(c0_blockers) and len(assigned) == len(set(assigned)) and bool(c0_blockers),
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
    c0_sha256 = _digest(c0_path)
    report = review(c0, plan, c0_sha256)
    report["input_bindings"] = {
        "c0_path": str(c0_path),
        "c0_sha256": c0_sha256,
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
