"""Articulate the original field wolf from Git commit ee4251ae.

Run with the original hostile_wolf.glb and the desired output GLB as arguments.
The original textured mesh and four non-attack clips are retained.
"""

import math
import sys
from pathlib import Path

import numpy as np
from build_camp_line import read_model, write_model

if len(sys.argv) != 3:
    raise SystemExit("usage: build_wolf_attack.py SOURCE_WOLF.glb OUTPUT_WOLF.glb")
source, dest = map(Path, sys.argv[1:])
doc, binary = read_model(
    source, "da3d6f196081067f68fc960285acc09a5d1dba3c6feb3ebda9f9c4b01a32cc58"
)
dtypes = {5126: "<f4", 5125: "<u4", 5123: "<u2"}
dims = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def read(k):
    a = doc["accessors"][k]
    v = doc["bufferViews"][a["bufferView"]]
    return (
        np.frombuffer(
            binary,
            dtype=dtypes[a["componentType"]],
            offset=v.get("byteOffset", 0) + a.get("byteOffset", 0),
            count=a["count"] * dims[a["type"]],
        )
        .reshape(-1, dims[a["type"]])
        .copy()
    )


def put(arr, kind, component=5126, bounds=False, target=None):
    arr = np.asarray(arr, dtype=dtypes[component]).reshape(-1, dims[kind])
    while len(binary) % 4:
        binary.append(0)
    v = {"buffer": 0, "byteOffset": len(binary), "byteLength": arr.nbytes}
    if target:
        v["target"] = target
    doc["bufferViews"].append(v)
    binary.extend(arr.tobytes())
    a = {
        "bufferView": len(doc["bufferViews"]) - 1,
        "componentType": component,
        "type": kind,
        "count": len(arr),
    }
    if bounds:
        a.update(min=arr.min(0).tolist(), max=arr.max(0).tolist())
    doc["accessors"].append(a)
    return len(doc["accessors"]) - 1


verts, uv, norm, ids, weights = [read(i) for i in [1, 2, 3, 5, 6]]
tris = read(0).reshape(-1, 3)
nodes = doc["nodes"]
nodes[6].setdefault("children", []).append(len(nodes))
# The source muzzle looks toward +X as well as +Z. Place the hinge on its own axis.
axis = np.array([0.9165, 0, -0.4])
axis /= np.linalg.norm(axis)
forward = np.array([-axis[2], 0, axis[0]])
hinge = 0.885 * forward - 0.248 * axis + np.array([0, 1.147, 0])
nodes.append(
    {"name": "Jaw", "translation": (hinge - np.array([0.01, 1.328, 0.69])).tolist()}
)
jaw_slot = len(doc["skins"][0]["joints"])
doc["skins"][0]["joints"].append(len(nodes) - 1)
inv = read(4)
jaw_inv = np.eye(4, dtype=np.float32).flatten()
jaw_inv[12:15] = -hinge
doc["skins"][0]["inverseBindMatrices"] = put(np.vstack([inv, jaw_inv]), "MAT4")


def lip_height(q):
    return np.interp(
        q,
        [0.87, 0.925, 0.955, 1.01, 1.07, 1.12, 1.15, 1.17],
        [1.145, 1.144, 1.139, 1.123, 1.111, 1.104, 1.107, 1.111],
    )


def smooth(v):
    v = np.clip(v, 0, 1)
    return v * v * (3 - 2 * v)


def influences(old_ids, old_weights, f):
    b = {}
    for i, w in zip(old_ids, old_weights):
        b[int(i)] = b.get(int(i), 0) + w * (1 - f)
    b[jaw_slot] = f
    ranked = sorted(b.items(), key=lambda item: -item[1])[:4]
    ranked += [(0, 0.0)] * (4 - len(ranked))
    total = sum(w for _, w in ranked)
    return [i for i, _ in ranked], [w / total for _, w in ranked]


q = verts @ forward
relative = verts[:, 1] - lip_height(q)


def jaw_weight(u):
    return smooth((u - 0.907) / 0.09)


newpos = list(verts)
newuv = list(uv)
newnorm = list(norm)
newids = list(ids)
neww = list(weights)
for idx in np.flatnonzero((q > 0.907) & (relative < 0)):
    newids[idx], neww[idx] = influences(ids[idx], weights[idx], jaw_weight(q[idx]))
outer = []
edges = {}
seams = []


def intersection(a, b, lower):
    key = (min(a, b), max(a, b), lower)
    if key in edges:
        return edges[key]
    t = relative[a] / (relative[a] - relative[b])
    mix = lambda vs: vs[a] * (1 - t) + vs[b] * t
    p = mix(verts)
    n = mix(norm)
    n /= max(1e-9, np.linalg.norm(n))
    ww = np.r_[weights[a] * (1 - t), weights[b] * t]
    ii, ww = influences(
        np.r_[ids[a], ids[b]], ww, jaw_weight(p @ forward) if lower else 0
    )
    k = len(newpos)
    newpos.append(p)
    newnorm.append(n)
    newuv.append(mix(uv))
    newids.append(ii)
    neww.append(ww)
    edges[key] = k
    return k


for t in tris:
    if q[t].max() < 0.897 or relative[t].min() >= 0 or relative[t].max() <= 0:
        outer.append(t)
        continue
    caps = []
    for lower in [False, True]:
        poly = []
        line = []
        for a, b in zip(t, np.roll(t, -1)):
            ia = (relative[a] < 0) == lower
            ib = (relative[b] < 0) == lower
            if ia:
                poly.append(a)
            if ia != ib:
                idx = intersection(a, b, lower)
                poly.append(idx)
                line.append(idx)
        outer.extend([[poly[0], poly[s], poly[s + 1]] for s in range(1, len(poly) - 1)])
        caps.append(line)
    seams.append(caps)


def meshpart(pos, normal, bones, w, tri, material, tex=None):
    attrs = {
        "POSITION": put(pos, "VEC3", bounds=True, target=34962),
        "NORMAL": put(normal, "VEC3", target=34962),
        "JOINTS_0": put(bones, "VEC4", 5123, target=34962),
        "WEIGHTS_0": put(w, "VEC4", target=34962),
    }
    if tex is not None:
        attrs["TEXCOORD_0"] = put(tex, "VEC2", target=34962)
    return {
        "attributes": attrs,
        "indices": put(tri, "SCALAR", 5125, target=34963),
        "material": material,
        "mode": 4,
    }


parts = [meshpart(newpos, newnorm, newids, neww, outer, 0, newuv)]


def painted(name, color):
    doc["materials"].append(
        {
            "name": name,
            "doubleSided": True,
            "pbrMetallicRoughness": {
                "baseColorFactor": color + [1.0],
                "metallicFactor": 0.0,
                "roughnessFactor": 0.81,
            },
        }
    )
    return len(doc["materials"]) - 1


# Skin the two cut faces independently. Their centre curves inward so the
# lip, the dark palate and lower tongue read separately when the jaws part.
for side, mat in enumerate(
    [
        painted("Shadowed palate", [0.052, 0.013, 0.022]),
        painted("Lower mouth", [0.235, 0.059, 0.063]),
    ]
):
    p = []
    n = []
    ii = []
    ww = []
    faces = []
    for caps in seams:
        a, b = caps[side]
        off = len(p)
        for k in [a, b, b, a]:
            pp = np.array(newpos[k])
            u = pp @ forward
            if len(p) - off >= 2:
                lat = -0.249
                pp += axis * (lat - pp @ axis)
                pp[1] += (
                    (0.018 if side == 0 else -0.007)
                    * smooth((u - 0.91) / 0.07)
                    * smooth((1.165 - u) / 0.063)
                )
            p.append(pp)
            ii.append(newids[k])
            ww.append(neww[k])
            n.append([0, 1 if side else -1, 0])
        faces.extend([(off, off + 1, off + 2), (off, off + 2, off + 3)])
    parts.append(meshpart(p, n, ii, ww, faces, mat))


# Sculpt a shallow tongue along the mandibular centreline, recessed behind
# the lip, and small curved upper canines embedded inside the closed muzzle.
def oral_mesh(rings, jaw, material):
    pos = []
    faces = []
    sides = len(rings[0])
    for ring in rings:
        pos.extend(ring)
    for row in range(len(rings) - 1):
        for col in range(sides):
            a = row * sides + col
            b = row * sides + (col + 1) % sides
            faces.extend([(a, b, b + sides), (a, b + sides, a + sides)])
    vertices = np.asarray(pos)
    computed = np.zeros_like(vertices)
    for a, b, c in faces:
        n = np.cross(vertices[b] - vertices[a], vertices[c] - vertices[a])
        for k in (a, b, c):
            computed[k] += n
    computed /= np.maximum(1e-12, np.linalg.norm(computed, axis=1)[:, None])
    ids = [[jaw_slot if jaw else 5, 0, 0, 0]] * len(pos)
    parts.append(
        meshpart(vertices, computed, ids, [[1, 0, 0, 0]] * len(pos), faces, material)
    )


def point(u, l, y):
    return u * forward + l * axis + np.array([0.0, y, 0.0])


rings = []
for u, width, h in [
    (0.923, 0.003, 0),
    (0.951, 0.041, 0.006),
    (1.006, 0.065, 0.008),
    (1.067, 0.057, 0.009),
    (1.097, 0.041, 0.008),
    (1.115, 0.018, 0.005),
    (1.12, 0.002, 0.002),
]:
    ring = []
    for theta in np.linspace(0, 2 * np.pi, 13)[:-1]:
        ring.append(
            point(
                u,
                -0.250 + width * math.cos(theta),
                lip_height(u) + 0.002 + h * math.sin(theta),
            )
        )
    rings.append(ring)
oral_mesh(rings, True, painted("Tongue", [0.49, 0.138, 0.145]))
tooth_color = painted("Canine enamel", [0.80, 0.70, 0.54])
for side in [-1, 1]:
    for u, length, radius, w in [
        (1.088, 0.038, 0.010, 0.061),
        (1.013, 0.021, 0.008, 0.069),
    ]:
        rings = []
        for f, r in [
            (0.0, 0.86),
            (0.12, 1.0),
            (0.53, 0.71),
            (0.82, 0.37),
            (1.0, 0.035),
        ]:
            ring = []
            for theta in np.linspace(0, 2 * np.pi, 9)[:-1]:
                ring.append(
                    point(
                        u + 0.010 * f * f + math.sin(theta) * r * radius,
                        -0.250 + side * (w - 0.004 * f) + math.cos(theta) * r * radius,
                        lip_height(u) + 0.008 - length * f,
                    )
                )
            rings.append(ring)
        oral_mesh(rings, False, tooth_color)
doc["meshes"][0]["primitives"] = parts
# Segment lengths are taken from the real skeleton; keep the four paws
# planted through loading, then reach, recoil and land at different times.
name_to_id = {n["name"]: i for i, n in enumerate(nodes)}
local = {n["name"]: np.array(n.get("translation", [0, 0, 0])) for n in nodes}
parents = {nodes[c]["name"]: n["name"] for n in nodes for c in n.get("children", [])}


def rot(a):
    return np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])


def yzFK(name, angles, move):
    if name == "Root":
        return local[name][1:] + move, 0.0
    p, r = yzFK(parents[name], angles, move)
    return p + rot(r) @ local[name][1:], r + angles.get(name, 0.0)


def phase(root, torso, jaw, front, back, tail, asym=0.0):
    # root (height,forward), local Haunch,Spine,Chest,Neck,Head incl.
    # jaw; legs are (toe elevation,reach,angle of hock,paw inclination).
    angles = dict(zip(["Haunch", "Spine", "Chest", "Neck", "Head"], np.deg2rad(torso)))
    angles.update(dict(zip(["TailBase", "TailMid", "TailTip"], np.deg2rad(tail))))
    move = np.array(root)
    for key, foot in [
        ("FrontL", front),
        ("FrontR", front),
        ("RearL", back),
        ("RearR", back),
    ]:
        hip, knee, hock, paw = [key + s for s in ["Hip", "Knee", "Hock", "Paw"]]
        height, reach, hock_degrees, paw_degrees = foot
        sign = 1 if key.endswith("L") else -1
        q0, _ = yzFK(paw, {}, np.zeros(2))
        goal = q0 + [max(0, height + sign * asym * 0.23), reach + sign * asym]
        origin, base = yzFK(hip, angles, move)
        dh, dk, dp = [local[n][1:] for n in [knee, hock, paw]]
        hock_abs = math.radians(hock_degrees)
        target = goal - rot(hock_abs) @ dp - origin
        a, b = np.linalg.norm(dh), np.linalg.norm(dk)
        cross = dh[0] * dk[1] - dh[1] * dk[0]
        shape = math.copysign(
            math.acos(np.clip((target @ target - a * a - b * b) / (2 * a * b), -1, 1)),
            cross,
        )
        direction = math.atan2(target[1], target[0])
        angle1 = direction - math.atan2(b * math.sin(shape), a + b * math.cos(shape))
        angle2 = angle1 + shape
        wrap = lambda a: (a + math.pi) % (2 * math.pi) - math.pi
        hip_abs = wrap(angle1 - math.atan2(dh[1], dh[0]))
        knee_abs = wrap(angle2 - math.atan2(dk[1], dk[0]))
        angles[hip] = wrap(hip_abs - base)
        angles[knee] = wrap(knee_abs - hip_abs)
        angles[hock] = wrap(hock_abs - knee_abs)
        angles[paw] = wrap(math.radians(paw_degrees) - hock_abs)
    angles["Jaw"] = math.radians(jaw)
    return move, angles


rest = phase((0, 0), (0, 0, 0, 0, 0), 0, (0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0))
gather = phase(
    (-0.095, -0.070),
    (-5, -3, 6, -8, -4),
    16,
    (0, 0.015, -4, 0),
    (0, 0.018, 12, 0),
    (-6, -3, 3),
    0.012,
)
crouch = phase(
    (-0.165, -0.125),
    (-11, -5, 10, -10, -6),
    36,
    (0, 0.035, -11, 0),
    (0, 0.042, 22, 0),
    (-16, -7, 5),
    0.028,
)
push = phase(
    (-0.09, -0.01),
    (-6, -3, 1, -10, -8),
    47,
    (0.088, 0.08, -6, 12),
    (0.036, -0.12, -16, -14),
    (-11, 0, 9),
    0.049,
)
reach = phase(
    (0.048, 0.066),
    (-4, -7, 3, -5, 1),
    48,
    (0.105, 0.225, 16, 12),
    (0.094, -0.25, -31, -27),
    (2, 9, 9),
    0.053,
)
close = phase(
    (0.016, 0.096),
    (1, -2, 1, 1, 6),
    3,
    (0.008, 0.20, 7, 1),
    (0.12, -0.17, -26, -22),
    (11, 10, 3),
    0.041,
)
land = phase(
    (-0.094, 0.063),
    (-3, 2, 8, 3, 5),
    1,
    (0, 0.116, -8, 0),
    (0.067, -0.054, -8, -9),
    (9, 2, -4),
    0.032,
)
absorb = phase(
    (-0.119, 0.021),
    (-8, 4, 8, -4, 3),
    5,
    (0, 0.083, -9, 0),
    (0.023, 0.061, 9, -3),
    (3, -7, -6),
    0.024,
)
settle = phase(
    (-0.035, -0.02),
    (-3, 1, 4, -5, -2),
    2,
    (0.017, 0.012, 3, 0),
    (0, 0.033, 4, 0),
    (-3, -3, 2),
    0.013,
)


def anim(name, times, poses):
    samplers = []
    channels = []
    ti = put(times, "SCALAR", bounds=True)

    def track(node, path, arr, kind):
        idx = len(samplers)
        samplers.append(
            {"input": ti, "output": put(arr, kind), "interpolation": "LINEAR"}
        )
        channels.append(
            {"sampler": idx, "target": {"node": name_to_id[node], "path": path}}
        )

    track(
        "Root", "translation", [local["Root"] + np.r_[0, m] for m, _ in poses], "VEC3"
    )
    for bone in poses[0][1]:
        axis_rot = axis if bone == "Jaw" else np.array([1.0, 0, 0])
        track(
            bone,
            "rotation",
            [
                np.r_[axis_rot * math.sin(a[bone] * 0.5), math.cos(a[bone] * 0.5)]
                for _, a in poses
            ],
            "VEC4",
        )
    return {"name": name, "samplers": samplers, "channels": channels}


doc["animations"] = [
    a for a in doc["animations"] if a["name"] not in ("Brace", "Bite", "Recover")
]
doc["animations"] += [
    anim("Brace", [0, 0.105, 0.26, 0.30], [rest, gather, crouch, crouch]),
    anim(
        "Bite",
        [0, 0.05, 0.118, 0.136, 0.17, 0.26],
        [crouch, push, reach, reach, close, land],
    ),
    anim("Recover", [0, 0.095, 0.25, 0.46, 0.76], [land, absorb, settle, rest, rest]),
]
# Keep the existing UV atlas and all unrelated clips. Remove the replaced
# buffer regions instead of duplicating the entire mesh and skin in the GLB.
refs = []
for m in doc["meshes"]:
    for part in m["primitives"]:
        refs.append((part, "indices"))
        refs.extend((part["attributes"], k) for k in part["attributes"])
for a in doc["animations"]:
    refs.extend((s, k) for s in a["samplers"] for k in ("input", "output"))
refs += [(s, "inverseBindMatrices") for s in doc["skins"]]
used = sorted({o[k] for o, k in refs})
ar = [doc["accessors"][i] for i in used]
amap = {old: new for new, old in enumerate(used)}
for o, k in refs:
    o[k] = amap[o[k]]
doc["accessors"] = ar
viewrefs = ar + doc["images"]
used = sorted({x["bufferView"] for x in viewrefs})
newbinary = bytearray()
views = []
vm = {}
for old in used:
    row = dict(doc["bufferViews"][old])
    start = row.get("byteOffset", 0)
    while len(newbinary) % 4:
        newbinary.append(0)
    row["byteOffset"] = len(newbinary)
    newbinary.extend(binary[start : start + row["byteLength"]])
    vm[old] = len(views)
    views.append(row)
for x in viewrefs:
    x["bufferView"] = vm[x["bufferView"]]
doc["bufferViews"] = views
doc["buffers"][0]["byteLength"] = len(newbinary)
temp = dest.with_suffix(".tmp")
write_model((doc, newbinary), temp)
temp.replace(dest)
