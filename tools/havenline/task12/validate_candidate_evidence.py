#!/usr/bin/env python3
"""Validate the prepared T12 candidate-evidence template or a resolved packet.

Default mode validates template structure only. --require-resolved enforces the
future exact-candidate acceptance packet. This never substitutes for verifying
independent reviewer provenance in the review pipeline itself.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[3]
DEFAULT_PATH = ROOT / "Docs" / "Production" / "T12" / "CANDIDATE_EVIDENCE_TEMPLATE.json"

STATIC_REPORTS = {
    "level_100_completeness",
    "prerequisite_dag",
    "practical_progression_coverage",
    "visible_progression_cadence",
    "major_milestone_cadence",
    "spend_blind_audit",
    "stable_id_audit",
    "upstream_authority_audit",
    "one_time_idempotency",
    "later_owner_boundary",
}
SEQUENCES = {"ordinary_level_progression", "visible_progression_hook", "major_milestone"}
CRITICS = {"C2", "C3", "C4", "C6", "C7"}
INDEPENDENT_CRITICS = {"C2", "C3", "C4", "C7"}
GATES = {f"G{i}" for i in range(1, 15)}
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
EXACT_SOURCE_FIELDS = {
    "activation_base",
    "candidate_source",
    "integration_head",
    "authorized_changed_file_manifest_ref",
    "shipping_data_hashes",
    "upstream_sources",
    "validator_source",
}


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def exact_sha(value: Any) -> bool:
    return isinstance(value, str) and SHA40.fullmatch(value) is not None


def validate_packet(data: dict[str, Any], require_resolved: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if data.get("task_id") != "T12":
        errors.append("task_id must be T12")
    if not require_resolved and data.get("status") != "PREPARATION_ONLY_CANDIDATE_EVIDENCE_TEMPLATE":
        errors.append("template status must remain PREPARATION_ONLY_CANDIDATE_EVIDENCE_TEMPLATE")

    source = data.get("exact_source")
    if not isinstance(source, dict):
        errors.append("exact_source must be an object")
        source = {}
    elif set(source) != EXACT_SOURCE_FIELDS:
        errors.append("exact_source fields drifted from frozen provenance contract")
    upstream = source.get("upstream_sources")
    if not isinstance(upstream, dict) or set(upstream) != {"T07", "T08", "T10", "T11"}:
        errors.append("exact_source.upstream_sources must contain exactly T07,T08,T10,T11")
        upstream = {}
    if upstream.get("T07") != "94b3f6c5097356a3857ebd13a77fb1e316eb06ae":
        errors.append("T07 accepted integrated source drifted")
    if upstream.get("T08") != "9d56ea8ae972d0a0705ff8b985e13fab31dde493":
        errors.append("T08 accepted integrated source drifted")

    hashes = source.get("shipping_data_hashes")
    if not isinstance(hashes, dict) or set(hashes) != {
        "progression_levels_v1_json_sha256",
        "progression_milestones_v1_json_sha256",
        "binding_resolution_json_sha256",
    }:
        errors.append("shipping_data_hashes structure drifted")
        hashes = {}

    reports = data.get("static_reports")
    if not isinstance(reports, dict) or set(reports) != STATIC_REPORTS:
        errors.append("static_reports must contain the ten frozen reports")
        reports = {}
    for name, row in reports.items():
        if not isinstance(row, dict) or set(row) != {"status", "evidence_ref"}:
            errors.append(f"static report {name} structure drifted")

    parity = data.get("engine_parity")
    if not isinstance(parity, dict):
        errors.append("engine_parity must be an object")
        parity = {}
    regression = data.get("regression")
    if not isinstance(regression, dict):
        errors.append("regression must be an object")
        regression = {}
    if regression.get("approved_task_range") != "T01-T11":
        errors.append("regression approved_task_range must remain T01-T11")

    sequences = data.get("functional_sequences")
    if not isinstance(sequences, dict) or set(sequences) != SEQUENCES:
        errors.append("functional_sequences must contain the three frozen evidence sequences")
        sequences = {}

    adaptive = data.get("adaptive_readability")
    if not isinstance(adaptive, dict):
        errors.append("adaptive_readability must be an object")
        adaptive = {}
    if adaptive.get("required_if_player_facing_presentation_exists") is not True:
        errors.append("adaptive readability conditional requirement must remain true")
    if adaptive.get("physical_device_native_4k60_certified") is not False:
        errors.append("T12 evidence packet must not claim physical native-4K/60 certification")

    performance = data.get("performance_c6")
    if not isinstance(performance, dict):
        errors.append("performance_c6 must be an object")
        performance = {}
    if performance.get("prebuild_python_benchmark_used_as_shipping_c6") is not False:
        errors.append("prebuild Python benchmark must never be used as shipping C6")

    critics = data.get("critic_reviews")
    if not isinstance(critics, dict) or set(critics) != CRITICS:
        errors.append("critic_reviews must contain exactly C2,C3,C4,C6,C7")
        critics = {}
    for critic, row in critics.items():
        if not isinstance(row, dict):
            errors.append(f"critic {critic} record must be an object")
            continue
        expected_independence = critic in INDEPENDENT_CRITICS
        if row.get("independence_required") is not expected_independence:
            errors.append(f"critic {critic} independence_required must be {expected_independence}")

    gates = data.get("gates")
    if not isinstance(gates, dict) or set(gates) != GATES:
        errors.append("gates must contain exactly G1-G14")
        gates = {}

    defects = data.get("defects")
    if not isinstance(defects, dict) or set(defects) != {"unresolved_mandatory", "closed_mandatory"}:
        errors.append("defects structure drifted")
        defects = {}

    rule = data.get("acceptance_rule")
    if not isinstance(rule, dict):
        errors.append("acceptance_rule must be an object")
        rule = {}
    if rule.get("operator") != ">" or rule.get("threshold") != 9.0 or rule.get("unrounded") is not True:
        errors.append("acceptance score rule must remain strictly >9.0 unrounded")
    if rule.get("target") != 10.0:
        errors.append("acceptance target must remain 10.0")
    if rule.get("zero_unresolved_mandatory_defects") is not True or rule.get("all_G1_G14_required") is not True:
        errors.append("mandatory defect/gate acceptance rules drifted")
    if set(rule.get("independent_critic_set", [])) != INDEPENDENT_CRITICS:
        errors.append("independent critic set must remain C2,C3,C4,C7")
    if set(rule.get("quantitative_specialist_set", [])) != {"C6"}:
        errors.append("quantitative specialist set must remain C6")

    scope = data.get("scope_limits")
    if not isinstance(scope, dict):
        errors.append("scope_limits must be an object")
        scope = {}
    if scope.get("this_packet_can_approve_t12_only") is not True:
        errors.append("candidate packet must remain scoped to T12 only")
    if scope.get("whole_game_approved") is not False:
        errors.append("T12 candidate packet cannot approve the whole game")
    if scope.get("physical_phone_tablet_native_4k60_certified_by_t12") is not False:
        errors.append("T12 candidate packet cannot certify final physical-device native-4K/60")

    if require_resolved:
        candidate = source.get("candidate_source")
        if not exact_sha(source.get("activation_base")):
            errors.append("resolved activation_base must be exact 40-hex SHA")
        if not exact_sha(candidate):
            errors.append("resolved candidate_source must be exact 40-hex SHA")
        if not exact_sha(source.get("integration_head")):
            errors.append("resolved integration_head must be exact 40-hex SHA")
        if not nonempty(source.get("authorized_changed_file_manifest_ref")):
            errors.append("resolved authorized changed-file manifest reference is required")
        for name, value in hashes.items():
            if not isinstance(value, str) or SHA256.fullmatch(value) is None:
                errors.append(f"resolved {name} must be exact lowercase SHA-256")
        for dep in ("T10", "T11"):
            if not exact_sha(upstream.get(dep)):
                errors.append(f"resolved upstream {dep} must be exact 40-hex SHA")
        if not nonempty(source.get("validator_source")):
            errors.append("resolved validator_source is required")

        for name, row in reports.items():
            if row.get("status") != "PASS" or not nonempty(row.get("evidence_ref")):
                errors.append(f"resolved static report {name} must PASS with evidence")

        if parity.get("status") != "PASS" or parity.get("candidate_source") != candidate:
            errors.append("engine parity must PASS against exact candidate")
        if not nonempty(parity.get("output_ref")) or not nonempty(parity.get("comparator_output_ref")):
            errors.append("engine parity output/comparator evidence refs are required")

        if regression.get("status") != "PASS" or regression.get("candidate_source") != candidate:
            errors.append("T01-T11 regression must PASS against exact candidate")
        if not isinstance(regression.get("run_id"), int) or regression.get("run_id") <= 0:
            errors.append("resolved regression run_id must be positive integer")
        if not nonempty(regression.get("artifact_ref")) or regression.get("failed_suites") != []:
            errors.append("resolved regression needs artifact and zero failed suites")

        for name, row in sequences.items():
            if not isinstance(row, dict) or row.get("status") != "PASS":
                errors.append(f"functional sequence {name} must PASS")
                continue
            refs = row.get("evidence_refs")
            if not isinstance(refs, list) or not refs or any(not nonempty(x) for x in refs):
                errors.append(f"functional sequence {name} must have evidence refs")

        player_facing = adaptive.get("player_facing_presentation_exists")
        if not isinstance(player_facing, bool):
            errors.append("resolved player_facing_presentation_exists must be boolean")
        elif player_facing:
            for key in ("phone_landscape_ref", "tablet_landscape_ref", "foldable_landscape_ref", "native_3840x2160_scale1_ref"):
                if not nonempty(adaptive.get(key)):
                    errors.append(f"resolved player-facing evidence missing {key}")

        if performance.get("status") != "PASS" or performance.get("candidate_source") != candidate:
            errors.append("shipping C6 must PASS against exact candidate")
        if not isinstance(performance.get("run_id"), int) or performance.get("run_id") <= 0:
            errors.append("shipping C6 run_id must be positive integer")
        if not nonempty(performance.get("evidence_ref")) or performance.get("shipping_measurements_present") is not True:
            errors.append("shipping C6 requires exact evidence and shipping measurements")
        c6_score = performance.get("score")
        if not isinstance(c6_score, (int, float)) or isinstance(c6_score, bool) or c6_score <= 9.0:
            errors.append("shipping C6 score must be strictly >9.0")

        for critic, row in critics.items():
            if row.get("status") != "PASS" or row.get("candidate_source") != candidate:
                errors.append(f"critic {critic} must PASS exact candidate")
            if not nonempty(row.get("reviewer_runtime_id")) or not nonempty(row.get("evidence_ref")):
                errors.append(f"critic {critic} requires reviewer/evidence provenance")
            score = row.get("minimum_mandatory_dimension_score")
            if not isinstance(score, (int, float)) or isinstance(score, bool) or score <= 9.0:
                errors.append(f"critic {critic} minimum mandatory dimension must be strictly >9.0")
            if critic in INDEPENDENT_CRITICS and row.get("independent") is not True:
                errors.append(f"critic {critic} requires independent reviewer provenance")
            if critic == "C6" and row.get("independence_required") is not False:
                errors.append("C6 must remain quantitative specialist, not fake independent-model requirement")

        if any(value is not True for value in gates.values()):
            errors.append("all G1-G14 must PASS")
        if defects.get("unresolved_mandatory") != []:
            errors.append("resolved candidate packet must have zero unresolved mandatory defects")

    return {
        "passed": not errors,
        "mode": "resolved" if require_resolved else "template",
        "static_report_count": len(reports),
        "critic_count": len(critics),
        "gate_count": len(gates),
        "errors": errors,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=str(DEFAULT_PATH.relative_to(ROOT)))
    ap.add_argument("--require-resolved", action="store_true")
    args = ap.parse_args()
    data = json.loads((ROOT / args.input).read_text())
    result = validate_packet(data, require_resolved=args.require_resolved)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
