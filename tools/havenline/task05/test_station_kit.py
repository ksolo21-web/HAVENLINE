#!/usr/bin/env python3
"""Source-level determinism and integrity checks for the T05 GLB kit."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
ASSET_DIR = ROOT / "HavenlineGodot/assets/stations_v2"
CATALOG = ASSET_DIR / "catalog.json"
GENERATOR = ROOT / "tools/havenline/task05/generate_station_kit.py"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def glb_document(path: Path):
    raw = path.read_bytes()
    magic, version, length = struct.unpack_from("<4sII", raw, 0)
    assert magic == b"glTF" and version == 2 and length == len(raw), path
    json_length, json_type = struct.unpack_from("<I4s", raw, 12)
    assert json_type == b"JSON", path
    document = json.loads(raw[20 : 20 + json_length])
    binary_offset = 20 + json_length
    binary_length, binary_type = struct.unpack_from("<I4s", raw, binary_offset)
    assert binary_type == b"BIN\0", path
    blob = raw[binary_offset + 8 : binary_offset + 8 + binary_length]
    return document, blob


def accessor(document, blob, index):
    row = document["accessors"][index]
    view = document["bufferViews"][row["bufferView"]]
    offset = int(view.get("byteOffset", 0)) + int(row.get("byteOffset", 0))
    components = {"SCALAR": 1, "VEC3": 3}[row["type"]]
    dtype = {5125: "<u4", 5126: "<f4"}[int(row["componentType"])]
    return np.frombuffer(blob, dtype=dtype, count=int(row["count"]) * components, offset=offset).reshape((-1, components))


def winding_failures(path: Path) -> int:
    document, blob = glb_document(path)
    failures = 0
    for primitive in document["meshes"][0]["primitives"]:
        positions = accessor(document, blob, primitive["attributes"]["POSITION"])
        normals = accessor(document, blob, primitive["attributes"]["NORMAL"])
        indices = accessor(document, blob, primitive["indices"]).reshape(-1)
        for ia, ib, ic in indices.reshape((-1, 3)):
            geometric = np.cross(positions[ib] - positions[ia], positions[ic] - positions[ia])
            authored = normals[ia] + normals[ib] + normals[ic]
            if float(np.dot(geometric, authored)) < -1e-8:
                failures += 1
    return failures


def snapshot():
    return {path.name: digest(path) for path in sorted(ASSET_DIR.glob("*.glb"))} | {"catalog.json": digest(CATALOG)}


def main() -> int:
    subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, check=True, capture_output=True, text=True)
    first = snapshot()
    subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, check=True, capture_output=True, text=True)
    second = snapshot()
    assert first == second, "generator output is not byte deterministic"

    catalog = json.loads(CATALOG.read_text())
    assert catalog["authority_id"] == "T05-station-kit-v1"
    assert catalog["runtime_logic_included"] is False
    assert catalog["visual_approval_claimed"] is False
    assert catalog["physical_4k60_certified"] is False
    assert catalog["requirements"] == [f"T05-R{i:02d}" for i in range(1, 13)]
    entries = catalog["entries"]
    assert len(entries) == 22
    assert len({row["id"] for row in entries}) == 22
    assert sum(int(row["triangles"]) for row in entries) == 24928
    assert sum((ASSET_DIR / f"{row['id']}.glb").stat().st_size for row in entries) == 826604
    assert sum((ASSET_DIR / f"{row['id']}.glb").stat().st_size for row in entries) <= 15 * 1024 * 1024
    palette = {material for row in entries for material in row["materials"]}
    assert palette == {"snow", "cream", "wood", "wood_light", "metal", "blue", "cyan", "orange", "yellow", "green", "red", "dark"}
    assert catalog["performance_contract"] == {
        "triangles_max": 180000, "draw_calls_max": 48, "visible_materials_max": 12,
        "texture_memory_mib_max": 96, "storage_delta_mib_max": 15,
        "active_physics": 0, "skeletons": 0, "animations": 0, "population": 0,
    }

    by_id = {row["id"]: row for row in entries}
    pad_variants = [by_id[f"pad_{kind}"]["visual_variant"] for kind in ("build", "upgrade", "input", "output", "stock", "payment")]
    assert len({row["silhouette"] for row in pad_variants}) == 6
    assert len({row["icon"] for row in pad_variants}) == 6
    assert [row["trim"] for row in pad_variants] == ["yellow", "orange", "cyan", "blue", "cream", "green"]
    for row in entries:
        path = ASSET_DIR / f"{row['id']}.glb"
        assert path.exists() and row["asset"] == f"res://assets/stations_v2/{path.name}"
        assert row["sha256"] == digest(path)
        document, _blob = glb_document(path)
        material_names = {material["name"].removeprefix("HL_") for material in document["materials"]}
        assert material_names == set(row["materials"]), row["id"]
        assert all(name.startswith("HL_") for name in [material["name"] for material in document["materials"]])
        assert winding_failures(path) == 0, row["id"]
        assert row["sockets"] and all(len(value) == 3 for value in row["sockets"].values())
        assert all(float(value) > 0 for value in row["footprint"])

    arrangements = catalog["arrangements"]
    assert {name: len(rows) for name, rows in arrangements.items()} == {"camp": 11, "lakeshore": 10}
    expected_triangles = {"camp": 12876, "lakeshore": 9456}
    expected_surfaces = {"camp": 12, "lakeshore": 10}
    for name, placements in arrangements.items():
        assert len({row["id"] for row in placements}) == len(placements)
        assert sum(by_id[row["id"]]["triangles"] for row in placements) == expected_triangles[name]
        assert len({material for row in placements for material in by_id[row["id"]]["materials"]}) == expected_surfaces[name]
        assert expected_surfaces[name] <= catalog["performance_contract"]["draw_calls_max"]

    report = {
        "suite": "T05_station_kit_source_integrity",
        "passed": True,
        "asset_count": len(entries),
        "triangles": sum(row["triangles"] for row in entries),
        "storage_bytes": sum((ASSET_DIR / f"{row['id']}.glb").stat().st_size for row in entries),
        "deterministic_files": len(first),
        "opposite_winding_triangles": 0,
        "nominal_batched_draw_calls": expected_surfaces,
        "independent_critic": False,
        "physical_4k60_verified": False,
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
