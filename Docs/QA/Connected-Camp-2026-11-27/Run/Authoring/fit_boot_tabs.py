"""Attach the inside fastening tabs to the existing winter-boot shaft.

Usage: python fit_boot_tabs.py short_stride.glb final.glb
The mesh, UV atlas, materials, joints, inverse bind matrices and animation
curves are untouched. This stage only replaces the local skin weights.
"""
import json
from pathlib import Path
import sys

import numpy as np
from scipy.spatial import cKDTree

from gltf_pose import Model


def smoothstep(fraction):
    return fraction * fraction * (3.0 - 2.0 * fraction)


def fit_tabs(source, destination):
    model = Model(source)
    primitive = model.document["meshes"][0]["primitives"][0]
    attributes = primitive["attributes"]
    position = model.accessor(attributes["POSITION"])
    joint_ids = model.accessor(attributes["JOINTS_0"])
    weights = model.accessor(attributes["WEIGHTS_0"])
    skin = model.document["skins"][0]
    mapped = json.loads(Path(__file__).with_name("boot_tab_vertices.json").read_text())
    original_outer = cKDTree(position[mapped["outer_fastener_vertices"]])
    outer_distance = original_outer.query(position)[0]
    preserve_outer = smoothstep(np.clip(outer_distance / 0.021, 0, 1))

    for side in ("L", "R"):
        tab_tree = cKDTree(position[mapped["tab_vertices"][side]])
        tab_distance = tab_tree.query(position)[0]
        fraction = np.clip(tab_distance / 0.052, 0, 1)
        influence = (1.0 - smoothstep(fraction)) * preserve_outer
        shaft = skin["joints"].index(model.names["BootFleece." + side])
        for vertex in np.flatnonzero(influence > 0.000001):
            amount = influence[vertex]
            merged = {
                int(bone): float(weight) * (1 - amount)
                for bone, weight in zip(joint_ids[vertex], weights[vertex])
                if weight > 0
            }
            merged[shaft] = merged.get(shaft, 0.0) + amount
            strongest = sorted(merged.items(), key=lambda pair: -pair[1])[:4]
            total = sum(weight for _, weight in strongest)
            joint_ids[vertex] = 0
            weights[vertex] = 0
            for slot, (bone, weight) in enumerate(strongest):
                joint_ids[vertex, slot] = bone
                weights[vertex, slot] = weight / total
    model.write(destination)


if __name__ == "__main__":
    fit_tabs(sys.argv[1], sys.argv[2])
