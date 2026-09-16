#!/usr/bin/env python3
"""Validate prepared T12 downstream consumer boundaries."""
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

EXPECTED_REGION_CONSUMERS = {
    "T32": ("band_opening_frozen", [1,10]),
    "T44": ("band_forest", [11,20]),
    "T45": ("band_desert", [21,30]),
    "T46": ("band_underwater", [31,40]),
    "T47": ("band_sky", [41,50]),
    "T48": ("band_volcanic", [51,60]),
    "T49": ("band_swamp", [61,70]),
    "T50": ("band_ruins", [71,80]),
    "T51": ("band_underground", [81,90]),
    "T52": ("band_alien", [91,100]),
}
REQUIRED_CONSUMERS = {"T13","T14","T62",*EXPECTED_REGION_CONSUMERS.keys()}
REQUIRED_SHARED_OUTPUTS = {
    "current_level_id","completed_level_ids","unlockable_level_ids",
    "current_region_band_id","completed_milestone_ids","progression_intents",
    "progression_snapshot",
}


def semantic_blob(value: Any) -> str:
    """Serialize semantic text without escaping Unicode punctuation such as 1–100."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True).lower()


def validate_contract(data: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if data.get("task_id") != "T12":
        errors.append("task_id must be T12")
    if data.get("status") != "PREPARATION_ONLY_DOWNSTREAM_CONTRACT":
        errors.append("status must remain PREPARATION_ONLY_DOWNSTREAM_CONTRACT")

    outputs = data.get("shared_outputs")
    if not isinstance(outputs, dict):
        errors.append("shared_outputs must be an object")
        outputs = {}
    missing_outputs = sorted(REQUIRED_SHARED_OUTPUTS - set(outputs))
    if missing_outputs:
        errors.append(f"missing shared outputs: {missing_outputs}")

    consumers = data.get("consumers")
    if not isinstance(consumers, dict):
        return {"passed": False, "consumer_count": 0, "errors": errors + ["consumers must be an object"]}
    missing_consumers = sorted(REQUIRED_CONSUMERS - set(consumers))
    if missing_consumers:
        errors.append(f"missing required downstream consumers: {missing_consumers}")

    for task, (band, level_range) in EXPECTED_REGION_CONSUMERS.items():
        row = consumers.get(task)
        if not isinstance(row, dict):
            continue
        if row.get("owned_band") != band:
            errors.append(f"{task}: owned_band must be {band}")
        if row.get("owned_levels") != level_range:
            errors.append(f"{task}: owned_levels must be {level_range}")
        boundary = str(row.get("boundary", "")).lower()
        if "authors" not in boundary and "authors/integrates" not in boundary:
            errors.append(f"{task}: boundary must explicitly retain authored region/content ownership outside T12")

    t13 = consumers.get("T13", {}) if isinstance(consumers.get("T13"), dict) else {}
    t13_blob = semantic_blob(t13)
    for token in ("difficulty", "purchase", "vip", "payer"):
        if token not in t13_blob:
            errors.append(f"T13 boundary must explicitly cover {token}")

    t14 = consumers.get("T14", {}) if isinstance(consumers.get("T14"), dict) else {}
    t14_blob = semantic_blob(t14)
    for token in ("global save", "migration", "version"):
        if token not in t14_blob:
            errors.append(f"T14 boundary must explicitly retain {token} ownership outside T12")

    t62 = consumers.get("T62", {}) if isinstance(consumers.get("T62"), dict) else {}
    t62_blob = semantic_blob(t62)
    if "full level 1–100 acceptance" not in t62_blob and "complete level 1–100 acceptance" not in t62_blob:
        errors.append("T62 boundary must retain full Level 1–100 acceptance outside T12")
    if "release certification" not in t62_blob:
        errors.append("T62 boundary must not infer release certification from T12")

    rules = data.get("global_rules")
    if not isinstance(rules, list) or not rules:
        errors.append("global_rules must be non-empty")
        rules = []
    rules_blob = " ".join(str(x) for x in rules).lower()
    for token in ("purchase", "t12 never calls downstream", "change request"):
        if token not in rules_blob:
            errors.append(f"global downstream boundary rules must include {token!r}")

    return {"passed": not errors, "consumer_count": len(consumers), "errors": errors}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="Docs/Production/T12/DOWNSTREAM_CONSUMER_CONTRACT.json")
    args = parser.parse_args()
    data = json.loads(pathlib.Path(args.input).read_text())
    result = validate_contract(data)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
