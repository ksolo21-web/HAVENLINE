#!/usr/bin/env python3
"""Read-only replay of provenance, timestamp and role-sign facts; not computer vision."""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

VIDEO_SHA = "4c9051cbea6df0efa3e7288b13b6d17da46e857274869b0b43d2f96ff6cc79d2"
SCENE_SHA = "dcc64291acfa167ee55b38b071f0ebec0620a3713faefc104e881e1add7259e1"
SAMPLES = {372: 7.395222, 390: 7.997667, 420: 8.999856, 450: 10.0, 480: 11.004622, 510: 12.007011}

def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for part in iter(lambda: f.read(1 << 20), b""):
            h.update(part)
    return h.hexdigest()

def require(condition, label):
    if not condition:
        raise SystemExit(f"HOLD: {label}")

def run(video, scene):
    require(digest(video) == VIDEO_SHA, "exact reference source mismatch")
    require(digest(scene) == SCENE_SHA, "exact detached donor scene mismatch")
    raw = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "frame=best_effort_timestamp_time", "-of", "json", str(video)], text=True)
    pts = json.loads(raw)["frames"]
    for i, t in SAMPLES.items():
        require(abs(float(pts[i]["best_effort_timestamp_time"]) - t) < 0.000001, f"PTS {i}")
    source = Path(scene).read_text()
    actual = {}
    for marker in ("CustomerExteriorStance", "WorkerInteriorStance"):
        row = source.split(f'[node name="{marker}"', 1)[1].split("[node", 1)[0]
        v = re.search(r"position = Vector3\(([^)]*)\)", row)
        require(v is not None, f"position {marker}")
        actual[marker] = tuple(float(x) for x in v.group(1).split(","))
    require(actual["CustomerExteriorStance"] == (0, 0, -1.45), "exterior authored witness")
    require(actual["WorkerInteriorStance"] == (0, 0, 1.35), "interior authored witness")
    require("Markers_NotBindings" in source and "CounterSealedBridge" in source, "detached role-only guard")
    print(json.dumps({"samples": SAMPLES, "scene_role_positions_m": actual, "scope": "source and role-sign only, human image review separate"}, indent=2))

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: check.py <owner-supplied-reference-124510.mp4> <north_counter_donor.tscn>")
    run(*sys.argv[1:])
