#!/usr/bin/env python3
"""Static source-contract validation for a future T10 candidate.

This validator intentionally does not approve T10. It verifies that the isolated
candidate contains the frozen files/recipe schema before engine/runtime review.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "HavenlineGodot" / "scripts" / "world_transform.gd"
VIEW = ROOT / "HavenlineGodot" / "scripts" / "world_transform_view.gd"
RECIPES = ROOT / "HavenlineGodot" / "data" / "world_transform_recipes.json"
TEST_DOMAIN = ROOT / "HavenlineGodot" / "tests" / "test_task10_world_transform.gd"
TEST_INTEGRATION = ROOT / "HavenlineGodot" / "tests" / "test_task10_integration.gd"
CAPTURE = ROOT / "HavenlineGodot" / "tests" / "capture_task10_world_transform.gd"

REQUIRED_RECIPE_FIELDS = {
    "recipe_id", "source_state", "target_state", "costs",
    "prerequisites", "progression_tags", "presentation_key",
}
REQUIRED_DOMAIN_MARKERS = (
    "preview_transform",
    "commit_transform",
    "transaction_id",
    "export_component_state",
    "import_component_state",
)
REQUIRED_VIEW_MARKERS = (
    "locked", "ready", "preview", "committing", "complete",
)


def fail(errors, output: pathlib.Path | None, candidate: str):
    payload = {"task_id": "T10", "candidate": candidate, "passed": False, "errors": errors}
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))
    raise SystemExit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", default="HEAD")
    ap.add_argument("--output")
    args = ap.parse_args()
    output = pathlib.Path(args.output) if args.output else None

    errors: list[str] = []
    required = [SCRIPT, VIEW, RECIPES, TEST_DOMAIN, TEST_INTEGRATION, CAPTURE]
    for path in required:
        if not path.exists() or not path.read_text().strip():
            errors.append(f"missing or empty required T10 file: {path.relative_to(ROOT)}")
    if errors:
        fail(errors, output, args.candidate)

    domain = SCRIPT.read_text()
    view = VIEW.read_text()
    for marker in REQUIRED_DOMAIN_MARKERS:
        if marker not in domain:
            errors.append(f"world_transform.gd missing frozen contract marker: {marker}")
    for marker in REQUIRED_VIEW_MARKERS:
        if marker not in view:
            errors.append(f"world_transform_view.gd missing lifecycle marker: {marker}")

    # Presentation is not allowed to become an alternate resource/progression authority.
    forbidden_view_mutators = ("grant_resource", "set_resource_count", "add_resource", "advance_progression")
    for marker in forbidden_view_mutators:
        if re.search(rf"\b{re.escape(marker)}\b", view):
            errors.append(f"presentation contains forbidden authority marker: {marker}")

    try:
        raw = json.loads(RECIPES.read_text())
    except Exception as exc:
        errors.append(f"recipe registry is not valid JSON: {exc}")
        raw = {}

    recipes = raw.get("recipes") if isinstance(raw, dict) else None
    if not isinstance(recipes, list) or not recipes:
        errors.append("world_transform_recipes.json must contain non-empty recipes[] fixtures")
        recipes = []

    seen_ids = set()
    for index, recipe in enumerate(recipes):
        if not isinstance(recipe, dict):
            errors.append(f"recipe[{index}] must be an object")
            continue
        missing = REQUIRED_RECIPE_FIELDS - set(recipe)
        if missing:
            errors.append(f"recipe[{index}] missing fields: {sorted(missing)}")
            continue
        rid = recipe["recipe_id"]
        if not isinstance(rid, str) or not rid.strip():
            errors.append(f"recipe[{index}] recipe_id must be non-empty string")
        elif rid in seen_ids:
            errors.append(f"duplicate recipe_id: {rid}")
        seen_ids.add(rid)
        if recipe["source_state"] == recipe["target_state"] and not recipe.get("allow_self_transition", False):
            errors.append(f"recipe {rid} has forbidden implicit self-transition")
        costs = recipe["costs"]
        if not isinstance(costs, list) or not costs:
            errors.append(f"recipe {rid} costs must be non-empty list")
            continue
        cost_resources = set()
        for cost in costs:
            if not isinstance(cost, dict) or set(cost) < {"resource_id", "quantity"}:
                errors.append(f"recipe {rid} has malformed cost row")
                continue
            resource = cost["resource_id"]
            quantity = cost["quantity"]
            if not isinstance(resource, str) or not resource:
                errors.append(f"recipe {rid} has empty resource_id")
            if resource in cost_resources:
                errors.append(f"recipe {rid} repeats resource cost {resource}; costs must be normalized")
            cost_resources.add(resource)
            if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
                errors.append(f"recipe {rid} cost for {resource} must be positive integer")
        for key in ("prerequisites", "progression_tags"):
            if not isinstance(recipe[key], list) or len(recipe[key]) != len(set(recipe[key])):
                errors.append(f"recipe {rid} {key} must be a duplicate-free list")
        if not isinstance(recipe["presentation_key"], str) or not recipe["presentation_key"]:
            errors.append(f"recipe {rid} presentation_key must be non-empty string")
        reversible = recipe.get("reversible", False)
        if reversible and not recipe.get("inverse_recipe_id"):
            errors.append(f"reversible recipe {rid} requires inverse_recipe_id")
        if not reversible and recipe.get("inverse_recipe_id"):
            errors.append(f"non-reversible recipe {rid} must not declare inverse_recipe_id")

    if errors:
        fail(errors, output, args.candidate)

    payload = {
        "task_id": "T10",
        "candidate": args.candidate,
        "passed": True,
        "recipe_count": len(recipes),
        "recipe_ids": sorted(seen_ids),
        "required_files": [str(p.relative_to(ROOT)) for p in required],
        "domain_contract_markers": list(REQUIRED_DOMAIN_MARKERS),
        "view_lifecycle_markers": list(REQUIRED_VIEW_MARKERS),
        "task_approved": False,
    }
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
