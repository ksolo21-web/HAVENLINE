#!/usr/bin/env python3
"""Validate complete T12 R01-R16 acceptance traceability preparation."""
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

EXPECTED_IDS = [f"T12-R{i:02d}" for i in range(1, 17)]
REQUIRED_CRITICS = {"C2", "C3", "C4", "C6", "C7"}
MANDATORY_CRITIC_REQUIREMENTS = {
    "T12-R03": {"C3"},
    "T12-R06": {"C3"},
    "T12-R11": {"C3"},
    "T12-R12": {"C6"},
    "T12-R16": REQUIRED_CRITICS,
}


def validate_traceability(data: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if data.get("task_id") != "T12":
        errors.append("task_id must be T12")
    if data.get("status") != "PREPARATION_TRACEABILITY_PLAN":
        errors.append("status must remain PREPARATION_TRACEABILITY_PLAN")

    declared_critics = data.get("required_critics")
    if not isinstance(declared_critics, list) or set(declared_critics) != REQUIRED_CRITICS:
        errors.append("required_critics must be exactly C2/C3/C4/C6/C7")

    rule = data.get("acceptance_rule")
    if not isinstance(rule, dict):
        errors.append("acceptance_rule must be an object")
    else:
        if rule.get("operator") != ">" or rule.get("threshold") != 9.0 or rule.get("unrounded") is not True:
            errors.append("acceptance rule must remain strictly >9.0 unrounded")
        if rule.get("target") != 10.0:
            errors.append("acceptance target must remain 10.0")
        if rule.get("zero_unresolved_mandatory_defects") is not True:
            errors.append("zero unresolved mandatory defects must remain required")

    requirements = data.get("requirements")
    if not isinstance(requirements, list):
        return {"passed": False, "requirement_count": 0, "errors": errors + ["requirements must be a list"]}

    ids = [row.get("id") for row in requirements if isinstance(row, dict)]
    if ids != EXPECTED_IDS:
        errors.append(f"requirements must appear exactly once in frozen order {EXPECTED_IDS}; got {ids}")

    for index, row in enumerate(requirements):
        if not isinstance(row, dict):
            errors.append(f"requirements[{index}] must be an object")
            continue
        req_id = row.get("id")
        if not isinstance(row.get("name"), str) or not row["name"].strip():
            errors.append(f"{req_id}: name must be non-empty")
        for key in ("prepared_checks", "shipping_tests", "required_evidence", "critics"):
            value = row.get(key)
            if not isinstance(value, list) or not value:
                errors.append(f"{req_id}: {key} must be a non-empty list")
                continue
            if any(not isinstance(item, str) or not item.strip() for item in value):
                errors.append(f"{req_id}: {key} contains invalid/empty entries")
        critics = set(row.get("critics", [])) if isinstance(row.get("critics"), list) else set()
        unknown = critics - REQUIRED_CRITICS
        if unknown:
            errors.append(f"{req_id}: unknown critics {sorted(unknown)}")
        mandatory = MANDATORY_CRITIC_REQUIREMENTS.get(str(req_id), set())
        missing = mandatory - critics
        if missing:
            errors.append(f"{req_id}: missing mandatory critic coverage {sorted(missing)}")

    # High-risk requirements must explicitly contain the evidence concepts that prevent shallow sign-off.
    by_id = {row.get("id"): row for row in requirements if isinstance(row, dict)}
    concept_requirements = {
        "T12-R01": ("100", "graph"),
        "T12-R03": ("cadence", "milestone"),
        "T12-R05": ("binding", "mutation"),
        "T12-R07": ("spend", "energy"),
        "T12-R08": ("replay", "duplicate"),
        "T12-R10": ("reachability", "1->100"),
        "T12-R12": ("performance", "unchanged"),
        "T12-R14": ("ownership", "changed-file"),
        "T12-R15": ("activation", "dependency"),
        "T12-R16": ("critic", "G1-G14"),
    }
    for req_id, concepts in concept_requirements.items():
        row = by_id.get(req_id, {})
        blob = " ".join(str(x) for key in ("prepared_checks", "shipping_tests", "required_evidence") for x in row.get(key, []))
        for concept in concepts:
            if concept.lower() not in blob.lower():
                errors.append(f"{req_id}: traceability coverage must explicitly include concept {concept!r}")

    return {"passed": not errors, "requirement_count": len(requirements), "errors": errors}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="Docs/Production/T12/ACCEPTANCE_TRACEABILITY.json")
    args = parser.parse_args()
    data = json.loads(pathlib.Path(args.input).read_text())
    result = validate_traceability(data)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
