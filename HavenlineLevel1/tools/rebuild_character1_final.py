#!/usr/bin/env python3
"""Rebuild Character 1 gloves, boots, and rear parka as whole closed meshes.

Panel patches are not used. Each glove is one boolean solid (palm hull, thumb,
four fingers, cuff). Each boot is one hull plus its shearling cuff. The hood
and parka back are one closed shell. Skin weights use the existing joints.
Chop, mine, and carry clips are added on that same skeleton.
"""

from __future__ import annotations

import json
import struct
from collections import Counter
from pathlib import Path

import numpy as np
from manifold3d import Manifold
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "HavenlineLevel1" / "assets" / "characters" / "Character1.glb"
DST = SRC
SOCKETS = ROOT / "HavenlineLevel1" / "assets" / "characters" / "character1_sockets.json"

LEATHER = (91 / 255, 58 / 255, 38 / 255, 1.0)
CREAM = (232 / 255, 208 / 255, 192 / 255, 1.0)
BOOT = (84 / 255, 52 / 255, 34 / 255, 1.0)
SOLE = (46 / 255, 30 / 255, 20 / 255, 1.0)
NAVY = (45 / 255, 54 / 255, 74 / 255, 1.0)
ORANGE = (217 / 255, 111 / 255, 31 / 255, 1.0)


def normalize(v):
    n = float(np.linalg.norm(v))
    if n < 1e-10:
        return np.zeros(3)
    return np.asarray(v, np.float64) / n


def quat_to_mat(q):
    x, y, z, w = [float(v) for v in q]
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ],
        np.float64,
    )


def mat_to_quat(m):
    t = float(m[0, 0] + m[1, 1] + m[2, 2])
    if t > 0:
        s = np.sqrt(t + 1.0) * 2
        w = 0.25 * s
        x = (m[2, 1] - m[1, 2]) / s
        y = (m[0, 2] - m[2, 0]) / s
        z = (m[1, 0] - m[0, 1]) / s
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = np.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        w = (m[2, 1] - m[1, 2]) / s
        x = 0.25 * s
        y = (m[0, 1] + m[1, 0]) / s
        z = (m[0, 2] + m[2, 0]) / s
    elif m[1, 1] > m[2, 2]:
        s = np.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        w = (m[0, 2] - m[2, 0]) / s
        x = (m[0, 1] + m[1, 0]) / s
        y = 0.25 * s
        z = (m[1, 2] + m[2, 1]) / s
    else:
        s = np.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
        w = (m[1, 0] - m[0, 1]) / s
        x = (m[0, 2] + m[2, 0]) / s
        y = (m[1, 2] + m[2, 1]) / s
        z = 0.25 * s
    q = np.array([x, y, z, w], np.float64)
    n = np.linalg.norm(q)
    return q / n if n else np.array([0, 0, 0, 1], np.float64)


def rodrigues(axis, ang):
    x, y, z = normalize(axis)
    k = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]], np.float64)
    return np.eye(3) + np.sin(ang) * k + (1 - np.cos(ang)) * (k @ k)


def rot_between(a, b):
    a = normalize(a)
    b = normalize(b)
    c = float(np.clip(np.dot(a, b), -1, 1))
    if c > 0.999999:
        return np.eye(3)
    if c < -0.999999:
        axis = np.cross(a, np.array([1.0, 0, 0]))
        if np.linalg.norm(axis) < 1e-4:
            axis = np.cross(a, np.array([0.0, 1, 0]))
        return rodrigues(axis, np.pi)
    axis = np.cross(a, b)
    return rodrigues(axis, np.arctan2(np.linalg.norm(axis), c))


def frame(zdir, up=None):
    z = normalize(zdir)
    if up is None:
        up = np.array([0.0, 1.0, 0.0])
    x = np.cross(up, z)
    if np.linalg.norm(x) < 1e-6:
        x = np.cross(np.array([1.0, 0, 0]), z)
    x = normalize(x)
    y = np.cross(z, x)
    return np.stack([x, y, z], axis=1)


def transform_manifold(mesh, rotation, translation):
    affine = np.concatenate([rotation, np.asarray(translation, np.float64).reshape(3, 1)], axis=1)
    return mesh.transform(np.ascontiguousarray(affine))


def capsule(a, b, radius, segments=12):
    a = np.asarray(a, np.float64)
    b = np.asarray(b, np.float64)
    direction = b - a
    length = float(np.linalg.norm(direction))
    ball = max(8, segments // 2)
    if length < 1e-6:
        return Manifold.sphere(radius, ball).translate(a.tolist())
    tube = Manifold.cylinder(length, radius, radius, segments)
    tube = transform_manifold(tube, frame(direction), a)
    return tube + Manifold.sphere(radius, ball).translate(a.tolist()) + Manifold.sphere(radius, ball).translate(b.tolist())


def mesh_from_manifold(mesh):
    raw = mesh.to_mesh()
    verts = np.array(raw.vert_properties, np.float64)[:, :3]
    tris = np.array(raw.tri_verts, np.int32)
    return verts, tris


def boundary_stats(tris):
    edges = Counter()
    for a, b, c in tris:
        for edge in ((int(a), int(b)), (int(b), int(c)), (int(c), int(a))):
            edges[tuple(sorted(edge))] += 1
    boundary = sum(1 for count in edges.values() if count == 1)
    nonmanifold = sum(1 for count in edges.values() if count > 2)
    return boundary, nonmanifold


def require_solid(mesh, label):
    parts = list(mesh.decompose())
    print(
        f"{label}: status={mesh.status()} genus={mesh.genus()} parts={len(parts)} "
        f"vol={mesh.volume():.6f} tris={mesh.num_tri()}"
    )
    if "NoError" not in str(mesh.status()) or len(parts) != 1 or mesh.volume() <= 0:
        raise SystemExit(f"{label} is not one closed solid")
    return mesh


def build_glove(points, sign):
    points = np.asarray(points, np.float64)
    outward = points[:, 0] * sign
    wrist_o = float(np.quantile(outward, 0.18))
    knuckle_o = float(np.quantile(outward, 0.58))
    wrist = points[outward < np.quantile(outward, 0.35)]
    center_y = float(np.median(wrist[:, 1]))
    center_z = float(np.median(wrist[:, 2]))
    radius = float(np.linalg.norm(wrist[:, 1:] - np.array([center_y, center_z]), axis=1).max()) + 0.006
    # Palm is a closed box. Fingers and thumb stay separated on that one solid.
    # The cuff is a straight cylinder so its radius cannot swallow the digits.
    cuff_radius = float(min(max(radius, 0.045), 0.082))
    cuff_a = np.array([sign * (wrist_o - 0.028), center_y, center_z])
    cuff_b = np.array([sign * (wrist_o + 0.012), center_y, center_z])
    cuff = Manifold.cylinder(np.linalg.norm(cuff_b - cuff_a), cuff_radius, cuff_radius, 18)
    solid = transform_manifold(cuff, frame(cuff_b - cuff_a), cuff_a)
    palm_len = 0.040
    palm = Manifold.cube([palm_len, 0.070, 0.024], True)
    palm_center = np.array([sign * (wrist_o + 0.030), center_y + 0.004, center_z])
    solid += transform_manifold(palm, np.eye(3), palm_center)
    knuckle = wrist_o + 0.046
    lengths = (0.032, 0.042, 0.036, 0.028)
    offsets = (-0.026, -0.009, 0.009, 0.026)
    for index, offset in enumerate(offsets):
        start = np.array([sign * (knuckle - 0.016), center_y + offset, center_z])
        end = np.array([sign * (knuckle + lengths[index]), center_y + offset, center_z + 0.003])
        solid += capsule(start, end, 0.0048, 12)
    solid += capsule(
        np.array([sign * (knuckle - 0.02), center_y + 0.020, center_z + 0.006]),
        np.array([sign * (knuckle + 0.006), center_y + 0.052, center_z + 0.026]),
        0.0068,
        12,
    )
    solid = require_solid(solid, f"glove:{'+' if sign > 0 else '-'}")
    verts, tris = mesh_from_manifold(solid)
    outward_c = verts[:, 0] * sign
    cream_cut = wrist_o + 0.016
    groups = {"cream": [], "leather": []}
    for face_index, face in enumerate(tris):
        centroid = verts[face].mean(axis=0)
        key = "cream" if centroid[0] * sign < cream_cut else "leather"
        groups[key].append(face_index)
    mid = (outward > np.quantile(outward, 0.30)) & (outward < np.quantile(outward, 0.62))
    palm_points = points[mid] if mid.any() else points
    meta = {
        "wrist_o": wrist_o,
        "center_y": center_y,
        "center_z": center_z,
        "sign": sign,
        "palm": palm_points.mean(axis=0),
        "outward_gain": float(verts[:, 0].max() * sign - points[:, 0].max() * sign) if sign > 0 else float((-verts[:, 0]).max() - (-points[:, 0]).max()),
    }
    print(f"  finger extension {meta['outward_gain']:.3f} m mesh, palm {meta['palm']}")
    return verts, tris, groups, meta


def build_boot(points):
    points = np.asarray(points, np.float64)
    low = points[points[:, 1] < np.quantile(points[:, 1], 0.4)]
    flat = low[:, [0, 2]] - low[:, [0, 2]].mean(axis=0)
    _vals, axes = np.linalg.eigh(np.cov(flat.T))
    axis = np.array([axes[0, 1], 0.0, axes[1, 1]])
    axis = normalize(axis)
    if axis[2] < 0:
        axis = -axis
    side = np.array([-axis[2], 0.0, axis[0]])
    upper = points[points[:, 1] > 0.09]
    center = np.median(upper, axis=0)
    ring = points[(points[:, 1] > 0.10) & (points[:, 1] < 0.148)]
    radial = np.linalg.norm(ring[:, [0, 2]] - center[[0, 2]], axis=1)
    cuff_radius = float(np.quantile(radial, 0.9)) + 0.008
    sole = Manifold.cube([0.20, 0.04, 0.09], True)
    sole = transform_manifold(sole, np.stack([axis, np.array([0.0, 1.0, 0.0]), side], axis=1), np.array([center[0], 0.02, center[2]]))
    toe = Manifold.sphere(0.030, 16).translate((np.array([center[0], 0.034, center[2]]) + axis * 0.09).tolist())
    shaft = Manifold.cylinder(0.125, cuff_radius * 0.82, cuff_radius * 0.72, 20)
    shaft = transform_manifold(shaft, frame(np.array([0.0, 1.0, 0.0])), np.array([center[0], 0.015, center[2]]))
    y_top = 0.172
    cuff = Manifold.cylinder(0.034, cuff_radius, cuff_radius * 0.96, 22)
    cuff = transform_manifold(cuff, frame(np.array([0.0, 1.0, 0.0])), np.array([center[0], y_top - 0.032, center[2]]))
    solid = require_solid(sole + toe + shaft + cuff, "boot")
    verts, tris = mesh_from_manifold(solid)
    groups = {"sole": [], "boot": [], "cream": []}
    for face_index, face in enumerate(tris):
        height = float(verts[face][:, 1].mean())
        if height < 0.02:
            groups["sole"].append(face_index)
        elif height > y_top - 0.026:
            groups["cream"].append(face_index)
        else:
            groups["boot"].append(face_index)
    return verts, tris, groups, {"y_top": y_top, "center": center}


def build_rear(back_points, flare):
    ys = np.linspace(0.355, 0.74, 24)
    cols = 20
    outer = []
    for y in ys:
        band = back_points[np.abs(back_points[:, 1] - y) < 0.035]
        if len(band) < 12:
            band = back_points[np.abs(back_points[:, 1] - y) < 0.07]
        z_back = float(np.quantile(band[:, 2], 0.06)) if len(band) else -0.15
        z_back -= 0.016 + flare
        if y < 0.58:
            half = 0.168
            z_row = z_back
        else:
            u = (y - 0.58) / (0.74 - 0.58)
            half = 0.168 * (1.0 - 0.42 * u)
            z_row = z_back - 0.03 * np.sin(u * np.pi)
        xs = np.linspace(-half, half, cols) + 0.012
        curve = (np.abs(xs - 0.012) / max(half, 1e-4)) ** 2 * 0.05
        row = np.stack([xs, np.full(cols, y), np.full(cols, z_row) + curve], axis=1)
        outer.append(row)
    outer = np.stack(outer, axis=0)
    inner = outer + np.array([0.0, 0.0, 0.016])
    rows, width, _ = outer.shape
    verts = np.concatenate([outer.reshape(-1, 3), inner.reshape(-1, 3)], axis=0)

    def index(layer, row, col):
        return layer * rows * width + row * width + col

    tris = []
    tags = []

    def add(a, b, c, tag):
        tris.append((a, b, c))
        tags.append(tag)

    for row in range(rows - 1):
        y_here = float(outer[row, 0, 1])
        tag = "cream" if y_here > 0.69 else ("orange" if y_here < 0.385 or 0.50 < y_here < 0.53 else "navy")
        for col in range(width - 1):
            a, b, c, d = index(0, row, col), index(0, row + 1, col), index(0, row + 1, col + 1), index(0, row, col + 1)
            add(a, b, c, tag)
            add(a, c, d, tag)
            a, b, c, d = index(1, row, col), index(1, row, col + 1), index(1, row + 1, col + 1), index(1, row + 1, col)
            add(a, b, c, tag)
            add(a, c, d, tag)

    def loop(layer):
        seq = [index(layer, 0, col) for col in range(width)]
        seq += [index(layer, row, width - 1) for row in range(1, rows)]
        seq += [index(layer, rows - 1, col) for col in range(width - 2, -1, -1)]
        seq += [index(layer, row, 0) for row in range(rows - 2, 0, -1)]
        return seq

    outer_loop, inner_loop = loop(0), loop(1)
    for i in range(len(outer_loop)):
        o0, o1 = outer_loop[i], outer_loop[(i + 1) % len(outer_loop)]
        i0, i1 = inner_loop[i], inner_loop[(i + 1) % len(inner_loop)]
        add(o0, o1, i1, "navy")
        add(o0, i1, i0, "navy")
    tris = np.array(tris, np.int32)
    boundary, nonmanifold = boundary_stats(tris)
    print(f"rear shell flare={flare:.3f} verts={len(verts)} tris={len(tris)} boundary={boundary} nonmanifold={nonmanifold}")
    if boundary or nonmanifold:
        raise SystemExit("rear shell is not a single closed surface")
    return verts, tris, tags


def load_glb(path):
    data = path.read_bytes()
    length = struct.unpack_from("<I", data, 12)[0]
    document = json.loads(data[20 : 20 + length])
    offset = 20 + length
    while offset % 4:
        offset += 1
    chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
    if chunk_type != 0x004E4942:
        raise SystemExit("missing BIN chunk")
    blob = bytearray(data[offset + 8 : offset + 8 + chunk_length])
    return document, blob


def accessor(document, blob, index):
    acc = document["accessors"][index]
    view = document["bufferViews"][acc["bufferView"]]
    start = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    component = {5120: "b", 5121: "B", 5122: "h", 5123: "H", 5125: "I", 5126: "f"}[acc["componentType"]]
    width = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[acc["type"]]
    count = acc["count"]
    item = np.dtype("<" + component).itemsize
    stride = view.get("byteStride", item * width)
    if stride != item * width:
        raise SystemExit("unexpected interleaved accessor")
    array = np.frombuffer(blob[start : start + count * stride], dtype="<" + component).reshape(count, width).copy()
    return array


def node_matrix(node):
    matrix = np.eye(4)
    matrix[:3, 3] = node.get("translation", (0, 0, 0))
    rotation = np.eye(4)
    rotation[:3, :3] = quat_to_mat(node.get("rotation", (0, 0, 0, 1)))
    scale = np.diag([*node.get("scale", (1, 1, 1)), 1.0])
    return matrix @ rotation @ scale


def world_matrices(nodes):
    parent = {}
    for index, node in enumerate(nodes):
        for child in node.get("children", []):
            parent[child] = index
    worlds = {}

    def walk(index):
        if index in worlds:
            return worlds[index]
        local = node_matrix(nodes[index])
        worlds[index] = walk(parent[index]) @ local if index in parent else local
        return worlds[index]

    for index in range(len(nodes)):
        walk(index)
    return worlds, parent


def bone_weights(joints, weights, names, wanted):
    ids = [names.index(name) for name in wanted]
    total = np.zeros(len(joints), np.float64)
    for slot in range(4):
        total += np.where(np.isin(joints[:, slot], ids), weights[:, slot], 0.0)
    return total


def vertex_normals(verts, tris):
    normals = np.zeros_like(verts)
    faces = verts[tris]
    face_n = np.cross(faces[:, 1] - faces[:, 0], faces[:, 2] - faces[:, 0])
    for corner in range(3):
        np.add.at(normals, tris[:, corner], face_n)
    lengths = np.linalg.norm(normals, axis=1)
    lengths[lengths < 1e-12] = 1
    return normals / lengths[:, None]


def two_bone(shoulder, rest_elbow, rest_hand, target, pole):
    upper = float(np.linalg.norm(rest_elbow - shoulder))
    forearm = float(np.linalg.norm(rest_hand - rest_elbow))
    direction = np.asarray(target, np.float64) - shoulder
    distance = float(np.linalg.norm(direction))
    distance = float(np.clip(distance, abs(upper - forearm) + 1e-4, upper + forearm - 1e-4))
    reached = shoulder + normalize(direction) * distance
    cosine = np.clip((upper * upper + distance * distance - forearm * forearm) / (2 * upper * distance), -1, 1)
    along = normalize(reached - shoulder)
    sideways = np.asarray(pole, np.float64) - shoulder
    sideways = sideways - along * np.dot(sideways, along)
    if np.linalg.norm(sideways) < 1e-5:
        sideways = np.array([0.0, 1.0, 0.0])
    sideways = normalize(sideways)
    elbow = shoulder + along * (upper * cosine) + sideways * (upper * np.sqrt(max(0.0, 1 - cosine * cosine)))
    return elbow, reached


class PoseRig:
    def __init__(self, nodes, worlds):
        self.nodes = nodes
        self.by_name = {node["name"]: index for index, node in enumerate(nodes) if node.get("name")}
        self.rest = {name: worlds[self.index(name)] for name in (
            "L_Clavicle", "L_Upperarm", "L_Forearm", "L_Hand",
            "R_Clavicle", "R_Upperarm", "R_Forearm", "R_Hand",
        )}
        self.by_name = {node["name"]: i for i, node in enumerate(nodes) if node.get("name")}

    def index(self, name):
        return self.by_name[name]

    def solve_arms(self, left_palm, right_palm, palm_local):
        solved = {}
        for side, palm, pole_sign in (("L", left_palm, 1.0), ("R", right_palm, -1.0)):
            shoulder = self.rest[f"{side}_Upperarm"][:3, 3]
            elbow_rest = self.rest[f"{side}_Forearm"][:3, 3]
            hand_rest = self.rest[f"{side}_Hand"][:3, 3]
            palm = np.asarray(palm, np.float64)
            wrist_guess = palm - normalize(palm - shoulder) * float(np.linalg.norm(palm_local[side]))
            pole = shoulder + np.array([0.28 * pole_sign, -0.08, -0.05])
            for _ in range(4):
                elbow, wrist = two_bone(shoulder, elbow_rest, hand_rest, wrist_guess, pole)
                swing_u = rot_between(elbow_rest - shoulder, elbow - shoulder)
                upper = swing_u @ self.rest[f"{side}_Upperarm"][:3, :3]
                swing_f = rot_between(hand_rest - elbow_rest, wrist - elbow)
                forearm = swing_f @ self.rest[f"{side}_Forearm"][:3, :3]
                hand_y = normalize(wrist - elbow)
                swing_h = rot_between(self.rest[f"{side}_Hand"][:3, 1], hand_y)
                hand = swing_h @ self.rest[f"{side}_Hand"][:3, :3]
                # Roll the palm normal (rest local +Z-ish, stored as palm axis) toward the other palm.
                current_palm = wrist + hand @ palm_local[side]
                to_haft = (right_palm if side == "L" else left_palm) - current_palm
                rest_axis = normalize(self.rest[f"{side}_Hand"][:3, :3].T @ np.array([0.0, 0.0, 1.0]))
                if np.linalg.norm(rest_axis) < 0.5:
                    rest_axis = np.array([0.0, 0.0, 1.0])
                current_axis = hand @ rest_axis
                axis = hand_y
                projected_current = current_axis - axis * np.dot(current_axis, axis)
                projected_target = to_haft - axis * np.dot(to_haft, axis)
                if np.linalg.norm(projected_current) > 1e-5 and np.linalg.norm(projected_target) > 1e-5:
                    hand = rot_between(projected_current, projected_target) @ hand
                current_palm = wrist + hand @ palm_local[side]
                wrist_guess = wrist + (palm - current_palm)
            solved[side] = {"upper": upper, "forearm": forearm, "hand": hand, "wrist": wrist, "palm": wrist + hand @ palm_local[side]}
        return solved


def local_quat(world_rotation, parent_world_rotation):
    return mat_to_quat(parent_world_rotation.T @ world_rotation)


def continuous(quats):
    out = [quats[0]]
    for quat in quats[1:]:
        if np.dot(out[-1], quat) < 0:
            quat = -quat
        out.append(quat)
    return out


def pack_glb(document, blob):
    raw = json.dumps(document, separators=(",", ":")).encode("utf-8")
    raw += b" " * ((4 - len(raw) % 4) % 4)
    blob = bytes(blob)
    blob += b"\x00" * ((4 - len(blob) % 4) % 4)
    total = 12 + 8 + len(raw) + 8 + len(blob)
    out = bytearray()
    out += struct.pack("<4sII", b"glTF", 2, total)
    out += struct.pack("<I4s", len(raw), b"JSON")
    out += raw
    out += struct.pack("<I4s", len(blob), b"BIN\x00")
    out += blob
    return out


def add_array(document, blob, array, component_type, type_name, target=None):
    array = np.ascontiguousarray(array)
    while len(blob) % 4:
        blob.append(0)
    offset = len(blob)
    payload = array.tobytes()
    blob += payload
    view_index = len(document["bufferViews"])
    view = {"buffer": 0, "byteOffset": offset, "byteLength": len(payload)}
    if target is not None:
        view["target"] = target
    document["bufferViews"].append(view)
    accessor_index = len(document["accessors"])
    entry = {
        "bufferView": view_index,
        "componentType": component_type,
        "count": int(array.shape[0]),
        "type": type_name,
    }
    if type_name != "SCALAR":
        flat = array.reshape(array.shape[0], -1).astype(np.float64)
        entry["min"] = flat.min(axis=0).tolist()
        entry["max"] = flat.max(axis=0).tolist()
    elif component_type == 5126:
        entry["min"] = [float(array.min())]
        entry["max"] = [float(array.max())]
    document["accessors"].append(entry)
    return accessor_index


def main():
    document, blob = load_glb(SRC)
    if any(anim.get("name", "").endswith(":chop") for anim in document.get("animations", [])):
        raise SystemExit("Character1.glb already has the final clips; restore the source asset before rebuilding")
    nodes = document["nodes"]
    primitive = document["meshes"][0]["primitives"][0]
    positions = accessor(document, blob, primitive["attributes"]["POSITION"]).astype(np.float64)
    joints = accessor(document, blob, primitive["attributes"]["JOINTS_0"]).astype(np.int32)
    weights = accessor(document, blob, primitive["attributes"]["WEIGHTS_0"]).astype(np.float64)
    indices = accessor(document, blob, primitive["indices"]).reshape(-1, 3).astype(np.int32)
    skin = document["skins"][0]
    names = [nodes[joint]["name"] for joint in skin["joints"]]
    worlds, parent = world_matrices(nodes)
    original_min = positions.min(axis=0)
    original_max = positions.max(axis=0)
    print("source verts", len(positions), "faces", len(indices), "y", original_min[1], original_max[1])

    left_hand = (
        (positions[:, 0] > 0.398)
        & (positions[:, 1] > 0.46)
        & (positions[:, 1] < 0.62)
        & (positions[:, 2] > -0.13)
        & (positions[:, 2] < 0.05)
    )
    right_hand = (
        (positions[:, 0] < -0.398)
        & (positions[:, 1] > 0.46)
        & (positions[:, 1] < 0.62)
        & (positions[:, 2] > -0.13)
        & (positions[:, 2] < 0.05)
    )
    left_boot = (positions[:, 0] > 0.02) & (positions[:, 0] < 0.24) & (positions[:, 1] < 0.148) & (positions[:, 2] > -0.14) & (positions[:, 2] < 0.16)
    right_boot = (positions[:, 0] < -0.02) & (positions[:, 0] > -0.24) & (positions[:, 1] < 0.148) & (positions[:, 2] > -0.14) & (positions[:, 2] < 0.16)
    # The live back is already one skinned shell. Cutting it open left a hole at the
# shoulder once the arms lifted, so the coat back stays the original piece.
    rear = np.zeros(len(positions), dtype=bool)
    print("regions", int(left_hand.sum()), int(right_hand.sum()), int(left_boot.sum()), int(right_boot.sum()), int(rear.sum()))

    glove_l = build_glove(positions[left_hand], 1.0)
    glove_r = build_glove(positions[right_hand], -1.0)
    boot_l = build_boot(positions[left_boot])
    boot_r = build_boot(positions[right_boot])

    flare = 0.0
    print("rear shell skipped; original parka back kept")

    # Assemble skinned vertices.
    batches = []

    def add_skinned(verts, tris, groups, weight_fn, material_of):
        base = 0
        normals = vertex_normals(verts, tris)
        skin_j = np.zeros((len(verts), 4), np.uint8)
        skin_w = np.zeros((len(verts), 4), np.float32)
        for i, vertex in enumerate(verts):
            pairs = weight_fn(vertex)
            pairs = sorted(pairs, key=lambda item: -item[1])[:4]
            total = sum(weight for _, weight in pairs) or 1
            for slot, (name, weight) in enumerate(pairs):
                skin_j[i, slot] = names.index(name)
                skin_w[i, slot] = weight / total
        batches.append((verts, normals, skin_j, skin_w, tris, groups, material_of))

    def glove_weights(side, meta):
        hand = f"{side}_Hand"
        forearm = f"{side}_Forearm"

        def weight(vertex):
            if vertex[0] * meta["sign"] < meta["wrist_o"] + 0.004:
                return [(hand, 0.58), (forearm, 0.42)]
            return [(hand, 1.0)]

        return weight

    def boot_weights(side, meta):
        foot, toe, calf = f"{side}_Foot", f"{side}_ToeBase", f"{side}_Calf"

        def weight(vertex):
            if vertex[1] < 0.03:
                return [(toe, 0.72), (foot, 0.28)]
            if vertex[1] > meta["y_top"] - 0.006:
                return [(calf, 0.62), (foot, 0.38)]
            return [(foot, 0.74), (toe, 0.26)]

        return weight

    def rear_weights(vertex):
        y = vertex[1]
        if y > 0.68:
            return [("Head", 0.15), ("NeckTwist02", 0.30), ("Spine02", 0.55)]
        if y > 0.54:
            return [("Spine02", 0.80), ("Spine01", 0.20)]
        if y > 0.45:
            return [("Spine01", 0.75), ("Spine02", 0.25)]
        return [("Waist", 0.88), ("Spine01", 0.12)]

    add_skinned(*glove_l[:3], glove_weights("L", glove_l[3]), {"cream": "cream", "leather": "leather"})
    add_skinned(*glove_r[:3], glove_weights("R", glove_r[3]), {"cream": "cream", "leather": "leather"})
    add_skinned(*boot_l[:3], boot_weights("L", boot_l[3]), {"sole": "sole", "boot": "boot", "cream": "cream"})
    add_skinned(*boot_r[:3], boot_weights("R", boot_r[3]), {"sole": "sole", "boot": "boot", "cream": "cream"})
    all_v = np.concatenate([batch[0] for batch in batches], axis=0)
    print("new y", all_v[:, 1].min(), all_v[:, 1].max(), "source y", original_min[1], original_max[1])
    if all_v[:, 1].min() < original_min[1] - 1e-4 or all_v[:, 1].max() > original_max[1] + 1e-3:
        raise SystemExit("replacement pieces changed the character height envelope")

    # Drop replaced faces. A face goes if its centroid lies in a replaced region
    # or at least two corners do, so sliver triangles cannot bridge the hole.
    region = left_hand | right_hand | left_boot | right_boot | rear
    corner = region[indices]
    centroid = positions[indices].mean(axis=1)
    centroid_hit = (
        ((centroid[:, 0] > 0.398) & (centroid[:, 1] > 0.46) & (centroid[:, 1] < 0.62) & (centroid[:, 2] > -0.13) & (centroid[:, 2] < 0.05))
        | ((centroid[:, 0] < -0.398) & (centroid[:, 1] > 0.46) & (centroid[:, 1] < 0.62) & (centroid[:, 2] > -0.13) & (centroid[:, 2] < 0.05))
        | ((centroid[:, 0] > 0.02) & (centroid[:, 0] < 0.24) & (centroid[:, 1] < 0.148) & (centroid[:, 2] > -0.14) & (centroid[:, 2] < 0.16))
        | ((centroid[:, 0] < -0.02) & (centroid[:, 0] > -0.24) & (centroid[:, 1] < 0.148) & (centroid[:, 2] > -0.14) & (centroid[:, 2] < 0.16))
        )
    keep = ~((corner.sum(axis=1) >= 2) | centroid_hit)
    kept = indices[keep]
    print("kept faces", len(kept), "of", len(indices))

    # Sockets from the glove palm centers, in hand-bone local space.
    rig = PoseRig(nodes, worlds)
    palm_local = {}
    palms = {}
    for side, meta in (("L", glove_l[3]), ("R", glove_r[3])):
        origin = worlds[rig.index(f"{side}_Hand")][:3, 3]
        rotation = worlds[rig.index(f"{side}_Hand")][:3, :3]
        palm_local[side] = rotation.T @ (meta["palm"] - origin)
        palms[side] = meta["palm"]
        print(side, "palm", meta["palm"], "local", palm_local[side])

    # Action poses. Targets are palm positions; IK places the wrist behind them.
    clips = {
        "chop": {
            "times": [0.0, 0.16, 0.34, 0.50, 0.68],
            "palms": [
                (np.array([0.10, 0.60, 0.05]), np.array([-0.02, 0.50, 0.06])),
                (np.array([0.08, 0.56, 0.08]), np.array([-0.01, 0.46, 0.09])),
                (np.array([0.05, 0.50, 0.11]), np.array([0.00, 0.42, 0.12])),
                (np.array([0.03, 0.46, 0.13]), np.array([0.01, 0.37, 0.14])),
                (np.array([0.04, 0.48, 0.12]), np.array([0.00, 0.39, 0.13])),
            ],
        },
        "mine": {
            "times": [0.0, 0.16, 0.34, 0.52, 0.70],
            "palms": [
                (np.array([0.02, 0.64, 0.02]), np.array([-0.02, 0.54, 0.03])),
                (np.array([0.01, 0.60, 0.06]), np.array([-0.01, 0.50, 0.07])),
                (np.array([0.00, 0.54, 0.11]), np.array([0.00, 0.44, 0.12])),
                (np.array([-0.01, 0.48, 0.14]), np.array([0.01, 0.38, 0.15])),
                (np.array([0.00, 0.50, 0.13]), np.array([0.00, 0.40, 0.14])),
            ],
        },
        "carry": {
            "times": [0.0, 1.1],
            "palms": [
                (np.array([0.09, 0.42, 0.11]), np.array([-0.09, 0.42, 0.11])),
                (np.array([0.09, 0.42, 0.11]), np.array([-0.09, 0.42, 0.11])),
            ],
        },
    }

    rest_local_rot = {}
    rest_local_pos = {}
    for index, node in enumerate(nodes):
        if not node.get("name"):
            continue
        rest_local_rot[index] = np.array(node.get("rotation", (0, 0, 0, 1)), np.float64)
        rest_local_pos[index] = np.array(node.get("translation", (0, 0, 0)), np.float64)

    def arm_locals(solved):
        locals_ = {}
        for side in ("L", "R"):
            upper_i = rig.index(f"{side}_Upperarm")
            forearm_i = rig.index(f"{side}_Forearm")
            hand_i = rig.index(f"{side}_Hand")
            parent_upper = worlds[parent[upper_i]][:3, :3]
            locals_[upper_i] = local_quat(solved[side]["upper"], parent_upper)
            locals_[forearm_i] = local_quat(solved[side]["forearm"], solved[side]["upper"])
            locals_[hand_i] = local_quat(solved[side]["hand"], solved[side]["forearm"])
            err = np.linalg.norm(solved[side]["palm"] - (solved[side]["wrist"] + solved[side]["hand"] @ palm_local[side]))
            print(side, "palm residual", err, "palm", solved[side]["palm"])
        return locals_

    # Write geometry into the existing GLB, then append the three action clips.
    new_positions = []
    new_normals = []
    new_joints = []
    new_weights = []
    grouped = {key: [] for key in ("leather", "cream", "boot", "sole", "navy", "orange")}
    cursor_v = 0
    for verts, norms, js, ws, tris, groups, material_of in batches:
        new_positions.append(verts.astype(np.float32))
        new_normals.append(norms.astype(np.float32))
        new_joints.append(js)
        new_weights.append(ws.astype(np.float32))
        for group, face_ids in groups.items():
            if not face_ids:
                continue
            material = material_of[group]
            grouped[material].append(tris[np.array(face_ids, np.int32)] + cursor_v)
        cursor_v += len(verts)
    pos_a = np.concatenate(new_positions, axis=0)
    nrm_a = np.concatenate(new_normals, axis=0)
    j_a = np.concatenate(new_joints, axis=0)
    w_a = np.concatenate(new_weights, axis=0)
    if not np.allclose(w_a.sum(axis=1), 1, atol=1e-3):
        raise SystemExit("skin weights do not sum to 1")

    document["bufferViews"] = document["bufferViews"]
    pos_acc = add_array(document, blob, pos_a, 5126, "VEC3", 34962)
    nrm_acc = add_array(document, blob, nrm_a, 5126, "VEC3", 34962)
    j_acc = add_array(document, blob, j_a, 5121, "VEC4", 34962)
    w_acc = add_array(document, blob, w_a, 5126, "VEC4", 34962)
    kept_acc = add_array(document, blob, kept.astype(np.uint32).reshape(-1), 5125, "SCALAR", 34963)
    primitive["indices"] = kept_acc

    colors = {"leather": LEATHER, "cream": CREAM, "boot": BOOT, "sole": SOLE, "navy": NAVY, "orange": ORANGE}
    document["materials"] = document.get("materials", [])
    material_ids = {}
    for name, color in colors.items():
        material_ids[name] = len(document["materials"])
        document["materials"].append(
            {
                "name": f"C1_{name}",
                "doubleSided": True,
                "pbrMetallicRoughness": {
                    "baseColorFactor": list(color),
                    "metallicFactor": 0.0,
                    "roughnessFactor": 0.58 if name != "cream" else 0.72,
                },
            }
        )
    mesh = document["meshes"][0]
    for name, chunks in grouped.items():
        if not chunks:
            continue
        faces = np.concatenate(chunks, axis=0).astype(np.uint32)
        idx_acc = add_array(document, blob, faces.reshape(-1), 5125, "SCALAR", 34963)
        mesh["primitives"].append(
            {
                "attributes": {"POSITION": pos_acc, "NORMAL": nrm_acc, "JOINTS_0": j_acc, "WEIGHTS_0": w_acc},
                "indices": idx_acc,
                "material": material_ids[name],
            }
        )
        bcount, ncount = boundary_stats(faces)
        print(f"prim {name} tris={len(faces)} boundary={bcount}")

    # Animations.
    animated_nodes = [index for index, node in enumerate(nodes) if node.get("name") and index in parent or node.get("name") in ("Root", "Armature")]
    # Every skinned joint node, which is the set the idle clip already drives.
    joint_nodes = list(skin["joints"])
    for clip_name, clip in clips.items():
        times = np.array(clip["times"], np.float32)
        time_acc = add_array(document, blob, times, 5126, "SCALAR")
        samplers = []
        channels = []
        solved_keys = [rig.solve_arms(left, right, palm_local) for left, right in clip["palms"]]
        arm_quats = {rig.index(f"{side}_{bone}"): [] for side in ("L", "R") for bone in ("Upperarm", "Forearm", "Hand")}
        for solved in solved_keys:
            locals_ = arm_locals(solved)
            for index, quat in locals_.items():
                arm_quats[index].append(quat)
        for index in arm_quats:
            arm_quats[index] = continuous(arm_quats[index])
        for node_index in joint_nodes:
            if node_index in arm_quats:
                values = np.stack(arm_quats[node_index], axis=0).astype(np.float32)
            else:
                values = np.repeat(rest_local_rot[node_index][None, :].astype(np.float32), len(times), axis=0)
            out_acc = add_array(document, blob, values, 5126, "VEC4")
            sampler_index = len(samplers)
            samplers.append({"input": time_acc, "output": out_acc, "interpolation": "LINEAR"})
            channels.append({"sampler": sampler_index, "target": {"node": node_index, "path": "rotation"}})
            pos_values = np.repeat(rest_local_pos[node_index][None, :].astype(np.float32), len(times), axis=0)
            pos_acc_i = add_array(document, blob, pos_values, 5126, "VEC3")
            sampler_index = len(samplers)
            samplers.append({"input": time_acc, "output": pos_acc_i, "interpolation": "LINEAR"})
            channels.append({"sampler": sampler_index, "target": {"node": node_index, "path": "translation"}})
        document["animations"].append({"name": f"preset:biped:{clip_name}", "samplers": samplers, "channels": channels})
        print("added", clip_name, "channels", len(channels))

    document["buffers"][0]["byteLength"] = len(blob)
    DST.write_bytes(pack_glb(document, blob))

    spine = worlds[rig.index("Spine02")]
    # World -Z is the character's back. Keep the sheathed haft on the rear torso.
    sheath_world = spine[:3, 3] + np.array([0.02, 0.04, -0.11])
    sheath_local = spine[:3, :3].T @ (sheath_world - spine[:3, 3])
    payload = {
        "left_palm_bone": "L_Hand",
        "right_palm_bone": "R_Hand",
        "left_palm_local": palm_local["L"].tolist(),
        "right_palm_local": palm_local["R"].tolist(),
        "sheath_bone": "Spine02",
        "sheath_local": sheath_local.tolist(),
        "axe_grip_y": [-0.34, -0.08],
        "pick_grip_y": [-0.38, -0.08],
        "rear_flare": flare,
    }
    SOCKETS.write_text(json.dumps(payload, indent=2) + "\n")
    print("wrote", DST, "bytes", DST.stat().st_size)
    print("sockets", json.dumps(payload))


if __name__ == "__main__":
    main()
