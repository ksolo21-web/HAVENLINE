#!/usr/bin/env python3
"""Generate deterministic authored T09 harvesting tools.

The mesh vocabulary is shared with the approved T05 deterministic sculptor,
but every tool, socket and catalog entry is owned by T09. No downloaded mesh,
engine primitive fallback or runtime geometry mutation is used.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCULPTOR_PATH = ROOT / "tools" / "havenline" / "task05" / "generate_station_kit.py"
OUT = ROOT / "HavenlineGodot" / "assets" / "harvesting_v1"

spec = importlib.util.spec_from_file_location("havenline_t05_sculptor", SCULPTOR_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("approved T05 deterministic sculptor is unavailable")
sculptor = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = sculptor
spec.loader.exec_module(sculptor)
MeshBuilder = sculptor.MeshBuilder


def _face(builder, material, points):
    a, b, c = points[:3]
    ab = sculptor.vsub(b, a)
    ac = sculptor.vsub(c, a)
    normal = sculptor.vnorm(sculptor.vcross(ab, ac))
    indices = [0, 1, 2] if len(points) == 3 else [0, 1, 2, 0, 2, 3]
    builder.triangles(material, points, [normal] * len(points), indices)


def _wedge(builder, material, center, width, height, depth, reverse=False):
    cx, cy, cz = center
    half_depth = depth * 0.5
    direction = -1.0 if reverse else 1.0
    x0 = cx - width * 0.5 * direction
    x1 = cx + width * 0.5 * direction
    y0, y1 = cy - height * 0.5, cy + height * 0.5
    front = [(x0, y0, cz - half_depth), (x0, y1, cz - half_depth), (x1, cy, cz - half_depth)]
    back = [(x1, cy, cz + half_depth), (x0, y1, cz + half_depth), (x0, y0, cz + half_depth)]
    for face in [front, back]:
        _face(builder, material, face)
    _face(builder, material, [front[0], back[2], back[1], front[1]])
    _face(builder, material, [front[1], back[1], back[0], front[2]])
    _face(builder, material, [front[2], back[0], back[2], front[0]])


def build_axe():
    b = MeshBuilder("t09_harvest_axe")
    b.cylinder("wood_light", (0.0, 0.02, 0.0), 0.055, 1.18, 14)
    b.cylinder("wood", (0.0, -0.43, 0.0), 0.069, 0.30, 14)
    b.cylinder("blue", (0.0, -0.29, 0.0), 0.073, 0.045, 14)
    b.cylinder("metal", (0.0, 0.56, 0.0), 0.115, 0.22, 16, rotation=(0.0, 0.0, math.pi / 2.0))
    _wedge(b, "metal", (0.25, 0.56, 0.0), 0.50, 0.38, 0.12)
    b.beveled_box("orange", (-0.14, 0.56, 0.0), (0.13, 0.22, 0.14), 0.025)
    b.beveled_box("cyan", (0.24, 0.56, 0.061), (0.31, 0.035, 0.018), 0.006)
    return b


def build_pickaxe():
    b = MeshBuilder("t09_harvest_pickaxe")
    b.cylinder("wood_light", (0.0, -0.02, 0.0), 0.052, 1.24, 14)
    b.cylinder("wood", (0.0, -0.47, 0.0), 0.068, 0.27, 14)
    b.cylinder("orange", (0.0, -0.33, 0.0), 0.072, 0.045, 14)
    b.beveled_box("metal", (0.0, 0.59, 0.0), (0.34, 0.18, 0.16), 0.035)
    b.cylinder("metal", (-0.31, 0.59, 0.0), 0.115, 0.52, 16, rotation=(0.0, 0.0, math.pi / 2.0), top_radius=0.018)
    b.cylinder("metal", (0.31, 0.59, 0.0), 0.018, 0.52, 16, rotation=(0.0, 0.0, math.pi / 2.0), top_radius=0.115)
    b.beveled_box("blue", (0.0, 0.59, 0.085), (0.23, 0.07, 0.025), 0.008)
    b.beveled_box("cyan", (0.0, 0.59, -0.085), (0.23, 0.07, 0.025), 0.008)
    return b


def build_salvage_pry_tool():
    b = MeshBuilder("t09_harvest_salvage_pry")
    b.cylinder("metal", (0.0, 0.05, 0.0), 0.045, 1.02, 14)
    b.cylinder("orange", (0.0, -0.31, 0.0), 0.072, 0.34, 16)
    b.cylinder("dark", (0.0, -0.49, 0.0), 0.078, 0.055, 16)
    b.cylinder("blue", (0.0, -0.13, 0.0), 0.074, 0.05, 16)
    b.rod_between("metal", (0.0, 0.55, 0.0), (0.16, 0.69, 0.0), 0.048, 14)
    b.rod_between("metal", (0.16, 0.69, 0.0), (0.28, 0.63, 0.0), 0.048, 14)
    _wedge(b, "metal", (0.33, 0.61, 0.0), 0.20, 0.18, 0.095)
    b.beveled_box("cyan", (0.17, 0.69, 0.052), (0.16, 0.035, 0.018), 0.006)
    return b


TOOLS = {
    "axe": {
        "builder": build_axe,
        "resources": ["wood"],
        "action": "chop",
        "animation_profile": "human_player_chop",
        "contact_marker": "C1TwoHandContact",
        "grip_socket": [0.0, -0.30, 0.0],
        "second_hand_socket": [0.0, -0.20, 0.0],
        "impact_socket": [0.46, 0.56, 0.0],
    },
    "pickaxe": {
        "builder": build_pickaxe,
        "resources": ["stone", "metal"],
        "action": "mine",
        "animation_profile": "human_player_mine",
        "contact_marker": "C1TwoHandContact",
        "grip_socket": [0.0, -0.14, 0.0],
        "second_hand_socket": [0.0, -0.32, 0.0],
        "impact_socket": [0.57, 0.59, 0.0],
    },
    "salvage_pry_tool": {
        "builder": build_salvage_pry_tool,
        "resources": ["fuel"],
        "action": "dismantle",
        "animation_profile": "human_player_dismantle",
        "contact_marker": "C1RightHandContact",
        "grip_socket": [0.0, -0.10, 0.0],
        "second_hand_socket": [],
        "impact_socket": [0.42, 0.61, 0.0],
    },
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    entries = []
    for tool_id in sorted(TOOLS):
        row = TOOLS[tool_id]
        builder = row["builder"]()
        path = OUT / f"{tool_id}.glb"
        sculptor.pack_glb(builder, path)
        entries.append({
            "id": tool_id,
            "asset": f"res://assets/harvesting_v1/{path.name}",
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "resources": row["resources"],
            "action": row["action"],
            "animation_profile": row["animation_profile"],
            "contact_marker": row["contact_marker"],
            "grip_socket": row["grip_socket"],
            "second_hand_socket": row["second_hand_socket"],
            "impact_socket": row["impact_socket"],
            "triangles": builder.triangle_count(),
            "materials": sorted(builder.surfaces),
        })
    catalog = {
        "schema_version": 1,
        "authority_id": "T09-harvesting-tools-v1",
        "generator": "tools/havenline/task09/generate_harvesting_tools.py",
        "art_language": "bright sculpted winter work tools with warm wood, dark metal, blue structure, orange grips and cyan contact accents",
        "entries": entries,
        "runtime_logic_included": False,
        "simulation_authoritative": True,
        "mutates_inventory": False,
        "performance_contract": {
            "tool_instances_per_presented_actor": 1,
            "triangles_max_per_tool": 2500,
            "materials_max_per_tool": 6,
            "active_physics": 0,
            "skeletons": 0,
        },
    }
    catalog_path = OUT / "catalog.json"
    catalog_path.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "assets": len(entries),
        "triangles": {row["id"]: row["triangles"] for row in entries},
        "catalog": str(catalog_path.relative_to(ROOT)),
    }, indent=2))


if __name__ == "__main__":
    main()
