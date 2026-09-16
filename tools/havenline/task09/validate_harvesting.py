#!/usr/bin/env python3
"""Fail-closed static validation for the first T09 harvesting milestone."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ASSETS = ROOT / "HavenlineGodot" / "assets" / "harvesting_v1"
SCRIPT = ROOT / "HavenlineGodot" / "scripts" / "harvest_presentation.gd"
MAIN = ROOT / "HavenlineGodot" / "scripts" / "main.gd"
REGISTRY = ROOT / "Docs" / "Production" / "RESOURCE_ACTION_REGISTRY.json"
REFERENCE_SELECTION = ROOT / "Docs" / "Production" / "T09" / "reference-selection.json"

EXPECTED = {
    "axe": ("chop", "human_player_chop", "C1TwoHandContact", ["wood"]),
    "pickaxe": ("mine", "human_player_mine", "C1TwoHandContact", ["stone", "metal"]),
    "salvage_pry_tool": ("dismantle", "human_player_dismantle", "C1RightHandContact", ["fuel"]),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    errors: list[str] = []
    catalog_path = ASSETS / "catalog.json"
    if not catalog_path.exists() or not SCRIPT.exists():
        errors.append("T09 catalog or presentation script missing")
        catalog = {"entries": []}
    else:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    if catalog.get("authority_id") != "T09-harvesting-tools-v1":
        errors.append("unexpected T09 tool authority")
    entries = {row.get("id"): row for row in catalog.get("entries", [])}
    if set(entries) != set(EXPECTED):
        errors.append("catalog must contain exactly axe, pickaxe and salvage_pry_tool")
    asset_rows = []
    for tool_id, expected in EXPECTED.items():
        row = entries.get(tool_id, {})
        actual = (row.get("action"), row.get("animation_profile"), row.get("contact_marker"), row.get("resources"))
        if actual != expected:
            errors.append(f"frozen tool mapping mismatch: {tool_id}")
        path = ROOT / str(row.get("asset", "")).replace("res://", "HavenlineGodot/")
        if not path.is_file():
            errors.append(f"authored asset missing: {tool_id}")
            continue
        raw = path.read_bytes()
        if len(raw) < 12:
            errors.append(f"invalid GLB: {tool_id}")
            continue
        magic, version, total = struct.unpack("<4sII", raw[:12])
        digest = sha256(path)
        if magic != b"glTF" or version != 2 or total != len(raw):
            errors.append(f"invalid GLB header: {tool_id}")
        if row.get("sha256") != digest:
            errors.append(f"catalog hash mismatch: {tool_id}")
        if not 300 <= int(row.get("triangles", 0)) <= 2500:
            errors.append(f"triangle budget mismatch: {tool_id}")
        if len(row.get("materials", [])) < 5 or len(row.get("materials", [])) > 6:
            errors.append(f"palette role budget mismatch: {tool_id}")
        json_length, json_type = struct.unpack("<I4s", raw[12:20])
        document = json.loads(raw[20:20 + json_length]) if json_type == b"JSON" else {}
        primitives = [primitive for mesh in document.get("meshes", []) for primitive in mesh.get("primitives", [])]
        if row.get("render_materials") != 1 or row.get("vertex_color_palette") is not True or len(document.get("materials", [])) != 1 or len(primitives) != 1 or "COLOR_0" not in primitives[0].get("attributes", {}):
            errors.append(f"single-draw vertex palette mismatch: {tool_id}")
        if len(row.get("grip_socket", [])) != 3 or len(row.get("impact_socket", [])) != 3:
            errors.append(f"socket metadata missing: {tool_id}")
        asset_rows.append({"id": tool_id, "sha256": digest, "bytes": len(raw), "triangles": row.get("triangles"), "render_materials": row.get("render_materials")})

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))["resources"]
    expected_resource_tools = {"wood": "axe", "stone": "pickaxe", "metal": "pickaxe", "fuel": "salvage_pry_tool"}
    for resource, tool in expected_resource_tools.items():
        if registry.get(resource, {}).get("tool_profile") != tool or registry.get(resource, {}).get("production_ready") is not True:
            errors.append(f"resource registry drift: {resource}")

    reference_rows = []
    if not REFERENCE_SELECTION.exists():
        errors.append("T09 locked-reference selection manifest missing")
    else:
        selection = json.loads(REFERENCE_SELECTION.read_text(encoding="utf-8"))
        if selection.get("source_manifest_sha256") != "e271986bcbf319b7dd3c94bee0813e8cbd7caa4699781096c3f68e701f295d01":
            errors.append("T09 locked-reference source manifest drift")
        if {row.get("source_id") for row in selection.get("selected_pixels", [])} != {"A", "B"}:
            errors.append("T09 reference selection must contain locked A and B pixels")
        for row in selection.get("selected_pixels", []):
            path = ROOT / str(row.get("path", ""))
            if not path.is_file() or sha256(path) != row.get("sha256"):
                errors.append(f"locked reference pixel mismatch: {row.get('path')}")
            else:
                reference_rows.append({"source_id": row.get("source_id"), "path": row.get("path"), "sha256": row.get("sha256")})

    source = SCRIPT.read_text(encoding="utf-8") if SCRIPT.exists() else ""
    for token in ["simulation_authoritative", "emits_gameplay_events", "mutates_inventory", "RECEIPT_WINDOW", "MAX_FRAGMENT_DESCRIPTORS", "MAX_IMPACT_PULSES", "SOCKET_CONTACT_TOLERANCE_METERS", "SECOND_HAND_TOLERANCE_METERS", "MAX_GRIP_SETTLE_METERS", "impact_socket", "grip_socket", "second_hand_socket", "primary_grip_marker", "secondary_grip_marker"]:
        if token not in source:
            errors.append(f"presentation contract token missing: {token}")
    main_source = MAIN.read_text(encoding="utf-8") if MAIN.exists() else ""
    runtime_wiring = all(token in main_source for token in [
        "HarvestPresentation.new()", "harvest_presentation.bind_source(",
        "harvest_presentation.synchronize_committed_contact(",
        "harvest_presentation.accept_committed_impact(",
    ])
    if not runtime_wiring:
        errors.append("shipping T09 runtime wiring is incomplete")
    result = {
        "task": "T09",
        "candidate_commit": args.candidate,
        "passed": not errors,
        "errors": errors,
        "catalog_sha256": sha256(catalog_path) if catalog_path.exists() else None,
        "presentation_sha256": sha256(SCRIPT) if SCRIPT.exists() else None,
        "assets": asset_rows,
        "runtime_wiring_included": runtime_wiring,
        "locked_reference_pixels": reference_rows,
        "reference_selection_sha256": sha256(REFERENCE_SELECTION) if REFERENCE_SELECTION.exists() else None,
        "task_approved": False,
    }
    output = json.dumps(result, indent=2)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    print(output)
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
