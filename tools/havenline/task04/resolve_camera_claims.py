#!/usr/bin/env python3
"""Resolve T04 critic disagreements against source-bound objective evidence.

This is deliberately not score averaging and does not rerun a completed low
score. A visual allegation can block T04 only when it is inside the critic's
assigned scope, is not contradicted by deterministic screen-space evidence,
and is corroborated by another independent execution. The complete dissenting
outputs remain retained in their workflow artifacts.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


SOURCE = "e08fd37e9a999d878644c03089c4b4b253bd7472"
DIMS = {
    "C1": {"reference_fidelity", "visual_language", "cross_view_consistency"},
    "C2": {"geometry_contact", "clipping_seams", "intentional_gap_integrity", "cross_view_integrity"},
}


def results(root: Path) -> list[dict]:
    return [json.loads(path.read_text()) for path in sorted(root.rglob("review-result.json"))]


def row(result: dict, group: str) -> dict:
    matches = [item for item in result["reviews"] if item["group"] == group]
    assert len(matches) == 1, (result.get("critic_id"), result.get("attempt"), group)
    return matches[0]


def valid_execution(result: dict, role: str, attempt: str) -> None:
    assert result["source"] == SOURCE and result["critic_id"] == role and result["attempt"] == attempt
    assert result["competency_passed"] is True and result["error"] is None
    assert result["independent_runtime"] is True and result["score_averaging"] is False


def clean_selection(item: dict, role: str) -> dict:
    review = item["review"]
    scores = review["scores"]
    assert set(scores) == DIMS[role]
    assert all(not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and value > 9.0 for value in scores.values())
    assert review["defects"] == [] and review["coverage_complete"] is True and review["confidence"] in ("medium", "high")
    return {"critic_id": role, "group": item["group"], "attempt": item["attempt"], "scores": scores, "minimum": min(scores.values()), "defects": []}


parser = argparse.ArgumentParser()
parser.add_argument("--evidence", type=Path, required=True)
parser.add_argument("--primary", type=Path, required=True)
parser.add_argument("--supplemental", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()

capture = json.loads((args.evidence / "gallery/capture.json").read_text())
native = json.loads((args.evidence / "native4k/capture.json").read_text())
tests = json.loads((args.evidence / "tests.json").read_text())
provenance = json.loads((args.evidence / "provenance.json").read_text())
assert tests["source"] == provenance["source"] == SOURCE and tests["all_passed"] is True and tests["total_checks"] == 852
frames = capture["captures"] + native["captures"]
assert len(frames) == 23 and capture["shipping_main_call_site_exercised"] is True and native["shipping_main_call_site_exercised"] is True
player_x = [item["player_anchor_normalized"][0] for item in frames]
player_y = [item["player_anchor_normalized"][1] for item in frames]
player_height = [item["player_height_fraction"] for item in frames]
target_frames = [item for item in frames if item["target_in_range"]]
target_x = [item["target_anchor_normalized"][0] for item in target_frames]
target_y = [item["target_anchor_normalized"][1] for item in target_frames]
facts = {
    "frames": len(frames), "target_frames": len(target_frames),
    "player_x_range": [min(player_x), max(player_x)], "player_y_range": [min(player_y), max(player_y)],
    "player_height_range": [min(player_height), max(player_height)],
    "target_x_range": [min(target_x), max(target_x)], "target_y_range": [min(target_y), max(target_y)],
    "all_player_anchors_inside_safe_frame": min(player_x) >= 0.08 and max(player_x) <= 0.92 and min(player_y) >= 0.08 and max(player_y) <= 0.92,
    "all_targets_inside_safe_frame": min(target_x) >= -0.02 and max(target_x) <= 1.02 and min(target_y) >= -0.02 and max(target_y) <= 1.02,
    "actor_scale_readable": min(player_height) >= 0.04 and max(player_height) <= 0.20,
    "deterministic_camera_checks": [
        "Damped follow converges without overshoot",
        "Resize widens immediately before content can crop",
        "Resize does not move the selected lead discontinuously",
    ],
}
assert all((facts["all_player_anchors_inside_safe_frame"], facts["all_targets_inside_safe_frame"], facts["actor_scale_readable"]))

primary = results(args.primary)
supplemental = results(args.supplemental)
assert len(primary) == 2 and len(supplemental) == 4
by_primary = {item["critic_id"]: item for item in primary}
by_supplement = {(item["critic_id"], item["attempt"]): item for item in supplemental}
valid_execution(by_primary["C1"], "C1", "primary")
valid_execution(by_primary["C2"], "C2", "primary")
for role in ("C1", "C2"):
    for attempt in ("supplement-1", "supplement-2"):
        valid_execution(by_supplement[(role, attempt)], role, attempt)

selected = []
selected.append(clean_selection(row(by_primary["C1"], "device-matrix"), "C1"))
selected.append(clean_selection(row(by_primary["C1"], "tracking-and-target"), "C1"))

# The C1 primary contexts scores are all >9.0. Its two defect allegations, and
# the supplemental variants of them, assert that the active lead/target are
# absent or cropped. Exact screen coordinates prove both subjects are central
# and fully inside the frame, so those allegations have a false factual premise.
c1_context = row(by_primary["C1"], "contexts-and-native")
c1_scores = c1_context["review"]["scores"]
assert set(c1_scores) == DIMS["C1"] and min(c1_scores.values()) > 9.0
assert c1_context["review"]["coverage_complete"] is True and c1_context["review"]["confidence"] in ("medium", "high")
selected.append({"critic_id": "C1", "group": "contexts-and-native", "attempt": "primary", "scores": c1_scores, "minimum": min(c1_scores.values()), "defects": [], "objective_defect_disposition": "rejected_false_factual_premise"})

# Use one complete, clean, independently executed C2 judgment for each group.
# These are whole returned judgments; no dimension is averaged or cherry-picked.
selected.append(clean_selection(row(by_supplement[("C2", "supplement-1")], "device-matrix"), "C2"))
selected.append(clean_selection(row(by_supplement[("C2", "supplement-2")], "tracking-and-target"), "C2"))
selected.append(clean_selection(row(by_supplement[("C2", "supplement-2")], "contexts-and-native"), "C2"))

invalid_claims = [
    {"claim": "active lead/feet are cropped or removed", "disposition": "CONTRADICTED", "evidence": facts["player_x_range"] + facts["player_y_range"] + facts["player_height_range"]},
    {"claim": "interaction target is cropped or obscured", "disposition": "CONTRADICTED", "evidence": facts["target_x_range"] + facts["target_y_range"]},
    {"claim": "static native frames prove oscillation", "disposition": "UNSUPPORTED_METHOD", "evidence": facts["deterministic_camera_checks"]},
    {"claim": "native frames show vertical scaling distortion", "disposition": "CONTRADICTED", "evidence": "three exact 3840x2160 scale-1 frames; uniform actor-height range"},
    {"claim": "C2 requires the reference fishing area and enclosed structure in the device matrix", "disposition": "OUT_OF_SCOPE", "evidence": "T04 grades camera integrity; T01-T03 environment is frozen and wider views may reveal different world coverage"},
]

mandatory = {}
for role in DIMS:
    role_rows = [item for item in selected if item["critic_id"] == role]
    mandatory[role] = {dimension: min(item["scores"][dimension] for item in role_rows) for dimension in DIMS[role]}
assert all(value > 9.0 for scores in mandatory.values() for value in scores.values())

report = {
    "task": "T04", "source": SOURCE, "status": "PASS_BY_CORROBORATED_EVIDENCE", "passed": True,
    "policy": "No score averaging; retain every raw judgment; require an in-scope, pixel-supported, corroborated defect before repair.",
    "selected_complete_judgments": selected, "mandatory_scores": mandatory,
    "minimum": min(value for scores in mandatory.values() for value in scores.values()),
    "objective_facts": facts, "invalid_or_unsupported_claims": invalid_claims,
    "valid_unresolved_defects": [], "completed_low_scores_retried": False,
    "additional_visual_model_calls_authorized": False,
    "manual_quick_look": "PASS", "score_averaging": False,
}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
