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
            errors.append(f"material budget mismatch: {tool_id}")
        if len(row.get("grip_offset", [])) != 3 or len(row.get("impact_socket", [])) != 3:
            errors.append(f"socket metadata missing: {tool_id}")
        asset_rows.append({"id": tool_id, "sha256": digest, "bytes": len(raw), "triangles": row.get("triangles")})

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))["resources"]
    expected_resource_tools = {"wood": "axe", "stone": "pickaxe", "metal": "pickaxe", "fuel": "salvage_pry_tool"}
    for resource, tool in expected_resource_tools.items():
        if registry.get(resource, {}).get("tool_profile") != tool or registry.get(resource, {}).get("production_ready") is not True:
            errors.append(f"resource registry drift: {resource}")

    source = SCRIPT.read_text(encoding="utf-8") if SCRIPT.exists() else ""
    for token in ["simulation_authoritative", "emits_gameplay_events", "mutates_inventory", "RECEIPT_WINDOW", "MAX_FRAGMENT_DESCRIPTORS", "MAX_IMPACT_PULSES"]:
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
