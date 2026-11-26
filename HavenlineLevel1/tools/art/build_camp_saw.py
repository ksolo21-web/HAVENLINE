"""Expose the existing saw's timber workpiece for driven, stocked cuts.

python tools/art/build_camp_saw.py assets/shore_workshops/shore_saw_bench.glb assets/shore_workshops/camp_saw_bench.glb
"""
import argparse

import numpy as np

from build_camp_line import append_values, read_model, values, write_model


def split_workpiece(model):
    doc, _ = model
    frame = doc["meshes"][0]["primitives"][0]
    positions = values(model, frame["attributes"]["POSITION"]).reshape(-1, 3, 3)
    # In build_shore_processors the trunk, two collars, fourteen bark ridges
    # and both sawn end-grain rings are adjacent in the stream. Identify the
    # continuous cylinder between the upper depth stop and the blade axle.
    x, y, z = positions.transpose(2, 0, 1)
    enclosed = ((abs(x) < 1.06) & (np.hypot(y - 1.415, z + .14) < .288)).all(axis=1)
    edges = np.flatnonzero(np.diff(np.r_[False, enclosed, False])).reshape(-1, 2)
    start, end = max(edges, key=lambda run: run[1] - run[0])
    if (start, end) != (1384, 7872):
        raise ValueError("Unexpected timber, guide or axle geometry")
    indices = np.arange(positions.size // 3, dtype="<u2")
    start, end = start * 3, end * 3
    fixed = np.r_[indices[:start], indices[end:]].reshape(-1, 1)
    workpiece = {**frame, "indices": append_values(model, indices[start:end, None], 34963)}
    frame["indices"] = append_values(model, fixed, 34963)
    mesh = len(doc["meshes"])
    node = len(doc["nodes"])
    doc["meshes"].append({"name": "TimberWorkpiece", "primitives": [workpiece]})
    doc["nodes"].append({"name": "TimberWorkpiece", "mesh": mesh})
    doc["scenes"][doc["scene"]]["nodes"].append(node)
    # The source atlas is already a first-class project asset. This preserves
    # the frame, bark and end grain without importing a second texture.
    doc["images"][0] = {"uri": "shore_saw_bench_0.jpg"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("output")
    from pathlib import Path
    args = parser.parse_args()
    source = read_model(Path(args.source), "0f8bd0a11cea058dfd0b711bcace5c5f2717dfe63a22dc012541f6fbb6c0701b")
    split_workpiece(source)
    write_model(source, Path(args.output))
