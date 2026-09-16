#!/usr/bin/env python3
"""Static source-contract validation for a future T11 candidate.

This validator never approves T11. It verifies that an isolated candidate
contains the frozen camp-content files and respects T10 authority boundaries
before engine/runtime/visual review begins.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "HavenlineGodot" / "scripts" / "camp_construction.gd"
VIEW = ROOT / "HavenlineGodot" / "scripts" / "camp_construction_view.gd"
RECIPES = ROOT / "HavenlineGodot" / "data" / "camp_upgrade_recipes.json"
TEST_DOMAIN = ROOT / "HavenlineGodot" / "tests" / "test_task11_camp_construction.gd"
TEST_INTEGRATION = ROOT / "HavenlineGodot" / "tests" / "test_task11_integration.gd"
CAPTURE = ROOT / "HavenlineGodot" / "tests" / "capture_task11_camp_upgrade.gd"

REQUIRED_RECIPE_FIELDS = {
    "camp_state_id",
    "t10_recipe_id",
    "source_camp_state",
    "target_camp_state",
    "presentation_key",
    "asset_manifest_key",
    "shipping",
    "route_clearance_profile",
    "camera_readability_profile",
}
REQUIRED_DOMAIN_MARKERS = (
    "preview_camp_upgrade",
    "commit_camp_upgrade",
    "camp_state_id",
    "t10_recipe_id",
)
REQUIRED_VIEW_MARKERS = ("blocked", "ready", "preview", "committing", "complete")
FORBIDDEN_VIEW_MUTATORS = (
    "grant_resource",
    "set_resource_count",
    "add_resource",
    "advance_progression",
    "commit_transform",
    "commit_camp_upgrade",
)


def emit(payload, output: pathlib.Path | None):
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


def fail(errors, output: pathlib.Path | None, candidate: str):
    payload = {"task_id": "T11", "candidate": candidate, "passed": False, "errors": errors}
    emit(payload, output)
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
            errors.append(f"missing or empty required T11 file: {path.relative_to(ROOT)}")
    if errors:
        fail(errors, output, args.candidate)

    domain = SCRIPT.read_text()
    view = VIEW.read_text()
    for marker in REQUIRED_DOMAIN_MARKERS:
        if marker not in domain:
            errors.append(f"camp_construction.gd missing frozen contract marker: {marker}")
    for marker in REQUIRED_VIEW_MARKERS:
        if marker not in view:
            errors.append(f"camp_construction_view.gd missing lifecycle marker: {marker}")
    for marker in FORBIDDEN_VIEW_MUTATORS:
        if re.search(rf"\b{re.escape(marker)}\b", view):
            errors.append(f"presentation contains forbidden authority marker: {marker}")

    try:
        raw = json.loads(RECIPES.read_text())
    except Exception as exc:
        errors.append(f"camp registry is not valid JSON: {exc}")
        raw = {}

    recipes = raw.get("recipes") if isinstance(raw, dict) else None
    if not isinstance(recipes, list) or not recipes:
        errors.append("camp_upgrade_recipes.json must contain non-empty recipes[]")
        recipes = []

    seen_states = set()
    seen_t10 = set()
    shipping_count = 0
    test_only_count = 0
    for index, recipe in enumerate(recipes):
        if not isinstance(recipe, dict):
            errors.append(f"recipe[{index}] must be an object")
            continue
        missing = REQUIRED_RECIPE_FIELDS - set(recipe)
        if missing:
            errors.append(f"recipe[{index}] missing fields: {sorted(missing)}")
            continue

        sid = recipe["camp_state_id"]
        t10 = recipe["t10_recipe_id"]
        if not isinstance(sid, str) or not sid.strip():
            errors.append(f"recipe[{index}] camp_state_id must be non-empty string")
        elif sid in seen_states:
            errors.append(f"duplicate camp_state_id: {sid}")
        seen_states.add(sid)

        if not isinstance(t10, str) or not t10.strip():
            errors.append(f"recipe {sid} t10_recipe_id must be non-empty string")
        elif t10 in seen_t10:
            errors.append(f"duplicate T10 recipe binding: {t10}")
        seen_t10.add(t10)

        source = recipe["source_camp_state"]
        target = recipe["target_camp_state"]
        if not isinstance(source, str) or not source:
            errors.append(f"recipe {sid} source_camp_state must be non-empty string")
        if not isinstance(target, str) or not target:
            errors.append(f"recipe {sid} target_camp_state must be non-empty string")
        if source == target and not recipe.get("allow_self_transition", False):
            errors.append(f"recipe {sid} has forbidden implicit self-transition")

        for field in ("presentation_key", "asset_manifest_key", "route_clearance_profile", "camera_readability_profile"):
            if not isinstance(recipe[field], str) or not recipe[field].strip():
                errors.append(f"recipe {sid} {field} must be non-empty string")

        shipping = recipe["shipping"]
        if not isinstance(shipping, bool):
            errors.append(f"recipe {sid} shipping must be boolean")
            continue
        if shipping:
            shipping_count += 1
            price_source = recipe.get("price_source") or recipe.get("tuning_record")
            if not isinstance(price_source, str) or not price_source.strip():
                errors.append(f"shipping recipe {sid} requires price_source or tuning_record provenance")
            if recipe.get("test_only_costs"):
                errors.append(f"shipping recipe {sid} may not contain test_only_costs")
        else:
            test_only_count += 1
            if recipe.get("price_source") and recipe.get("test_only_costs"):
                errors.append(f"test recipe {sid} must not mix shipping price_source with test_only_costs")

    if errors:
        fail(errors, output, args.candidate)

    payload = {
        "task_id": "T11",
        "candidate": args.candidate,
        "passed": True,
        "recipe_count": len(recipes),
        "shipping_recipe_count": shipping_count,
        "test_only_recipe_count": test_only_count,
        "camp_state_ids": sorted(seen_states),
        "required_files": [str(p.relative_to(ROOT)) for p in required],
        "domain_contract_markers": list(REQUIRED_DOMAIN_MARKERS),
        "view_lifecycle_markers": list(REQUIRED_VIEW_MARKERS),
        "task_approved": False,
    }
    emit(payload, output)


if __name__ == "__main__":
    main()
