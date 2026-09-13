#!/usr/bin/env python3
"""Measured exact-source T05 C6 gate against the accepted T04 baseline."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import struct
import subprocess
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_capture_hashes(root: Path, manifest: dict, label: str) -> list[str]:
    failures = []
    captures = manifest.get("captures")
    if not isinstance(captures, dict) or not captures:
        return [f"{label} provenance has no capture hash map"]
    for relative, expected in captures.items():
        path = root / relative
        if not path.is_file() or digest(path) != expected:
            failures.append(f"{label} missing or changed capture: {relative}")
    return failures


def git_head(root: Path) -> str:
    return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()


def index(rows: list[dict]) -> dict[str, dict]:
    return {row["name"]: row for row in rows}


def glb_texture_count(path: Path) -> int:
    data = path.read_bytes()
    if len(data) < 20 or data[:4] != b"glTF":
        raise ValueError(f"invalid GLB: {path}")
    json_length, json_type = struct.unpack_from("<II", data, 12)
    if json_type != 0x4E4F534A:
        raise ValueError(f"missing GLB JSON chunk: {path}")
    document = json.loads(data[20:20 + json_length].decode("utf-8").rstrip(" \t\r\n\0"))
    return len(document.get("textures", [])) + len(document.get("images", []))


def regression_score(ratio: float, allowed: float = 0.10) -> float:
    """10 at/below baseline, exactly 9 at the material-regression boundary."""
    if not math.isfinite(ratio) or ratio < 0:
        return 0.0
    return round(max(0.0, min(10.0, 10.0 - max(0.0, ratio - 1.0) / allowed)), 6)


def budget_score(value: float, cap: float) -> float:
    if not math.isfinite(value) or value < 0 or cap <= 0:
        return 0.0
    ratio = value / cap
    if ratio <= 1.0:
        # The frozen contract defines the cap as valid; retain a 0.1 strict-score margin at the cap.
        return round(10.0 - 0.9 * ratio, 6)
    return round(max(0.0, 9.0 - 10.0 * (ratio - 1.0)), 6)


parser = argparse.ArgumentParser()
parser.add_argument("--candidate", required=True)
parser.add_argument("--baseline-source", required=True)
parser.add_argument("--candidate-root", type=Path, required=True)
parser.add_argument("--baseline-root", type=Path, required=True)
parser.add_argument("--candidate-benchmark", type=Path, required=True)
parser.add_argument("--baseline-benchmark", type=Path, required=True)
parser.add_argument("--candidate-rss-kb", type=int, required=True)
parser.add_argument("--baseline-rss-kb", type=int, required=True)
parser.add_argument("--evidence", type=Path, required=True)
parser.add_argument("--baseline-evidence", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()

errors: list[str] = []
if git_head(args.candidate_root) != args.candidate:
    errors.append("candidate checkout is not the frozen T05 source")
if git_head(args.baseline_root) != args.baseline_source:
    errors.append("baseline checkout is not the accepted T04 source")

tests = read_json(args.evidence / "tests.json")
provenance = read_json(args.evidence / "provenance.json")
baseline_provenance = read_json(args.baseline_evidence / "provenance.json")
current_gameplay = read_json(args.evidence / "gameplay/capture.json")
current_native = read_json(args.evidence / "native4k/capture.json")
base_gallery = read_json(args.baseline_evidence / "gallery/capture.json")
base_native = read_json(args.baseline_evidence / "native4k/capture.json")
preflight = read_json(args.evidence / "performance-preflight.json")
candidate_benchmark = read_json(args.candidate_benchmark)
baseline_benchmark = read_json(args.baseline_benchmark)
catalog_path = args.candidate_root / "HavenlineGodot/assets/stations_v2/catalog.json"
catalog = read_json(catalog_path)

measurement_paths = []
for folder in (args.candidate_benchmark.parent, args.baseline_benchmark.parent):
    for name in ("benchmark.json", "time.txt", "run.log", "import.log", "start-native.png", "end-native.png"):
        path = folder / name
        if not path.is_file():
            errors.append(f"missing raw measurement file: {folder.name}/{name}")
        else:
            measurement_paths.append(path)
measurement_files = {f"{path.parent.name}/{path.name}": digest(path) for path in measurement_paths}

if tests.get("source") != args.candidate or provenance.get("source") != args.candidate:
    errors.append("T05 evidence is not candidate-bound")
if baseline_provenance.get("source") != args.baseline_source:
    errors.append("T04 artifact is not accepted-baseline-bound")
errors.extend(validate_capture_hashes(args.evidence, provenance, "T05"))
errors.extend(validate_capture_hashes(args.baseline_evidence, baseline_provenance, "T04"))
if not tests.get("all_passed") or tests.get("suite_count") != 18 or tests.get("total_checks", 0) < 1117:
    errors.append("T05 mechanical evidence is incomplete")
if not provenance.get("cheap_performance_gate_passed") or not preflight.get("passed"):
    errors.append("T05 deterministic performance preflight failed")
if current_gameplay.get("renderer") != base_gallery.get("renderer") or current_native.get("renderer") != base_native.get("renderer"):
    errors.append("T04/T05 capture renderer mismatch")
if not base_gallery.get("source_bound") or not base_native.get("source_bound"):
    errors.append("T04 capture manifests are not source-bound")
if current_native.get("captures") and any(row.get("internal_size") != [3840, 2160] or row.get("render_scale") != 1.0 for row in current_native["captures"]):
    errors.append("T05 native capture conditions are not 3840x2160 scale 1")
if base_native.get("captures") and any(row.get("internal_size") != [3840, 2160] or row.get("render_scale") != 1.0 for row in base_native["captures"]):
    errors.append("T04 native capture conditions are not 3840x2160 scale 1")

current = index(current_gameplay["captures"] + current_native["captures"])
baseline = index(base_gallery["captures"] + base_native["captures"])
if set(current) != set(baseline) or len(current) != 23:
    errors.append("T04/T05 matched-frame set mismatch")
    draw_deltas = primitive_deltas = [math.inf]
else:
    draw_deltas = [current[name]["draw_calls"] - baseline[name]["draw_calls"] for name in current]
    primitive_deltas = [current[name]["submitted_primitives"] - baseline[name]["submitted_primitives"] for name in current]

required_benchmark_fields = {"samples", "retained_seconds", "average_engine_fps", "p95_ms", "p99_ms", "renderer", "display_driver", "gpu", "native_dimensions_and_scale_maintained", "fixed_timestep_used", "software_renderer"}
for label, benchmark in (("candidate", candidate_benchmark), ("baseline", baseline_benchmark)):
    missing = required_benchmark_fields - set(benchmark)
    if missing:
        errors.append(f"{label} benchmark missing fields: {sorted(missing)}")
    if benchmark.get("samples", 0) < 300 or benchmark.get("retained_seconds", 0) < 30:
        errors.append(f"{label} benchmark duration/sample count is insufficient")
    if benchmark.get("native_dimensions_and_scale_maintained") is not True or benchmark.get("fixed_timestep_used") is not False:
        errors.append(f"{label} benchmark was not real elapsed native-4K scale-1 rendering")
if any(candidate_benchmark.get(key) != baseline_benchmark.get(key) for key in ("renderer", "display_driver", "gpu", "software_renderer")):
    errors.append("candidate/baseline benchmark conditions differ")
if args.candidate_rss_kb <= 0 or args.baseline_rss_kb <= 0:
    errors.append("measured maximum RSS is unavailable")

entries = {row["id"]: row for row in catalog["entries"]}
arrangements = {
    name: {
        "assets": len(placements),
        "triangles": sum(entries[row["id"]]["triangles"] for row in placements),
        "visible_materials": len({material for row in placements for material in entries[row["id"]]["materials"]}),
    }
    for name, placements in catalog["arrangements"].items()
}
contract = catalog["performance_contract"]
asset_paths = [args.candidate_root / row["asset"].replace("res://", "HavenlineGodot/") for row in catalog["entries"]]
kit_triangles = sum(row["triangles"] for row in catalog["entries"])
kit_materials = len({material for row in catalog["entries"] for material in row["materials"]})
kit_storage_bytes = sum(path.stat().st_size for path in asset_paths)
texture_records = sum(glb_texture_count(path) for path in asset_paths)
max_arrangement_triangles = max(row["triangles"] for row in arrangements.values())
max_arrangement_materials = max(row["visible_materials"] for row in arrangements.values())

if max(draw_deltas) > contract["draw_calls_max"]:
    errors.append("matched-frame draw-call delta exceeds assigned cap")
if max(primitive_deltas) > contract["triangles_max"] or max_arrangement_triangles > contract["triangles_max"]:
    errors.append("station geometry exceeds assigned cap")
if max_arrangement_materials > contract["visible_materials_max"]:
    errors.append("station materials exceed the assigned cap")
if kit_storage_bytes > contract["storage_delta_mib_max"] * 1024 * 1024:
    errors.append("station-kit storage exceeds the assigned cap")
if texture_records != 0:
    errors.append("station GLBs unexpectedly contain texture/image records")
for key in ("active_physics", "animations", "population", "skeletons"):
    if contract.get(key) != 0:
        errors.append(key + " must remain zero for T05")

frame_ratios = [
    candidate_benchmark["p95_ms"] / baseline_benchmark["p95_ms"],
    candidate_benchmark["p99_ms"] / baseline_benchmark["p99_ms"],
    baseline_benchmark["average_engine_fps"] / candidate_benchmark["average_engine_fps"],
]
frame_ratio = max(frame_ratios)
rss_ratio = args.candidate_rss_kb / args.baseline_rss_kb
dimensions = {
    "frame_time": regression_score(frame_ratio),
    "draw_calls": budget_score(max(0, max(draw_deltas)), contract["draw_calls_max"]),
    "geometry": budget_score(max(max_arrangement_triangles, max(0, max(primitive_deltas))), contract["triangles_max"]),
    "texture_memory": 10.0 if texture_records == 0 else 0.0,
    "shader_cost": min(regression_score(frame_ratio), budget_score(max_arrangement_materials, contract["visible_materials_max"])),
    "physics": 10.0 if contract["active_physics"] == 0 else 0.0,
    "animation": 10.0 if contract["animations"] == 0 and contract["skeletons"] == 0 else 0.0,
    "population": 10.0 if contract["population"] == 0 else 0.0,
    "thermal_risk": min(regression_score(frame_ratio), regression_score(rss_ratio)),
}
for name, score in dimensions.items():
    if score <= 9.0:
        errors.append(f"{name} score is not strictly above 9.0 ({score})")

record = {
    "candidate_commit": args.candidate, "baseline_commit": args.baseline_source,
    "scene_state": "same-runner T04/T05 shipping scene, 23 matched frames, catalog-bound nominal arrangements",
    "resolution": "real elapsed 3840x2160 scale-1 render benchmark plus 23 matched captures",
    "renderer": candidate_benchmark["renderer"], "gpu": candidate_benchmark["gpu"],
    "software_renderer": candidate_benchmark["software_renderer"],
    "visible_triangles": max(row["submitted_primitives"] for row in current.values()),
    "draw_calls": max(row["draw_calls"] for row in current.values()),
    "materials_visible": max_arrangement_materials,
    "texture_gpu_memory_mb": 0 if texture_records == 0 else None,
    "process_memory_mb": args.candidate_rss_kb / 1024,
    "process_memory_baseline_mb": args.baseline_rss_kb / 1024,
    "physics_active_bodies": 0, "animated_rigs_active": 0, "npc_companion_active_population": 0,
    "storage_download_mb": kit_storage_bytes / (1024 * 1024),
    "cpu_frame_ms": None, "gpu_frame_ms_where_measurable": None,
    "engine_frame_p99_ms": candidate_benchmark["p99_ms"],
    "measurement_method": "Same Ubuntu runner, pinned Godot 4.7.2, Mobile Vulkan, Xvfb native 4K scale 1, real elapsed 30-second candidate and T04-baseline runs; GNU time maximum RSS; exact matched capture counters; GLB JSON/catalog inspection.",
    "incremental_record": True, "matched_frames": 23,
    "draw_call_delta_min": min(draw_deltas), "draw_call_delta_max": max(draw_deltas),
    "primitive_delta_min": min(primitive_deltas), "primitive_delta_max": max(primitive_deltas),
    "frame_regression_ratio": frame_ratio, "rss_regression_ratio": rss_ratio,
    "candidate_benchmark": candidate_benchmark, "baseline_benchmark": baseline_benchmark,
    "kit_total_triangles": kit_triangles, "kit_unique_materials": kit_materials,
    "kit_storage_bytes": kit_storage_bytes, "embedded_texture_or_image_records": texture_records,
    "nominal_arrangements": arrangements,
    "new_physics_bodies": 0, "new_animations": 0, "new_population": 0,
    "known_unmeasured_fields": ["physical display presentation", "physical-device thermal behavior", "isolated CPU time", "GPU time"],
    "physical_device_certification": False,
}
args.output.mkdir(parents=True, exist_ok=True)
(args.output / "input-manifest.json").write_text(json.dumps({
    "candidate_commit": args.candidate,
    "baseline_commit": args.baseline_source,
    "candidate_catalog_sha256": digest(catalog_path),
    "T05_evidence_provenance_sha256": digest(args.evidence / "provenance.json"),
    "T04_evidence_provenance_sha256": digest(args.baseline_evidence / "provenance.json"),
    "measurement_files": measurement_files,
}, indent=2, sort_keys=True) + "\n")
(args.output / "performance-record.json").write_text(json.dumps(record, indent=2) + "\n")

harness = subprocess.run([
    "python3", "tools/havenline/production/critic_harness.py", "performance",
    "--candidate", args.candidate, "--record", str(args.output / "performance-record.json"),
], text=True, capture_output=True)
(args.output / "critic-harness-stdout.json").write_text(harness.stdout)
if harness.returncode != 0:
    errors.append("global performance harness failed: " + (harness.stdout + harness.stderr).strip())

result = {
    "task": "T05", "critic_id": "C6", "candidate_commit": args.candidate,
    "baseline_commit": args.baseline_source,
    "provider": "deterministic-quantitative-specialist-gate", "model": "critic_harness.py performance",
    "request_or_run_id": ":".join((os.environ.get("GITHUB_RUN_ID", "local"), os.environ.get("GITHUB_RUN_ATTEMPT", "0"), args.candidate)), "independent": True,
    "input_manifest_path": "task05-C6/input-manifest.json",
    "input_manifest_hash": digest(args.output / "input-manifest.json"),
    "raw_output_path": f"{args.candidate_benchmark.parent.name}/{args.candidate_benchmark.name}",
    "raw_output_hash": digest(args.candidate_benchmark),
    "measurement_files": measurement_files,
    "performance_record_path": "task05-C6/performance-record.json",
    "performance_record_hash": digest(args.output / "performance-record.json"),
    "mandatory_dimensions": dimensions, "minimum": min(dimensions.values()),
    "defects": errors, "coverage_complete": not errors, "confidence": "high" if not errors else "medium",
    "passed": not errors and min(dimensions.values()) > 9.0,
    "scoring_basis": "Scores are computed from measured same-runner frame/RSS regression and explicit station-kit budgets; no score is assigned to an unmeasured value.",
    "thermal_risk_is_early_proxy": True, "physical_device_certification": False,
    "limitations": "T68/T69 retain sustained physical native-4K/60, presentation timing, GPU-time and thermal certification.",
}
(args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
raise SystemExit(0 if result["passed"] else 1)
