#!/usr/bin/env python3
"""Validate the non-shipping T12 Level 1-100 preparation matrix.

This validator is intentionally stricter than a prose review. It proves that the
prepared matrix has deterministic IDs/topology/cadence/owners and contains no
unresolved or activation-unverified T10/T11 binding IDs. It never writes shipping progression.
"""
from __future__ import annotations

import argparse
import json
import pathlib
from copy import deepcopy
from typing import Any

EXPECTED_BANDS = [
    (1, 10, "band_opening_frozen", "T32"),
    (11, 20, "band_forest", "T44"),
    (21, 30, "band_desert", "T45"),
    (31, 40, "band_underwater", "T46"),
    (41, 50, "band_sky", "T47"),
    (51, 60, "band_volcanic", "T48"),
    (61, 70, "band_swamp", "T49"),
    (71, 80, "band_ruins", "T50"),
    (81, 90, "band_underground", "T51"),
    (91, 100, "band_alien", "T52"),
]

ROLE_PATTERN = {
    1: ("band_entry", "entry", False, False),
    2: ("interaction_expansion", "interaction", False, False),
    3: ("visible_progression", "visible", True, False),
    4: ("loop_expansion", "loop", False, False),
    5: ("mid_band_capability", "capability", False, False),
    6: ("visible_progression", "visible", True, False),
    7: ("exploration_system_expansion", "exploration", False, False),
    8: ("mastery_integration", "mastery", False, False),
    9: ("visible_pre_milestone", "visible_pre_milestone", True, False),
    0: ("major_milestone", "milestone", True, True),
}

REQUIRED_FORBIDDEN_INPUTS = {
    "purchase_history",
    "premium_spend",
    "vip_status",
    "payer_tier",
    "ad_spend",
    "energy_required_to_continue",
}

EXPECTED_INVARIANTS = {
    "exact_level_count": 100,
    "range": [1, 100],
    "max_visible_gap": 3,
    "major_each_band": True,
    "spend_blind": True,
    "energy_wall_forbidden": True,
    "counter_only_filler_forbidden": True,
    "upstream_ids_require_activation_resolution": True,
}


def expected_band(level: int) -> tuple[str, str]:
    for start, end, band, owner in EXPECTED_BANDS:
        if start <= level <= end:
            return band, owner
    raise ValueError(level)


def validate_matrix(matrix: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []

    if matrix.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if matrix.get("task_id") != "T12":
        errors.append("task_id must be T12")
    if matrix.get("status") != "PREPARATION_ONLY_NON_SHIPPING":
        errors.append("matrix status must remain PREPARATION_ONLY_NON_SHIPPING")
    if matrix.get("shipping_path_forbidden") is not True:
        errors.append("shipping_path_forbidden must remain true")

    invariants = matrix.get("invariants")
    if invariants != EXPECTED_INVARIANTS:
        errors.append(
            "matrix invariants drifted from frozen T12 contract: "
            + json.dumps({"expected": EXPECTED_INVARIANTS, "actual": invariants}, sort_keys=True)
        )

    concrete = matrix.get("concrete_binding_ids")
    if concrete != {"T10": [], "T11": []}:
        errors.append("concrete T10/T11 binding IDs must remain empty before activation reconciliation")

    forbidden = set(matrix.get("forbidden_eligibility_inputs", []))
    missing_forbidden = sorted(REQUIRED_FORBIDDEN_INPUTS - forbidden)
    if missing_forbidden:
        errors.append(f"missing forbidden eligibility inputs: {missing_forbidden}")

    profiles = matrix.get("binding_profiles")
    if not isinstance(profiles, dict):
        errors.append("binding_profiles must be an object")
        profiles = {}
    for name in {row[1] for row in ROLE_PATTERN.values()}:
        profile = profiles.get(name)
        if not isinstance(profile, dict):
            errors.append(f"missing binding profile: {name}")
            continue
        if not isinstance(profile.get("effect"), str) or not profile["effect"].strip():
            errors.append(f"binding profile {name} needs a practical effect description")
        classes = profile.get("classes")
        if not isinstance(classes, list) or not classes or any(not isinstance(x, str) or not x for x in classes):
            errors.append(f"binding profile {name} requires one or more binding classes")

    levels = matrix.get("levels")
    if not isinstance(levels, list):
        return {"passed": False, "errors": errors + ["levels must be a list"]}
    if len(levels) != 100:
        errors.append(f"exactly 100 prepared levels required, got {len(levels)}")

    seen_levels: set[int] = set()
    seen_ids: set[str] = set()
    visible_levels: list[int] = []
    major_levels: list[int] = []

    for index, row in enumerate(levels):
        if not isinstance(row, dict):
            errors.append(f"levels[{index}] must be an object")
            continue
        level = row.get("level")
        if not isinstance(level, int) or isinstance(level, bool) or not 1 <= level <= 100:
            errors.append(f"levels[{index}].level must be integer 1..100")
            continue
        if level in seen_levels:
            errors.append(f"duplicate level: {level}")
        seen_levels.add(level)

        expected_id = f"t12.level.{level:03d}"
        if row.get("id") != expected_id:
            errors.append(f"level {level}: id must be {expected_id}")
        if expected_id in seen_ids:
            errors.append(f"duplicate id: {expected_id}")
        seen_ids.add(expected_id)

        band, owner = expected_band(level)
        if row.get("band") != band:
            errors.append(f"level {level}: expected band {band}, got {row.get('band')!r}")
        if row.get("owner") != owner:
            errors.append(f"level {level}: expected content owner {owner}, got {row.get('owner')!r}")

        relative = level % 10
        role, binding_profile, visible, major = ROLE_PATTERN[relative]
        if row.get("role") != role:
            errors.append(f"level {level}: expected role {role}, got {row.get('role')!r}")
        if row.get("binding_profile") != binding_profile:
            errors.append(f"level {level}: expected binding_profile {binding_profile}")
        if binding_profile not in profiles:
            errors.append(f"level {level}: unknown binding_profile {binding_profile}")
        if row.get("visible") is not visible:
            errors.append(f"level {level}: visible must be {visible}")
        if row.get("major") is not major:
            errors.append(f"level {level}: major must be {major}")

        expected_requires = [] if level == 1 else [f"t12.level.{level - 1:03d}"]
        if row.get("requires") != expected_requires:
            errors.append(f"level {level}: baseline prerequisite must be {expected_requires}")

        if visible:
            visible_levels.append(level)
        if major:
            major_levels.append(level)

    missing_levels = sorted(set(range(1, 101)) - seen_levels)
    if missing_levels:
        errors.append(f"missing levels: {missing_levels}")

    expected_visible = [level for level in range(1, 101) if level % 10 in {0, 3, 6, 9}]
    if visible_levels != expected_visible:
        errors.append("visible cadence does not match the frozen x3/x6/x9/x0 pattern")
    for previous, current in zip(visible_levels, visible_levels[1:]):
        if current - previous > 3:
            errors.append(f"visible cadence gap exceeds 3 levels: {previous}->{current}")

    expected_major = list(range(10, 101, 10))
    if major_levels != expected_major:
        errors.append(f"major milestones must be exactly {expected_major}, got {major_levels}")

    serialized = json.dumps(matrix, sort_keys=True).lower()
    for forbidden_prefix in ("t10_provisional:", "t11_provisional:", "provisional:t10", "provisional:t11"):
        if forbidden_prefix in serialized:
            errors.append(f"concrete provisional upstream ID leaked into matrix: {forbidden_prefix}")

    return {
        "passed": not errors,
        "level_count": len(levels),
        "visible_level_count": len(visible_levels),
        "major_level_count": len(major_levels),
        "concrete_t10_binding_count": len(concrete.get("T10", [])) if isinstance(concrete, dict) and isinstance(concrete.get("T10"), list) else None,
        "concrete_t11_binding_count": len(concrete.get("T11", [])) if isinstance(concrete, dict) and isinstance(concrete.get("T11"), list) else None,
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="Docs/Production/T12/LEVEL_1_100_MATRIX.json")
    args = parser.parse_args()
    matrix = json.loads(pathlib.Path(args.input).read_text())
    result = validate_matrix(matrix)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
