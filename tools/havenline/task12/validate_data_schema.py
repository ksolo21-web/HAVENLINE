#!/usr/bin/env python3
"""Validate the prepared T12 progression-data schema contract.

Preparation only. This validates schema ownership/structure and never writes
shipping progression data.
"""
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[3]
DEFAULT_SCHEMA = ROOT / "Docs" / "Production" / "T12" / "PROGRESSION_DATA_SCHEMA.json"

EXPECTED_LEVEL_FIELDS = {
    "level",
    "level_id",
    "region_band_id",
    "prerequisite_level_ids",
    "required_fact_ids",
    "progression_effects",
    "visible_progression_hook_ids",
    "milestone_ids",
    "one_time_event_ids",
}
EXPECTED_MILESTONE_FIELDS = {
    "milestone_id",
    "level",
    "kind",
    "progression_hook_ids",
    "visible_change_required",
    "owner_task",
}
REQUIRED_FORBIDDEN_KEYS = {
    "purchase_history",
    "vip_status",
    "premium_spend",
    "payer_status",
    "energy",
    "energy_required",
    "energy_cost",
}
REQUIRED_PROMOTION_TOKENS = {
    "t07/t08/t10/t11 approved",
    "t10/t11 integrated",
    "binding_resolution.json",
    "activation preflight pass",
    "@reservation:t12",
}


def validate_schema(data: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if data.get("task_id") != "T12":
        errors.append("task_id must be T12")
    if data.get("status") != "PREPARATION_ONLY_SCHEMA":
        errors.append("status must remain PREPARATION_ONLY_SCHEMA")

    level = data.get("level_record")
    if not isinstance(level, dict):
        errors.append("level_record must be an object")
        level = {}
    level_fields = set(level.get("required_fields", [])) if isinstance(level.get("required_fields"), list) else set()
    if level_fields != EXPECTED_LEVEL_FIELDS:
        errors.append(f"level required_fields mismatch: {sorted(level_fields)}")
    level_contracts = level.get("field_contracts", {})
    if not isinstance(level_contracts, dict) or set(level_contracts) != EXPECTED_LEVEL_FIELDS:
        errors.append("level field_contracts must define every and only required level field")
    else:
        if "^t12\\.level\\.[0-9]{3}$" not in str(level_contracts.get("level_id")):
            errors.append("level_id contract must freeze the t12.level.NNN namespace")
        if "acyclic" not in str(level_contracts.get("prerequisite_level_ids", "")).lower():
            errors.append("prerequisite contract must explicitly require acyclic topology")
        if "replay" not in str(level_contracts.get("one_time_event_ids", "")).lower():
            errors.append("one_time_event_ids contract must retain replay safety")

    forbidden = set(level.get("forbidden_eligibility_fields", [])) if isinstance(level.get("forbidden_eligibility_fields"), list) else set()
    missing_forbidden = sorted(REQUIRED_FORBIDDEN_KEYS - forbidden)
    if missing_forbidden:
        errors.append(f"schema lost mandatory spend/energy guards: {missing_forbidden}")

    authority_blob = " ".join(str(x) for x in level.get("authority_rules", [])).lower()
    for token in ("inventory", "t10", "t11", "t13", "t14", "t32/t44-t52"):
        if token not in authority_blob:
            errors.append(f"level authority_rules must preserve boundary token {token!r}")

    milestone = data.get("milestone_record")
    if not isinstance(milestone, dict):
        errors.append("milestone_record must be an object")
        milestone = {}
    milestone_fields = set(milestone.get("required_fields", [])) if isinstance(milestone.get("required_fields"), list) else set()
    if milestone_fields != EXPECTED_MILESTONE_FIELDS:
        errors.append(f"milestone required_fields mismatch: {sorted(milestone_fields)}")
    milestone_contracts = milestone.get("field_contracts", {})
    if not isinstance(milestone_contracts, dict) or set(milestone_contracts) != EXPECTED_MILESTONE_FIELDS:
        errors.append("milestone field_contracts must define every and only required milestone field")
    else:
        if "^t12\\.milestone" not in str(milestone_contracts.get("milestone_id")):
            errors.append("milestone_id contract must freeze t12.milestone namespace")
        if "ten-level" not in str(milestone_contracts.get("kind", "")).lower():
            errors.append("milestone kind contract must retain ten-level major cadence")

    manifest = data.get("shipping_manifest")
    if not isinstance(manifest, dict):
        errors.append("shipping_manifest must be an object")
        manifest = {}
    if manifest.get("exact_level_count") != 100:
        errors.append("shipping_manifest exact_level_count must be 100")
    if manifest.get("required_task_id") != "T12":
        errors.append("shipping_manifest required_task_id must be T12")
    top = set(manifest.get("required_top_level_fields", [])) if isinstance(manifest.get("required_top_level_fields"), list) else set()
    if top != {"schema_version", "task_id", "levels", "milestones"}:
        errors.append("shipping_manifest top-level field contract drifted")
    promotion_blob = " ".join(str(x) for x in manifest.get("promotion_requires", [])).lower()
    for token in REQUIRED_PROMOTION_TOKENS:
        if token not in promotion_blob:
            errors.append(f"shipping promotion rule missing {token!r}")

    return {
        "passed": not errors,
        "level_field_count": len(level_fields),
        "milestone_field_count": len(milestone_fields),
        "forbidden_eligibility_guard_count": len(forbidden),
        "errors": errors,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=str(DEFAULT_SCHEMA.relative_to(ROOT)))
    args = ap.parse_args()
    data = json.loads((ROOT / args.input).read_text())
    result = validate_schema(data)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
