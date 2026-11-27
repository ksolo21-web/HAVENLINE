"""Calibrate anatomical correspondence in measured metres before skin transfer."""
import json
from pathlib import Path

import numpy as np
from scipy.interpolate import RBFInterpolator
from scipy.spatial.transform import Rotation


def transforms(doc):
    nodes = doc["nodes"]
    parents = {child: i for i, node in enumerate(nodes) for child in node.get("children", [])}
    cache = {}

    def world(i):
        if i not in cache:
            node = nodes[i]
            if "matrix" in node:
                local = np.asarray(node["matrix"]).reshape((4, 4)).T
            else:
                local = np.eye(4)
                local[:3, :3] = Rotation.from_quat(node.get("rotation", [0., 0., 0., 1.])).as_matrix() @ np.diag(node.get("scale", [1., 1., 1.]))
                local[:3, 3] = node.get("translation", [0., 0., 0.])
            cache[i] = world(parents[i]) @ local if i in parents else local
        return cache[i]

    return parents, [world(i) for i in range(len(nodes))]


def warp(points, anchors, frames):
    if anchors is None:
        return points.copy()
    source, target = zip(*[(frames[name], position) for name, position in anchors.items()])
    source = np.asarray(source, float)
    target = np.asarray(target, float)
    if len(source) < 4 or np.linalg.matrix_rank(source - source.mean(axis=0)) != 3:
        raise ValueError("Measure at least four non-coplanar rest-pose landmarks")
    return points + RBFInterpolator(source, target - source, kernel="thin_plate_spline", smoothing=0.0)(points)


def transformed(points, matrix):
    return points @ matrix[:3, :3].T + matrix[:3, 3]


def landmarks(model):
    _, matrices = transforms(model.doc)
    return {node["name"]: m[:3, 3] for node, m in zip(model.doc["nodes"], matrices) if "name" in node}


def inventory(model, filename):
    _, matrices = transforms(model.doc)
    parts = []
    for i, node in enumerate(model.doc["nodes"]):
        if "mesh" not in node:
            continue
        for surface in model.doc["meshes"][node["mesh"]]["primitives"]:
            vertices = transformed(model.read(surface["attributes"]["POSITION"]), matrices[i])
            parts.append({"node": node.get("name", i), "vertices": len(vertices),
                          "bounds": [vertices.min(axis=0).round(4).tolist(), vertices.max(axis=0).round(4).tolist()],
                          "skinned": "JOINTS_0" in surface["attributes"]})
    return {"filename": str(filename), "parts": parts, "skins": [len(s["joints"]) for s in model.doc.get("skins", [])],
            "animations": [a.get("name") for a in model.doc.get("animations", [])], "materials": [m.get("name") for m in model.doc.get("materials", [])]}


if __name__ == "__main__":
    import argparse
    from glb_helper import Glb

    args = argparse.ArgumentParser()
    args.add_argument("glb", type=Path)
    args.add_argument("--landmarks", action="store_true")
    options = args.parse_args()
    model = Glb(options.glb)
    info = inventory(model, options.glb)
    if options.landmarks:
        info["bind_centers"] = {k: v.round(4).tolist() for k, v in landmarks(model).items()}
    print(json.dumps(info, indent=2))
