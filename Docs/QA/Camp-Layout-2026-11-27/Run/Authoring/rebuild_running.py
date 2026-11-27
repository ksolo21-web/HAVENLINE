"""Reshape loading, push-off and heel recovery on the 18617 model, holding the floor-space soles."""

import sys
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from gltf_pose import Model
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter1d
import json

if len(sys.argv) != 3:
    raise SystemExit(
        "Usage: python rebuild_running.py BUILD8_CHARACTER.glb NEW_CHARACTER.glb"
    )
source, destination = sys.argv[1:3]
model = Model(source)
duration = 44 / 60
cycle = np.linspace(0, 1, 241)
frame_count = len(cycle)
joints_by_name = model.names
translations, rotations, scales = model.samples("FieldRun", cycle * duration)
poses = model.world(translations, rotations, scales)
base = (translations.copy(), rotations.copy(), scales.copy())


def current_poses():
    return model.world(translations, rotations, scales)


def unit(vector):
    return vector / np.maximum(np.linalg.norm(vector, axis=-1, keepdims=True), 1.0e-8)


def global_rotation(mat, i):
    return Rotation.from_matrix(
        mat[i, :, :3, :3] / np.linalg.norm(mat[i, :, :3, :3], axis=1)[:, None, :]
    )


def set_global_rotation(i, q):
    rotations[i] = (
        global_rotation(current_poses(), model.parent[i]).inv() * q
    ).as_quat()


def align(a, b):
    a, b = unit(a), unit(b)
    return Rotation.from_quat(np.c_[np.cross(a, b), 1 + (a * b).sum(1)])


def smooth(a, b, x):
    z = np.clip((x - a) / (b - a), 0, 1)
    return z * z * (3 - 2 * z)


def loop_curve(cycle, phase_keys, y):
    curve = PchipInterpolator(
        np.r_[np.array(phase_keys[:-1]) - 1, phase_keys, np.array(phase_keys[1:]) + 1],
        np.r_[y[:-1], y, y[1:]],
    )
    return curve(cycle)


motion_capture = json.loads(
    (Path(__file__).resolve().parent.parent / "Human-running-data.json").read_text()
)["median"]
pelvis = joints_by_name["Pelvis"]
support_offsets = []
joints = {}
pelvis_limits = []
# Keep the genuine stance sole in world positions. The pelvis rises enough
# to remove the sharp early squat; its low point now comes later under load.
for side, o in [("L", 0.0), ("R", 0.5)]:
    q = (cycle + o) % 1
    swing_phase = loop_curve(
        q,
        [0, 0.223, 0.31, 0.42, 0.51, 0.615, 0.677, 0.76, 0.88, 0.966, 1],
        [0, 0.223, 0.300, 0.37, 0.43, 0.53, 0.594, 0.698, 0.86, 0.966, 1],
    )
    swing_phase = q + 0.50 * (swing_phase - q) * smooth(0.225, 0.306, q) * (
        1 - smooth(0.898, 0.963, q)
    )
    sample_phase = (swing_phase - o) % 1
    t = sample_phase.copy()
    t[-1] = t[0]
    sampled_positions, sampled_rotations, sampled_scales = model.samples(
        "FieldRun", t * duration
    )
    sampled_poses = model.world(sampled_positions, sampled_rotations, sampled_scales)
    k = [joints_by_name[x + "." + side] for x in ["Thigh", "Shin", "Foot", "Toe"]]
    thigh, shin, foot, toe = k
    target = sampled_poses[foot, :, :3, 3].copy()
    # Heel tucks smoothly as the thigh comes forward, keeping the airborne shoe close to the hip.
    heel = smooth(0.34, 0.52, q) * (1 - smooth(0.63, 0.82, q))
    target[:, 1] += 0.024 * heel
    target[:, 2] -= 0.015 * heel
    hip, knee, ankle = (poses[idx, :, :3, 3] for idx in k[:3])
    thigh_length = np.linalg.norm(knee - hip, axis=1)
    shin_length = np.linalg.norm(ankle - knee, axis=1)
    # Short-limbed anatomy needs less push-off travel than a full-sized adult.
    # Measure actual cuff/ankle rather than projecting a designed unit skeleton.
    strike = (q + 0.018) % 1
    humanphase = np.interp(strike, [0, 0.15, 0.271, 0.50, 1], [0, 0.15, 0.35, 0.56, 1])
    ang = np.radians(
        np.interp(humanphase, np.arange(101) / 100, motion_capture["RkneeAngZ45"])
    )
    required_reach_squared = (
        thigh_length**2 + shin_length**2 + 2 * thigh_length * shin_length * np.cos(ang)
    )
    dy = np.sqrt(
        np.maximum(
            required_reach_squared - np.sum((target - hip)[:, [0, 2]] ** 2, axis=1),
            0.0025,
        )
    )
    correction = target[:, 1] + dy - hip[:, 1]
    weight = (1 - smooth(0.225, 0.267, strike)) + smooth(0.952, 0.988, strike)
    support_offsets.append((correction, weight))
    # Reserve a measurable bend at touchdown instead of allowing the solver
    # to touch its kinematic limit at the supporting leg or the landing leg.
    limit = (
        thigh_length**2
        + shin_length**2
        + 2 * thigh_length * shin_length * np.cos(np.radians(14.0))
        - np.sum((target - hip)[:, [0, 2]] ** 2, axis=1)
    )
    pelvis_limits.append(target[:, 1] + np.sqrt(np.maximum(0.0025, limit)) - hip[:, 1])
    # Heel/boot orientation, the toes and all original fitted hardware advance
    # through the same instantaneous swing phase as the actual ankle.
    for key in joints_by_name:
        if key.endswith("." + side) and (
            key.startswith("Boot") or key.startswith("Toe.")
        ):
            idx = joints_by_name[key]
            translations[idx] = sampled_positions[idx]
            rotations[idx] = sampled_rotations[idx]
            scales[idx] = sampled_scales[idx]
    mesh = model.document["meshes"][0]["primitives"][0]["attributes"]
    meshpos = model.accessor(mesh["POSITION"]).copy()
    mask = (meshpos[:, 1] < 0.045) & (meshpos[:, 0] * (1 if side == "L" else -1) > 0)
    skin = model.document["skins"][0]
    inverse_bind = (
        model.accessor(skin["inverseBindMatrices"])
        .copy()
        .reshape(-1, 4, 4)
        .transpose(0, 2, 1)
    )
    joint_indices = model.accessor(mesh["JOINTS_0"])[mask]
    joint_weights = model.accessor(mesh["WEIGHTS_0"])[mask]
    vertices = np.c_[meshpos[mask], np.ones(mask.sum())]
    low = []
    for ii in range(frame_count):
        palette = (sampled_poses[skin["joints"], ii] @ inverse_bind)[:, :3, :]
        low.append(
            np.einsum(
                "nvij,nj,nv->ni", palette[joint_indices], vertices, joint_weights
            )[:, 1].min()
        )
    joints[side] = (
        k,
        target,
        global_rotation(sampled_poses, foot),
        np.array(low) - sampled_poses[foot, :, 1, 3],
        q,
    )
pelvis_offset = np.sum(
    [np.clip(v, -0.017, 0.060) * w for v, w in support_offsets], axis=0
)
c = gaussian_filter1d(pelvis_offset[:-1], 4.5, mode="wrap")
c = np.r_[c, c[0]]
for ceiling in pelvis_limits:
    gap = ceiling - c
    c += np.minimum(0.0, gap) - 0.002 * np.log1p(np.exp(-abs(gap) / 0.002))
parent_basis = poses[model.parent[pelvis], :, :3, :3]
translations[pelvis] += np.linalg.solve(
    parent_basis, np.c_[0 * c, c, 0 * c][:, :, None]
)[:, :, 0]
for s, (k, target, boot, sole_offset, phase) in joints.items():
    thigh, shin, foot, toe = k
    poses = current_poses()
    hip, knee, ankle = (poses[idx, :, :3, 3] for idx in k[:3])
    # Reconstruct the whole free-flight hinge trajectory from marker data, including
    # the slow initial folding and brief late extension. Keep the loaded sole untouched.
    upper = np.linalg.norm(knee - hip, axis=1)
    lower = np.linalg.norm(ankle - knee, axis=1)
    ray = target - hip
    curve_phase = (phase + 0.010) % 1
    theta = np.interp(curve_phase, np.arange(101) / 100, motion_capture["RkneeAngZ45"])
    reach = np.sqrt(upper**2 + lower**2 + 2 * upper * lower * np.cos(np.radians(theta)))
    profile = smooth(0.258, 0.359, phase) * (1 - smooth(0.864, 0.974, phase))
    dist = np.linalg.norm(ray, axis=1)
    reach_adjustment = (reach - dist) * profile
    candidate = target + unit(ray) * reach_adjustment[:, None]
    # The rear boot cannot grow through the snow when its recovering knee is
    # straighter. Preserve its release clearance; use available rear reach instead.
    floor = np.minimum(target[:, 1] + sole_offset, 0.059) - sole_offset
    clipped = candidate[:, 1] < floor
    candidate[:, 1] = np.maximum(candidate[:, 1], floor)
    rem = np.maximum(
        0.0,
        (dist + reach_adjustment) ** 2
        - (candidate[:, 1] - hip[:, 1]) ** 2
        - (candidate[:, 0] - hip[:, 0]) ** 2,
    )
    rear = ray[:, 2] < -0.04
    candidate[clipped & rear, 2] = hip[clipped & rear, 2] - np.sqrt(rem[clipped & rear])
    target = candidate
    forward = unit(target - hip)
    bend = unit(knee - hip - forward * np.sum((knee - hip) * forward, axis=1)[:, None])
    thigh_length = np.linalg.norm(knee - hip, axis=1)
    shin_length = np.linalg.norm(ankle - knee, axis=1)
    d = np.clip(
        np.linalg.norm(target - hip, axis=1),
        abs(thigh_length - shin_length) + 0.0002,
        thigh_length + shin_length - 0.0005,
    )
    knee_forward = (thigh_length * thigh_length - shin_length * shin_length + d * d) / (
        2 * d
    )
    pole = (
        hip
        + knee_forward[:, None] * forward
        + np.sqrt(
            np.maximum(0.0, thigh_length * thigh_length - knee_forward * knee_forward)
        )[:, None]
        * bend
    )
    set_global_rotation(
        thigh, align(knee - hip, pole - hip) * global_rotation(poses, thigh)
    )
    set_global_rotation(
        shin,
        align(ankle - knee, hip + d[:, None] * forward - pole)
        * global_rotation(poses, shin),
    )
    set_global_rotation(foot, boot)
    # Honor the leather shaft's flexion limit on the freely traveling foot.
    # The support angles fall outside this correction.
    ankle = Rotation.from_quat(rotations[foot]).as_euler("xyz", degrees=True)
    x = ankle[:, 0]
    ankle[:, 0] = np.where(x < -128.0, -128.0 - 4.2 * np.tanh((-128.0 - x) / 4.2), x)
    rotations[foot] = Rotation.from_euler("xyz", ankle, degrees=True).as_quat()
    # Shape the airborne center-of-mass arc after fitting the hinge.
    # Translate the whole runner, preserving the angles and both support patches.
soles = []
world = current_poses()
for side, sign in [("L", 1), ("R", -1)]:
    mesh = model.document["meshes"][0]["primitives"][0]["attributes"]
    mesh_vertices = model.accessor(mesh["POSITION"]).copy()
    mask = (mesh_vertices[:, 1] < 0.048) & (mesh_vertices[:, 0] * sign > 0)
    sk = model.document["skins"][0]
    inverse_bind = (
        model.accessor(sk["inverseBindMatrices"])
        .copy()
        .reshape(-1, 4, 4)
        .transpose(0, 2, 1)
    )
    joint_indices = model.accessor(mesh["JOINTS_0"])[mask]
    joint_weights = model.accessor(mesh["WEIGHTS_0"])[mask]
    vertices = np.c_[mesh_vertices[mask], np.ones(mask.sum())]
    soles.append(
        [
            np.einsum(
                "nvij,nj,nv->ni",
                (world[sk["joints"], frame] @ inverse_bind)[joint_indices, :3, :],
                vertices,
                joint_weights,
            )[:, 1].min()
            for frame in range(frame_count)
        ]
    )
lowest = np.min(soles, axis=0)
lower = np.maximum(0, lowest - 0.034) * smooth(0.023, 0.045, lowest)
translations[pelvis] -= np.linalg.solve(
    world[model.parent[pelvis], :, :3, :3],
    np.c_[0 * lower, lower, 0 * lower][:, :, None],
)[:, :, 0]


def add(data, typ):
    data = np.array(data, dtype="<f4")
    model.binary.extend(b"\0" * (-len(model.binary) % 4))
    model.document["bufferViews"].append(
        {"buffer": 0, "byteOffset": len(model.binary), "byteLength": data.nbytes}
    )
    model.binary.extend(data.tobytes())
    ac = {
        "bufferView": len(model.document["bufferViews"]) - 1,
        "componentType": 5126,
        "count": len(data),
        "type": typ,
    }
    if typ == "SCALAR":
        ac.update(min=[float(data.min())], max=[float(data.max())])
    model.document["accessors"].append(ac)
    return len(model.document["accessors"]) - 1


a = next(a for a in model.document["animations"] if a["name"] == "FieldRun")
t = add(cycle * duration, "SCALAR")
for ch in a["channels"]:
    t0 = ch["target"]
    i = t0["node"]
    path = t0["path"]
    src = {"translation": translations, "rotation": rotations, "scale": scales}[path][
        i
    ].copy()
    if (
        np.max(
            abs(
                src
                - {"translation": base[0], "rotation": base[1], "scale": base[2]}[path][
                    i
                ]
            )
        )
        < 1e-9
    ):
        continue
    if path == "rotation":
        for f in range(1, len(src)):
            if src[f - 1] @ src[f] < 0:
                src[f] *= -1
    key = a["samplers"][ch["sampler"]]
    key["input"] = t
    key["output"] = add(src, "VEC4" if path == "rotation" else "VEC3")
model.document["buffers"][0]["byteLength"] = len(model.binary)
model.write(destination)
