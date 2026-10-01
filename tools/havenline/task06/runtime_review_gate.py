#!/usr/bin/env python3
"""Fail-closed inventory gate for the artifact-only T06 runtime review GLB."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

REQUIRED = {
    "idle", "walk", "run", "start_walk", "start_run", "stop_walk", "stop_run",
    "walk_to_run", "run_to_walk", "turn_left_030", "turn_right_030",
    "turn_left_090", "turn_right_090", "turn_left_180", "turn_right_180",
    "chop", "mine", "dismantle", "deposit", "build", "repair", "rescue",
    "service", "attack_contact",
}


def model(path: Path) -> tuple[dict, str]:
    data = path.read_bytes()
    if len(data) < 28 or struct.unpack_from("<III", data) != (0x46546C67, 2, len(data)):
        raise ValueError("invalid GLB 2.0 header")
    size, kind = struct.unpack_from("<II", data, 12)
    if kind != 0x4E4F534A:
        raise ValueError("first GLB chunk is not JSON")
    return json.loads(data[20:20 + size]), hashlib.sha256(data).hexdigest()


def validate(glb: Path, ledger_path: Path, candidate: str) -> dict:
    errors: list[str] = []
    document, digest = model(glb)
    ledger = json.loads(ledger_path.read_text())
    animations = [row.get("name", "") for row in document.get("animations", [])]
    runtime = {name.removeprefix("t06_") for name in animations}
    if len(animations) != 24 or runtime != REQUIRED or any(not name.startswith("t06_") for name in animations):
        errors.append("runtime review GLB does not contain the exact 24 t06 clips")
    skins = document.get("skins", [])
    if len(skins) != 1:
        errors.append("runtime review GLB must contain exactly one skin")
        joints: set[str] = set()
    else:
        joints = {document["nodes"][index].get("name", f"node:{index}") for index in skins[0].get("joints", [])}
        if len(joints) != 66:
            errors.append(f"runtime review GLB skin has {len(joints)} unique joints, expected 66")
    if ledger.get("candidate_commit") != candidate:
        errors.append("motion ledger candidate mismatch")
    if ledger.get("sample_rate_hz") != 120:
        errors.append("motion ledger is not sampled at 120 Hz")
    if set(ledger.get("clips", {})) != REQUIRED:
        errors.append("motion ledger clip inventory mismatch")
    mapped = [joint for part in ledger.get("semantic_parts", []) for joint in part.get("joints", [])]
    if len(mapped) != 66 or len(set(mapped)) != 66 or set(mapped) != joints:
        errors.append("semantic part map does not cover each exact skin joint once")
    for clip, row in ledger.get("clips", {}).items():
        if row.get("skin_joints_sampled") != 66 or row.get("all_joint_transforms_finite") is not True:
            errors.append(f"{clip} lacks valid all-joint sampling")
        if len(row.get("joint_metrics", {})) != 66:
            errors.append(f"{clip} joint metrics do not cover all 66 joints")
        if row.get("maximum_joint_scale_error", 1.0) >= 0.001:
            errors.append(f"{clip} has unstable joint scale")
    return {
        "task": "T06",
        "candidate_commit": candidate,
        "runtime_review_glb": str(glb),
        "runtime_review_glb_sha256": digest,
        "shipping_asset": False,
        "runtime_clip_count": len(animations),
        "skin_joint_count": len(joints),
        "sample_rate_hz": ledger.get("sample_rate_hz"),
        "semantic_part_count": len(ledger.get("semantic_parts", [])),
        "passed": not errors,
        "errors": errors,
        "note": "Inventory/transform coverage gate; independent textured visual and surface-clearance judgment remains mandatory.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--glb", type=Path, required=True)
    parser.add_argument("--motion-ledger", type=Path, required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = validate(args.glb, args.motion_ledger, args.candidate)
    except (OSError, ValueError, KeyError, TypeError, struct.error) as exc:
        result = {"task": "T06", "candidate_commit": args.candidate, "passed": False, "errors": [str(exc)]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
