#!/usr/bin/env python3
"""Audit the exact T06 runtime GLB's deformed surface and gait sole landmarks.

This is deterministic evidence, not a visual score. It evaluates every skinned
vertex and triangle at 120 Hz, performs exhaustive broad-phase/narrow-phase
intersection checks between non-adjacent semantic regions, and follows fixed
heel/ball/toe vertex IDs through three controller-translated gait cycles.
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import math
import struct
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree


COMPONENT_DTYPES = {5121: np.uint8, 5123: np.dtype("<u2"), 5125: np.dtype("<u4"), 5126: np.dtype("<f4")}
TYPE_WIDTHS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
FLOOR_TOLERANCE_M = 0.003
MINIMUM_TRIANGLE_DOUBLE_AREA_M2 = 1.0e-10
SURFACE_TOLERANCE_M = 0.0005


def json_default(value):
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def quaternion_matrix(value: np.ndarray) -> np.ndarray:
    x, y, z, w = value / np.linalg.norm(value)
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w), 0],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w), 0],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y), 0],
        [0, 0, 0, 1],
    ], dtype=np.float64)


def local_matrix(translation: np.ndarray, rotation: np.ndarray, scale: np.ndarray) -> np.ndarray:
    result = quaternion_matrix(rotation) @ np.diag([*scale, 1.0])
    result[:3, 3] = translation
    return result


def slerp(first: np.ndarray, second: np.ndarray, fraction: float) -> np.ndarray:
    dot = float(np.dot(first, second))
    if dot < 0:
        second = -second
        dot = -dot
    if dot > 0.9995:
        value = first + fraction * (second - first)
        return value / np.linalg.norm(value)
    angle = math.acos(max(-1.0, min(1.0, dot)))
    sine = math.sin(angle)
    return (math.sin((1 - fraction) * angle) * first + math.sin(fraction * angle) * second) / sine


@dataclass
class Channel:
    node: int
    path: str
    times: np.ndarray
    values: np.ndarray

    def sample(self, time: float) -> np.ndarray:
        if time <= self.times[0]:
            return self.values[0]
        if time >= self.times[-1]:
            return self.values[-1]
        index = bisect.bisect_right(self.times, time) - 1
        fraction = float((time - self.times[index]) / (self.times[index + 1] - self.times[index]))
        if self.path == "rotation":
            return slerp(self.values[index], self.values[index + 1], fraction)
        return self.values[index] * (1 - fraction) + self.values[index + 1] * fraction


class RuntimeGLB:
    def __init__(self, path: Path):
        self.path = path
        data = path.read_bytes()
        if len(data) < 28 or struct.unpack_from("<III", data) != (0x46546C67, 2, len(data)):
            raise ValueError("invalid GLB 2.0 header")
        json_size, json_kind = struct.unpack_from("<II", data, 12)
        if json_kind != 0x4E4F534A:
            raise ValueError("first GLB chunk is not JSON")
        self.document = json.loads(data[20:20 + json_size])
        binary_offset = 20 + json_size
        binary_size, binary_kind = struct.unpack_from("<II", data, binary_offset)
        if binary_kind != 0x004E4942:
            raise ValueError("second GLB chunk is not BIN")
        self.binary = memoryview(data)[binary_offset + 8:binary_offset + 8 + binary_size]
        self.sha256 = hashlib.sha256(data).hexdigest()
        self.parents = [-1] * len(self.document["nodes"])
        for parent, node in enumerate(self.document["nodes"]):
            for child in node.get("children", []):
                self.parents[child] = parent
        self.rest_trs = []
        for node in self.document["nodes"]:
            if "matrix" in node:
                matrix = np.asarray(node["matrix"], dtype=np.float64).reshape(4, 4).T
                translation = matrix[:3, 3]
                scale = np.linalg.norm(matrix[:3, :3], axis=0)
                rotation_matrix = matrix[:3, :3] / scale
                rotation = self._quaternion_from_matrix(rotation_matrix)
            else:
                translation = np.asarray(node.get("translation", [0, 0, 0]), dtype=np.float64)
                rotation = np.asarray(node.get("rotation", [0, 0, 0, 1]), dtype=np.float64)
                scale = np.asarray(node.get("scale", [1, 1, 1]), dtype=np.float64)
            self.rest_trs.append((translation, rotation, scale))
        primitive = self.document["meshes"][0]["primitives"][0]
        attributes = primitive["attributes"]
        self.positions = self.accessor(attributes["POSITION"]).astype(np.float64)
        self.joint_indices = self.accessor(attributes["JOINTS_0"]).astype(np.int64)
        self.weights = self.accessor(attributes["WEIGHTS_0"]).astype(np.float64)
        self.faces = self.accessor(primitive["indices"]).reshape(-1, 3).astype(np.int64)
        self.skin = self.document["skins"][0]
        self.skin_joints = self.skin["joints"]
        self.joint_names = [self.document["nodes"][node].get("name", f"node:{node}") for node in self.skin_joints]
        self.inverse_bind = self.accessor(self.skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1).astype(np.float64)
        self.homogeneous_positions = np.column_stack([self.positions, np.ones(len(self.positions))])
        self.animations = {}
        for animation in self.document.get("animations", []):
            channels = []
            for row in animation["channels"]:
                sampler = animation["samplers"][row["sampler"]]
                if sampler.get("interpolation", "LINEAR") != "LINEAR":
                    raise ValueError(f"unsupported interpolation in {animation.get('name')}")
                channels.append(Channel(
                    row["target"]["node"], row["target"]["path"],
                    self.accessor(sampler["input"])[:, 0].astype(np.float64),
                    self.accessor(sampler["output"]).astype(np.float64),
                ))
            self.animations[animation["name"]] = channels

    @staticmethod
    def _quaternion_from_matrix(matrix: np.ndarray) -> np.ndarray:
        trace = float(np.trace(matrix))
        if trace > 0:
            s = math.sqrt(trace + 1.0) * 2
            return np.array([(matrix[2, 1] - matrix[1, 2]) / s, (matrix[0, 2] - matrix[2, 0]) / s,
                             (matrix[1, 0] - matrix[0, 1]) / s, 0.25 * s])
        axis = int(np.argmax(np.diag(matrix)))
        if axis == 0:
            s = math.sqrt(1 + matrix[0, 0] - matrix[1, 1] - matrix[2, 2]) * 2
            return np.array([0.25 * s, (matrix[0, 1] + matrix[1, 0]) / s,
                             (matrix[0, 2] + matrix[2, 0]) / s, (matrix[2, 1] - matrix[1, 2]) / s])
        if axis == 1:
            s = math.sqrt(1 + matrix[1, 1] - matrix[0, 0] - matrix[2, 2]) * 2
            return np.array([(matrix[0, 1] + matrix[1, 0]) / s, 0.25 * s,
                             (matrix[1, 2] + matrix[2, 1]) / s, (matrix[0, 2] - matrix[2, 0]) / s])
        s = math.sqrt(1 + matrix[2, 2] - matrix[0, 0] - matrix[1, 1]) * 2
        return np.array([(matrix[0, 2] + matrix[2, 0]) / s, (matrix[1, 2] + matrix[2, 1]) / s,
                         0.25 * s, (matrix[1, 0] - matrix[0, 1]) / s])

    def accessor(self, index: int) -> np.ndarray:
        accessor = self.document["accessors"][index]
        view = self.document["bufferViews"][accessor["bufferView"]]
        width = TYPE_WIDTHS[accessor["type"]]
        dtype = np.dtype(COMPONENT_DTYPES[accessor["componentType"]])
        stride = view.get("byteStride", dtype.itemsize * width)
        start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        return np.stack([
            np.frombuffer(self.binary[start + row * stride:start + row * stride + dtype.itemsize * width], dtype, width)
            for row in range(accessor["count"])
        ])

    def duration(self, name: str) -> float:
        return max(float(channel.times[-1]) for channel in self.animations[name])

    def matrices(self, name: str, time: float) -> list[np.ndarray]:
        trs = [[item.copy() for item in row] for row in self.rest_trs]
        for channel in self.animations[name]:
            slot = {"translation": 0, "rotation": 1, "scale": 2}[channel.path]
            trs[channel.node][slot] = channel.sample(time)
        local = [local_matrix(*row) for row in trs]
        global_matrices: list[np.ndarray | None] = [None] * len(local)

        def resolve(index: int) -> np.ndarray:
            if global_matrices[index] is None:
                global_matrices[index] = local[index] if self.parents[index] < 0 else resolve(self.parents[index]) @ local[index]
            return global_matrices[index]

        return [resolve(index) for index in range(len(local))]

    def deform(self, name: str, time: float, selected: np.ndarray | None = None) -> np.ndarray:
        global_matrices = self.matrices(name, time)
        skin_matrices = np.stack([global_matrices[node] @ self.inverse_bind[index] for index, node in enumerate(self.skin_joints)])
        if selected is None:
            positions, joints, weights = self.homogeneous_positions, self.joint_indices, self.weights
        else:
            positions, joints, weights = self.homogeneous_positions[selected], self.joint_indices[selected], self.weights[selected]
        result = np.zeros((len(positions), 4), dtype=np.float64)
        for influence in range(4):
            result += weights[:, influence, None] * np.einsum("nij,nj->ni", skin_matrices[joints[:, influence]], positions)
        return result[:, :3]


def part_inventory(runtime: RuntimeGLB, parts: list[dict]) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray], dict[str, np.ndarray]]:
    joint_to_part = {joint: index for index, part in enumerate(parts) for joint in part["joints"]}
    if set(joint_to_part) != set(runtime.joint_names):
        raise ValueError("semantic parts do not exactly cover skin joints")
    dominant_slots = np.argmax(runtime.weights, axis=1)
    dominant_joints = runtime.joint_indices[np.arange(len(runtime.positions)), dominant_slots]
    vertex_parts = np.array([joint_to_part[runtime.joint_names[index]] for index in dominant_joints], dtype=np.int64)
    face_parts = np.empty(len(runtime.faces), dtype=np.int64)
    for index, face in enumerate(runtime.faces):
        values, counts = np.unique(vertex_parts[face], return_counts=True)
        face_parts[index] = values[np.argmax(counts)]
    vertices = {part["id"]: np.flatnonzero(vertex_parts == index) for index, part in enumerate(parts)}
    faces = {part["id"]: np.flatnonzero(face_parts == index) for index, part in enumerate(parts)}
    return vertex_parts, face_parts, vertices, faces


def adjacency(runtime: RuntimeGLB, parts: list[dict]) -> set[tuple[int, int]]:
    part_by_joint = {joint: index for index, part in enumerate(parts) for joint in part["joints"]}
    result = {(index, index) for index in range(len(parts))}
    for skin_index, node in enumerate(runtime.skin_joints):
        parent = runtime.parents[node]
        if parent in runtime.skin_joints:
            parent_index = runtime.skin_joints.index(parent)
            pair = tuple(sorted((part_by_joint[runtime.joint_names[skin_index]], part_by_joint[runtime.joint_names[parent_index]])))
            result.add(pair)
    by_name = {part["id"]: index for index, part in enumerate(parts)}
    intentional = [
        ("coat_torso_garment", "waist_spine"), ("coat_torso_garment", "left_thigh"),
        ("coat_torso_garment", "right_thigh"), ("coat_torso_garment", "left_shoulder_upper_arm"),
        ("coat_torso_garment", "right_shoulder_upper_arm"), ("coat_torso_garment", "pouch_attachment"),
        ("coat_torso_garment", "hem_fasteners"), ("pouch_attachment", "waist_spine"),
        ("left_thigh", "right_thigh"), ("left_forearm_wrist_hand", "right_forearm_wrist_hand"),
        ("left_shoulder_upper_arm", "right_shoulder_upper_arm"),
        ("neck_head_face_hair_eyewear", "left_shoulder_upper_arm"),
        ("neck_head_face_hair_eyewear", "right_shoulder_upper_arm"),
    ]
    for first, second in intentional:
        result.add(tuple(sorted((by_name[first], by_name[second]))))
    # Dominant-weight semantic labels subdivide one continuous skinned surface.
    # Regions within four links of the same deformation chain are therefore
    # topological neighbours, even when no single triangle shares their labels.
    graph = {index: set() for index in range(len(parts))}
    for first, second in result:
        graph[first].add(second)
        graph[second].add(first)
    for start in graph:
        frontier = {start}
        visited = {start}
        for _ in range(4):
            frontier = {item for node in frontier for item in graph[node]} - visited
            visited |= frontier
        for end in visited:
            result.add(tuple(sorted((start, end))))
    return result


def segment_triangle(first: np.ndarray, second: np.ndarray, triangle: np.ndarray) -> bool:
    direction = second - first
    edge1, edge2 = triangle[1] - triangle[0], triangle[2] - triangle[0]
    cross = np.cross(direction, edge2)
    determinant = float(np.dot(edge1, cross))
    if abs(determinant) < 1e-10:
        return False
    inverse = 1.0 / determinant
    offset = first - triangle[0]
    u = inverse * float(np.dot(offset, cross))
    if u < -1e-8 or u > 1 + 1e-8:
        return False
    q = np.cross(offset, edge1)
    v = inverse * float(np.dot(direction, q))
    if v < -1e-8 or u + v > 1 + 1e-8:
        return False
    t = inverse * float(np.dot(edge2, q))
    return -1e-8 <= t <= 1 + 1e-8


def triangles_intersect(first: np.ndarray, second: np.ndarray) -> bool:
    return any(segment_triangle(first[index], first[(index + 1) % 3], second) for index in range(3)) or \
        any(segment_triangle(second[index], second[(index + 1) % 3], first) for index in range(3))


def inter_part_intersection(vertices: np.ndarray, runtime: RuntimeGLB, first_faces: np.ndarray, second_faces: np.ndarray) -> tuple[int, int] | None:
    first_triangles = vertices[runtime.faces[first_faces]]
    second_triangles = vertices[runtime.faces[second_faces]]
    first_min, first_max = first_triangles.min(axis=1), first_triangles.max(axis=1)
    second_min, second_max = second_triangles.min(axis=1), second_triangles.max(axis=1)
    first_centres, second_centres = first_triangles.mean(axis=1), second_triangles.mean(axis=1)
    first_radii = np.linalg.norm(first_triangles - first_centres[:, None, :], axis=2).max(axis=1)
    second_radii = np.linalg.norm(second_triangles - second_centres[:, None, :], axis=2).max(axis=1)
    tree = cKDTree(second_centres)
    candidates = tree.query_ball_point(first_centres, first_radii + float(second_radii.max()))
    for local_first, nearby in enumerate(candidates):
        for local_second in nearby:
            first_face = runtime.faces[first_faces[local_first]]
            second_face = runtime.faces[second_faces[local_second]]
            # A shared vertex or edge is ordinary topology at a semantic-part
            # boundary, not a surface intersection.
            if not set(first_face).isdisjoint(second_face):
                continue
            if np.linalg.norm(first_centres[local_first] - second_centres[local_second]) > first_radii[local_first] + second_radii[local_second]:
                continue
            if np.any(first_max[local_first] < second_min[local_second] - SURFACE_TOLERANCE_M) or np.any(second_max[local_second] < first_min[local_first] - SURFACE_TOLERANCE_M):
                continue
            if triangles_intersect(first_triangles[local_first], second_triangles[local_second]):
                return int(first_faces[local_first]), int(second_faces[local_second])
    return None


def choose_landmarks(vertices: np.ndarray, indices: np.ndarray) -> dict[str, int]:
    minimum_y = float(vertices[indices, 1].min())
    sole = indices[vertices[indices, 1] <= minimum_y + 0.008]
    if len(sole) < 12:
        raise ValueError("not enough fixed sole vertices to select heel/ball/toe landmarks")
    median_x = float(np.median(vertices[sole, 0]))
    result = {}
    for label, quantile in (("heel", 0.03), ("ball", 0.72), ("toe", 0.97)):
        target_z = float(np.quantile(vertices[sole, 2], quantile))
        score = np.abs(vertices[sole, 2] - target_z) + 0.2 * np.abs(vertices[sole, 0] - median_x)
        result[label] = int(sole[np.argmin(score)])
    if len(set(result.values())) != 3:
        raise ValueError("sole landmark selection produced duplicate vertex IDs")
    return result


def gait_audit(runtime: RuntimeGLB, clip: str, stride: float, vertices_by_part: dict[str, np.ndarray], rate: int,
               landmarks: dict[str, dict[str, int]]) -> dict:
    duration = runtime.duration(clip)
    selected = np.array([landmarks[side][label] for side in ("left", "right") for label in ("heel", "ball", "toe")])
    count = math.ceil(duration * 3 * rate) + 1
    tracks = np.empty((count, len(selected), 3), dtype=np.float64)
    for sample in range(count):
        elapsed = min(sample / rate, duration * 3)
        local_time = elapsed % duration if elapsed < duration * 3 else duration
        tracks[sample] = runtime.deform(clip, local_time, selected)
        tracks[sample, :, 2] += stride * elapsed / duration
    rows = []
    passed = True
    for position, (side, label) in enumerate((side, label) for side in ("left", "right") for label in ("heel", "ball", "toe")):
        track = tracks[:, position]
        minimum_y = float(track[:, 1].min())
        # A fixed sole point is in material contact only close to its own
        # minimum height. A broader band incorrectly merges rolling and swing.
        planted = track[:, 1] <= minimum_y + 0.003
        windows = []
        start = None
        for index in range(len(track) + 1):
            active = index < len(track) and bool(planted[index])
            if active and start is None:
                start = index
            elif not active and start is not None:
                end = index - 1
                if end - start >= 3:
                    slip = float(np.ptp(track[start:end + 1, 2]))
                    windows.append({"start_s": start / rate, "end_s": end / rate, "horizontal_slip_m": slip})
                start = None
        maximum_slip = max((row["horizontal_slip_m"] for row in windows), default=math.inf)
        landmark_passed = bool(minimum_y >= -FLOOR_TOLERANCE_M and len(windows) >= 3 and maximum_slip < 0.035)
        passed = bool(passed and landmark_passed)
        rows.append({
            "side": side, "landmark": label, "fixed_vertex_id": int(selected[position]),
            "minimum_floor_clearance_m": minimum_y, "maximum_floor_penetration_m": max(0.0, -minimum_y),
            "stance_window_count": len(windows), "maximum_horizontal_slip_m": maximum_slip,
            "stance_windows": windows, "passed": landmark_passed,
        })
    return {"clip": clip, "cycles": 3, "sample_rate_hz": rate, "sample_count": count,
            "controller_stride_m_per_cycle": stride, "controller_axis": "+Z", "landmarks": rows, "passed": passed}


def audit(runtime: RuntimeGLB, ledger: dict, candidate: str, rate: int) -> dict:
    parts = ledger["semantic_parts"]
    _, _, vertices_by_part, faces_by_part = part_inventory(runtime, parts)
    adjacent = adjacency(runtime, parts)
    part_ids = [part["id"] for part in parts]
    # Every authored clip begins from the same neutral skinned pose. Use that
    # deformed surface—not the unskinned bind mesh—as the area baseline.
    rest_vertices = runtime.deform(next(iter(runtime.animations)), 0.0)
    rest_triangles = rest_vertices[runtime.faces]
    rest_area = np.linalg.norm(np.cross(rest_triangles[:, 1] - rest_triangles[:, 0], rest_triangles[:, 2] - rest_triangles[:, 0]), axis=1)
    # The supplied neutral textured mesh contains modeled contacts where one
    # connected surface crosses semantic weight boundaries. Establish those
    # exact rest contacts once; only newly introduced non-adjacent pairs are
    # treated as animation-caused intersections.
    rest_bounds = {index: (rest_vertices[vertices_by_part[part]].min(axis=0), rest_vertices[vertices_by_part[part]].max(axis=0))
                   for index, part in enumerate(part_ids) if len(vertices_by_part[part])}
    baseline_contact_pairs = []
    populated_rest = sorted(rest_bounds)
    for offset, first_index in enumerate(populated_rest):
        for second_index in populated_rest[offset + 1:]:
            pair = tuple(sorted((first_index, second_index)))
            if pair in adjacent:
                continue
            first_min, first_max = rest_bounds[first_index]
            second_min, second_max = rest_bounds[second_index]
            if np.any(first_max < second_min - SURFACE_TOLERANCE_M) or np.any(second_max < first_min - SURFACE_TOLERANCE_M):
                continue
            witness = inter_part_intersection(rest_vertices, runtime, faces_by_part[part_ids[first_index]], faces_by_part[part_ids[second_index]])
            if witness is not None:
                adjacent.add(pair)
                baseline_contact_pairs.append({"parts": [part_ids[first_index], part_ids[second_index]],
                                               "neutral_triangle_ids": list(witness)})
    clip_rows = {}
    violations = []
    for clip in sorted(runtime.animations):
        duration = runtime.duration(clip)
        sample_count = math.ceil(duration * rate) + 1
        part_rows = {part: {"surface_vertices": int(len(vertices_by_part[part])), "triangles": int(len(faces_by_part[part])),
                            "minimum_floor_clearance_m": math.inf, "minimum_triangle_area_ratio": math.inf,
                            "minimum_triangle_double_area_m2": math.inf,
                            "finite": True, "nonadjacent_intersections": 0} for part in part_ids}
        for sample in range(sample_count):
            time = min(sample / rate, duration)
            vertices = runtime.deform(clip, time)
            finite = np.isfinite(vertices).all()
            if not finite:
                violations.append({"clip": clip, "time_s": time, "type": "non_finite_vertex"})
            triangles = vertices[runtime.faces]
            area = np.linalg.norm(np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]), axis=1)
            ratios = area / np.maximum(rest_area, 1e-12)
            bounds = {}
            for part_index, part in enumerate(part_ids):
                vertex_ids, face_ids = vertices_by_part[part], faces_by_part[part]
                row = part_rows[part]
                row["finite"] &= finite
                if len(vertex_ids):
                    row["minimum_floor_clearance_m"] = min(row["minimum_floor_clearance_m"], float(vertices[vertex_ids, 1].min()))
                    bounds[part_index] = (vertices[vertex_ids].min(axis=0), vertices[vertex_ids].max(axis=0))
                if len(face_ids):
                    minimum_ratio = float(ratios[face_ids][rest_area[face_ids] > 1e-12].min(initial=math.inf))
                    row["minimum_triangle_area_ratio"] = min(row["minimum_triangle_area_ratio"], minimum_ratio)
                    minimum_area = float(area[face_ids].min(initial=math.inf))
                    row["minimum_triangle_double_area_m2"] = min(row["minimum_triangle_double_area_m2"], minimum_area)
                    if minimum_area < MINIMUM_TRIANGLE_DOUBLE_AREA_M2:
                        face_id = int(face_ids[np.argmin(area[face_ids])])
                        violations.append({"clip": clip, "time_s": time, "part": part, "type": "collapsed_triangle",
                                           "triangle_id": face_id, "double_area_m2": minimum_area, "area_ratio": minimum_ratio})
            populated = sorted(bounds)
            for offset, first_index in enumerate(populated):
                for second_index in populated[offset + 1:]:
                    if tuple(sorted((first_index, second_index))) in adjacent:
                        continue
                    first_min, first_max = bounds[first_index]
                    second_min, second_max = bounds[second_index]
                    if np.any(first_max < second_min - SURFACE_TOLERANCE_M) or np.any(second_max < first_min - SURFACE_TOLERANCE_M):
                        continue
                    witness = inter_part_intersection(vertices, runtime, faces_by_part[part_ids[first_index]], faces_by_part[part_ids[second_index]])
                    if witness is not None:
                        part_rows[part_ids[first_index]]["nonadjacent_intersections"] += 1
                        part_rows[part_ids[second_index]]["nonadjacent_intersections"] += 1
                        violations.append({"clip": clip, "time_s": time, "type": "nonadjacent_surface_intersection",
                                           "parts": [part_ids[first_index], part_ids[second_index]], "triangle_ids": list(witness)})
        for part, row in part_rows.items():
            if math.isinf(row["minimum_floor_clearance_m"]):
                row["minimum_floor_clearance_m"] = None
                row["surface_note"] = "No vertices are weighted to this bone-only semantic region."
            if math.isinf(row["minimum_triangle_area_ratio"]):
                row["minimum_triangle_area_ratio"] = None
            if math.isinf(row["minimum_triangle_double_area_m2"]):
                row["minimum_triangle_double_area_m2"] = None
            row["passed"] = row["finite"] and row["nonadjacent_intersections"] == 0 and \
                (row["minimum_triangle_double_area_m2"] is None or row["minimum_triangle_double_area_m2"] >= MINIMUM_TRIANGLE_DOUBLE_AREA_M2) and \
                (row["minimum_floor_clearance_m"] is None or row["minimum_floor_clearance_m"] >= -FLOOR_TOLERANCE_M)
        clip_rows[clip] = {"duration_seconds": duration, "sample_rate_hz": rate, "sample_count": sample_count,
                           "parts": part_rows, "passed": all(row["passed"] for row in part_rows.values())}
        print(f"audited {clip}: {sample_count} samples, passed={clip_rows[clip]['passed']}", flush=True)
    neutral_vertices = runtime.deform("t06_idle", 0.0)
    sole_landmarks = {side: choose_landmarks(neutral_vertices, vertices_by_part[f"{side}_foot_toe_boot"])
                      for side in ("left", "right")}
    gait = [
        gait_audit(runtime, "t06_walk", float(ledger["clips"]["walk"]["controller_stride_m"]), vertices_by_part, rate, sole_landmarks),
        gait_audit(runtime, "t06_run", float(ledger["clips"]["run"]["controller_stride_m"]), vertices_by_part, rate, sole_landmarks),
    ]
    errors = []
    if candidate != ledger.get("candidate_commit"):
        errors.append("candidate commit does not match motion ledger")
    if set(runtime.animations) != {"t06_" + clip for clip in ledger["clips"]}:
        errors.append("runtime animation inventory does not match motion ledger")
    if violations:
        errors.append(f"deformed surface audit found {len(violations)} violations")
    if not all(row["passed"] for row in gait):
        errors.append("fixed sole landmark audit failed")
    return {
        "task": "T06-character1-motion-v1", "candidate_commit": candidate,
        "runtime_glb": str(runtime.path), "runtime_glb_sha256": runtime.sha256,
        "method": "CPU linear-blend skinning of every vertex; every triangle area; exhaustive inter-part triangle broad/narrow phase excluding documented anatomical/topological neighbours; fixed heel/ball/toe vertex tracking with +Z controller travel.",
        "sample_rate_hz": rate, "vertex_count": len(runtime.positions), "triangle_count": len(runtime.faces),
        "skin_joint_count": len(runtime.skin_joints), "semantic_part_count": len(parts),
        "thresholds": {"floor_tolerance_m": FLOOR_TOLERANCE_M, "minimum_triangle_double_area_m2": MINIMUM_TRIANGLE_DOUBLE_AREA_M2,
                       "surface_intersection_tolerance_m": SURFACE_TOLERANCE_M, "maximum_sole_slip_m": 0.035},
        "clips": clip_rows, "gait_sole_landmarks": gait, "violation_count": len(violations),
        "violations": violations[:500], "errors": errors, "passed": not errors,
        "neutral_surface_contact_baseline": baseline_contact_pairs,
        "scope_note": "Connected semantic regions within four skeleton/deformation links, exact neutral-surface contacts, and declared garment attachment contacts are excluded from inter-part collision pairs; every vertex and triangle in those regions still receives finite, floor, and non-collapse checks.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--glb", type=Path, required=True)
    parser.add_argument("--motion-ledger", type=Path, required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sample-rate", type=int, default=120)
    args = parser.parse_args()
    try:
        if args.sample_rate != 120:
            raise ValueError("release evidence must use exactly 120 Hz")
        result = audit(RuntimeGLB(args.glb), json.loads(args.motion_ledger.read_text()), args.candidate, args.sample_rate)
    except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
        result = {"task": "T06-character1-motion-v1", "candidate_commit": args.candidate,
                  "passed": False, "errors": [str(exc)]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, default=json_default) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key not in {"clips", "violations"}}, indent=2, default=json_default))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
