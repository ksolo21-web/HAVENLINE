#!/usr/bin/env python3
"""Static source-contract validation for the T11 build-pending candidate.

This validator never approves T11 and never proves final T10 compatibility.
It verifies that the isolated candidate contains the frozen camp-content files,
uses authored stages, keeps build-pending recipes non-shipping, exposes truthful
in-world lifecycle presentation, produces real rendered evidence, and respects
T10/later-task authority boundaries before final integration review.
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
MANIFEST = ROOT / "HavenlineGodot" / "assets" / "camp_upgrades_v1" / "manifest.json"
WORKFLOOR = ROOT / "HavenlineGodot" / "assets" / "camp_upgrades_v1" / "camp_workfloor.obj"
CANOPY = ROOT / "HavenlineGodot" / "assets" / "camp_upgrades_v1" / "camp_canopy.obj"
CANOPY_MTL = ROOT / "HavenlineGodot" / "assets" / "camp_upgrades_v1" / "camp_canopy.mtl"
STAGES = [
    ROOT / "HavenlineGodot" / "assets" / "camp_upgrades_v1" / "site_unbuilt.tscn",
    ROOT / "HavenlineGodot" / "assets" / "camp_upgrades_v1" / "camp_initial.tscn",
    ROOT / "HavenlineGodot" / "assets" / "camp_upgrades_v1" / "camp_upgraded_01.tscn",
]
TEST_DOMAIN = ROOT / "HavenlineGodot" / "tests" / "test_task11_camp_construction.gd"
TEST_INTEGRATION = ROOT / "HavenlineGodot" / "tests" / "test_task11_integration.gd"
CAPTURE = ROOT / "HavenlineGodot" / "tests" / "capture_task11_camp_upgrade.gd"

REQUIRED_RECIPE_FIELDS = {
    "camp_state_id",
    "t10_recipe_id",
    "source_camp_state",
    "target_camp_state",
    "t10_source_state",
    "t10_target_state",
    "presentation_key",
    "asset_manifest_key",
    "shipping",
    "route_clearance_profile",
    "camera_readability_profile",
}
REQUIRED_DOMAIN_MARKERS = (
    "preview_camp_upgrade",
    "commit_camp_upgrade",
    "accept_camp_receipt",
    "camp_state_id",
    "t10_recipe_id",
    "transform_port",
)
REQUIRED_VIEW_MARKERS = ("blocked", "ready", "preview", "committing", "complete", "error")
REQUIRED_VIEW_VISUAL_MARKERS = (
    "LifecycleStatus",
    "LifecycleRing",
    "LifecycleSpire",
    "LifecycleOrb",
    "STATUS_BEACON_OFFSET",
    "STATUS_ORB_RADIUS",
    "lifecycle_color",
    "status_descriptor",
    "t11_presentation_only",
)
REQUIRED_CAPTURE_MARKERS = (
    "SubViewport",
    "save_png",
    "--native-4k",
    "3840, 2160",
    "CameraPolicy.VIEW_OFFSET",
    "CampBoundaryView",
    "Boundary.GATE_AUTHORITY_ID",
    "approved_t03_boundary_rendered",
    "source_bound",
    "final_visual_critic_evidence",
)
FORBIDDEN_VIEW_MUTATORS = (
    "grant_resource",
    "set_resource_count",
    "add_resource",
    "advance_progression",
    "commit_transform",
    "commit_camp_upgrade",
)
REQUIRED_STAGES = {"site_unbuilt", "camp_initial", "camp_upgraded_01"}
REQUIRED_UPGRADE_NODES = {
    "UpgradeCanopyWest",
    "UpgradeCanopyEast",
    "UpgradeLanternNW",
    "UpgradeLanternNE",
    "UpgradeLanternSW",
    "UpgradeLanternSE",
    "UpgradeTimberWest",
    "UpgradeTimberEast",
}


def emit(payload, output: pathlib.Path | None):
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


def fail(errors, output: pathlib.Path | None, candidate: str):
    payload = {"task_id": "T11", "candidate": candidate, "passed": False, "errors": errors, "task_approved": False}
    emit(payload, output)
    raise SystemExit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", default="HEAD")
    ap.add_argument("--output")
    args = ap.parse_args()
    output = pathlib.Path(args.output) if args.output else None

    errors: list[str] = []
    required = [SCRIPT, VIEW, RECIPES, MANIFEST, WORKFLOOR, CANOPY, CANOPY_MTL, *STAGES, TEST_DOMAIN, TEST_INTEGRATION, CAPTURE]
    for path in required:
        if not path.exists() or not path.read_text().strip():
            errors.append(f"missing or empty required T11 file: {path.relative_to(ROOT)}")
    if errors:
        fail(errors, output, args.candidate)

    domain = SCRIPT.read_text()
    view = VIEW.read_text()
    capture = CAPTURE.read_text()
    for marker in REQUIRED_DOMAIN_MARKERS:
        if marker not in domain:
            errors.append(f"camp_construction.gd missing frozen contract marker: {marker}")
    if "world_transform.gd" in domain:
        errors.append("camp_construction.gd may not preload unfinished T10 runtime")
    for marker in REQUIRED_VIEW_MARKERS:
        if marker not in view:
            errors.append(f"camp_construction_view.gd missing lifecycle marker: {marker}")
    for marker in REQUIRED_VIEW_VISUAL_MARKERS:
        if marker not in view:
            errors.append(f"camp_construction_view.gd missing visible lifecycle contract marker: {marker}")
    for marker in FORBIDDEN_VIEW_MUTATORS:
        if re.search(rf"\b{re.escape(marker)}\b", view):
            errors.append(f"presentation contains forbidden authority marker: {marker}")
    if "func _process" in view or "func _physics_process" in view:
        errors.append("T11 lifecycle presentation may not add continuous per-frame rebuild/update authority")
    for marker in REQUIRED_CAPTURE_MARKERS:
        if marker not in capture:
            errors.append(f"capture harness missing real rendered-evidence marker: {marker}")
    if "real_t11_stage_scenes" not in capture or "review_snow_and_lane_stage_is_not_shipping_content" not in capture:
        errors.append("capture harness must disclose real T11 stages and non-shipping review staging")
    if "CampBoundaryView.new()" not in capture or "boundary_view.configure(self)" not in capture:
        errors.append("capture harness must instantiate the approved T03 boundary presentation rather than recreating perimeter geometry")

    try:
        raw = json.loads(RECIPES.read_text())
    except Exception as exc:
        errors.append(f"camp registry is not valid JSON: {exc}")
        raw = {}

    if raw.get("build_pending_dependency") is not True:
        errors.append("camp registry must disclose build_pending_dependency=true")
    if raw.get("final_t10_reconciliation_required") is not True:
        errors.append("camp registry must require final T10 reconciliation")

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

        if "costs" in recipe or "debits" in recipe:
            errors.append(f"recipe {sid} duplicates T10 cost/debit authority")

        source = recipe["source_camp_state"]
        target = recipe["target_camp_state"]
        if not isinstance(source, str) or not source:
            errors.append(f"recipe {sid} source_camp_state must be non-empty string")
        if not isinstance(target, str) or not target:
            errors.append(f"recipe {sid} target_camp_state must be non-empty string")
        if source == target and not recipe.get("allow_self_transition", False):
            errors.append(f"recipe {sid} has forbidden implicit self-transition")

        for field in ("t10_source_state", "t10_target_state", "presentation_key", "asset_manifest_key", "route_clearance_profile", "camera_readability_profile"):
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
            errors.append(f"build-pending candidate may not contain shipping recipe: {sid}")
        else:
            test_only_count += 1
            if recipe.get("test_only") is not True:
                errors.append(f"non-shipping build-pending recipe {sid} must set test_only=true")
            if recipe.get("binding_status") != "t10_prebuild_fixture_unapproved":
                errors.append(f"recipe {sid} must disclose unapproved T10 prebuild binding")

    try:
        manifest = json.loads(MANIFEST.read_text())
    except Exception as exc:
        errors.append(f"camp asset manifest is not valid JSON: {exc}")
        manifest = {}
    stages = manifest.get("stages", {}) if isinstance(manifest, dict) else {}
    if set(stages) != REQUIRED_STAGES:
        errors.append(f"camp asset manifest stages must equal {sorted(REQUIRED_STAGES)}, got {sorted(stages)}")
    if manifest.get("content_boundaries", {}).get("t03_perimeter_reused_not_duplicated") is not True:
        errors.append("manifest must preserve T03 perimeter authority")
    if manifest.get("content_boundaries", {}).get("shipping_prices_included") is not False:
        errors.append("build-pending manifest may not claim shipping prices")
    canopy_row = manifest.get("authored_assets", {}).get("counter_canopy", {})
    if canopy_row.get("mesh") != "res://assets/camp_upgrades_v1/camp_canopy.obj":
        errors.append("manifest must lock the T11-authored counter canopy mesh")
    if canopy_row.get("shipping_behavior") is not False:
        errors.append("counter canopy must remain presentation-only in T11")
    for state, row in stages.items():
        scene_path = row.get("scene")
        if not isinstance(scene_path, str) or not scene_path.startswith("res://assets/camp_upgrades_v1/"):
            errors.append(f"stage {state} must use a T11-owned scene")
    upgrade_nodes = set(stages.get("camp_upgraded_01", {}).get("required_visible_upgrade_nodes", []))
    if upgrade_nodes != REQUIRED_UPGRADE_NODES:
        errors.append(f"camp_upgraded_01 visible nodes must equal {sorted(REQUIRED_UPGRADE_NODES)}, got {sorted(upgrade_nodes)}")

    stage_text = "\n".join(path.read_text() for path in STAGES)
    upgraded_text = STAGES[-1].read_text()
    if "defense_platform.glb" in stage_text:
        errors.append("T11 may not pre-spawn T22 defense platform")
    if "barricade.glb" in stage_text:
        errors.append("T11 may not duplicate T03 perimeter/barricade authority")
    for required_asset in ("pad_build.glb", "hearth_vessel.glb", "pad_upgrade.glb"):
        if required_asset not in stage_text:
            errors.append(f"authored T11 stages missing required approved T05 asset: {required_asset}")
    if "WarmWorkFloor" not in stage_text:
        errors.append("constructed T11 stages must include authored warm work floor")
    if "camp_canopy.obj" not in upgraded_text:
        errors.append("first visible upgrade must include authored canopy geometry")
    for node in REQUIRED_UPGRADE_NODES:
        if f'name="{node}"' not in upgraded_text:
            errors.append(f"first visible upgrade missing required authored node: {node}")

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
        "authored_stage_ids": sorted(stages),
        "required_visible_upgrade_nodes": sorted(REQUIRED_UPGRADE_NODES),
        "required_file_count": len(required),
        "required_files": [str(p.relative_to(ROOT)) for p in required],
        "domain_contract_markers": list(REQUIRED_DOMAIN_MARKERS),
        "view_lifecycle_markers": list(REQUIRED_VIEW_MARKERS),
        "view_visual_contract_markers": list(REQUIRED_VIEW_VISUAL_MARKERS),
        "rendered_capture_contract_markers": list(REQUIRED_CAPTURE_MARKERS),
        "approved_t03_boundary_required_in_rendered_evidence": True,
        "readable_lifecycle_orb_beacon_required": True,
        "build_pending_dependency": True,
        "final_t10_compatibility_claimed": False,
        "task_approved": False,
    }
    emit(payload, output)


if __name__ == "__main__":
    main()
