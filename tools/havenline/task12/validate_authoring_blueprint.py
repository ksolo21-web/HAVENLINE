#!/usr/bin/env python3
"""Validate the non-shipping T12 100-level authoring blueprint and fact-slot catalog."""
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[3]
TASK = ROOT / "tools" / "havenline" / "task12"
DOCS = ROOT / "Docs" / "Production" / "T12"
BLUEPRINT_PATH = DOCS / "AUTHORING_BLUEPRINT.json"
CATALOG_PATH = DOCS / "BINDING_SLOT_CATALOG.json"
MATRIX_PATH = DOCS / "LEVEL_1_100_MATRIX.json"
T10_CATALOG_PATH = ROOT / "HavenlineGodot" / "data" / "world_transform_recipes.json"

INTERNAL_PRESENTATION_REQUIREMENTS = {"visible_progression_required", "major_milestone_completed"}

AUTHORITY_CLASS_BY_FACT = {
    "context_action_completed": "T07_CONTEXT",
    "resource_delivery_completed": "T08_DELIVERY_INTEGRATION",
    "world_transform_completed": "T10_TRANSFORM",
    "camp_state_completed": "T11_CAMP",
    "band_entry_condition_completed": "CONTENT_OWNER",
    "capability_condition_completed": "CONTENT_OWNER",
    "route_or_interaction_condition_completed": "CONTENT_OWNER",
    "mastery_condition_completed": "CONTENT_OWNER",
    "visible_progression_required": "T12_INTERNAL",
    "major_milestone_completed": "T12_INTERNAL",
}

def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, TASK / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

materializer = _load_module("t12_materializer", "materialize_progression_data.py")

def load(path: pathlib.Path) -> Any:
    return json.loads(path.read_text())

def validate(
    blueprint: dict[str, Any],
    catalog: dict[str, Any],
    matrix: dict[str, Any],
    t10_catalog: dict[str, Any],
) -> dict[str, Any]:
    errors: list[str] = []

    if blueprint.get("schema_version") != 1 or blueprint.get("task_id") != "T12":
        errors.append("authoring blueprint identity must be schema_version=1 task_id=T12")
    if blueprint.get("status") != "PREPARATION_ONLY_AUTHORING_BLUEPRINT":
        errors.append("authoring blueprint status drifted")
    if blueprint.get("shipping_path_forbidden") is not True:
        errors.append("authoring blueprint must remain non-shipping")

    materialization = blueprint.get("materialization_contract")
    expected_outputs = [
        "HavenlineGodot/data/progression_levels_v1.json",
        "HavenlineGodot/data/progression_milestones_v1.json",
        "HavenlineGodot/data/progression_bindings_v1.json",
    ]
    if not isinstance(materialization, dict) or materialization.get("output_files") != expected_outputs:
        errors.append("authoring blueprint output_files must be the three canonical shipping datasets")
    binding_output_rule = str((materialization or {}).get("binding_output_rule", "")).lower()
    for token in ("progression_bindings_v1.json", "fully dispositioned", "99-slot", "never invents"):
        if token not in binding_output_rule:
            errors.append(f"authoring blueprint binding output rule missing {token!r}")

    if catalog.get("schema_version") != 1 or catalog.get("task_id") != "T12":
        errors.append("binding slot catalog identity must be schema_version=1 task_id=T12")
    if catalog.get("status") != "PREPARATION_ONLY_BINDING_SLOT_CATALOG":
        errors.append("binding slot catalog status drifted")
    if catalog.get("shipping_path_forbidden") is not True:
        errors.append("binding slot catalog must remain non-shipping")
    if catalog.get("fact_slot_namespace") != "t12.fact.slot.NNN":
        errors.append("fact-slot namespace must remain t12.fact.slot.NNN")

    levels = blueprint.get("levels")
    matrix_levels = matrix.get("levels")
    slots = catalog.get("slots")
    milestones = blueprint.get("milestones")
    if not isinstance(levels, list) or len(levels) != 100:
        errors.append("authoring blueprint must contain exactly 100 levels")
        levels = []
    if not isinstance(matrix_levels, list) or len(matrix_levels) != 100:
        errors.append("source matrix must contain exactly 100 levels")
        matrix_levels = []
    if not isinstance(slots, list) or len(slots) != 100:
        errors.append("binding slot catalog must contain exactly 100 slots")
        slots = []
    if not isinstance(milestones, list) or len(milestones) != 10:
        errors.append("authoring blueprint must contain exactly 10 major milestones")
        milestones = []

    matrix_by_level = {
        int(row["level"]): row for row in matrix_levels if isinstance(row, dict) and isinstance(row.get("level"), int)
    }
    blueprint_by_level = {
        int(row["level"]): row for row in levels if isinstance(row, dict) and isinstance(row.get("level"), int)
    }
    slot_by_level = {
        int(row["level"]): row for row in slots if isinstance(row, dict) and isinstance(row.get("level"), int)
    }

    if set(matrix_by_level) != set(range(1, 101)):
        errors.append("source matrix level numbers must be exactly 1..100")
    if set(blueprint_by_level) != set(range(1, 101)):
        errors.append("blueprint level numbers must be exactly 1..100")
    if set(slot_by_level) != set(range(1, 101)):
        errors.append("binding slot level numbers must be exactly 1..100")

    profiles = matrix.get("binding_profiles", {})
    for level in range(1, 101):
        matrix_row = matrix_by_level.get(level)
        row = blueprint_by_level.get(level)
        slot = slot_by_level.get(level)
        if not isinstance(matrix_row, dict) or not isinstance(row, dict) or not isinstance(slot, dict):
            continue
        n = f"{level:03d}"
        profile = profiles.get(matrix_row.get("binding_profile"))
        if not isinstance(profile, dict):
            errors.append(f"level {level}: matrix binding profile is missing")
            continue
        all_classes = list(profile.get("classes", []))
        allowed_facts = [kind for kind in all_classes if kind not in INTERNAL_PRESENTATION_REQUIREMENTS]
        presentation_requirements = [kind for kind in all_classes if kind in INTERNAL_PRESENTATION_REQUIREMENTS]
        authority_classes = list(dict.fromkeys(
            AUTHORITY_CLASS_BY_FACT[kind]
            for kind in allowed_facts
            if kind in AUTHORITY_CLASS_BY_FACT
        ))

        expected = {
            "level_id": f"t12.level.{n}",
            "progression_slot_id": f"t12.slot.{n}",
            "fact_slot_id": f"t12.fact.slot.{n}",
            "region_band_id": matrix_row.get("band"),
            "content_owner_task": matrix_row.get("owner"),
            "role": matrix_row.get("role"),
            "binding_profile": matrix_row.get("binding_profile"),
            "prerequisite_level_ids": matrix_row.get("requires"),
            "allowed_fact_kinds": allowed_facts,
            "presentation_requirements": presentation_requirements,
            "authority_classes": authority_classes,
            "materialized_required_fact_ids": [] if level == 1 else [f"t12.fact.slot.{n}"],
            "visible_progression_hook_ids": [f"t12.visible.{n}"] if matrix_row.get("visible") else [],
            "milestone_ids": [f"t12.milestone.{n}"] if matrix_row.get("major") else [],
            "one_time_event_ids": [f"t12.event.level.{n}.completed"],
        }
        for key, expected_value in expected.items():
            if row.get(key) != expected_value:
                errors.append(f"level {level}: blueprint {key} drifted; expected {expected_value!r}, got {row.get(key)!r}")

        effect = row.get("progression_effect_template")
        expected_effect = {
            "effect_id": f"t12.effect.level.{n}",
            "kind": matrix_row.get("binding_profile"),
            "semantic": profile.get("effect"),
            "owner_task": matrix_row.get("owner"),
            "exact_payload_must_be_unique": True,
        }
        if effect != expected_effect:
            errors.append(f"level {level}: progression effect template drifted")

        expected_slot = {
            "fact_slot_id": f"t12.fact.slot.{n}",
            "content_owner_task": matrix_row.get("owner"),
            "binding_profile": matrix_row.get("binding_profile"),
            "allowed_fact_kinds": allowed_facts,
            "authority_classes": authority_classes,
            "resolution_mode": "INTRINSIC_READY" if level == 1 else "AUTHORITATIVE_BINDING",
            "activation_binding_relevant": (
                "T10_TRANSFORM" in authority_classes or "T11_CAMP" in authority_classes
            ),
            "later_owner_registration_allowed": matrix_row.get("owner") != "T12",
            "concrete_source_id": None,
        }
        for key, expected_value in expected_slot.items():
            if slot.get(key) != expected_value:
                errors.append(f"level {level}: binding slot {key} drifted")

    expected_milestones = [
        {
            "milestone_id": f"t12.milestone.{level:03d}",
            "level": level,
            "kind": "major",
            "progression_hook_ids": [f"t12.visible.{level:03d}"],
            "visible_change_required": True,
            "owner_task": matrix_by_level[level].get("owner"),
        }
        for level in range(10, 101, 10)
        if level in matrix_by_level
    ]
    if milestones != expected_milestones:
        errors.append("authoring blueprint milestone records drifted from matrix")

    authorities = catalog.get("authority_classes")
    if not isinstance(authorities, dict):
        errors.append("binding slot authority_classes must be an object")
        authorities = {}

    for row in levels:
        if not isinstance(row, dict):
            continue
        leaked = sorted(set(row.get("allowed_fact_kinds", [])) & INTERNAL_PRESENTATION_REQUIREMENTS)
        if leaked:
            errors.append(
                f"level {row.get('level')}: internal presentation requirements leaked into authoritative allowed_fact_kinds: {leaked}"
            )

    internal = authorities.get("T12_INTERNAL")
    if not isinstance(internal, dict):
        errors.append("T12_INTERNAL authority class missing")
    else:
        if set(internal.get("allowed_requirements", [])) != INTERNAL_PRESENTATION_REQUIREMENTS:
            errors.append("T12_INTERNAL presentation requirement set drifted")
        if "never" not in str(internal.get("shipping_rule", "")).lower() or "authoritative fact" not in str(internal.get("shipping_rule", "")).lower():
            errors.append("T12_INTERNAL must explicitly forbid presentation requirements as authoritative facts")

    t11 = authorities.get("T11_CAMP")
    if not isinstance(t11, dict):
        errors.append("T11_CAMP authority class missing")
    else:
        if t11.get("status") != "UNRESOLVED_T11_ASSIGNED":
            errors.append("T11_CAMP must remain unresolved until T11 approval")
        if t11.get("current_public_ids") != []:
            errors.append("T11_CAMP may not contain invented/future public IDs before T11 approval")

    t10 = authorities.get("T10_TRANSFORM")
    expected_t10_hints = [
        {
            "recipe_id": row.get("recipe_id"),
            "source_state": row.get("source_state"),
            "target_state": row.get("target_state"),
            "progression_tags": row.get("progression_tags"),
            "presentation_key": row.get("presentation_key"),
        }
        for row in t10_catalog.get("recipes", [])
    ]
    if not isinstance(t10, dict):
        errors.append("T10_TRANSFORM authority class missing")
    else:
        if t10.get("integrated_source") != "eba0107def258824549fb10d81785290d0c81d97":
            errors.append("T10_TRANSFORM accepted source drifted")
        if t10.get("current_public_id_hints") != expected_t10_hints:
            errors.append("T10_TRANSFORM public ID hints drifted from current accepted recipe catalog")

    try:
        materialized = materializer.validate_materialized(blueprint)
        if not materialized.get("passed"):
            errors.append(
                "materialized in-memory shipping documents failed progression validation: "
                + json.dumps(materialized.get("progression_validation", {}).get("errors", []))
            )
    except Exception as exc:
        errors.append(f"authoring blueprint materialization failed: {exc}")
        materialized = {"passed": False, "level_count": 0, "milestone_count": 0}

    return {
        "passed": not errors,
        "blueprint_level_count": len(levels),
        "binding_slot_count": len(slots),
        "milestone_count": len(milestones),
        "materialized_level_count": materialized.get("level_count"),
        "materialized_milestone_count": materialized.get("milestone_count"),
        "materialized_progression_passed": materialized.get("passed") is True,
        "errors": errors,
    }

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--blueprint", default=str(BLUEPRINT_PATH.relative_to(ROOT)))
    ap.add_argument("--catalog", default=str(CATALOG_PATH.relative_to(ROOT)))
    ap.add_argument("--matrix", default=str(MATRIX_PATH.relative_to(ROOT)))
    ap.add_argument("--t10-catalog", default=str(T10_CATALOG_PATH.relative_to(ROOT)))
    args = ap.parse_args()
    result = validate(
        load(ROOT / args.blueprint),
        load(ROOT / args.catalog),
        load(ROOT / args.matrix),
        load(ROOT / args.t10_catalog),
    )
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
