"""Reshape the three authored bank pines while retaining their UVs and footprints."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

import numpy as np


def read_glb(path):
    data = path.read_bytes()
    magic, version, length, json_size, json_type = struct.unpack_from("<4sIIII", data)
    assert (magic, version, length, json_type) == (b"glTF", 2, len(data), 0x4E4F534A)
    payload = 20 + json_size
    data_size, data_type = struct.unpack_from("<II", data, payload)
    assert data_type == 0x004E4942
    return json.loads(data[20:payload]), bytearray(data[payload + 8:payload + 8 + data_size])


def write_glb(path, doc, binary):
    metadata = json.dumps(doc, separators=(",", ":")).encode()
    metadata += b" " * (-len(metadata) % 4)
    header = struct.pack("<4sIIII", b"glTF", 2, 28 + len(metadata) + len(binary), len(metadata), 0x4E4F534A)
    path.write_bytes(header + metadata + struct.pack("<II", len(binary), 0x004E4942) + binary)


def channel(doc, binary, index, components):
    accessor = doc["accessors"][index]
    view = doc["bufferViews"][accessor["bufferView"]]
    assert accessor["componentType"] == 5126 and view.get("byteStride", 4 * components) == 4 * components
    offset = accessor.get("byteOffset", 0) + view.get("byteOffset", 0)
    return np.frombuffer(binary, "<f4", accessor["count"] * components, offset).reshape(-1, components)


def fade(a, b, t):
    x = np.clip((t - a) / (b - a), 0, 1)
    return x * x * (3 - 2 * x)


def unit(v):
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-8)


def reshape_points(points, crown, lip, strength):
    for tier, (cap, underside) in enumerate(zip(crown, lip)):
        eave = underside[0]
        bottom = float(np.median(eave[:, 1]))
        tip = float(cap[0, 0, 1])
        # Leave the basal skirt and apex bounds exact. Above the eave, pull the
        # shoulder inward and lower the hidden points under the next tier.
        y = points[tier, :, 1]
        fraction = (y - bottom) / (tip - bottom)
        mid = fade(.06, .31, fraction) * (1 - fade(.62, .95, fraction))
        compression = (.28, .24, 0.)[tier] * strength
        neck = (.27, .24, .16)[tier] * strength
        points[tier, :, 1] -= compression * fade(.03, .84, fraction)
        radius = np.linalg.norm(points[tier][:, [0, 2]], axis=1)
        silhouette = np.linalg.norm(eave[:, [0, 2]], axis=1).max()
        protected_rim = fade(.84, .98, radius / silhouette)
        radial = 1 - neck * mid * (1 - protected_rim)
        points[tier, :, 0] *= radial
        points[tier, :, 2] *= radial
    return points


def shape(source, target, strength, branch_tint):
    doc, binary = read_glb(source)
    surfaces = {doc["materials"][p["material"]]["name"]: p for p in doc["meshes"][0]["primitives"]}
    before = {}
    for part in ("crown", "lip"):
        access = surfaces[part]["attributes"]
        before[part] = channel(doc, binary, access["POSITION"], 3).copy().reshape(3, -1, 121, 3)
    assert before["crown"].shape == (3, 12, 121, 3)
    assert before["lip"].shape == (3, 4, 121, 3)
    for role, bands in before.items():
        access = surfaces[role]["attributes"]
        rest = bands.astype(np.float64).reshape(3, -1, 3)
        transform = lambda p: reshape_points(p.copy(), before["crown"], before["lip"], strength)
        points = transform(rest)
        normal = channel(doc, binary, access["NORMAL"], 3).reshape(rest.shape)
        tangent = channel(doc, binary, access["TANGENT"], 4).reshape(3, -1, 4)
        epsilon = .0001
        shifts = np.eye(3) * epsilon
        jacobian = np.stack([(transform(rest + shift) - transform(rest - shift)) / (epsilon * 2)
                             for shift in shifts], axis=-1)
        assert np.min(np.linalg.det(jacobian)) > .20
        world_normal = unit(np.linalg.solve(np.swapaxes(jacobian, -1, -2), normal[..., None])[..., 0])
        world_tangent = (jacobian @ tangent[..., :3, None])[..., 0]
        tangent[..., :3] = unit(world_tangent - (world_tangent * world_normal).sum(-1, keepdims=True) * world_normal)
        normal[:] = world_normal
        positions = channel(doc, binary, access["POSITION"], 3)
        positions[:] = points.reshape(-1, 3)
        updated = {"POSITION": positions, "NORMAL": normal.reshape(-1, 3),
                   "TANGENT": tangent.reshape(-1, 4)}
        if branch_tint and role == "crown":
            paint = channel(doc, binary, access["COLOR_0"], 4)
            colors = paint.reshape(3, -1, 4)
            for tier in range(3):
                start = np.median(before["lip"][tier, 0, :, 1])
                crest = before["crown"][tier, 0, 0, 1]
                height = (rest[tier, :, 1] - start) / (crest - start)
                x, z = rest[tier, :, 0], rest[tier, :, 2]
                angle = np.arctan2(z, x)
                # Offset the visible snow edges on each tier. The broad recess
                # behind the author's eave reads as slate without a cyan ring.
                drift = .08 * np.sin(3 * angle + .9 * tier) + .04 * np.cos(5 * angle - tier)
                ends = ((.10, .29), (.11, .32), (.22, .46))[tier]
                snow = fade(ends[0] + drift, ends[1] + drift, height)
                tint = np.array([.62, .70, .82])
                colors[tier, :, :3] *= tint + snow[:, None] * (1 - tint)
            updated["COLOR_0"] = paint
        for key, values in updated.items():
            accessor = doc["accessors"][access[key]]
            accessor["min"] = values.min(0).tolist()
            accessor["max"] = values.max(0).tolist()
    # Validate the new authored outline against the dimensions gameplay uses.
    all_before = np.concatenate([x.reshape(-1, 3) for x in before.values()])
    all_after = np.concatenate([channel(doc, binary, surfaces[k]["attributes"]["POSITION"], 3) for k in before])
    assert np.isclose(np.linalg.norm(all_before[:, [0, 2]], axis=1).max(),
                      np.linalg.norm(all_after[:, [0, 2]], axis=1).max(), atol=.00025)
    assert np.isclose(all_before[:, 1].max(), all_after[:, 1].max(), atol=.00025)
    write_glb(target, doc, binary)


def main():
    args = argparse.ArgumentParser()
    args.add_argument("input", type=Path)
    args.add_argument("output", type=Path)
    args.add_argument("--strength", type=float, default=1)
    args.add_argument("--branch-tint", action="store_true")
    request = args.parse_args()
    request.output.mkdir(exist_ok=True, parents=True)
    receipt = {}
    for source in sorted(request.input.glob("bank_pine_[123].glb")):
        target = request.output / source.name
        shape(source, target, request.strength, request.branch_tint)
        receipt[source.name] = {key: hashlib.sha256(path.read_bytes()).hexdigest()
                                for key, path in (("input", source), ("output", target))}
    assert len(receipt) == 3
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
