#!/usr/bin/env python3
"""Bind a passing exact-source T05 visual decision to its measured C6 artifact."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path


EXPECTED_DIMENSIONS = {
    "frame_time", "draw_calls", "geometry", "texture_memory", "shader_cost",
    "physics", "animation", "population", "thermal_risk",
}
MEASUREMENT_NAMES = {
    f"{repeat}/{name}"
    for repeat in ("baseline-a", "candidate-a", "candidate-b", "baseline-b")
    for name in ("benchmark.json", "time.txt", "run.log", "import.log", "start-native.png", "end-native.png")
}
MEASUREMENT_NAMES |= {
    f"warmup-{repeat}/{name}"
    for repeat in ("baseline-a", "candidate-a", "candidate-b", "baseline-b")
    for name in ("benchmark.json", "run.log", "start-native.png", "end-native.png")
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_gate(visual_root: Path, performance_root: Path, source: str, baseline: str) -> dict:
    errors: list[str] = []
    visual_files = list(visual_root.rglob("final-visual-decision.json"))
    c6_files = list(performance_root.rglob("result.json"))
    if len(visual_files) != 1 or len(c6_files) != 1:
        return {
            "task": "T05", "source": source, "passed": False,
            "ready_for_final_pixel_signoff": False, "task_approved": False,
            "physical_4k60_verified": False,
            "errors": ["expected exactly one visual decision and one C6 result"],
        }
    visual = json.loads(visual_files[0].read_text())
    c6 = json.loads(c6_files[0].read_text())
    if visual.get("source") != source or visual.get("passed") is not True:
        errors.append("C1/C2 visual gate")
    if visual.get("status") not in ("PASS", "PASS_BY_QUORUM") or visual.get("score_averaging") is not False:
        errors.append("visual decision policy")
    if any(row.get("status") not in ("PASS", "PASS_BY_QUORUM") for row in visual.get("decisions", [])):
        errors.append("unresolved visual decision")

    scores = c6.get("mandatory_dimensions", {})
    if c6.get("candidate_commit") != source or c6.get("baseline_commit") != baseline or c6.get("passed") is not True or c6.get("defects") != []:
        errors.append("C6 result")
    if set(scores) != EXPECTED_DIMENSIONS or any(
        isinstance(value, bool) or not isinstance(value, (int, float))
        or not math.isfinite(value) or value <= 9.0 for value in scores.values()
    ):
        errors.append("C6 strict scores")

    def check_bound(relative: str, key: str) -> bool:
        path = performance_root / relative
        return path.is_file() and digest(path) == c6.get(key)

    if not check_bound(c6.get("input_manifest_path", ""), "input_manifest_hash"):
        errors.append("C6 input manifest integrity")
    if not check_bound(c6.get("raw_output_path", ""), "raw_output_hash"):
        errors.append("C6 raw output integrity")
    if not check_bound(c6.get("performance_record_path", ""), "performance_record_hash"):
        errors.append("C6 performance record integrity")
    measurement_files = c6.get("measurement_files", {})
    if set(measurement_files) != MEASUREMENT_NAMES:
        errors.append("C6 measurement-file set")
    for relative, expected_hash in measurement_files.items():
        path = performance_root / relative
        if not path.is_file() or digest(path) != expected_hash:
            errors.append("C6 measurement integrity " + relative)
    manifest_path = performance_root / c6.get("input_manifest_path", "")
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text())
        if manifest.get("measurement_files") != measurement_files or manifest.get("candidate_commit") != source or manifest.get("baseline_commit") != baseline:
            errors.append("C6 input binding")
    run_id = c6.get("request_or_run_id", "").split(":", 1)[0]
    if not run_id.isdigit():
        errors.append("C6 actual workflow run id")
    return {
        "task": "T05", "source": source, "passed": not errors,
        "strict_rule": ">9.0 unrounded; no averaging; isolated dissent only; both-primary failures cannot be outvoted",
        "visual_status": visual.get("status"), "quorums": visual.get("quorums", []),
        "visual_decision_sha256": digest(visual_files[0]),
        "C6_result_sha256": digest(c6_files[0]), "C6_run_id": run_id,
        "C6_minimum": min(scores.values()) if scores else None,
        "ready_for_final_pixel_signoff": not errors,
        "task_approved": False, "physical_4k60_verified": False, "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--visual", type=Path, required=True)
    parser.add_argument("--performance", type=Path, required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_gate(args.visual, args.performance, args.source, args.baseline)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as handle:
            handle.write("```json\n" + json.dumps(result, indent=2) + "\n```\n")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
