#!/usr/bin/env python3
"""Validate T12 reference runtime semantics against the frozen runtime interface."""
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "Docs" / "Production" / "T12"
DEFAULT_SEMANTICS = DOCS / "REFERENCE_RUNTIME_SEMANTICS.json"
DEFAULT_RUNTIME = DOCS / "RUNTIME_INTERFACE_CONTRACT.json"

def load(path: pathlib.Path) -> Any:
    return json.loads(path.read_text())

def validate(semantics: dict[str, Any], runtime: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if semantics.get("schema_version") != 1 or semantics.get("task_id") != "T12":
        errors.append("reference runtime semantics identity must be schema_version=1 task_id=T12")
    if semantics.get("status") != "PREPARATION_ONLY_REFERENCE_RUNTIME_SEMANTICS":
        errors.append("reference runtime semantics status drifted")
    if semantics.get("shipping_path_forbidden") is not True:
        errors.append("reference runtime semantics must remain non-shipping")

    state = runtime.get("component_state_contract", {})
    allowed = state.get("allowed_fields")
    initial = semantics.get("initial_state")
    if not isinstance(initial, dict):
        errors.append("reference initial_state must be an object")
        initial = {}
    if not isinstance(allowed, list) or set(initial) != set(allowed):
        errors.append("reference initial_state fields must exactly match runtime component state allowed_fields")
    for key in ("completed_level_ids","satisfied_fact_slot_ids","consumed_fact_keys","emitted_completion_event_ids","emitted_milestone_ids"):
        if initial.get(key) != []:
            errors.append(f"reference initial_state {key} must be empty list")
    if initial.get("fact_slot_source_keys") != {}:
        errors.append("reference initial_state fact_slot_source_keys must be empty object")

    observe = runtime.get("runtime_api", {}).get("observe_authoritative_fact", {})
    reference_observe = semantics.get("authoritative_fact_observation", {})
    if reference_observe.get("identity_fields") != observe.get("inputs"):
        errors.append("reference fact identity fields drifted from runtime observe_authoritative_fact inputs")
    rules_blob = " ".join(str(v) for v in reference_observe.values()).lower()
    for token in ("resolved", "source_task", "fact_kind", "source_id", "idempotency_domain", "no-op", "out-of-order", "retained", "deferred_later_owner", "fail closed"):
        if token not in rules_blob:
            errors.append(f"reference authoritative fact semantics missing {token!r}")

    transition = runtime.get("transition_semantics", {})
    settlement = semantics.get("settlement", {})
    settlement_blob = " ".join(str(v) for v in settlement.values()).lower()
    for token in ("ascending", "fixed", "prerequisite", "satisfied", "replay"):
        if token not in settlement_blob:
            errors.append(f"reference settlement semantics missing {token!r}")
    if transition.get("out_of_order_fact") is None or "retained" not in str(transition.get("out_of_order_fact")).lower():
        errors.append("runtime transition semantics must retain out-of-order facts")
    if transition.get("settlement") is None or "required_fact_ids" not in str(transition.get("settlement")).lower():
        errors.append("runtime transition settlement must require satisfied fact slots")

    intent = runtime.get("progression_intent_contract", {})
    intent_ref = semantics.get("progression_intent", {})
    field_semantics = intent.get("field_semantics", {})
    if intent_ref.get("intent_id") != "t12.intent.level.NNN.completed":
        errors.append("reference intent identity drifted")
    for token in ("direct dependent", "fact-locked"):
        if token not in str(intent_ref.get("unlocked_level_ids", "")).lower():
            errors.append(f"reference unlocked_level_ids rule missing {token!r}")
    if "domain-scoped" not in str(intent_ref.get("source_fact_keys", "")).lower():
        errors.append("reference source_fact_keys rule must retain domain-scoped causality")
    if set(field_semantics) != set(intent.get("required_fields", [])):
        errors.append("runtime progression intent field semantics are incomplete")

    restore = semantics.get("snapshot_restore", {})
    if set(restore.get("required_state_fields", [])) != set(allowed or []):
        errors.append("reference snapshot fields must exactly match runtime component state allowed_fields")
    restore_blob = " ".join(str(v) for v in restore.values()).lower()
    for token in (
        "unknown",
        "duplicate",
        "prerequisite",
        "satisfied",
        "re-emitting",
        "consumed_fact_keys",
        "fact_slot_source_keys",
        "completion event",
        "exactly justified",
    ):
        if token not in restore_blob:
            errors.append(f"reference snapshot/restore semantics missing {token!r}")

    boundary_blob = " ".join(str(x) for x in semantics.get("authority_boundaries", [])).lower()
    for token in ("inventory", "t10", "t11", "purchase", "energy", "t13", "t14", "cannot approve"):
        if token not in boundary_blob:
            errors.append(f"reference authority boundaries missing {token!r}")

    return {"passed": not errors, "errors": errors}

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--semantics", default=str(DEFAULT_SEMANTICS.relative_to(ROOT)))
    ap.add_argument("--runtime", default=str(DEFAULT_RUNTIME.relative_to(ROOT)))
    args = ap.parse_args()
    result = validate(load(ROOT / args.semantics), load(ROOT / args.runtime))
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
