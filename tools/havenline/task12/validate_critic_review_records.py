#!/usr/bin/env python3
"""Validate T12 critic-review record template or future resolved reviews.

Template mode freezes the exact T12-specific mandatory dimensions and critic
provenance rules. --require-resolved enforces strict >9.0 on every mandatory
dimension, evidence on every dimension, zero unresolved defects, exact candidate
identity, and genuine independent-review flags for C2/C3/C4/C7. C6 remains the
quantitative specialist gate rather than a fake independent-model review.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[3]
DEFAULT_PATH = ROOT / "Docs" / "Production" / "T12" / "CRITIC_REVIEW_RECORD_TEMPLATE.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")

EXPECTED_DIMENSIONS = {
    "C2": {
        "state_integrity",
        "authoritative_transition_truth",
        "objective_freshness",
        "upstream_id_integrity",
        "cross_view_consistency",
    },
    "C3": {
        "core_loop_reinforcement",
        "no_action_button_growth",
        "no_management_substitution",
        "physical_world_response",
        "spend_blind_eligibility",
    },
    "C4": {
        "current_and_next_clarity",
        "milestone_state_clarity",
        "causal_world_change_readability",
        "prerequisite_explainability",
        "adaptive_layout_readability",
    },
    "C6": {
        "dataset_load_parse_validation",
        "current_next_query_cost",
        "milestone_prerequisite_query_cost",
        "allocation_object_growth",
        "event_history_bounds",
        "no_per_frame_full_rebuild",
        "integrated_scene_telemetry",
    },
    "C7": {
        "meaningful_every_level",
        "no_boring_or_empty_stretches",
        "visible_cadence_quality",
        "major_milestone_meaning",
        "no_impossible_chain",
        "no_stat_only_substitute",
        "bounded_t13_interface",
    },
}
INDEPENDENT = {"C2", "C3", "C4", "C7"}


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_record(data: dict[str, Any], *, require_resolved: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    if data.get("task_id") != "T12":
        errors.append("task_id must be T12")
    expected_status = "CRITIC_REVIEWS_COMPLETE" if require_resolved else "PREPARATION_ONLY_CRITIC_REVIEW_TEMPLATE"
    if data.get("status") != expected_status:
        errors.append(f"status must be {expected_status} in this mode")

    candidate_source = data.get("candidate_source")
    if require_resolved:
        if not isinstance(candidate_source, str) or SHA40.fullmatch(candidate_source) is None:
            errors.append("resolved candidate_source must be exact lowercase 40-hex SHA")
    elif candidate_source != "<T12_CANDIDATE_SHA>":
        errors.append("template candidate_source placeholder drifted")

    acceptance = data.get("acceptance")
    if not isinstance(acceptance, dict):
        errors.append("acceptance must be an object")
        acceptance = {}
    if acceptance.get("operator") != ">" or acceptance.get("threshold") != 9.0 or acceptance.get("unrounded") is not True:
        errors.append("critic acceptance rule must remain strictly >9.0 unrounded")
    if acceptance.get("target") != 10.0 or acceptance.get("no_average_waiver") is not True:
        errors.append("critic target/no-average-waiver rule drifted")
    if acceptance.get("zero_unresolved_mandatory_defects") is not True:
        errors.append("critic reviews must require zero unresolved mandatory defects")

    critics = data.get("critics")
    if not isinstance(critics, dict) or set(critics) != set(EXPECTED_DIMENSIONS):
        errors.append("critics must contain exactly C2,C3,C4,C6,C7")
        critics = {}

    total_dimensions = 0
    global_minimum: float | None = None
    minimum_by_critic: dict[str, float | None] = {}

    for critic, expected_ids in EXPECTED_DIMENSIONS.items():
        row = critics.get(critic)
        if not isinstance(row, dict):
            errors.append(f"missing critic record {critic}")
            minimum_by_critic[critic] = None
            continue

        required_independence = critic in INDEPENDENT
        if row.get("independence_required") is not required_independence:
            errors.append(f"{critic} independence_required must be {required_independence}")
        if critic == "C6" and row.get("quantitative_specialist_gate") is not True:
            errors.append("C6 must remain the quantitative specialist gate")
        if critic != "C6" and "quantitative_specialist_gate" in row:
            errors.append(f"{critic} must not be labeled as quantitative specialist gate")

        dimensions = row.get("dimensions")
        if not isinstance(dimensions, list):
            errors.append(f"{critic}.dimensions must be a list")
            minimum_by_critic[critic] = None
            continue
        ids: list[str] = []
        scores: list[float] = []
        for index, dimension in enumerate(dimensions):
            total_dimensions += 1
            prefix = f"{critic}.dimensions[{index}]"
            if not isinstance(dimension, dict):
                errors.append(f"{prefix} must be an object")
                continue
            dim_id = dimension.get("id")
            if not isinstance(dim_id, str) or not dim_id:
                errors.append(f"{prefix}.id must be non-empty")
                continue
            ids.append(dim_id)
            if dimension.get("mandatory") is not True:
                errors.append(f"{critic}.{dim_id} must remain mandatory")
            if not nonempty(dimension.get("description")):
                errors.append(f"{critic}.{dim_id} description must be non-empty")

            score = dimension.get("score")
            evidence_refs = dimension.get("evidence_refs")
            unresolved = dimension.get("unresolved_defects")
            if not isinstance(evidence_refs, list):
                errors.append(f"{critic}.{dim_id}.evidence_refs must be a list")
                evidence_refs = []
            if not isinstance(unresolved, list):
                errors.append(f"{critic}.{dim_id}.unresolved_defects must be a list")
                unresolved = []

            if require_resolved:
                if not isinstance(score, (int, float)) or isinstance(score, bool):
                    errors.append(f"{critic}.{dim_id} score must be numeric")
                else:
                    numeric = float(score)
                    scores.append(numeric)
                    if numeric <= 9.0:
                        errors.append(f"{critic}.{dim_id} score {numeric} is not strictly >9.0")
                if not evidence_refs or any(not nonempty(ref) for ref in evidence_refs):
                    errors.append(f"{critic}.{dim_id} requires non-empty evidence refs")
                if unresolved:
                    errors.append(f"{critic}.{dim_id} has unresolved mandatory defects")
            else:
                if score is not None:
                    errors.append(f"template {critic}.{dim_id} score must remain null")
                if evidence_refs != []:
                    errors.append(f"template {critic}.{dim_id} evidence_refs must remain empty")
                if unresolved != []:
                    errors.append(f"template {critic}.{dim_id} unresolved_defects must remain empty")

        if set(ids) != expected_ids or len(ids) != len(expected_ids):
            errors.append(f"{critic} dimension IDs must be exactly {sorted(expected_ids)}")

        if require_resolved:
            if required_independence and row.get("independent") is not True:
                errors.append(f"{critic} requires genuine independent-review flag")
            if not nonempty(row.get("reviewer_runtime_id")):
                errors.append(f"{critic} requires reviewer_runtime_id provenance")
            if not nonempty(row.get("review_evidence_ref")):
                errors.append(f"{critic} requires review_evidence_ref provenance")
            minimum = min(scores) if len(scores) == len(expected_ids) else None
            minimum_by_critic[critic] = minimum
            if minimum is not None:
                global_minimum = minimum if global_minimum is None else min(global_minimum, minimum)
        else:
            if row.get("independent") is not None:
                errors.append(f"template {critic}.independent must remain null")
            if row.get("reviewer_runtime_id") != "" or row.get("review_evidence_ref") != "":
                errors.append(f"template {critic} provenance fields must remain blank")
            minimum_by_critic[critic] = None

    return {
        "passed": not errors,
        "mode": "resolved" if require_resolved else "template",
        "critic_count": len(critics),
        "mandatory_dimension_count": total_dimensions,
        "minimum_by_critic": minimum_by_critic,
        "global_minimum_mandatory_dimension_score": global_minimum,
        "score_averaging_used": False,
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_PATH.relative_to(ROOT)))
    parser.add_argument("--require-resolved", action="store_true")
    args = parser.parse_args()
    data = json.loads((ROOT / args.input).read_text())
    result = validate_record(data, require_resolved=args.require_resolved)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
