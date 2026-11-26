"""Articulate the expedition owl's existing talons. Pass the original GLB and an output GLB."""
import argparse
from pathlib import Path

import numpy as np

from build_camp_line import append_values, read_model, values, write_model


SOURCE_HASH = "7bcfd1277b8ff0eebfc70e8ba8c726750e34c4e1a999cefb9463ae0fd3953f41"


def ramp(low, high, value):
    t = np.clip((value - low) / (high - low), 0, 1)
    return t * t * (3 - 2 * t)


def normal_delta(pos, normal, delta, triangles):
    """Transform the original smooth, UV-seamed normal by the local change in surface slope."""
    origin = pos[triangles]
    moved = (pos + delta)[triangles]
    def face_normals(v):
        cross = np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0])
        return cross / np.maximum(np.linalg.norm(cross, axis=1, keepdims=True), 1e-12)
    face = face_normals(origin)
    adjusted = face_normals(moved)
    sign = np.sign(np.sum(face * normal[triangles].mean(1), axis=1, keepdims=True))
    difference = (adjusted - face) * sign
    accum = np.zeros_like(pos)
    counts = np.zeros(len(pos))
    for column in triangles.T:
        np.add.at(accum, column, difference)
        np.add.at(counts, column, 1)
    adjusted = normal + accum / np.maximum(counts, 1)[:, None]
    adjusted /= np.maximum(np.linalg.norm(adjusted, axis=1, keepdims=True), 1e-12)
    return (adjusted - normal).astype("<f4")


def build(source, dest):
    model = read_model(source, SOURCE_HASH)
    doc, buffer = model
    image_view = doc["images"][0]["bufferView"]
    if image_view != len(doc["bufferViews"]) - 1:
        raise ValueError("Expected the embedded plumage atlas to be the final original view")
    del buffer[doc["bufferViews"].pop()["byteOffset"]:]
    body = doc["meshes"][0]
    primitive = body["primitives"][0]
    coords = values(model, primitive["attributes"]["POSITION"])
    normals = values(model, primitive["attributes"]["NORMAL"])
    faces = values(model, primitive["indices"]).reshape(-1, 3)
    tuck = values(model, primitive["targets"][0]["POSITION"])
    x, y, z = coords.T
    # Fade up the shanks, leaving the tail, harness, belly and wings untouched.
    shank = (1 - ramp(.055, .238, y)) * ramp(-.18, -.075, z)
    toe = (1 - ramp(.039, .096, y)) * shank
    side = np.sign(x)
    # Flex the ankle and fan the toes out before the strike. The second pose
    # brings them together around the contact and rakes back under the body.
    radial = x - side * .094
    reach = np.column_stack((side * shank * .026 + radial * toe * .39,
                             -shank * .072 - toe * .020,
                             shank * .148 + toe * .057 + toe * (z + .02) * .38))
    close = np.column_stack((side * shank * .008 - radial * toe * .48,
                             -shank * .077 - toe * .041,
                             shank * .079 + toe * .020 - toe * (z + .02) * .39))
    for name, delta in [("StrikeReach", reach), ("GripAndRake", close)]:
        delta = delta.astype("<f4")
        primitive["targets"].append({"POSITION": append_values(model, delta, 34962),
                                     "NORMAL": append_values(model, normal_delta(coords, normals, delta, faces), 34962)})
        body["extras"]["targetNames"].append(name)
        body["weights"].append(0.)
    # Bind contact sensors to six real low claw vertices. The child offsets are
    # the very same deformations used by their respective rendered vertices.
    for sign, foot in [(-1, "Left"), (1, "Right")]:
        for slot, center in enumerate([.057, .105, .149]):
            candidates = np.flatnonzero((x * sign > center - .022) & (x * sign < center + .022) &
                                        (y < .045) & (z > -.008))
            index = candidates[np.argmax(z[candidates] - .65 * y[candidates])]
            sensor = {"name": f"Claw{foot}{slot}", "translation": coords[index].tolist(), "children": []}
            doc["nodes"][1].setdefault("children", []).append(len(doc["nodes"]))
            doc["nodes"].append(sensor)
            for name, delta in [("Tuck", tuck), ("Reach", reach), ("Grip", close)]:
                sensor["children"].append(len(doc["nodes"]))
                doc["nodes"].append({"name": name, "translation": delta[index].tolist()})
    # Share the existing imported atlas across both versions of the asset.
    doc["images"] = [{"name": "OwlEightViewPlumage", "uri": "expedition_owl_OwlEightViewPlumage.jpg"}]
    write_model(model, dest)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build(args.source, args.output)
