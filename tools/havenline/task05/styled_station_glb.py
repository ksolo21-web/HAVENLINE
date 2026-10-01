#!/usr/bin/env python3
"""Deterministic T05 authored vertex-color material finish.

The early-camp user renders use visible wood grain/value breakup, cooler metal,
localized snow shading and non-uniform painted machinery. The previous non-hearth
GLBs carried only uniform baseColorFactor values, which made otherwise-authored
geometry read like clean primitive material fills in actual Godot captures.

This packer keeps:
- the exact 11-name shared material vocabulary and original PBR factors;
- every vertex position, normal, index, triangle count and footprint;
- one material surface per existing builder surface;
- deterministic output with no textures or additional draw calls.

It adds COLOR_0 only. Godot's station batcher already preserves COLOR_0 and forces
vertex_color_use_as_albedo on the duplicated batch material.
"""
from __future__ import annotations

import json
import math
import struct
from pathlib import Path

import legacy_station_kit_v1 as legacy


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def authored_color(material: str, position, normal):
    x, y, z = (float(v) for v in position)
    nx, ny, nz = (float(v) for v in normal)

    # Geometry-bound deterministic breakup: broad construction variation plus
    # finer grain. No random state means exact regeneration on every CI host.
    broad = math.sin(x * 3.71 + z * 4.93 + y * 2.17)
    fine = math.sin(x * 15.7 - z * 12.1 + y * 8.3)
    grain = math.sin((x + z * .37) * 27.0 + y * 4.2)
    upward = _clamp((ny + 1.0) * .5)
    edge = _clamp(1.0 - abs(ny))

    if material == "snow":
        tone = _clamp(.86 + .10 * upward + .035 * broad, .79, 1.0)
        # Cooler vertical/underside snow, brighter top accumulation.
        return (_clamp(tone * .94), _clamp(tone * .98), tone, 1.0)

    if material == "wood":
        tone = _clamp(.76 + .10 * broad + .075 * grain + .025 * fine, .58, .96)
        return (tone, _clamp(tone * .88), _clamp(tone * .72), 1.0)

    if material == "wood_light":
        tone = _clamp(.82 + .085 * broad + .060 * grain + .020 * fine, .66, 1.0)
        return (tone, _clamp(tone * .91), _clamp(tone * .77), 1.0)

    if material == "metal":
        tone = _clamp(.76 + .10 * broad + .075 * edge + .025 * fine, .62, 1.0)
        return (_clamp(tone * .82), _clamp(tone * .91), tone, 1.0)

    if material == "dark":
        tone = _clamp(.72 + .10 * broad + .045 * edge, .58, .91)
        return (_clamp(tone * .82), _clamp(tone * .90), tone, 1.0)

    if material == "blue":
        tone = _clamp(.79 + .09 * broad + .035 * fine + .025 * upward, .66, .98)
        return (_clamp(tone * .82), _clamp(tone * .93), tone, 1.0)

    if material == "cyan":
        tone = _clamp(.82 + .075 * broad + .025 * fine, .70, .99)
        return (_clamp(tone * .84), _clamp(tone * .96), tone, 1.0)

    if material == "orange":
        tone = _clamp(.84 + .08 * broad + .025 * fine, .70, 1.0)
        return (tone, _clamp(tone * .89), _clamp(tone * .72), 1.0)

    if material == "yellow":
        tone = _clamp(.86 + .07 * broad + .020 * fine, .74, 1.0)
        return (tone, _clamp(tone * .94), _clamp(tone * .75), 1.0)

    if material == "green":
        tone = _clamp(.81 + .08 * broad + .030 * fine, .68, .98)
        return (_clamp(tone * .88), tone, _clamp(tone * .79), 1.0)

    if material == "cream":
        tone = _clamp(.88 + .055 * broad + .020 * fine + .015 * upward, .79, 1.0)
        return (tone, _clamp(tone * .97), _clamp(tone * .89), 1.0)

    raise ValueError(f"unknown material {material}")


def pack_styled_glb(builder: legacy.MeshBuilder, path: Path) -> None:
    blob = bytearray()
    views = []
    accessors = []
    primitives = []
    materials = []
    used = list(builder.surfaces)

    for key in used:
        color, metallic, rough = legacy.MATERIALS[key]
        materials.append({
            "name": "HL_" + key,
            "pbrMetallicRoughness": {
                "baseColorFactor": color,
                "metallicFactor": metallic,
                "roughnessFactor": rough,
            },
            "doubleSided": False,
        })

    def add_view(data: bytes, target: int) -> int:
        while len(blob) % 4:
            blob.append(0)
        offset = len(blob)
        blob.extend(data)
        views.append({
            "buffer": 0,
            "byteOffset": offset,
            "byteLength": len(data),
            "target": target,
        })
        return len(views) - 1

    for material_index, key in enumerate(used):
        surface = builder.surfaces[key]
        colors = [
            authored_color(key, position, normal)
            for position, normal in zip(surface.positions, surface.normals)
        ]
        pos_data = b"".join(struct.pack("<3f", *p) for p in surface.positions)
        nor_data = b"".join(struct.pack("<3f", *n) for n in surface.normals)
        col_data = b"".join(struct.pack("<4f", *c) for c in colors)
        idx_data = b"".join(struct.pack("<I", i) for i in surface.indices)

        p_view = add_view(pos_data, 34962)
        n_view = add_view(nor_data, 34962)
        c_view = add_view(col_data, 34962)
        i_view = add_view(idx_data, 34963)

        mins = [min(p[i] for p in surface.positions) for i in range(3)]
        maxs = [max(p[i] for p in surface.positions) for i in range(3)]

        p_acc = len(accessors)
        accessors.append({
            "bufferView": p_view,
            "componentType": 5126,
            "count": len(surface.positions),
            "type": "VEC3",
            "min": mins,
            "max": maxs,
        })
        n_acc = len(accessors)
        accessors.append({
            "bufferView": n_view,
            "componentType": 5126,
            "count": len(surface.normals),
            "type": "VEC3",
        })
        c_acc = len(accessors)
        accessors.append({
            "bufferView": c_view,
            "componentType": 5126,
            "count": len(colors),
            "type": "VEC4",
        })
        i_acc = len(accessors)
        accessors.append({
            "bufferView": i_view,
            "componentType": 5125,
            "count": len(surface.indices),
            "type": "SCALAR",
        })
        primitives.append({
            "attributes": {"POSITION": p_acc, "NORMAL": n_acc, "COLOR_0": c_acc},
            "indices": i_acc,
            "material": material_index,
            "mode": 4,
        })

    doc = {
        "asset": {"version": "2.0", "generator": "HAVENLINE T05 authored material finish v1"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": builder.name, "mesh": 0}],
        "meshes": [{"name": builder.name, "primitives": primitives}],
        "materials": materials,
        "accessors": accessors,
        "bufferViews": views,
        "buffers": [{"byteLength": len(blob)}],
    }

    encoded = json.dumps(doc, separators=(",", ":"), sort_keys=True).encode()
    while len(encoded) % 4:
        encoded += b" "
    while len(blob) % 4:
        blob.append(0)
    total = 12 + 8 + len(encoded) + 8 + len(blob)
    data = (
        struct.pack("<4sII", b"glTF", 2, total)
        + struct.pack("<I4s", len(encoded), b"JSON")
        + encoded
        + struct.pack("<I4s", len(blob), b"BIN\0")
        + blob
    )
    path.write_bytes(data)


def color_span(builder: legacy.MeshBuilder):
    values = []
    for key, surface in builder.surfaces.items():
        values.extend(
            authored_color(key, position, normal)
            for position, normal in zip(surface.positions, surface.normals)
        )
    channels = [v for color in values for v in color[:3]]
    return {
        "vertex_colors": len(values),
        "minimum": min(channels) if channels else 1.0,
        "maximum": max(channels) if channels else 1.0,
        "span": (max(channels) - min(channels)) if channels else 0.0,
    }


if __name__ == "__main__":
    import json as _json
    samples = {
        "wood": authored_color("wood", (.31, .8, -.24), (.3, .7, .2)),
        "metal": authored_color("metal", (.31, .8, -.24), (.3, .7, .2)),
        "snow": authored_color("snow", (.31, .8, -.24), (.3, .7, .2)),
        "blue": authored_color("blue", (.31, .8, -.24), (.3, .7, .2)),
    }
    print(_json.dumps(samples, indent=2))
