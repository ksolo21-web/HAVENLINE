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
import struct
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


def pack_colored_glb(builder: MeshBuilder, path: Path) -> None:
    """Pack the authored palette into one vertex-colored render surface.

    The old GLBs emitted one primitive per palette role. A held tool therefore
    cost six color and shadow submissions even though the geometry is tiny.
    Vertex colors preserve every authored wood/metal/blue/orange/cyan decision
    while making the complete tool one bounded draw surface.
    """
    positions = []
    normals = []
    colors = []
    indices = []
    for material, surface in builder.surfaces.items():
        base = len(positions)
        color = sculptor.MATERIALS[material][0]
        positions.extend(surface.positions)
        normals.extend(surface.normals)
        colors.extend([color] * len(surface.positions))
        indices.extend(base + index for index in surface.indices)

    blob = bytearray()
    views = []
    accessors = []

    def add_view(data: bytes, target: int) -> int:
        while len(blob) % 4:
            blob.append(0)
        offset = len(blob)
        blob.extend(data)
        views.append({"buffer": 0, "byteOffset": offset, "byteLength": len(data), "target": target})
        return len(views) - 1

    position_view = add_view(b"".join(struct.pack("<3f", *value) for value in positions), 34962)
    normal_view = add_view(b"".join(struct.pack("<3f", *value) for value in normals), 34962)
    color_view = add_view(b"".join(struct.pack("<4f", *value) for value in colors), 34962)
    index_view = add_view(b"".join(struct.pack("<I", value) for value in indices), 34963)
    mins = [min(value[axis] for value in positions) for axis in range(3)]
    maxs = [max(value[axis] for value in positions) for axis in range(3)]
    accessors.extend([
        {"bufferView": position_view, "componentType": 5126, "count": len(positions), "type": "VEC3", "min": mins, "max": maxs},
        {"bufferView": normal_view, "componentType": 5126, "count": len(normals), "type": "VEC3"},
        {"bufferView": color_view, "componentType": 5126, "count": len(colors), "type": "VEC4"},
        {"bufferView": index_view, "componentType": 5125, "count": len(indices), "type": "SCALAR"},
    ])
    document = {
        "asset": {"version": "2.0", "generator": "Havenline T09 deterministic vertex-color sculptor v2"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": builder.name, "mesh": 0}],
        "meshes": [{"name": builder.name, "primitives": [{
            "attributes": {"POSITION": 0, "NORMAL": 1, "COLOR_0": 2},
            "indices": 3,
            "material": 0,
            "mode": 4,
        }]}],
        "materials": [{
            "name": "HL_harvest_vertex_palette",
            "pbrMetallicRoughness": {
                "baseColorFactor": [1.0, 1.0, 1.0, 1.0],
                "metallicFactor": 0.18,
                "roughnessFactor": 0.42,
            },
            "doubleSided": False,
        }],
        "accessors": accessors,
        "bufferViews": views,
        "buffers": [{"byteLength": len(blob)}],
    }
    encoded = json.dumps(document, separators=(",", ":"), sort_keys=True).encode()
    while len(encoded) % 4:
        encoded += b" "
    while len(blob) % 4:
        blob.append(0)
    total = 12 + 8 + len(encoded) + 8 + len(blob)
    path.write_bytes(
        struct.pack("<4sII", b"glTF", 2, total)
        + struct.pack("<I4s", len(encoded), b"JSON")
        + encoded
        + struct.pack("<I4s", len(blob), b"BIN\0")
        + blob
    )


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
    b.cylinder("wood_light", (0.0, -0.08, 0.0), 0.055, 0.70, 14)
    b.cylinder("wood", (0.0, -0.35, 0.0), 0.069, 0.18, 14)
    b.cylinder("orange", (0.0, -0.10, 0.0), 0.071, 0.10, 14)
    b.cylinder("blue", (0.0, -0.26, 0.0), 0.073, 0.10, 14)
    b.cylinder("metal", (0.0, 0.13, 0.0), 0.095, 0.16, 16, rotation=(0.0, 0.0, math.pi / 2.0))
    _wedge(b, "metal", (0.17, 0.13, 0.0), 0.28, 0.25, 0.12)
    b.beveled_box("orange", (-0.10, 0.13, 0.0), (0.10, 0.16, 0.14), 0.025)
    b.beveled_box("cyan", (0.18, 0.13, 0.061), (0.20, 0.035, 0.018), 0.006)
    return b


def build_pickaxe():
    b = MeshBuilder("t09_harvest_pickaxe")
    b.cylinder("wood_light", (0.0, -0.08, 0.0), 0.052, 0.78, 14)
    b.cylinder("wood", (0.0, -0.39, 0.0), 0.068, 0.20, 14)
    b.cylinder("orange", (0.0, -0.08, 0.0), 0.072, 0.10, 14)
    b.cylinder("blue", (0.0, -0.24, 0.0), 0.072, 0.10, 14)
    b.beveled_box("metal", (0.0, 0.14, 0.0), (0.20, 0.15, 0.16), 0.035)
    b.cylinder("metal", (-0.19, 0.14, 0.0), 0.09, 0.28, 16, rotation=(0.0, 0.0, math.pi / 2.0), top_radius=0.018)
    b.cylinder("metal", (0.19, 0.14, 0.0), 0.018, 0.28, 16, rotation=(0.0, 0.0, math.pi / 2.0), top_radius=0.09)
    b.beveled_box("cyan", (0.0, 0.14, -0.085), (0.16, 0.05, 0.025), 0.008)
    return b


def build_salvage_pry_tool():
    b = MeshBuilder("t09_harvest_salvage_pry")
    b.cylinder("metal", (0.0, -0.01, 0.0), 0.045, 0.82, 14)
    b.cylinder("orange", (0.0, -0.20, 0.0), 0.086, 0.36, 16)
    b.cylinder("dark", (0.0, -0.40, 0.0), 0.078, 0.055, 16)
    b.cylinder("blue", (0.0, -0.01, 0.0), 0.074, 0.05, 16)
    b.rod_between("metal", (0.0, 0.38, 0.0), (0.11, 0.46, 0.0), 0.048, 14)
    b.rod_between("metal", (0.11, 0.46, 0.0), (0.22, 0.43, 0.0), 0.048, 14)
    _wedge(b, "metal", (0.25, 0.43, 0.0), 0.13, 0.14, 0.095)
    b.beveled_box("cyan", (0.12, 0.46, 0.052), (0.13, 0.035, 0.018), 0.006)
    return b


TOOLS = {
    "axe": {
        "builder": build_axe,
        "resources": ["wood"],
        "action": "chop",
        "animation_profile": "human_player_chop",
        "contact_marker": "C1TwoHandContact",
        "grip_socket": [0.0, -0.10, 0.0],
        "second_hand_socket": [0.0, -0.26, 0.0],
        "impact_socket": [0.29, 0.13, 0.0],
    },
    "pickaxe": {
        "builder": build_pickaxe,
        "resources": ["stone", "metal"],
        "action": "mine",
        "animation_profile": "human_player_mine",
        "contact_marker": "C1TwoHandContact",
        "grip_socket": [0.0, -0.08, 0.0],
        "second_hand_socket": [0.0, -0.24, 0.0],
        "impact_socket": [0.28, 0.14, 0.0],
    },
    "salvage_pry_tool": {
        "builder": build_salvage_pry_tool,
        "resources": ["fuel"],
        "action": "dismantle",
        "animation_profile": "human_player_dismantle",
        "contact_marker": "C1RightHandContact",
        "grip_socket": [0.0, -0.20, 0.0],
        "second_hand_socket": [],
        "impact_socket": [0.28, 0.43, 0.0],
    },
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    entries = []
    for tool_id in sorted(TOOLS):
        row = TOOLS[tool_id]
        builder = row["builder"]()
        path = OUT / f"{tool_id}.glb"
        pack_colored_glb(builder, path)
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
            "render_materials": 1,
            "vertex_color_palette": True,
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
            "palette_roles_max_per_tool": 6,
            "render_materials_max_per_tool": 1,
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
