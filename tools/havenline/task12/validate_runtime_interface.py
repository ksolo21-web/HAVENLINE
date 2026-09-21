#!/usr/bin/env python3
"""Validate the prepared T12 runtime interface/authority contract.

The contract is non-shipping preparation. This guard prevents authority creep,
ID namespace drift, missing idempotency/recovery boundaries, or accidental
ownership of T10/T11/T13/T14/economy concerns before implementation begins.
"""
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

EXPECTED_LEVEL_PATTERN = "t12.level.NNN"
EXPECTED_SLOT_PATTERN = "t12.slot.NNN"
EXPECTED_EVENT_PATTERN = "t12.event.level.NNN.completed"
EXPECTED_MILESTONE_PATTERN = "t12.milestone.NNN"
EXPECTED_MILESTONE_LEVELS = [10,20,30,40,50,60,70,80,90,100]
EXPECTED_BANDS = [
    "band_opening_frozen","band_forest","band_desert","band_underwater",
    "band_sky","band_volcanic","band_swamp","band_ruins",
    "band_underground","band_alien",
]
REQUIRED_API = {
    "load_contract": "initialization",
    "get_level_state": "pure_query",
    "get_unlockable_levels": "pure_query",
    "observe_authoritative_fact": "state_transition",
    "snapshot_component_state": "recovery_boundary",
    "restore_component_state": "recovery_boundary",
    "get_metrics": "diagnostic_query",
}
REQUIRED_FACT_KINDS = {
    "context_action_completed",
    "resource_delivery_completed",
    "world_transform_completed",
    "camp_state_completed",
    "band_entry_condition_completed",
    "capability_condition_completed",
    "route_or_interaction_condition_completed",
    "mastery_condition_completed",
}
REQUIRED_INTENT_FIELDS = {
    "intent_id","level_id","completion_event_id","unlocked_level_ids",
    "milestone_ids","source_fact_keys",
}
REQUIRED_COMPONENT_FIELDS = {
    "completed_level_ids","consumed_fact_keys","emitted_completion_event_ids",
    "emitted_milestone_ids",
}
REQUIRED_FORBIDDEN_STATE_FIELDS = {
    "purchase_history","vip_status","premium_spend","energy","inventory_counts",
    "T10 transaction internals","T11 asset instances","T13 difficulty state",
}
AUTHORITY_BOUNDARY_TERMS = ("T10", "T11", "T13", "T14", "economy")


def validate_contract(contract: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []

    if contract.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if contract.get("task_id") != "T12":
        errors.append("task_id must be T12")
    if contract.get("status") != "PREPARATION_ONLY_INTERFACE_CONTRACT":
        errors.append("status must remain PREPARATION_ONLY_INTERFACE_CONTRACT")

    ids = contract.get("stable_id_namespaces")
    if not isinstance(ids, dict):
        errors.append("stable_id_namespaces must be an object")
        ids = {}
    expected_patterns = {
        "level": EXPECTED_LEVEL_PATTERN,
        "progression_slot": EXPECTED_SLOT_PATTERN,
        "level_completion_event": EXPECTED_EVENT_PATTERN,
        "major_milestone": EXPECTED_MILESTONE_PATTERN,
    }
    for key, pattern in expected_patterns.items():
        row = ids.get(key)
        if not isinstance(row, dict) or row.get("pattern") != pattern:
            errors.append(f"stable ID namespace {key} must use pattern {pattern}")
    milestone = ids.get("major_milestone")
    if isinstance(milestone, dict) and milestone.get("levels") != EXPECTED_MILESTONE_LEVELS:
        errors.append("major milestone namespace must remain levels 10..100 by tens")
    if ids.get("region_band") != EXPECTED_BANDS:
        errors.append("region_band IDs drifted from frozen T12 band topology")

    authority = contract.get("authority_model")
    if not isinstance(authority, dict):
        errors.append("authority_model must be an object")
        authority = {}
    never = authority.get("T12_never_owns")
    if not isinstance(never, list):
        errors.append("authority_model.T12_never_owns must be a list")
        never = []
    never_text = " ".join(str(x) for x in never)
    for term in AUTHORITY_BOUNDARY_TERMS:
        if term.lower() not in never_text.lower():
            errors.append(f"authority boundary must explicitly retain {term} outside T12 ownership")

    api = contract.get("runtime_api")
    if not isinstance(api, dict):
        errors.append("runtime_api must be an object")
        api = {}
    for name, kind in REQUIRED_API.items():
        row = api.get(name)
        if not isinstance(row, dict):
            errors.append(f"missing runtime API contract: {name}")
            continue
        if row.get("kind") != kind:
            errors.append(f"runtime API {name} kind must be {kind}")
        requirements = row.get("requirements")
        if not isinstance(requirements, list) or not requirements:
            errors.append(f"runtime API {name} requires explicit requirements")

    facts = contract.get("authoritative_fact_kinds")
    if not isinstance(facts, list):
        errors.append("authoritative_fact_kinds must be a list")
        facts = []
    missing_facts = sorted(REQUIRED_FACT_KINDS - set(facts))
    if missing_facts:
        errors.append(f"missing authoritative fact kinds: {missing_facts}")

    intent = contract.get("progression_intent_contract")
    if not isinstance(intent, dict):
        errors.append("progression_intent_contract must be an object")
        intent = {}
    required_fields = intent.get("required_fields")
    if not isinstance(required_fields, list) or not REQUIRED_INTENT_FIELDS.issubset(set(required_fields)):
        errors.append("progression intent contract is missing required stable/idempotent fields")
    if "replay" not in str(intent.get("intent_id_rule", "")).lower():
        errors.append("progression intent identity rule must explicitly define replay behavior")
    forbidden_actions = " ".join(str(x) for x in intent.get("may_not_do", []))
    for term in ("inventory", "T10", "T11", "T13", "save"):
        if term.lower() not in forbidden_actions.lower():
            errors.append(f"progression intent boundary must explicitly forbid owning/mutating {term}")

    state = contract.get("component_state_contract")
    if not isinstance(state, dict):
        errors.append("component_state_contract must be an object")
        state = {}
    allowed = state.get("allowed_fields")
    if not isinstance(allowed, list) or not REQUIRED_COMPONENT_FIELDS.issubset(set(allowed)):
        errors.append("component-state contract missing required deterministic T12-local fields")
    forbidden = state.get("forbidden_fields")
    if not isinstance(forbidden, list) or not REQUIRED_FORBIDDEN_STATE_FIELDS.issubset(set(forbidden)):
        errors.append("component-state contract missing spend/upstream/difficulty forbidden fields")
    reconstruction = str(state.get("reconstruction_rule", "")).lower()
    for token in ("same", "without re-emitting"):
        if token not in reconstruction:
            errors.append("component reconstruction rule must guarantee deterministic no-reemit behavior")
            break

    performance = contract.get("performance_contract")
    if not isinstance(performance, dict):
        errors.append("performance_contract must be an object")
    else:
        if "no per-frame" not in str(performance.get("evaluation", "")).lower():
            errors.append("performance contract must forbid unchanged per-frame full progression traversal")
        measurements = performance.get("required_measurements_after_activation")
        if not isinstance(measurements, list) or len(measurements) < 5:
            errors.append("performance contract needs explicit post-activation measurements")

    activation_rule = str(contract.get("activation_rule", ""))
    if "T10/T11" not in activation_rule or "BINDING_RESOLUTION.json" not in activation_rule:
        errors.append("activation rule must keep concrete T10/T11 IDs external and exact-resolution gated")

    return {
        "passed": not errors,
        "runtime_api_count": len(api),
        "authoritative_fact_kind_count": len(facts),
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="Docs/Production/T12/RUNTIME_INTERFACE_CONTRACT.json")
    args = parser.parse_args()
    contract = json.loads(pathlib.Path(args.input).read_text())
    result = validate_contract(contract)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
