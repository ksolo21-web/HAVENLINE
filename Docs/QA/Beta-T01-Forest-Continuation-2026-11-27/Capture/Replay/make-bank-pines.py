"""Build bank-only pine variants from the established Havenline meshes.

The three existing crown skirts retain their UVs and topology.
Flare the lower rims and paint each crown with a cool blue shadow band.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import numpy as np

FLARE = (0.076, 0.105, 0.115)
HEIGHT = (0.86, 0.90, 0.94)
FLARE_WIDTH = 0.22
SKIRT_TINT = np.array((0.53, 0.66, 0.86), dtype=np.float32)


def glb_chunks(path):
    data = path.read_bytes()
    signature, version, size, json_size, json_kind = struct.unpack_from("<4sIIII", data)
    assert (signature, version, size, json_kind) == (b"glTF", 2, len(data), 0x4E4F534A)
    buffer_start = 20 + json_size
    buffer_size, buffer_kind = struct.unpack_from("<II", data, buffer_start)
    assert buffer_kind == 0x004E4942
    return json.loads(data[20:buffer_start]), bytearray(data[buffer_start + 8:buffer_start + 8 + buffer_size])


def attribute(document, data, accessor, components):
    info = document["accessors"][accessor]
    view = document["bufferViews"][info["bufferView"]]
    assert info["componentType"] == 5126 and view.get("byteStride", components * 4) == components * 4
    shift = view.get("byteOffset", 0) + info.get("byteOffset", 0)
    return np.frombuffer(data, dtype="<f4", count=info["count"] * components, offset=shift).reshape(-1, components)


def repack(document, data, path):
    properties = json.dumps(document, separators=(",", ":")).encode()
    properties += b" " * ((-len(properties)) % 4)
    data += b"\x00" * ((-len(data)) % 4)
    size = 28 + len(properties) + len(data)
    path.write_bytes(struct.pack("<4sIIII", b"glTF", 2, size, len(properties), 0x4E4F534A) + properties + struct.pack("<II", len(data), 0x004E4942) + data)


def unit(vector):
    return vector / np.maximum(np.linalg.norm(vector, axis=1, keepdims=True), 1e-9)


def profile(original, output):
    document, raw = glb_chunks(original)
    primitives = {document["materials"][p["material"]]["name"]: p for p in document["meshes"][0]["primitives"]}
    crown = attribute(document, raw, primitives["crown"]["attributes"]["POSITION"], 3)
    assert len(crown) == 4356
    bands = np.array_split(crown.copy(), 3)
    bounds = [(min(points[:, 1]), max(points[:, 1])) for points in bands]
    for role in ("crown", "lip"):
        values = primitives[role]["attributes"]
        positions = attribute(document, raw, values["POSITION"], 3)
        normals = attribute(document, raw, values["NORMAL"], 3)
        tangents = attribute(document, raw, values["TANGENT"], 4)
        paint = attribute(document, raw, values["COLOR_0"], 4)
        assert len(positions) == (4356 if role == "crown" else 1452)
        for tier, (anchor, apex) in enumerate(bounds):
            selection = slice(tier * len(positions) // 3, (tier + 1) * len(positions) // 3)
            before = positions[selection].copy()
            relative = (before[:, 1] - anchor) / (apex - anchor)
            skirt_band = relative - 0.10
            flare = FLARE[tier] * np.exp(-((skirt_band / FLARE_WIDTH) ** 2))
            radial_scale = 1.0 + flare
            derivative = -2.0 * skirt_band * flare / ((FLARE_WIDTH ** 2) * (apex - anchor))
            out = positions[selection]
            out[:, 0] = before[:, 0] * radial_scale
            out[:, 1] = anchor + HEIGHT[tier] * (before[:, 1] - anchor)
            out[:, 2] = before[:, 2] * radial_scale
            if role == "crown":
                edge = np.clip((relative - 0.18) / 0.19, 0.0, 1.0)
                shade = 1.0 - edge ** 2 * (3.0 - 2.0 * edge)
                paint[selection, :3] *= 1.0 - shade[:, None] * (1.0 - SKIRT_TINT)
            n = normals[selection].copy()
            tx = derivative * before[:, 0]
            tz = derivative * before[:, 2]
            # For this smooth deformation, use the inverse transpose for normals.
            nx = n[:, 0] / radial_scale
            nz = n[:, 2] / radial_scale
            normals[selection] = unit(np.column_stack((nx, (n[:, 1] - nx * tx - nz * tz) / HEIGHT[tier], nz)))
            t = tangents[selection].copy()
            transformed = np.column_stack((radial_scale * t[:, 0] + tx * t[:, 1], HEIGHT[tier] * t[:, 1], radial_scale * t[:, 2] + tz * t[:, 1]))
            n = normals[selection]
            tangents[selection, :3] = unit(transformed - ((transformed * n).sum(axis=1))[:, None] * n)
        for key, array in (("POSITION", positions), ("NORMAL", normals), ("TANGENT", tangents), ("COLOR_0", paint)):
            info = document["accessors"][values[key]]
            info["min"] = array.min(axis=0).tolist()
            info["max"] = array.max(axis=0).tolist()
    document["nodes"][0]["name"] = output.stem
    repack(document, raw, output)


def main():
    command = argparse.ArgumentParser()
    command.add_argument("directory", type=Path)
    args = command.parse_args()
    checks = {}
    for number in range(1, 4):
        source = args.directory / f"pine_{number}.glb"
        destination = args.directory / f"bank_pine_{number}.glb"
        profile(source, destination)
        checks[destination.name] = {
            "source": source.name,
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
        }
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
