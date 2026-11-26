"""Rebuild the camp cooker from its two authored Havenline donors.

python tools/art/build_camp_line.py assets/lakeshore/cooker_workshop.glb conveyor_straight.glb assets/lakeshore/cooker_camp_line.glb

The conveyor is HavenlineGodot/assets/stations_v2/conveyor_straight.glb from
Git blob b82e20764621f3582f1f647fa9316bd63574a9d9. Requires Python and NumPy.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

import numpy as np


def read_model(path, checksum):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != checksum:
        raise ValueError(f"Unexpected mesh revision for {path}")
    size = int.from_bytes(raw[12:16], "little")
    return json.loads(raw[20:20 + size]), bytearray(raw[28 + size:])


def values(model, index):
    doc, buffer = model
    a = doc["accessors"][index]
    view = doc["bufferViews"][a["bufferView"]]
    size = {"SCALAR": 1, "VEC3": 3}[a["type"]]
    dtype = {5123: "<u2", 5125: "<u4", 5126: "<f4"}[a["componentType"]]
    return np.frombuffer(buffer, dtype, a["count"] * size,
                         offset=view.get("byteOffset", 0) + a.get("byteOffset", 0)).reshape(-1, size).copy()


def append_values(model, data, target):
    doc, buffer = model
    data = np.ascontiguousarray(data)
    buffer.extend(b"\0" * (-len(buffer) % 4))
    view = len(doc["bufferViews"])
    doc["bufferViews"].append(dict(buffer=0, byteOffset=len(buffer), byteLength=data.nbytes, target=target))
    buffer.extend(data.tobytes())
    index = len(doc["accessors"])
    doc["accessors"].append(dict(bufferView=view, count=len(data),
                                 type="VEC3" if data.shape[1] == 3 else "SCALAR",
                                 componentType=5126 if data.dtype.kind == "f" else 5123,
                                 min=data.min(0).tolist(), max=data.max(0).tolist()))
    return index


def fixed_cooker(model):
    # Both trays were cast with portions already on them. Strip the real
    # portions and their garnish. The studs along the rims remain attached.
    doc, _ = model
    fixed = []
    removed = {}
    for p in doc["meshes"][0]["primitives"]:
        name = doc["materials"][p["material"]]["name"]
        positions = values(model, p["attributes"]["POSITION"])
        faces = values(model, p["indices"]).reshape(-1, 3)
        x, y, z = positions[faces].mean(1).T
        remove = np.zeros(len(faces), dtype=bool)
        if name == "HL_orange":
            remove = (abs(x) > .4) & (y > 1.04)
        elif name == "HL_yellow":
            remove[:] = True
        elif name == "HL_cream":
            remove = (abs(x) > .42) & (y > 1.17) & (z > -.22) & (z < .48)
            remove |= (x > 1.08) & (y > 1.17)
        elif name == "HL_metal":
            # Open the end of the tray where the blue receiver docks.
            face_x = positions[faces][:, :, 0]
            remove = (y > 1.01) & (face_x.min(1) > 1.12) & ~np.isclose(face_x, 1.177).any(1)
        if remove.any():
            removed[name] = int(remove.sum())
        if not remove.all():
            kept = faces[~remove].reshape(-1, 1)
            fixed.append({**p, "indices": append_values(model, kept, 34963)} if remove.any() else p)
    if removed != {"HL_metal": 12, "HL_cream": 336, "HL_orange": 832, "HL_yellow": 48}:
        raise ValueError(f"Unexpected food or rim geometry: {removed}")
    doc["meshes"][0]["primitives"] = fixed


def add_conveyor(model, donor):
    doc, _ = model
    original, _ = donor
    materials = {m["name"]: i for i, m in enumerate(doc["materials"])}
    sources = {}
    for p in original["meshes"][0]["primitives"]:
        points = values(donor, p["attributes"]["POSITION"])
        normals = values(donor, p["attributes"]["NORMAL"])
        faces = values(donor, p["indices"]).reshape(-1, 3)
        sources[original["materials"][p["material"]]["name"]] = (points, normals, faces)

    def piece(source, shade, scale, offset, select=None):
        pos, normal, faces = sources[source]
        if select is not None:
            faces = faces[select(pos[faces].mean(1))]
        used, compact = np.unique(faces, return_inverse=True)
        pos = pos[used] * scale + offset
        normal = normal[used] / scale
        normal /= np.linalg.norm(normal, axis=1)[:, None]
        return dict(attributes={
            "POSITION": append_values(model, pos.astype("<f4"), 34962),
            "NORMAL": append_values(model, normal.astype("<f4"), 34962)},
            indices=append_values(model, compact.reshape(-1, 1).astype("<u2"), 34963),
            material=materials[shade], mode=4)

    # Shorten the conveyor on its run axis to fit against the cooker. The
    # output end holds a steel receiving plate on the original blue frame.
    frame = doc["meshes"][0]["primitives"]
    frame.append(piece("HL_blue", "HL_blue", [.38, 1.36, .86], [1.15, -.04, .15]))
    frame.append(piece("HL_dark", "HL_metal", [.211, .66, .84], [1.418, .525, .15]))
    frame.append(piece("HL_orange", "HL_blue", [.225, .69, .84], [1.359, .477, .15],
                       lambda mid: mid[:, 0] > 0))
    # Use the cylinder from the actual conveyor and keep its machined profile.
    # A bronze facet on the working shaft makes rotation perceptible.
    def roller(mid):
        return abs(mid[:, 0]) < .12

    def stripe(mid):
        return roller(mid) & (mid[:, 0] > .065) & (mid[:, 1] > .8)

    scale = [.67, .67, .72]
    offset = [0, -.77 * scale[1], 0]
    mesh = len(doc["meshes"])
    doc["meshes"].append({"name": "WorkRoller", "primitives": [
        piece("HL_yellow", "HL_metal", scale, offset, lambda mid: roller(mid) & ~stripe(mid)),
        piece("HL_yellow", "HL_wood_light", scale, offset, stripe)]})
    for i, x in enumerate([-1.05, -.90, -.75, -.60, .56, .71, .86, 1.01]):
        node = len(doc["nodes"])
        doc["nodes"].append(dict(name=f"WorkRoller{i+1}", mesh=mesh,
                                  translation=[x, .999 if x < 0 else 1.008, .15]))
        doc["nodes"][0]["children"].append(node)


def write_model(model, path):
    doc, buffer = model
    buffer.extend(b"\0" * (-len(buffer) % 4))
    doc["buffers"][0]["byteLength"] = len(buffer)
    head = json.dumps(doc, separators=(",", ":")).encode()
    head += b" " * (-len(head) % 4)
    path.write_bytes(struct.pack("<4sIII4s", b"glTF", 2, 28 + len(head) + len(buffer), len(head), b"JSON")
                     + head + struct.pack("<I4s", len(buffer), b"BIN\0") + buffer)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("cooker", "conveyor", "output"):
        parser.add_argument(arg, type=Path)
    args = parser.parse_args()
    cooker = read_model(args.cooker, "1105f5c0f79b3b7b998dc59d76e0afdfd3c5cd339de14e17274c27cf39ddecde")
    conveyor = read_model(args.conveyor, "89bbeb9f7c38744497deefb414eb0456ed28100a07d4ae6bce47aa85cf40bb15")
    fixed_cooker(cooker)
    add_conveyor(cooker, conveyor)
    write_model(cooker, args.output)
