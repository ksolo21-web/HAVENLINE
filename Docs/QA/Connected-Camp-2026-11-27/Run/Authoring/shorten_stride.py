"""Shorten a toe-off corrected run while fitting each tread’s world-relative travel.

Usage: python shorten_stride.py recovery.glb build10.glb
The game controller uses the same contracted native speed, 4.63 × 0.77 m/s.
"""

import sys, numpy as np
from pathlib import Path
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter1d
from outsole import model_info
from scipy.spatial.transform import Rotation

model, phase, translation, rotation, scale, world, sole = model_info(sys.argv[1])
original = translation.copy(), rotation.copy(), scale.copy()
rate = 0.77
duration = 44 / 60


def frame_rotation(world, node):
    mats = world[node, :, :3, :3]
    return Rotation.from_matrix(mats / np.linalg.norm(mats, axis=1)[:, None, :])


def align(first, second):
    a = first / np.linalg.norm(first, axis=1)[:, None]
    b = second / np.linalg.norm(second, axis=1)[:, None]
    axis = np.cross(a, b)
    length = np.linalg.norm(axis, axis=1)
    angle = np.arctan2(length, np.einsum("ij,ij->i", a, b))
    return Rotation.from_rotvec(
        axis * angle[:, None] / np.maximum(length[:, None], 1e-12)
    )


def smooth(a, b, leg_phase):
    fraction = np.clip((leg_phase - a) / (b - a), 0, 1)
    return fraction * fraction * (3 - 2 * fraction)


mesh = model.document["meshes"][0]["primitives"][0]["attributes"]
skin = model.document["skins"][0]
base = model.accessor(mesh["POSITION"])
inverse_bind = (
    model.accessor(skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
)
feet = {}
candidate_elevations = []
for side, shift in [("L", 0), ("R", 0.5)]:
    leg_phase = (phase + shift) % 1
    hip, knee, ankle = [
        world[model.names[n + "." + side], :, :3, 3] for n in ("Thigh", "Shin", "Foot")
    ]
    old = ankle - hip
    target = old.copy()
    target[:, 2] *= rate
    forward_offset = target[:, 2] - old[:, 2]
    mask = (base[:, 1] < 0.048) & (base[:, 0] * (1 if side == "L" else -1) > 0)
    tread_vertices = base[mask]
    joints = model.accessor(mesh["JOINTS_0"])[mask]
    weights = model.accessor(mesh["WEIGHTS_0"])[mask]
    tread_homogeneous = np.c_[tread_vertices, np.ones(len(tread_vertices))]
    tread_positions = np.stack(
        [
            np.einsum(
                "nvij,nj,nv->ni",
                (world[skin["joints"], frame_index] @ inverse_bind)[joints, :3, :],
                tread_homogeneous,
                weights,
            )
            for frame_index in range(240)
        ]
    )
    # Surround central stance with preceding presentation and following breakover.
    offset = np.round(leg_phase[:240] * 240).astype(int) % 240
    order = np.argsort(offset)
    tread_positions = tread_positions[order]
    sole_y = tread_positions[:, :, 1].min(1)
    # Work in two copies of the first fifth of the cycle (straddles zero).
    center = 251
    length = 480
    extended = np.concatenate((tread_positions, tread_positions))
    correction = np.zeros((length, 2))
    for frame_index in range(210, 332):
        h = np.minimum(extended[frame_index, :, 1], extended[frame_index + 1, :, 1])
        weight = np.exp(-np.clip((h - h.min()) / 0.004, 0, 10))
        increment = extended[frame_index + 1] - extended[frame_index]
        displacement = np.average(increment[:, [0, 2]], axis=0, weights=weight)
        correction[frame_index + 1] = (
            correction[frame_index]
            + np.array([0.0, -4.63 * rate * duration / 240])
            - displacement
        )
    correction -= correction[center]
    correction[:, 1] += forward_offset[order[center % 240]]
    correction = gaussian_filter1d(correction, 0.75, axis=0)
    spread = np.where(leg_phase > 0.70, leg_phase - 1, leg_phase)
    contact_weight = smooth(-0.12, -0.04, spread) * (1 - smooth(0.205, 0.345, spread))
    indices = np.round((np.clip(spread, -0.038, 0.216) + 1) * 240).astype(int)
    forward_offset = (
        forward_offset * (1 - contact_weight) + correction[indices, 1] * contact_weight
    )
    lateral_offset = correction[indices, 0] * contact_weight
    target[:, 2] = old[:, 2] + forward_offset
    target[:, 0] = old[:, 0] + lateral_offset
    # Preserve loading angles and toe-off by allowing the hips to rise above a shorter step.
    requested = (
        np.sqrt(
            np.maximum(
                0.03, (old * old).sum(axis=1) - (target[:, [0, 2]] ** 2).sum(axis=1)
            )
        )
        + old[:, 1]
    )
    feet[side] = (hip, knee, ankle, target - old)
    confidence = smooth(-0.14, -0.05, spread) * (1 - smooth(0.28, 0.41, spread))
    candidate_elevations.append((requested, confidence))
weight_sum = sum(b for _, b in candidate_elevations)
rise = sum(a * b for a, b in candidate_elevations) / np.maximum(0.005, weight_sum)
rise = gaussian_filter1d(rise[:-1], 2.0, mode="wrap")
rise = np.r_[rise, rise[0]]
# Include both limbs when setting the reachable pelvis limit, including the incoming heel.
limit = []
for hip, knee, ankle, offset in feet.values():
    planar = (ankle + offset - hip)[:, [0, 2]]
    thigh_length = np.linalg.norm(knee - hip, axis=1)
    shin_length = np.linalg.norm(ankle - knee, axis=1)
    reach_squared = (
        thigh_length**2
        + shin_length**2
        + 2 * thigh_length * shin_length * np.cos(np.deg2rad(12))
    )
    bound = (
        np.sqrt(np.maximum(0.01, reach_squared - np.sum(planar**2, axis=1)))
        + (ankle - hip)[:, 1]
    )
    limit.append(bound)
rise = np.minimum(rise, np.minimum(*limit))
rise = gaussian_filter1d(rise[:-1], 1.05, mode="wrap")
rise = np.r_[rise, rise[0]]
pelvis = model.names["Pelvis"]
extra = np.c_[np.zeros(len(phase)), rise, np.zeros(len(phase))]
translation[pelvis] += np.linalg.solve(
    world[model.parent[pelvis], :, :3, :3], extra[:, :, None]
)[:, :, 0]
for side in ("L", "R"):
    hip, knee, ankle, offset = feet[side]
    upper_bone, lower_bone, boot = [
        model.names[n + "." + side] for n in ["Thigh", "Shin", "Foot"]
    ]
    hip_target = hip + extra
    ankle_target = ankle + offset
    # During recovery keep the fold of the previous anatomical solve. The bottom
    # of the boot bounds downward movement as it approaches touchdown.
    leg_phase = (phase + (0 if side == "L" else 0.5)) % 1
    clear = sole[side][0]
    full = np.linalg.norm(ankle - hip, axis=1)
    ideal = hip_target[:, 1] - np.sqrt(
        np.maximum(
            0.012, full**2 - np.sum((ankle_target - hip_target)[:, [0, 2]] ** 2, axis=1)
        )
    )
    weight = smooth(0.24, 0.42, leg_phase) * (1 - smooth(0.78, 0.92, leg_phase))
    vertical_offset = np.clip(
        (ideal - ankle_target[:, 1]) * weight, -np.maximum(0, clear - 0.022), 0.030
    )
    ankle_target[:, 1] += vertical_offset
    axis = ankle_target - hip_target
    hip_to_ankle = np.linalg.norm(axis, axis=1)
    unit = axis / hip_to_ankle[:, None]
    thigh_length = np.linalg.norm(knee - hip, axis=1)
    shin_length = np.linalg.norm(ankle - knee, axis=1)
    normal = np.cross(knee - hip, ankle - hip)
    bend = np.cross(unit, normal)
    bend /= np.linalg.norm(bend, axis=1)[:, None]
    hip_to_ankle = np.minimum(hip_to_ankle, thigh_length + shin_length - 0.00012)
    knee_projection = (
        thigh_length * thigh_length
        - shin_length * shin_length
        + hip_to_ankle * hip_to_ankle
    ) / (2 * hip_to_ankle)
    knee_target = (
        hip_target
        + unit * knee_projection[:, None]
        + bend
        * np.sqrt(
            np.maximum(
                0.000001,
                thigh_length * thigh_length - knee_projection * knee_projection,
            )
        )[:, None]
    )
    rotation[upper_bone] = (
        frame_rotation(world, model.parent[upper_bone]).inv()
        * align(knee - hip, knee_target - hip_target)
        * frame_rotation(world, upper_bone)
    ).as_quat()
    adjusted_world = model.world(translation, rotation, scale)
    rotation[lower_bone] = (
        frame_rotation(adjusted_world, model.parent[lower_bone]).inv()
        * align(ankle - knee, ankle_target - knee_target)
        * frame_rotation(world, lower_bone)
    ).as_quat()
    adjusted_world = model.world(translation, rotation, scale)
    boot_local = (
        frame_rotation(adjusted_world, model.parent[boot]).inv()
        * frame_rotation(world, boot)
    ).as_euler("xyz", degrees=True)
    boot_local[:, 0] = np.clip(boot_local[:, 0], -131.0, -34.5)
    rotation[boot] = Rotation.from_euler("xyz", boot_local, degrees=True).as_quat()


def add(a, accessor_type):
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
        type=accessor_type,
    )
    if accessor_type == "SCALAR":
        acc.update(min=[float(a.min())], max=[float(a.max())])
    model.document["accessors"].append(acc)
    return len(model.document["accessors"]) - 1


model.binary = bytearray(model.binary)
data = next(a for a in model.document["animations"] if a["name"] == "FieldRun")
time_accessor = add(phase * duration, "SCALAR")
for channel in data["channels"]:
    target = channel["target"]
    path = target["path"]
    node = target["node"]
    component = ["translation", "rotation", "scale"].index(path)
    values = (translation, rotation, scale)[component][node].copy()
    if np.max(abs(values - original[component][node])) < 1e-9:
        continue
    if path == "rotation":
        for key_index in range(1, len(values)):
            if values[key_index - 1] @ values[key_index] < 0:
                values[key_index] *= -1
    sampler = data["samplers"][channel["sampler"]]
    sampler["input"] = time_accessor
    sampler["output"] = add(values, "VEC4" if path == "rotation" else "VEC3")
model.document["buffers"][0]["byteLength"] = len(model.binary)
model.write(sys.argv[2])
