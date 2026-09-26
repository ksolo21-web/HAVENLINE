#!/usr/bin/env python3
"""Validate T12 fact-slot binding templates, resolved indexes, and shipping bindings."""
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "Docs" / "Production" / "T12"
DEFAULT_INDEX = DOCS / "FACT_SLOT_BINDING_INDEX_TEMPLATE.json"
DEFAULT_CATALOG = DOCS / "BINDING_SLOT_CATALOG.json"

FORBIDDEN_SIGNAL_TOKENS = ("purchase", "premium_spend", "vip", "payer", "energy")
BINDING_FIELDS = {
    "slot_id", "fact_kind", "source_task", "source_id",
    "resolution_state", "evidence_ref", "idempotency_domain",
}
INTERNAL_ONLY_FACT_KINDS = {"visible_progression_required", "major_milestone_completed"}
RESOLUTION_STATES = {"RESOLVED", "DEFERRED_LATER_OWNER"}

def load(path: pathlib.Path) -> Any:
    return json.loads(path.read_text())

def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())

def _allowed_source_tasks(fact_kind: str, content_owner_task: str) -> set[str]:
    if fact_kind == "context_action_completed":
        return {"T07"}
    if fact_kind == "resource_delivery_completed":
        return {"T08", "integration", "T08/integration"}
    if fact_kind == "world_transform_completed":
        return {"T10"}
    if fact_kind == "camp_state_completed":
        return {"T11"}
    if fact_kind in {
        "band_entry_condition_completed",
        "capability_condition_completed",
        "route_or_interaction_condition_completed",
        "mastery_condition_completed",
    }:
        return {content_owner_task}
    return set()

def _validate_binding(
    binding: Any,
    source: dict[str, Any],
    *,
    label: str,
    errors: list[str],
) -> None:
    if not isinstance(binding, dict) or set(binding) != BINDING_FIELDS:
        errors.append(f"{label} resolved_binding fields drifted")
        return
    slot_id = source.get("fact_slot_id")
    if binding.get("slot_id") != slot_id:
        errors.append(f"{label} slot_id does not match {slot_id}")
    fact_kind = binding.get("fact_kind")
    if fact_kind not in source.get("allowed_fact_kinds", []):
        errors.append(f"{label} fact_kind is not allowed for the slot")
    if fact_kind in INTERNAL_ONLY_FACT_KINDS:
        errors.append(f"{label} internal T12 presentation fact cannot satisfy an authoritative slot")
    state = binding.get("resolution_state")
    if state not in RESOLUTION_STATES:
        errors.append(f"{label} resolution_state must be RESOLVED or DEFERRED_LATER_OWNER")
        return
    if not _nonempty(binding.get("source_task")):
        errors.append(f"{label} source_task must be non-empty")
    if not _nonempty(binding.get("evidence_ref")):
        errors.append(f"{label} evidence_ref must be non-empty")
    evidence_blob = str(binding.get("evidence_ref", "")).lower()
    for token in FORBIDDEN_SIGNAL_TOKENS:
        if token in " ".join(str(v).lower() for v in binding.values()):
            errors.append(f"{label} contains forbidden spend/energy signal token {token!r}")

    if state == "RESOLVED":
        if not _nonempty(binding.get("source_id")):
            errors.append(f"{label} RESOLVED source_id must be non-empty")
        if not _nonempty(binding.get("idempotency_domain")):
            errors.append(f"{label} RESOLVED idempotency_domain must be non-empty")
        allowed_tasks = _allowed_source_tasks(str(fact_kind), str(source.get("content_owner_task", "")))
        if allowed_tasks and binding.get("source_task") not in allowed_tasks:
            errors.append(
                f"{label} source_task {binding.get('source_task')!r} is incompatible with fact_kind {fact_kind!r}; "
                f"allowed={sorted(allowed_tasks)}"
            )
        if binding.get("source_task") in {"T10", "T11"} and "binding" not in evidence_blob:
            errors.append(f"{label} T10/T11 resolved evidence_ref must identify binding-resolution proof")
    else:
        if source.get("later_owner_registration_allowed") is not True:
            errors.append(f"{label} DEFERRED_LATER_OWNER is not permitted for this slot")
        if binding.get("source_task") != source.get("content_owner_task"):
            errors.append(f"{label} deferred source_task must equal content_owner_task")
        if binding.get("source_id") not in ("", None):
            errors.append(f"{label} deferred source_id must be blank")
        if binding.get("idempotency_domain") not in ("", None):
            errors.append(f"{label} deferred idempotency_domain must be blank")

def _opening_activation_contract(
    catalog: dict[str, Any],
    errors: list[str],
) -> set[int]:
    contract = catalog.get("opening_activation_contract")
    expected_levels = [3, 4, 6, 9, 10]
    if not isinstance(contract, dict):
        errors.append("binding slot catalog opening_activation_contract must be an object")
        return set(expected_levels)
    if contract.get("required_resolved_levels") != expected_levels:
        errors.append("opening activation required levels must remain 3,4,6,9,10")
    if contract.get("required_resolution_state") != "RESOLVED":
        errors.append("opening activation required_resolution_state must be RESOLVED")
    if set(contract.get("required_upstream_task_coverage", [])) != {"T10", "T11"}:
        errors.append("opening activation upstream coverage must require T10 and T11")
    rule = str(contract.get("rule", "")).lower()
    for token in ("t10", "t11", "deferred", "forbidden", "resolved"):
        if token not in rule:
            errors.append(f"opening activation rule missing {token!r}")
    return set(expected_levels)


def _catalog_slots(catalog: dict[str, Any]) -> tuple[dict[int, dict[str, Any]], list[str]]:
    errors: list[str] = []
    slots = catalog.get("slots")
    if not isinstance(slots, list) or len(slots) != 100:
        return {}, ["binding slot catalog must contain exactly 100 slots"]
    expected: dict[int, dict[str, Any]] = {}
    for row in slots:
        if not isinstance(row, dict) or not isinstance(row.get("level"), int):
            errors.append("binding slot catalog contains invalid slot row")
            continue
        expected[int(row["level"])] = row
    if set(expected) != set(range(1, 101)):
        errors.append("binding slot catalog levels must be exactly 1..100")
    return expected, errors

def validate(data: dict[str, Any], catalog: dict[str, Any], *, require_resolved: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    if data.get("schema_version") != 1 or data.get("task_id") != "T12":
        errors.append("fact-slot binding-index identity must be schema_version=1 task_id=T12")
    expected_status = (
        "RESOLVED_FACT_SLOT_BINDING_INDEX"
        if require_resolved
        else "PREPARATION_ONLY_FACT_SLOT_BINDING_INDEX_TEMPLATE"
    )
    if data.get("status") != expected_status:
        errors.append(f"fact-slot binding-index status must be {expected_status}")
    if data.get("shipping_path_forbidden") is not (not require_resolved):
        errors.append("fact-slot binding-index shipping_path_forbidden does not match validation mode")

    shape = data.get("required_resolved_binding_shape")
    if not isinstance(shape, dict) or set(shape) != BINDING_FIELDS:
        errors.append("required_resolved_binding_shape fields drifted")

    entries = data.get("entries")
    if not isinstance(entries, list) or len(entries) != 99:
        errors.append("binding-index must contain exactly 99 entries for Levels 2-100")
        entries = []

    catalog_by_level, catalog_errors = _catalog_slots(catalog)
    errors.extend(catalog_errors)
    opening_required = _opening_activation_contract(catalog, errors)
    opening_tasks: set[str] = set()
    seen: set[int] = set()
    resolved_count = 0
    deferred_count = 0
    for index, row in enumerate(entries):
        if not isinstance(row, dict):
            errors.append(f"entries[{index}] must be an object")
            continue
        level = row.get("level")
        if not isinstance(level, int) or isinstance(level, bool) or not 2 <= level <= 100:
            errors.append(f"entries[{index}].level must be integer 2..100")
            continue
        if level in seen:
            errors.append(f"duplicate binding-index level {level}")
        seen.add(level)
        source = catalog_by_level.get(level)
        if source is None:
            errors.append(f"binding-index level {level} has no source catalog slot")
            continue
        exact = {
            "slot_id": source.get("fact_slot_id"),
            "content_owner_task": source.get("content_owner_task"),
            "allowed_fact_kinds": source.get("allowed_fact_kinds"),
            "authority_classes": source.get("authority_classes"),
            "activation_binding_relevant": source.get("activation_binding_relevant"),
            "later_owner_registration_allowed": source.get("later_owner_registration_allowed"),
        }
        for key, expected_value in exact.items():
            if row.get(key) != expected_value:
                errors.append(f"level {level}: binding-index {key} drifted")
        if row.get("slot_id") != f"t12.fact.slot.{level:03d}":
            errors.append(f"level {level}: slot_id must be canonical t12.fact.slot.{level:03d}")
        binding = row.get("resolved_binding")
        if require_resolved:
            _validate_binding(binding, source, label=f"level {level}", errors=errors)
            if isinstance(binding, dict):
                state = binding.get("resolution_state")
                if level in opening_required and state != "RESOLVED":
                    errors.append(f"level {level}: opening activation binding may not be deferred")
                if state == "RESOLVED":
                    resolved_count += 1
                    if level in opening_required and isinstance(binding.get("source_task"), str):
                        opening_tasks.add(binding["source_task"])
                elif state == "DEFERRED_LATER_OWNER":
                    deferred_count += 1
        elif binding is not None:
            errors.append(f"level {level}: preparation template resolved_binding must remain null")

    if seen != set(range(2, 101)):
        errors.append("binding-index levels must be exactly 2..100")
    if require_resolved:
        missing_opening_tasks = sorted({"T10", "T11"} - opening_tasks)
        if missing_opening_tasks:
            errors.append(
                f"opening activation bindings must consume both T10 and T11; missing {missing_opening_tasks}"
            )

    rules_blob = " ".join(str(x) for x in data.get("rules", [])).lower()
    for token in (
        "level 1", "level 2-100", "resolved", "deferred_later_owner",
        "t10/t11", "binding_resolution", "keep the level locked", "not shipping progression data",
    ):
        if token not in rules_blob:
            errors.append(f"binding-index rules missing {token!r}")
    for token in FORBIDDEN_SIGNAL_TOKENS:
        if token not in rules_blob:
            errors.append(f"binding-index spend-blind rules missing {token!r}")

    t11 = catalog.get("authority_classes", {}).get("T11_CAMP", {})
    if not require_resolved and t11.get("current_public_ids") != []:
        errors.append("T11 public IDs must remain empty before approval")

    return {
        "passed": not errors,
        "mode": "resolved" if require_resolved else "template",
        "entry_count": len(entries),
        "resolved_entry_count": resolved_count,
        "deferred_entry_count": deferred_count,
        "unresolved_entry_count": sum(
            1 for row in entries if isinstance(row, dict) and row.get("resolved_binding") is None
        ),
        "errors": errors,
    }

def validate_shipping(data: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(data, dict) or set(data) != {"schema_version", "task_id", "bindings"}:
        return {"passed": False, "entry_count": 0, "errors": ["shipping binding document fields must be exactly schema_version, task_id, bindings"]}
    if data.get("schema_version") != 1 or data.get("task_id") != "T12":
        errors.append("shipping binding document identity must be schema_version=1 task_id=T12")
    bindings = data.get("bindings")
    if not isinstance(bindings, list) or len(bindings) != 99:
        errors.append("shipping binding document must contain exactly 99 bindings")
        bindings = []
    catalog_by_level, catalog_errors = _catalog_slots(catalog)
    errors.extend(catalog_errors)
    opening_required = _opening_activation_contract(catalog, errors)
    opening_tasks: set[str] = set()
    by_slot = {row.get("fact_slot_id"): row for row in catalog_by_level.values()}
    seen: set[str] = set()
    resolved_count = 0
    deferred_count = 0
    for index, binding in enumerate(bindings):
        if not isinstance(binding, dict):
            errors.append(f"bindings[{index}] must be an object")
            continue
        slot = binding.get("slot_id")
        if slot in seen:
            errors.append(f"duplicate shipping binding slot {slot}")
        if isinstance(slot, str):
            seen.add(slot)
        source = by_slot.get(slot)
        if source is None:
            errors.append(f"bindings[{index}] unknown slot_id {slot!r}")
            continue
        _validate_binding(binding, source, label=f"binding {slot}", errors=errors)
        level = int(source.get("level", 0))
        state = binding.get("resolution_state")
        if level in opening_required and state != "RESOLVED":
            errors.append(f"binding {slot}: opening activation binding may not be deferred")
        if state == "RESOLVED":
            resolved_count += 1
            if level in opening_required and isinstance(binding.get("source_task"), str):
                opening_tasks.add(binding["source_task"])
        elif state == "DEFERRED_LATER_OWNER":
            deferred_count += 1
    expected_slots = {f"t12.fact.slot.{level:03d}" for level in range(2, 101)}
    if seen != expected_slots:
        errors.append("shipping binding slots must be exactly t12.fact.slot.002..100")
    missing_opening_tasks = sorted({"T10", "T11"} - opening_tasks)
    if missing_opening_tasks:
        errors.append(
            f"shipping opening activation bindings must consume both T10 and T11; missing {missing_opening_tasks}"
        )
    return {
        "passed": not errors,
        "entry_count": len(bindings),
        "resolved_entry_count": resolved_count,
        "deferred_entry_count": deferred_count,
        "errors": errors,
    }

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=str(DEFAULT_INDEX.relative_to(ROOT)))
    ap.add_argument("--catalog", default=str(DEFAULT_CATALOG.relative_to(ROOT)))
    ap.add_argument("--require-resolved", action="store_true")
    ap.add_argument("--shipping", action="store_true")
    args = ap.parse_args()
    data = load(ROOT / args.input)
    catalog = load(ROOT / args.catalog)
    result = validate_shipping(data, catalog) if args.shipping else validate(data, catalog, require_resolved=args.require_resolved)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
