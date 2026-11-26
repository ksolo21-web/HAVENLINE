#!/usr/bin/env python3
"""Rebuild the Character 1 paint from its reviewed GLB using NumPy, SciPy and Pillow."""

import argparse
import copy
import hashlib
import json
import struct
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import maximum_filter


BASELINE_SHA256 = "c27362d34459ce81ddfbadae19e91002985d69ae077fa25049dacae1247974f7"


def unpack_accessor(document, binary, index):
    accessor = document["accessors"][index]
    view = document["bufferViews"][accessor["bufferView"]]
    dtype = {5126: "<f4", 5125: "<u4", 5123: "<u2", 5121: "u1"}[accessor["componentType"]]
    width = {"SCALAR": 1, "VEC2": 2, "VEC3": 3}[accessor["type"]]
    offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    return np.frombuffer(binary, dtype=dtype, count=accessor["count"] * width, offset=offset).reshape(-1, width)


def ramp(low, high, values):
    t = np.clip((values - low) / (high - low), 0, 1)
    return t * t * (3 - 2 * t)


def paint(atlas, positions, uvs, triangles):
    uv_pixels = (uvs * (np.array(atlas.size) - 1)).round().astype("int32")
    x, y, z = positions[triangles].mean(axis=1).T

    def projected_mask(selected_faces):
        mask = Image.new("L", atlas.size)
        brush = ImageDraw.Draw(mask)
        for indices in triangles[selected_faces]:
            brush.polygon(list(map(tuple, uv_pixels[indices])), fill=255)
        # Include island padding so filtered edges stay continuous during motion.
        return maximum_filter(np.asarray(mask, dtype=float) / 255.0, size=7)

    coat = projected_mask((y > 0.49) & (y < 1.10) & (abs(x) < 0.70))
    hem = (y > 0.455) & (y < 0.575) & (abs(x) < 0.36)
    zipper = (y > 0.51) & (y < 0.99) & (abs(x) < 0.07) & (z > 0.088)
    shoulders = (y > 0.92) & (y < 1.115) & (abs(x) > 0.12) & (abs(x) < 0.46)
    trim = projected_mask(hem | zipper | shoulders)

    base = np.asarray(atlas, dtype=float)
    hue, saturation, value = np.moveaxis(np.array(atlas.convert("HSV"), float), 2, 0)
    blue = (coat * ramp(130, 146, hue) * (1 - ramp(164, 177, hue))
            * ramp(55, 135, saturation) * ramp(12, 52, value))
    orange = (trim * ramp(0, 5, hue) * (1 - ramp(24, 34, hue))
              * ramp(114, 185, saturation) * ramp(104, 190, value))

    # Preserve fabric folds and highlight headroom from the original map.
    fabric_response = ramp(0, 92, value) * (0.78 + 0.22 * value / 255.0)
    color = base + blue[:, :, None] * fabric_response[:, :, None] * np.array([5., 42., 70.]) * (1 - np.square(base / 255))
    color += orange[:, :, None] * np.array([105., 3., -11.]) * (1 - (base / 255) ** 2)

    # Extend existing orange edges onto touching blue cloth for subpixel coverage.
    edge = maximum_filter(orange, size=17) * (1 - orange) * blue * trim * 0.75
    grain = np.clip((value / 138) ** 0.55, 0.45, 1)
    edge_color = grain[:, :, None] * np.array([254., 86., 17.])
    color = color * (1 - edge[:, :, None]) + edge_color * edge[:, :, None]
    pixels = np.uint8(np.rint(color).clip(0, 255))
    changed = np.any(pixels != base, axis=-1)
    assert not np.any(changed & (blue == 0) & (orange == 0))
    return Image.fromarray(pixels)


def view_bytes(binary, view):
    start = view.get("byteOffset", 0)
    return binary[start:start + view["byteLength"]]


def rebuild(raw):
    json_length = struct.unpack_from("<I", raw, 12)[0]
    document = json.loads(raw[20:20 + json_length])
    binary = raw[28 + json_length:]

    primitive = document["meshes"][0]["primitives"][0]
    positions = unpack_accessor(document, binary, primitive["attributes"]["POSITION"])
    uvs = unpack_accessor(document, binary, primitive["attributes"]["TEXCOORD_0"])
    triangles = unpack_accessor(document, binary, primitive["indices"]).reshape(-1, 3)
    material = document["materials"][primitive["material"]]["pbrMetallicRoughness"]
    image_id = document["textures"][material["baseColorTexture"]["index"]]["source"]
    view_id = document["images"][image_id]["bufferView"]
    views = document["bufferViews"]
    atlas = Image.open(BytesIO(view_bytes(binary, views[view_id]))).convert("RGB")
    encoded = BytesIO()
    paint(atlas, positions, uvs, triangles).save(encoded, format="PNG", compress_level=4)
    new_image = encoded.getvalue()

    start = views[view_id].get("byteOffset", 0)
    offsets = [view.get("byteOffset", 0) for view in views]
    end = min((offset for offset in offsets if offset > start), default=len(binary))
    padded = new_image + bytes(-len(new_image) % 4)
    delta = len(padded) - (end - start)
    replacement = binary[:start] + padded + binary[end:]
    updated = copy.deepcopy(document)
    updated_views = updated["bufferViews"]
    for view in updated_views:
        if view.get("byteOffset", 0) > start:
            view["byteOffset"] += delta
    updated_views[view_id]["byteLength"] = len(new_image)
    updated["images"][image_id]["mimeType"] = "image/png"
    updated["buffers"][0]["byteLength"] += delta
    for i, view in enumerate(views):
        if i != view_id:
            assert view_bytes(binary, view) == view_bytes(replacement, updated_views[i])

    metadata = json.dumps(updated, separators=(",", ":")).encode()
    metadata += b" " * (-len(metadata) % 4)
    replacement += bytes(-len(replacement) % 4)
    chunks = (struct.pack("<I4s", len(metadata), b"JSON") + metadata
              + struct.pack("<I4s", len(replacement), b"BIN\0") + replacement)
    return struct.pack("<4sII", b"glTF", 2, 12 + len(chunks)) + chunks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    if args.baseline.resolve() == args.destination.resolve():
        parser.error("Choose a separate destination for the repaired character.")
    raw = args.baseline.read_bytes()
    if hashlib.sha256(raw).hexdigest() != BASELINE_SHA256:
        parser.error("This paint recipe requires the reviewed V3 character and its UV layout.")
    fitted = rebuild(raw)
    with NamedTemporaryFile(dir=args.destination.parent, delete=False) as handle:
        handle.write(fitted)
    Path(handle.name).replace(args.destination)
    print(hashlib.sha256(fitted).hexdigest(), args.destination)
