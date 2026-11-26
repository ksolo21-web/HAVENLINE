#!/usr/bin/env python3
"""Validate the scoped review against its candidate and evidence; exit 1 on HOLD."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path


def check(policy, review, source, root):
    problems = []
    if not re.fullmatch(r"[0-9a-f]{40}", source) or review.get("source") != source:
        problems.append("Candidate source does not match the requested full commit.")
    if review.get("scene") != policy["scene"]:
        problems.append("Wrong scene.")
    expected = {f"{group}.{key}" for group, spec in policy["scopes"].items()
                for key in spec["dimensions"]}
    rows = review["dimensions"]
    if set(rows) != expected:
        problems.append(f"Dimension set differs: {sorted(set(rows) ^ expected)}")
    checked = {}
    for key in sorted(expected & set(rows)):
        row = rows[key]
        limit = policy["style_minimums"].get(key.split(".")[1], policy["minimum"])
        score = row.get("score")
        if (type(score) not in (int, float) or not math.isfinite(score)
                or not limit <= score <= 10):
            problems.append(f"{key}: {score!r} (requires {limit:g})")
        if row.get("status") != "pass" or row.get("mandatory_defects") != []:
            problems.append(f"{key}: {row.get('status', 'missing result')}")
        if row.get("source") != source:
            problems.append(f"{key}: missing exact-candidate review")
        reviewer = row.get("reviewer")
        authors = row.get("authors")
        if not reviewer or not isinstance(authors, list) or not authors or reviewer in authors:
            problems.append(f"{key}: independent reviewer required")
        evidence = row.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            problems.append(f"{key}: no evidence")
            continue
        for entry in evidence:
            filename = entry["file"]
            path = (root / filename).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                problems.append(f"{key}: evidence missing {filename}")
                continue
            if path not in checked:
                with path.open("rb") as stream:
                    checked[path] = hashlib.file_digest(stream, "sha256").hexdigest()
            if entry.get("sha256") != checked[path]:
                problems.append(f"{key}: evidence hash mismatch {filename}")
        if key == "ultra.device_frame_pacing" and row.get("device_trace") != "physical":
            problems.append(f"{key}: physical device recording required")
    return problems


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("source", help="Full ID of gameplay commit to approve")
    cli.add_argument("--review", type=Path, default=here.parent / "review.json")
    args = cli.parse_args()
    try:
        problems = check(json.loads((here / "policy.json").read_text()),
                         json.loads(args.review.read_text()), args.source, here.parent)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        raise SystemExit(f"Invalid review: {error}")
    print("\n".join(problems + (["HOLD"] if problems else ["PASS"])))
    raise SystemExit(bool(problems))
