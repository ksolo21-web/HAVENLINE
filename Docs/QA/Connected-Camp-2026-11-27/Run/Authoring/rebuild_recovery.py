"""Rebuild the compact FieldRun clip using the Build 9 source and the measured right-leg marker cohort.

Usage: OPENBLAS_NUM_THREADS=1 python rebuild_recovery.py build9.glb recovery.glb
The upper body, weights, materials, original compact mesh, and other clips use the input asset.
"""

import sys, json
from pathlib import Path
import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.spatial.transform import Rotation as R


from outsole import model_info

model, phase, translations, rotations, scales, world, sole = model_info(sys.argv[1])
original = translations.copy(), rotations.copy(), scales.copy()
clip_seconds = 44 / 60


def world_rotation(world, index_i):
    return R.from_matrix(
        world[index_i, :, :3, :3]
        / np.linalg.norm(world[index_i, :, :3, :3], axis=1)[:, None, :]
    )


def sagittal_rotation(a):
    return R.from_rotvec(np.array([1, 0, 0]) * np.radians(a)[:, None])


def curve(leg_phase, keys, value):
    return PchipInterpolator(keys, value)(leg_phase)


def smooth(a, b, x):
    fraction = np.clip((x - a) / (b - a), 0, 1)
    return fraction * fraction * (3 - 2 * fraction)


# Follow each release with an airborne rise. Both boots are evaluated against the physical snow plane.
half_phase = phase % 0.5
arc = 0.062 * np.sin(np.pi * np.clip((half_phase - 0.178) / 0.285, 0.0, 1.0)) ** 2
rise = np.stack((np.zeros(len(phase)), arc, np.zeros(len(phase))), axis=1)
pelvis = model.names["Pelvis"]
translations[pelvis] += np.linalg.solve(
    world[model.parent[pelvis], :, :3, :3], rise[:, :, None]
)[:, :, 0]
for side, shift in [("L", 0), ("R", 0.5)]:
    leg_phase = (phase + shift) % 1
    thigh, shin, foot, toe_joint = [
        model.names[sample_count + "." + side]
        for sample_count in ["Thigh", "Shin", "Foot", "Toe"]
    ]
    hip, knee, ankle = [world[index_i, :, :3, 3] for index_i in (thigh, shin, foot)]
    sole_height, contact, heel, toe = sole[side]
    thigh_pitch = np.degrees(np.arctan2((knee - hip)[:, 2], -(knee - hip)[:, 1]))
    # Vary the three signed sagittal angles together. A short leg inside a broad
    # boot cannot reproduce adult marker positions exactly at the field speed.
    sample = json.loads(
        (Path(__file__).resolve().parents[1] / "Human-running-markers.json").read_text()
    )["median"]
    markers = lambda index: np.interp(leg_phase, np.arange(101) / 100, sample[index])
    goal_angle = markers("thigh_marker_pitch_degrees")
    goal_z = markers("heel_forward_of_pelvis_m") * 0.60
    ref_phase = np.interp(
        leg_phase,
        [0, 0.20, 0.27, 0.36, 0.47, 0.60, 0.72, 0.90, 1],
        [0, 0.31, 0.38, 0.455, 0.52, 0.615, 0.72, 0.90, 1],
    )
    goal_y = np.interp(ref_phase, np.arange(101) / 100, sample["heel_y_m"]) * 0.56
    keep_height = curve(
        leg_phase,
        [
            0,
            0.18,
            0.21,
            0.25,
            0.30,
            0.35,
            0.40,
            0.45,
            0.50,
            0.56,
            0.63,
            0.70,
            0.76,
            0.83,
            0.90,
            1,
        ],
        [
            0,
            0,
            0.10,
            0.145,
            0.180,
            0.20,
            0.210,
            0.225,
            0.242,
            0.275,
            0.302,
            0.23,
            0.16,
            0.045,
            0,
            0,
        ],
    )
    goal_roll = markers("heel_above_forefoot_m") * 0.94
    active = smooth(0.19, 0.34, leg_phase) * (1 - smooth(0.90, 0.988, leg_phase))
    mesh = model.document["meshes"][0]["primitives"][0]["attributes"]
    skin = model.document["skins"][0]
    vertices = model.accessor(mesh["POSITION"])
    mask = (vertices[:, 1] < 0.048) & (vertices[:, 0] * (1 if side == "L" else -1) > 0)
    joint_indices = model.accessor(mesh["JOINTS_0"])[mask]
    weights = model.accessor(mesh["WEIGHTS_0"])[mask]
    rest_homogeneous = np.c_[vertices[mask], np.ones(mask.sum())]
    inverse_bind = (
        model.accessor(skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    )
    tread_offsets = np.stack(
        [
            np.einsum(
                "nvij,nj,nv->ni",
                (world[skin["joints"], index_i] @ inverse_bind)[joint_indices, :3, :],
                rest_homogeneous,
                weights,
            )
            - ankle[index_i]
            for index_i in range(len(phase))
        ]
    )
    # Sample all vertices on the lower convex outline of each boot. It remains
    # valid as the sole rolls through the contact region, including the toe.
    from scipy.spatial import ConvexHull

    convex_indices = np.unique(
        np.concatenate([ConvexHull(a[:, 1:]).vertices for a in tread_offsets])
    )
    tread_offsets = tread_offsets[:, convex_indices]
    upper_vec = knee - hip
    lower_vec = ankle - knee

    def turn(vec, rad):
        cosine = np.cos(rad)
        sine = np.sin(rad)
        return np.stack(
            (
                vec[:, 0],
                cosine * vec[:, 1] - sine * vec[:, 2],
                sine * vec[:, 1] + cosine * vec[:, 2],
            ),
            axis=1,
        )

    old_dorsi = R.from_quat(rotations[foot]).as_euler("xyz", degrees=True)[:, 0]
    sample_count = len(phase)
    easing = active
    from scipy.optimize import least_squares
    from scipy.sparse import lil_matrix

    def residual(unknown):
        # Fit three sagittal rotations per phase, with full-sole clearance and bounded ankle flex.
        # First and second differences suppress changes of direction at contact transitions.
        params = unknown.reshape(-1, 3)
        weighted_delta = params * easing[:, None]
        weighted_delta[:, 2] *= smooth(0.34, 0.50, leg_phase)
        thigh_delta, flex_delta, boot_delta = weighted_delta.T
        ankle_new = (
            hip
            + rise
            + turn(upper_vec, -np.radians(thigh_delta))
            + turn(lower_vec, np.radians(flex_delta - thigh_delta))
        )
        heel_patch = ankle_new + turn(heel - ankle, np.radians(boot_delta))
        toe_patch = ankle_new + turn(toe - ankle, np.radians(boot_delta))
        lowest = ankle_new[:, 1] + (
            np.cos(np.radians(boot_delta))[:, None] * tread_offsets[:, :, 1]
            - np.sin(np.radians(boot_delta))[:, None] * tread_offsets[:, :, 2]
        ).min(1)
        swing_influence = (0.64 + 0.36 * smooth(0.45, 0.65, leg_phase)) * active
        lift = np.minimum(
            sole_height,
            0.037
            - 0.014
            * smooth(0.76, 0.82, leg_phase)
            * (1 - smooth(0.88, 0.95, leg_phase)),
        )
        ankle_flex = old_dorsi + boot_delta + thigh_delta - flex_delta
        terms = [
            swing_influence * (thigh_pitch + thigh_delta - goal_angle) / 7.0
            + np.minimum(0, thigh_pitch + thigh_delta + 29.0) * active / 1.5,
            swing_influence * ((heel_patch - hip)[:, 2] - goal_z) / 0.043,
            swing_influence * (heel_patch[:, 1] - goal_y) / 0.045
            + np.minimum(0, heel_patch[:, 1] - keep_height) / 0.0035,
            swing_influence * (heel_patch[:, 1] - toe_patch[:, 1] - goal_roll) / 0.05,
            flex_delta
            / (
                4.5
                + 5.5
                * smooth(0.205, 0.28, leg_phase)
                * (1 - smooth(0.49, 0.56, leg_phase))
            ),
            np.minimum(0, lowest - lift) / 0.0012,
            np.maximum(0, lowest - sole_height - 0.006)
            * (1 - smooth(0.008, 0.020, sole_height))
            / 0.0025,
            np.minimum(0, ankle_flex + 130.0) / 1.5,
            np.maximum(0, ankle_flex + 36.0) / 1.5,
        ]
        terms.extend(
            [params[:, index_i] / [75.0, 35.0, 65.0][index_i] for index_i in range(3)]
        )
        terms.extend(
            [
                (np.roll(weighted_delta[:, index_i], -1) - weighted_delta[:, index_i])
                / [3.2, 1.5, 3.6][index_i]
                for index_i in range(3)
            ]
        )
        terms.extend(
            [
                (
                    np.roll(weighted_delta[:, index_i], -1)
                    + np.roll(weighted_delta[:, index_i], 1)
                    - 2 * weighted_delta[:, index_i]
                )
                / [0.28, 0.17, 0.35][index_i]
                for index_i in range(3)
            ]
        )
        return np.stack(terms, axis=1).ravel()

    # The Jacobian only couples adjacent phases, including the loop seam.
    count = 18
    pattern = lil_matrix((sample_count * count, sample_count * 3), dtype=int)
    for index_i in range(sample_count):
        for row in range(count):
            if row < 12:
                pattern[index_i * count + row, index_i * 3 : index_i * 3 + 3] = 1
            elif row < 15:
                for index in [index_i, (index_i + 1) % sample_count]:
                    pattern[index_i * count + row, index * 3 + row - 12] = 1
            else:
                for index in [
                    (index_i - 1) % sample_count,
                    index_i,
                    (index_i + 1) % sample_count,
                ]:
                    pattern[index_i * count + row, index * 3 + row - 15] = 1
    solution = least_squares(
        residual,
        np.zeros((sample_count, 3)).ravel(),
        jac_sparsity=pattern.tocsr(),
        max_nfev=130,
        ftol=0.000003,
        xtol=0.00002,
    )
    delta = solution.x.reshape(sample_count, 3) * easing[:, None]
    delta[:, 2] *= smooth(0.34, 0.50, leg_phase)
    thigh_delta, flex_delta, boot_delta = delta.T
    print(side, solution.nfev, solution.cost, delta.min(0), delta.max(0), flush=True)
    rotations[thigh] = (
        world_rotation(world, model.parent[thigh]).inv()
        * sagittal_rotation(-thigh_delta)
        * world_rotation(world, thigh)
    ).as_quat()
    neww = model.world(translations, rotations, scales)
    rotations[shin] = (
        world_rotation(neww, model.parent[shin]).inv()
        * sagittal_rotation(flex_delta - thigh_delta)
        * world_rotation(world, shin)
    ).as_quat()
    neww = model.world(translations, rotations, scales)
    rotations[foot] = (
        world_rotation(neww, model.parent[foot]).inv()
        * sagittal_rotation(boot_delta)
        * world_rotation(world, foot)
    ).as_quat()


def add(a, toe_patch):
    # Append only changed animation curves. Original geometry and material buffers stay byte-identical.
    a = np.asarray(a, dtype="<f4")
    model.binary.extend(b"\0" * (-len(model.binary) % 4))
    model.document["bufferViews"].append(
        dict(buffer=0, byteOffset=len(model.binary), byteLength=a.nbytes)
    )
    model.binary.extend(a.tobytes())
    acc = dict(
        bufferView=len(model.document["bufferViews"]) - 1,
        componentType=5126,
        count=len(a),
        type=toe_patch,
    )
    if toe_patch == "SCALAR":
        acc.update(min=[float(a.min())], max=[float(a.max())])
    model.document["accessors"].append(acc)
    return len(model.document["accessors"]) - 1


model.binary = bytearray(model.binary)
data = next(a for a in model.document["animations"] if a["name"] == "FieldRun")
time_accessor = add(phase * clip_seconds, "SCALAR")
for channel in data["channels"]:
    target = channel["target"]
    path = target["path"]
    node = target["node"]
    idx = ["translation", "rotation", "scale"].index(path)
    values = (translations, rotations, scales)[idx][node].copy()
    if np.max(abs(values - original[idx][node])) < 1e-9:
        continue
    if path == "rotation":
        for index_j in range(1, len(values)):
            if values[index_j - 1] @ values[index_j] < 0:
                values[index_j] *= -1
    sampler = data["samplers"][channel["sampler"]]
    sampler["input"] = time_accessor
    sampler["output"] = add(values, "VEC4" if path == "rotation" else "VEC3")
model.document["buffers"][0]["byteLength"] = len(model.binary)
model.write(sys.argv[2])
