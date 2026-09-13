#!/usr/bin/env python3
"""Resolve T04 C1/C2 judgments with strict, non-averaged 2-of-3 quorum."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


SOURCE_GROUPS = {"device-matrix", "tracking-and-target", "contexts-and-native"}
DIMS = {
    "C1": {"reference_fidelity", "visual_language", "cross_view_consistency"},
    "C2": {"geometry_contact", "clipping_seams", "intentional_gap_integrity", "cross_view_integrity"},
}


def classify(row: dict, source: str, role: str, group: str) -> str:
    if row.get("source") != source or row.get("critic_id") != role or row.get("group") != group:
        return "INCOMPLETE"
    if row.get("independent_execution") is not True or row.get("error") is not None:
        return "INCOMPLETE"
    review = row.get("review", {})
    scores = review.get("scores", {})
    if set(scores) != DIMS[role] or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 10 for v in scores.values()):
        return "INCOMPLETE"
    if not review.get("observations") or review.get("coverage_complete") is not True or review.get("confidence") not in ("medium", "high") or not isinstance(review.get("defects"), list):
        return "INCOMPLETE"
    return "PASS" if all(v > 9.0 for v in scores.values()) and review["defects"] == [] else "DISSENT"


def load_rows(root: Path, source: str, attempts: set[str]) -> dict[tuple[str, str], list[dict]]:
    rows: dict[tuple[str, str], list[dict]] = {}
    for path in root.rglob("review-result.json"):
        result = json.loads(path.read_text())
        if result.get("source") != source or result.get("critic_id") not in DIMS or result.get("attempt") not in attempts:
            continue
        if result.get("competency_passed") is not True or result.get("error") is not None:
            for group in result.get("groups", []):
                rows.setdefault((result["critic_id"], group), []).append({"source": source, "critic_id": result["critic_id"], "group": group, "error": "invalid execution"})
            continue
        for row in result.get("reviews", []):
            rows.setdefault((result["critic_id"], row.get("group")), []).append(row)
    return rows


def evaluate(primary_root: Path, source: str, supplemental_root: Path | None) -> dict:
    primary = load_rows(primary_root, source, {"primary"})
    supplemental = load_rows(supplemental_root, source, {"supplement-1", "supplement-2"}) if supplemental_root else {}
    errors = []
    dissent_requests = []
    decisions = []
    quorums = []
    for role in sorted(DIMS):
        for group in sorted(SOURCE_GROUPS):
            key = (role, group)
            base = primary.get(key, [])
            if len(base) != 1:
                errors.append(f"expected one primary {role}/{group}, got {len(base)}")
                continue
            base_state = classify(base[0], source, role, group)
            if base_state == "INCOMPLETE":
                errors.append(f"incomplete primary {role}/{group}")
                continue
            if base_state == "PASS":
                decisions.append({"critic_id": role, "group": group, "status": "PASS", "clean_votes": 1, "total_votes": 1})
                continue
            dissent_requests.append({"critic_id": role, "group": group})
            supplements = supplemental.get(key, [])
            if supplemental_root is None:
                decisions.append({"critic_id": role, "group": group, "status": "ADJUDICATION_REQUIRED", "clean_votes": 0, "total_votes": 1})
                continue
            if len(supplements) != 2:
                errors.append(f"expected two supplemental judgments {role}/{group}, got {len(supplements)}")
                continue
            states = [classify(row, source, role, group) for row in supplements]
            if "INCOMPLETE" in states:
                errors.append(f"incomplete supplemental judgment {role}/{group}")
                continue
            clean = states.count("PASS")
            if clean == 2:
                decisions.append({"critic_id": role, "group": group, "status": "PASS_BY_QUORUM", "clean_votes": 2, "total_votes": 3})
                quorums.append({"critic_id": role, "group": group, "primary": "DISSENT", "supplemental": states, "clean_votes": 2, "total_votes": 3})
            else:
                decisions.append({"critic_id": role, "group": group, "status": "FAIL", "clean_votes": clean, "total_votes": 3})
    pending = supplemental_root is None and bool(dissent_requests) and not errors
    failed = any(row["status"] == "FAIL" for row in decisions)
    passed = not errors and not pending and not failed and len(decisions) == 6
    return {
        "task": "T04", "source": source,
        "status": "PASS_BY_QUORUM" if passed and quorums else "PASS" if passed else "ADJUDICATION_REQUIRED" if pending else "FAIL",
        "passed": passed, "strict_rule": ">9.0 unrounded; no score averaging; dissent only uses 2-of-3 same-role quorum",
        "decisions": decisions, "adjudication_requests": dissent_requests, "quorums": quorums,
        "errors": errors, "completed_low_scores_retried": False, "score_averaging": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--primary", type=Path, required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--supplemental", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(args.primary, args.source, args.supplemental)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if report["passed"]:
        return 0
    return 3 if report["status"] == "ADJUDICATION_REQUIRED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
