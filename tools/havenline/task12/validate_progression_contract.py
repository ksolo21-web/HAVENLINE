#!/usr/bin/env python3
"""Static validator for future T12 Level 1-100 progression manifests.

This is preparation tooling only. It validates candidate data supplied with
--input and never writes shipping progression files.
"""
from __future__ import annotations

import argparse
import json
import pathlib
from collections import defaultdict, deque
from typing import Any

FORBIDDEN_ELIGIBILITY_KEYS = {
    "purchase_history",
    "purchasehistory",
    "vip_status",
    "vipstatus",
    "vip_level",
    "viplevel",
    "premium_spend",
    "premiumspend",
    "premium_currency_spend",
    "premiumcurrencyspend",
    "spend_tier",
    "spendtier",
    "payer_status",
    "payerstatus",
    "energy",
    "energy_required",
    "energyrequired",
    "energy_cost",
    "energycost",
}

PROVISIONAL_PREFIXES = (
    "provisional:",
    "t10_provisional:",
    "t11_provisional:",
    "prepared_only:",
)

REQUIRED_LEVEL_FIELDS = (
    "level",
    "level_id",
    "region_band_id",
    "prerequisite_level_ids",
    "required_fact_ids",
    "progression_effects",
    "visible_progression_hook_ids",
    "milestone_ids",
    "one_time_event_ids",
)

REGION_BANDS = (
    (1, 10, "band_opening_frozen"),
    (11, 20, "band_forest"),
    (21, 30, "band_desert"),
    (31, 40, "band_underwater"),
    (41, 50, "band_sky"),
    (51, 60, "band_volcanic"),
    (61, 70, "band_swamp"),
    (71, 80, "band_ruins"),
    (81, 90, "band_underground"),
    (91, 100, "band_alien"),
)

FORBIDDEN_FILLER_EFFECT_KINDS = {
    "counter",
    "counter_only",
    "level_counter",
    "stat_only",
    "xp_only",
    "numeric_only",
}


def normalized_key(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def walk_keys(value: Any, path: str = "root"):
    if isinstance(value, dict):
        for key, child in value.items():
            yield path, str(key), child
            yield from walk_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_keys(child, f"{path}[{index}]")


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    levels = manifest.get("levels")
    milestones = manifest.get("milestones", [])
    if not isinstance(levels, list):
        return {"passed": False, "errors": ["manifest.levels must be a list"], "warnings": []}
    if not isinstance(milestones, list):
        errors.append("manifest.milestones must be a list")
        milestones = []

    if len(levels) != 100:
        errors.append(f"exactly 100 shipping level records required, got {len(levels)}")

    by_number: dict[int, dict[str, Any]] = {}
    id_to_number: dict[str, int] = {}
    duplicate_numbers: set[int] = set()
    duplicate_ids: set[str] = set()

    for index, row in enumerate(levels):
        if not isinstance(row, dict):
            errors.append(f"levels[{index}] must be an object")
            continue

        level = row.get("level")
        level_id = row.get("level_id")
        if not isinstance(level, int) or isinstance(level, bool) or not 1 <= level <= 100:
            errors.append(f"levels[{index}].level must be integer 1..100, got {level!r}")
            continue
        if level in by_number:
            duplicate_numbers.add(level)
        by_number[level] = row

        if not isinstance(level_id, str) or not level_id.strip():
            errors.append(f"level {level}: level_id must be a non-empty string")
        elif level_id in id_to_number:
            duplicate_ids.add(level_id)
        else:
            id_to_number[level_id] = level

        effects = row.get("progression_effects")
        if not isinstance(effects, list) or not effects:
            errors.append(f"level {level}: progression_effects must contain at least one practical effect")

        prereqs = row.get("prerequisite_level_ids", [])
        if not isinstance(prereqs, list) or any(not isinstance(x, str) or not x for x in prereqs):
            errors.append(f"level {level}: prerequisite_level_ids must be a list of non-empty strings")

        for key_path, key, _ in walk_keys(row, f"level[{level}]"):
            if normalized_key(key) in FORBIDDEN_ELIGIBILITY_KEYS:
                errors.append(f"level {level}: forbidden spend/energy eligibility key at {key_path}.{key}: {key}")

        for hook in as_list(row.get("visible_progression_hook_ids")) + as_list(row.get("one_time_event_ids")):
            if isinstance(hook, str) and hook.lower().startswith(PROVISIONAL_PREFIXES):
                errors.append(f"level {level}: provisional hook/event ID cannot ship: {hook}")

    if duplicate_numbers:
        errors.append(f"duplicate level numbers: {sorted(duplicate_numbers)}")
    if duplicate_ids:
        errors.append(f"duplicate level IDs: {sorted(duplicate_ids)}")

    expected_numbers = set(range(1, 101))
    missing_numbers = sorted(expected_numbers - set(by_number))
    if missing_numbers:
        errors.append(f"missing level numbers: {missing_numbers}")

    # Stable prerequisite graph checks.
    graph: dict[str, list[str]] = defaultdict(list)
    indegree: dict[str, int] = {level_id: 0 for level_id in id_to_number}
    for level, row in by_number.items():
        level_id = row.get("level_id")
        if not isinstance(level_id, str) or level_id not in id_to_number:
            continue
        prereqs = row.get("prerequisite_level_ids", [])
        if not isinstance(prereqs, list):
            continue
        if level == 1 and prereqs:
            errors.append("level 1 must not require another level")
        for prereq_id in prereqs:
            if prereq_id not in id_to_number:
                errors.append(f"level {level}: prerequisite target does not exist: {prereq_id}")
                continue
            if prereq_id == level_id:
                errors.append(f"level {level}: self prerequisite is forbidden")
            graph[prereq_id].append(level_id)
            indegree[level_id] = indegree.get(level_id, 0) + 1

    queue = deque(sorted((node for node, degree in indegree.items() if degree == 0), key=lambda n: id_to_number[n]))
    visited: list[str] = []
    indegree_work = dict(indegree)
    while queue:
        node = queue.popleft()
        visited.append(node)
        for nxt in graph.get(node, []):
            indegree_work[nxt] -= 1
            if indegree_work[nxt] == 0:
                queue.append(nxt)
    if len(visited) != len(indegree):
        cycle_nodes = sorted(set(indegree) - set(visited), key=lambda n: id_to_number[n])
        errors.append(f"progression prerequisite graph contains a cycle/unresolved cyclic component: {cycle_nodes}")

    # Reachability must originate at level 1; disconnected roots are invalid.
    level1_id = by_number.get(1, {}).get("level_id") if 1 in by_number else None
    if isinstance(level1_id, str) and level1_id in id_to_number:
        reachable = {level1_id}
        frontier = [level1_id]
        while frontier:
            node = frontier.pop()
            for nxt in graph.get(node, []):
                if nxt not in reachable:
                    reachable.add(nxt)
                    frontier.append(nxt)
        unreachable = sorted(set(id_to_number) - reachable, key=lambda n: id_to_number[n])
        if unreachable:
            errors.append(f"shipping levels unreachable from level 1: {unreachable}")

    # Visible cadence: first visible hook by L3, then max 3 levels between hooks,
    # and a visible hook at/after L98 so the ending does not go visually stale.
    visible_levels: set[int] = set()
    for level, row in by_number.items():
        hooks = row.get("visible_progression_hook_ids", [])
        if isinstance(hooks, list) and any(isinstance(x, str) and x.strip() for x in hooks):
            visible_levels.add(level)

    milestone_by_level: dict[int, list[dict[str, Any]]] = defaultdict(list)
    milestone_ids: set[str] = set()
    for index, milestone in enumerate(milestones):
        if not isinstance(milestone, dict):
            errors.append(f"milestones[{index}] must be an object")
            continue
        milestone_id = milestone.get("milestone_id")
        level = milestone.get("level")
        if not isinstance(milestone_id, str) or not milestone_id.strip():
            errors.append(f"milestones[{index}].milestone_id must be non-empty")
        elif milestone_id in milestone_ids:
            errors.append(f"duplicate milestone_id: {milestone_id}")
        else:
            milestone_ids.add(milestone_id)
        if not isinstance(level, int) or level not in by_number:
            errors.append(f"milestone {milestone_id!r}: level must resolve to a shipping level")
            continue
        milestone_by_level[level].append(milestone)
        if milestone.get("visible_change_required") is True:
            visible_levels.add(level)

    if not visible_levels:
        errors.append("no visible progression hooks/milestones are declared")
    else:
        ordered_visible = sorted(visible_levels)
        if ordered_visible[0] > 3:
            errors.append(f"first visible progression hook occurs too late at level {ordered_visible[0]}")
        previous = 0
        for level in ordered_visible:
            gap = level - previous
            if previous and gap > 3:
                errors.append(f"visible progression gap exceeds 3 levels: {previous} -> {level}")
            previous = level
        if ordered_visible[-1] < 98:
            errors.append(f"final visible progression hook occurs too early at level {ordered_visible[-1]}")

    # Major milestone every ten-level band at the default x0 boundary.
    for boundary in range(10, 101, 10):
        rows = milestone_by_level.get(boundary, [])
        if not any(str(row.get("kind", "")).lower() == "major" for row in rows):
            errors.append(f"missing default major milestone at level {boundary}")

    # One-time event identity uniqueness across levels.
    event_owner: dict[str, int] = {}
    for level, row in by_number.items():
        events = row.get("one_time_event_ids", [])
        if not isinstance(events, list):
            errors.append(f"level {level}: one_time_event_ids must be a list")
            continue
        for event_id in events:
            if not isinstance(event_id, str) or not event_id.strip():
                errors.append(f"level {level}: one_time_event_ids contains invalid ID {event_id!r}")
                continue
            if event_id in event_owner:
                errors.append(f"duplicate one-time event ID {event_id} at levels {event_owner[event_id]} and {level}")
            else:
                event_owner[event_id] = level

    return {
        "passed": not errors,
        "level_record_count": len(levels),
        "unique_level_ids": len(id_to_number),
        "visible_level_count": len(visible_levels),
        "major_milestone_count": sum(
            1 for rows in milestone_by_level.values() for row in rows if str(row.get("kind", "")).lower() == "major"
        ),
        "errors": errors,
        "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Progression manifest JSON to validate")
    args = parser.parse_args()
    path = pathlib.Path(args.input)
    manifest = json.loads(path.read_text())
    result = validate_manifest(manifest)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
