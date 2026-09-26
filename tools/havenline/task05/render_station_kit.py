#!/usr/bin/env python3
"""Deterministic CPU quick-look renderer for T05 authored GLBs.

This is an early visual inspection tool, not acceptance evidence. The release
workflow still renders the same assets through Godot/Vulkan in the real scene.
"""

from __future__ import annotations

import argparse
import json
import math
import struct
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
ASSET_DIR = ROOT / "HavenlineGodot/assets/stations_v2"
CATALOG_PATH = ASSET_DIR / "catalog.json"
SCALE = 2
WIDTH, HEIGHT = 1280 * SCALE, 720 * SCALE


@dataclass(frozen=True)
class Camera:
    position: np.ndarray
    target: np.ndarray
    full_height: float


def read_glb(path: Path):
    raw = path.read_bytes()
    magic, version, _length = struct.unpack_from("<4sII", raw, 0)
    assert magic == b"glTF" and version == 2
    json_length, json_type = struct.unpack_from("<I4s", raw, 12)
    assert json_type == b"JSON"
    document = json.loads(raw[20 : 20 + json_length])
    offset = 20 + json_length
    bin_length, bin_type = struct.unpack_from("<I4s", raw, offset)
    assert bin_type == b"BIN\0"
    blob = raw[offset + 8 : offset + 8 + bin_length]

    colors = []
    for material in document["materials"]:
        factor = material["pbrMetallicRoughness"]["baseColorFactor"]
        colors.append(np.array(factor[:3], dtype=np.float64))

    def accessor(index: int):
        row = document["accessors"][index]
        view = document["bufferViews"][row["bufferView"]]
        start = int(view.get("byteOffset", 0)) + int(row.get("byteOffset", 0))
        component = int(row["componentType"])
        shape = {"SCALAR": 1, "VEC3": 3}[row["type"]]
        dtype = {5125: "<u4", 5126: "<f4"}[component]
        return np.frombuffer(blob, dtype=dtype, count=int(row["count"]) * shape, offset=start).reshape((-1, shape))

    triangles = []
    for primitive in document["meshes"][0]["primitives"]:
        positions = accessor(primitive["attributes"]["POSITION"])
        indices = accessor(primitive["indices"]).reshape(-1)
        faces = positions[indices].reshape((-1, 3, 3)).astype(np.float64)
        color = colors[int(primitive["material"])]
        triangles.extend((face, color) for face in faces)
    return triangles


def y_rotation(angle: float):
    c, s = math.cos(angle), math.sin(angle)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])


def transform_triangles(triangles, position, rotation_y):
    matrix = y_rotation(rotation_y)
    translation = np.array(position, dtype=np.float64)
    return [(vertices @ matrix.T + translation, color) for vertices, color in triangles]


def camera_basis(camera: Camera):
    forward = camera.target - camera.position
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, np.array([0.0, 1.0, 0.0]))
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    return right, up, forward


def project(points, camera: Camera):
    right, up, forward = camera_basis(camera)
    relative = points - camera.position
    x = relative @ right
    y = relative @ up
    depth = relative @ forward
    pixels_per_unit = HEIGHT / camera.full_height
    screen = np.column_stack((WIDTH * 0.5 + x * pixels_per_unit, HEIGHT * 0.53 - y * pixels_per_unit))
    return screen, depth


def stage_geometry(kind: str):
    def quad(x0, z0, x1, z1, y, color):
        a = np.array([x0, y, z0]); b = np.array([x1, y, z0])
        c = np.array([x1, y, z1]); d = np.array([x0, y, z1])
        return [(np.array([a, d, c]), color), (np.array([a, c, b]), color)]

    result = quad(-20, -20, 20, 20, -0.10, np.array([0.78, 0.88, 0.92]))
    if kind == "camp":
        result += quad(-11.8, -2.9, 11.8, 8.5, -0.03, np.array([0.57, 0.31, 0.20]))
    elif kind == "lakeshore":
        result += quad(-17, -11.3, 17, -3.1, -0.07, np.array([0.05, 0.44, 0.65]))
        result += quad(-14.5, -12.7, 14.5, -10.9, 0.02, np.array([0.52, 0.72, 0.80]))
    return result


def view_camera(view: str, full_height: float, target=(0.0, 0.7, 0.0)):
    offsets = {
        "front": np.array([10.2, 11.8, 14.2]),
        "reverse": np.array([-10.2, 10.7, -14.2]),
        "side": np.array([14.2, 9.8, 5.0]),
    }
    target = np.array(target, dtype=np.float64)
    return Camera(target + offsets[view], target, full_height)


def condition_palette(condition: str):
    return {
        "day": ((105, 151, 180), np.array([0.93, 0.84, 0.70]), 0.42),
        "night": ((22, 38, 63), np.array([0.48, 0.58, 0.82]), 0.28),
        "blizzard": ((139, 169, 185), np.array([0.86, 0.91, 0.94]), 0.52),
    }[condition]


def draw_shadow(draw: ImageDraw.ImageDraw, camera: Camera, position, footprint):
    x, _, z = position
    hx, hz = footprint[0] * 0.47, footprint[1] * 0.47
    corners = np.array([[x-hx, -0.015, z-hz], [x+hx, -0.015, z-hz], [x+hx, -0.015, z+hz], [x-hx, -0.015, z+hz]])
    screen, _ = project(corners, camera)
    draw.polygon([tuple(p) for p in screen], fill=(18, 39, 55, 54))


def scale_marker(draw: ImageDraw.ImageDraw, camera: Camera):
    x0 = x1 = 1192 * SCALE
    y0 = 646 * SCALE
    y1 = y0 - 1.75 * HEIGHT / camera.full_height
    width = 6 * SCALE
    draw.line([(x0, y0), (x1, y1)], fill=(17, 35, 54, 235), width=width)
    draw.line([(x0-10*SCALE, y0), (x0+10*SCALE, y0)], fill=(17, 35, 54, 235), width=3*SCALE)
    draw.line([(x1-10*SCALE, y1), (x1+10*SCALE, y1)], fill=(17, 35, 54, 235), width=3*SCALE)
    draw.text((x1+14*SCALE, y1-12*SCALE), "1.75 m", fill=(17, 35, 54, 255), font=ImageFont.load_default(size=16*SCALE))


def render_frame(output: Path, frame_id: str, kind: str, condition: str, view: str, placements, cache, camera: Camera, catalog_rows):
    background, light_color, ambient = condition_palette(condition)
    image = Image.new("RGB", (WIDTH, HEIGHT), background)
    draw = ImageDraw.Draw(image, "RGBA")

    stage_triangles = stage_geometry(kind)
    asset_triangles = []
    for asset_id, position, rotation in placements:
        asset_triangles.extend(transform_triangles(cache[asset_id], position, rotation))

    camera_direction = camera.position - camera.target
    camera_direction /= np.linalg.norm(camera_direction)
    light = np.array([-0.35, 0.84, 0.42])
    light /= np.linalg.norm(light)
    # Review stages are large intersecting planes. Render them as a background
    # layer so centroid sorting cannot incorrectly paint a floor over a prop.
    for triangle_group in (stage_triangles, asset_triangles):
        staged = []
        for vertices, base_color in triangle_group:
            edge_a, edge_b = vertices[1] - vertices[0], vertices[2] - vertices[0]
            normal = np.cross(edge_a, edge_b)
            length = np.linalg.norm(normal)
            if length < 1e-8:
                continue
            normal /= length
            centroid = vertices.mean(axis=0)
            if np.dot(normal, camera.position - centroid) <= 0.0:
                continue
            screen, depth = project(vertices, camera)
            if np.max(screen[:, 0]) < 0 or np.min(screen[:, 0]) >= WIDTH or np.max(screen[:, 1]) < 0 or np.min(screen[:, 1]) >= HEIGHT:
                continue
            diffuse = max(0.0, float(np.dot(normal, light)))
            toon = 0.18 if diffuse < 0.18 else (0.48 if diffuse < 0.55 else 0.84)
            shade = min(1.16, ambient + toon)
            color = np.clip(base_color * light_color * shade * 255.0, 0, 255).astype(np.uint8)
            staged.append((float(depth.mean()), screen, tuple(int(v) for v in color)))
        staged.sort(key=lambda row: row[0], reverse=True)
        for _depth, screen, color in staged:
            draw.polygon([tuple(p) for p in screen], fill=color + (255,))

    # A declared scale marker is intentionally an overlay, never scene content.
    scale_marker(draw, camera)
    badge_font = ImageFont.load_default(size=17*SCALE)
    title_font = ImageFont.load_default(size=25*SCALE)
    draw.rounded_rectangle((22*SCALE, 18*SCALE, 436*SCALE, 74*SCALE), radius=10*SCALE, fill=(9, 24, 38, 210))
    draw.text((38*SCALE, 28*SCALE), frame_id.replace("-", " ").upper(), fill=(245, 250, 252, 255), font=title_font)
    draw.rounded_rectangle((22*SCALE, 654*SCALE, 560*SCALE, 700*SCALE), radius=8*SCALE, fill=(9, 24, 38, 190))
    draw.text((36*SCALE, 666*SCALE), "ISOLATED GLB QUICK LOOK | NOT GAMEPLAY EVIDENCE", fill=(221, 237, 244, 255), font=badge_font)
    if condition == "blizzard":
        rng = np.random.default_rng(754219)
        for x, y, length in rng.integers([0, 0, 8], [WIDTH, HEIGHT, 38*SCALE], size=(360, 3)):
            draw.line((int(x), int(y), int(x-length), int(y+length//2)), fill=(244, 250, 252, 92), width=2*SCALE)
    image.resize((1280, 720), Image.Resampling.LANCZOS).save(output / f"{frame_id}.png")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    catalog = json.loads(CATALOG_PATH.read_text())
    rows = {row["id"]: row for row in catalog["entries"]}
    cache = {asset_id: read_glb(ASSET_DIR / f"{asset_id}.glb") for asset_id in rows}

    arrangements = {}
    for name, placements in catalog["arrangements"].items():
        arrangements[name] = [(row["id"], row["position"], row["rotation_y"]) for row in placements]
    singles = lambda asset: [(asset, [0.0, 0.0, 0.0], 0.0)]
    pads = [
        ("pad_build", [-3.6, 0.0, -1.2], 0.0), ("pad_upgrade", [-1.2, 0.0, -1.2], 0.0),
        ("pad_input", [1.2, 0.0, -1.2], 0.0), ("pad_output", [3.6, 0.0, -1.2], 0.0),
        ("pad_stock", [-1.2, 0.0, 1.3], 0.0), ("pad_payment", [1.2, 0.0, 1.3], 0.0),
    ]
    frames = [
        ("camp-day-front", "camp", "day", "front", arrangements["camp"], 14.3),
        ("camp-day-reverse", "camp", "day", "reverse", arrangements["camp"], 14.3),
        ("camp-night-front", "camp", "night", "front", arrangements["camp"], 14.3),
        ("camp-blizzard-side", "camp", "blizzard", "side", arrangements["camp"], 14.3),
        ("lakeshore-day-front", "lakeshore", "day", "front", arrangements["lakeshore"], 15.3),
        ("lakeshore-day-reverse", "lakeshore", "day", "reverse", arrangements["lakeshore"], 15.3),
        ("lakeshore-night-front", "lakeshore", "night", "front", arrangements["lakeshore"], 15.3),
        ("close-hearth-front", "camp", "day", "front", singles("hearth_vessel"), 4.4),
        ("close-counter-reverse", "camp", "day", "reverse", singles("service_counter"), 4.2),
        ("close-fishing-side", "lakeshore", "day", "side", singles("fishing_rack"), 4.4),
        ("close-processing-front", "lakeshore", "day", "front", singles("cooker_processor"), 4.4),
        ("close-defense-reverse", "camp", "day", "reverse", singles("defense_platform"), 4.8),
        ("close-pads-front", "camp", "day", "front", pads, 7.2),
        ("close-pads-reverse", "camp", "day", "reverse", pads, 7.2),
    ]
    report = {"task": "T05-station-kit-v1", "capture_kind": "deterministic-cpu-quick-look", "acceptance_evidence": False, "frames": []}
    for frame_id, kind, condition, view, placements, height in frames:
        if kind == "camp" and not frame_id.startswith("close-"):
            camera_target = (0.0, 0.7, 2.8)
        elif kind == "lakeshore" and not frame_id.startswith("close-"):
            camera_target = (3.0, 0.7, -14.0)
        else:
            camera_target = (0.0, 0.7, 0.0)
        camera = view_camera(view, height, camera_target)
        render_frame(args.out, frame_id, kind, condition, view, placements, cache, camera, rows)
        report["frames"].append({"id": frame_id, "arrangement": kind, "condition": condition, "view": view, "path": frame_id + ".png"})
    (args.out / "quick-look.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"frames": len(frames), "assets": len(rows), "output": str(args.out)}, indent=2))


if __name__ == "__main__":
    main()
