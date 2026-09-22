#!/usr/bin/env python3
"""Pure non-shipping reference oracle for prepared T12 engine parity vectors.

The oracle exists only to freeze query/idempotency semantics before activation.
It does not write progression state or call any gameplay/upstream system.
"""
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[3]
DEFAULT_VECTORS = ROOT / "Docs" / "Production" / "T12" / "ENGINE_TEST_VECTORS.json"


def evaluate(levels: list[dict[str, Any]], state: dict[str, Any]) -> dict[str, list[str]]:
    ids: set[str] = set()
    numbers: set[int] = set()
    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(levels):
        if not isinstance(row, dict):
            raise ValueError(f"levels[{index}] must be an object")
        level = row.get("level")
        level_id = row.get("level_id")
        if not isinstance(level, int) or isinstance(level, bool) or not 1 <= level <= 100:
            raise ValueError(f"levels[{index}].level must be integer 1..100")
        if not isinstance(level_id, str) or not level_id:
            raise ValueError(f"levels[{index}].level_id must be non-empty")
        if level in numbers:
            raise ValueError(f"duplicate level number {level}")
        if level_id in ids:
            raise ValueError(f"duplicate level_id {level_id}")
        numbers.add(level)
        ids.add(level_id)
        for key in ("prerequisite_level_ids", "required_fact_ids", "one_time_event_ids"):
            value = row.get(key, [])
            if not isinstance(value, list) or any(not isinstance(x, str) or not x for x in value):
                raise ValueError(f"{level_id}.{key} must be a list of non-empty strings")
        normalized.append(row)

    completed = set(state.get("completed_level_ids", []))
    facts = set(state.get("observed_fact_ids", []))
    emitted = set(state.get("emitted_event_ids", []))
    if any(not isinstance(x, str) or not x for group in (completed, facts, emitted) for x in group):
        raise ValueError("state identifiers must be non-empty strings")

    eligible: list[str] = []
    new_events: list[str] = []
    for row in sorted(normalized, key=lambda item: (item["level"], item["level_id"])):
        level_id = row["level_id"]
        if level_id in completed:
            continue
        if not set(row.get("prerequisite_level_ids", [])).issubset(completed):
            continue
        if not set(row.get("required_fact_ids", [])).issubset(facts):
            continue
        eligible.append(level_id)
        for event_id in sorted(set(row.get("one_time_event_ids", []))):
            if event_id not in emitted:
                new_events.append(event_id)

    return {
        "eligible_level_ids": eligible,
        "new_one_time_event_ids": new_events,
    }


def run_vectors(data: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if data.get("task_id") != "T12":
        errors.append("task_id must be T12")
    if data.get("status") != "PREPARATION_ONLY_TEST_VECTORS":
        errors.append("status must remain PREPARATION_ONLY_TEST_VECTORS")
    vectors = data.get("vectors")
    if not isinstance(vectors, list) or not vectors:
        return {"passed": False, "vector_count": 0, "errors": errors + ["vectors must be a non-empty list"]}

    seen: set[str] = set()
    for index, case in enumerate(vectors):
        if not isinstance(case, dict):
            errors.append(f"vectors[{index}] must be an object")
            continue
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            errors.append(f"vectors[{index}].id must be non-empty")
            continue
        if case_id in seen:
            errors.append(f"duplicate vector id {case_id}")
            continue
        seen.add(case_id)
        try:
            actual = evaluate(case.get("levels", []), case.get("state", {}))
        except Exception as exc:  # fail closed with a useful case identity
            errors.append(f"{case_id}: oracle input rejected: {exc}")
            continue
        expected = case.get("expected")
        if actual != expected:
            errors.append(f"{case_id}: expected {expected}, got {actual}")

    rules_blob = " ".join(str(x) for x in data.get("semantic_rules", [])).lower()
    for token in ("pure", "deterministic", "set semantics", "one_time_event_id", "never grants inventory"):
        if token not in rules_blob:
            errors.append(f"semantic_rules missing {token!r}")

    return {"passed": not errors, "vector_count": len(vectors), "errors": errors}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=str(DEFAULT_VECTORS.relative_to(ROOT)))
    args = ap.parse_args()
    data = json.loads((ROOT / args.input).read_text())
    result = run_vectors(data)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
