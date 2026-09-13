#!/usr/bin/env python3
"""Classify strict visual reviews without turning one outlier into a repair loop."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


ROLES = {"reference-fidelity", "visual-integrity"}
DIMS = {
    "reference_fidelity",
    "boundary_finish",
    "gate_readability",
    "lane_legibility",
    "river_preservation",
    "view_consistency",
}


def load_reviews(root: Path, source: str) -> tuple[dict[tuple[str, str], dict], list[str]]:
    reviews: dict[tuple[str, str], dict] = {}
    errors: list[str] = []
    for path in sorted(root.rglob("shard-review.json")):
        shard = json.loads(path.read_text())
        role = shard.get("role")
        if role not in ROLES or shard.get("source") != source:
            errors.append(f"bad shard provenance: {path}")
            continue
        if shard.get("competency_passed") is not True or shard.get("error") is not None:
            errors.append(f"incomplete shard: {role}/{shard.get('shard')}")
        for row in shard.get("reviews", []):
            group = row.get("group")
            key = (role, group)
            if key in reviews:
                errors.append(f"duplicate judgment: {role}/{group}")
            reviews[key] = row
    return reviews, errors


def classify(row: dict, source: str) -> tuple[str, list[str]]:
    label = f"{row.get('role')}/{row.get('group')}"
    reasons: list[str] = []
    if row.get("source") != source or row.get("independent_execution") is not True:
        reasons.append(f"{label}: bad source or execution provenance")
    if row.get("error") is not None:
        reasons.append(f"{label}: reviewer error: {row.get('error')}")
    review = row.get("review")
    if not isinstance(review, dict):
        reasons.append(f"{label}: missing review")
        return "INCOMPLETE", reasons
    scores = review.get("scores")
    if not isinstance(scores, dict) or set(scores) != DIMS or any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or not 0 <= value <= 10
        for value in scores.values()
    ):
        reasons.append(f"{label}: malformed mandatory scores")
    if not review.get("observations"):
        reasons.append(f"{label}: missing observations")
    if review.get("coverage_complete") is not True:
        reasons.append(f"{label}: incomplete response coverage")
    if review.get("confidence") not in ("medium", "high"):
        reasons.append(f"{label}: insufficient confidence")
    if reasons:
        return "INCOMPLETE", reasons
    defects = review.get("defects")
    if not isinstance(defects, list):
        return "INCOMPLETE", [f"{label}: malformed defects"]
    if defects or any(value <= 9.0 for value in scores.values()):
        return "DISSENT", []
    return "PASS", []


def evaluate(
    base: Path,
    source: str,
    expected_groups: set[str],
    adjudication: Path | None,
    supplemental: Path | None = None,
) -> dict:
    reviews, errors = load_reviews(base, source)
    expected = {(role, group) for role in ROLES for group in expected_groups}
    missing = sorted(expected - set(reviews))
    extra = sorted(set(reviews) - expected)
    errors += [f"missing judgment: {role}/{group}" for role, group in missing]
    errors += [f"unexpected judgment: {role}/{group}" for role, group in extra]

    states: dict[tuple[str, str], str] = {}
    state_reasons: dict[tuple[str, str], list[str]] = {}
    for key in sorted(expected & set(reviews)):
        state, reasons = classify(reviews[key], source)
        states[key] = state
        state_reasons[key] = reasons

    supplemental_adjudications: list[dict] = []
    if supplemental is not None:
        payload = json.loads(supplemental.read_text())
        if not isinstance(payload, list):
            errors.append("supplemental review payload must be a list")
            payload = []
        for row in payload:
            if not isinstance(row, dict):
                errors.append("malformed supplemental row")
                continue
            purpose = row.get("purpose")
            if purpose == "retry":
                key = (row.get("role"), row.get("group"))
                if states.get(key) != "INCOMPLETE":
                    errors.append(f"retry did not replace an incomplete judgment: {key}")
                    continue
                reviews[key] = row
                state, reasons = classify(row, source)
                states[key] = state
                state_reasons[key] = reasons
            elif purpose == "adjudication":
                supplemental_adjudications.append(row)
            else:
                errors.append("unknown supplemental review purpose")

    errors += [reason for reasons in state_reasons.values() for reason in reasons]

    incomplete = sorted(f"{role}/{group}" for (role, group), state in states.items() if state == "INCOMPLETE")
    dissent = sorted((role, group) for (role, group), state in states.items() if state == "DISSENT")
    passed = sorted(f"{role}/{group}" for (role, group), state in states.items() if state == "PASS")
    status = "FAIL"
    quorums: list[dict] = []

    if errors or incomplete:
        status = "RETRY_REQUIRED"
    elif not dissent:
        status = "PASS"
    else:
        split_groups: dict[str, tuple[str, str]] = {}
        for dissent_role, dissent_group in dissent:
            paired_role = next(iter(ROLES - {dissent_role}))
            if states.get((paired_role, dissent_group)) != "PASS" or dissent_group in split_groups:
                break
            split_groups[dissent_group] = (dissent_role, paired_role)
        else:
            status = "ADJUDICATION_REQUIRED"
            if adjudication is not None or supplemental_adjudications:
                payload = json.loads(adjudication.read_text()) if adjudication is not None else supplemental_adjudications
                rows = payload if isinstance(payload, list) else [payload]
                by_group = {row.get("group"): row for row in rows if isinstance(row, dict)}
                if set(by_group) != set(split_groups):
                    errors.append("adjudicator group coverage mismatch")
                adjudicator_failed = False
                adjudicator_incomplete = False
                for group, (dissent_role, paired_role) in sorted(split_groups.items()):
                    row = by_group.get(group, {})
                    state, adjudication_errors = classify(row, source)
                    errors += adjudication_errors
                    if row.get("role") != "independent-adjudicator":
                        errors.append(f"adjudicator identity mismatch: {group}")
                    if state == "INCOMPLETE":
                        adjudicator_incomplete = True
                    elif state == "DISSENT":
                        adjudicator_failed = True
                    else:
                        quorums.append({
                            "group": group,
                            "original_pass_role": paired_role,
                            "original_dissent_role": dissent_role,
                            "adjudicator": "independent-adjudicator",
                            "clean_votes": 2,
                            "total_votes": 3,
                        })
                if errors or adjudicator_incomplete:
                    status = "RETRY_REQUIRED"
                elif adjudicator_failed:
                    status = "FAIL"
                else:
                    status = "PASS_BY_QUORUM"

    return {
        "task": "T03",
        "source": source,
        "status": status,
        "passed": status in {"PASS", "PASS_BY_QUORUM"},
        "strict_rule": ">9.0 unrounded; no score averaging",
        "judgments_expected": len(expected),
        "judgments_present": len(reviews),
        "passed_judgments": passed,
        "incomplete_judgments": incomplete,
        "dissent_judgments": [f"{role}/{group}" for role, group in dissent],
        "quorums": quorums,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviews", type=Path, required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--groups", required=True, help="Comma-separated mandatory evidence groups")
    parser.add_argument("--adjudication", type=Path)
    parser.add_argument("--supplemental", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(args.reviews, args.source, set(args.groups.split(",")), args.adjudication, args.supplemental)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
