#!/usr/bin/env python3
"""Compare future Godot T12 vector output with the frozen preparation oracle.

No engine output exists before activation; unit tests exercise this comparator
with synthetic output generated from the frozen vectors.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[3]
DEFAULT_VECTORS = ROOT / "Docs" / "Production" / "T12" / "ENGINE_TEST_VECTORS.json"
DEFAULT_SCHEMA = ROOT / "Docs" / "Production" / "T12" / "ENGINE_PARITY_OUTPUT_SCHEMA.json"
EXPECTED_RESULT_FIELDS = {
    "vector_id",
    "eligible_level_ids",
    "new_one_time_event_ids",
    "state_hash_before",
    "state_hash_after",
    "repeat_output_hashes",
}


def compare(actual: dict[str, Any], vectors: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if schema.get("schema_version") != 1:
        errors.append("engine parity output schema_version must be 1")
    if schema.get("task_id") != "T12" or schema.get("status") != "PREPARATION_ONLY_EVIDENCE_SCHEMA":
        errors.append("engine parity output schema identity/status drifted")
    if vectors.get("schema_version") != 1:
        errors.append("engine test vectors schema_version must be 1")
    if vectors.get("task_id") != "T12" or vectors.get("status") != "PREPARATION_ONLY_TEST_VECTORS":
        errors.append("engine test vectors identity/status drifted")
    if set(schema.get("vector_result_required_fields", [])) != EXPECTED_RESULT_FIELDS:
        errors.append("engine parity output required vector fields drifted")

    if actual.get("task_id") != "T12":
        errors.append("actual task_id must be T12")
    candidate = actual.get("candidate_source")
    if not isinstance(candidate, str) or re.fullmatch(r"[0-9a-f]{40}", candidate) is None:
        errors.append("candidate_source must be an exact lowercase 40-hex commit SHA")

    expected_rows = vectors.get("vectors")
    if not isinstance(expected_rows, list):
        expected_rows = []
        errors.append("ENGINE_TEST_VECTORS vectors must be a list")
    expected = {
        row.get("id"): row.get("expected")
        for row in expected_rows
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    }

    rows = actual.get("vector_results")
    if not isinstance(rows, list):
        rows = []
        errors.append("actual vector_results must be a list")

    seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"vector_results[{index}] must be an object")
            continue
        if set(row) != EXPECTED_RESULT_FIELDS:
            errors.append(f"vector_results[{index}] fields mismatch")
        vector_id = row.get("vector_id")
        if not isinstance(vector_id, str) or not vector_id:
            errors.append(f"vector_results[{index}].vector_id must be non-empty")
            continue
        if vector_id in seen:
            errors.append(f"duplicate vector result {vector_id}")
            continue
        seen.add(vector_id)
        if vector_id not in expected:
            errors.append(f"unknown vector result {vector_id}")
            continue

        expected_output = expected[vector_id]
        actual_output = {
            "eligible_level_ids": row.get("eligible_level_ids"),
            "new_one_time_event_ids": row.get("new_one_time_event_ids"),
        }
        if actual_output != expected_output:
            errors.append(f"{vector_id}: engine output differs from frozen reference expected output")

        before = row.get("state_hash_before")
        after = row.get("state_hash_after")
        if not isinstance(before, str) or not before or before != after:
            errors.append(f"{vector_id}: pure query mutated state or emitted invalid state hash")

        repeats = row.get("repeat_output_hashes")
        if not isinstance(repeats, list) or len(repeats) < 2:
            errors.append(f"{vector_id}: repeat_output_hashes must contain at least two values")
        elif any(not isinstance(x, str) or not x for x in repeats) or len(set(repeats)) != 1:
            errors.append(f"{vector_id}: identical repeated queries were not deterministic")

    missing = sorted(set(expected) - seen)
    if missing:
        errors.append(f"missing engine vector results: {missing}")

    return {
        "passed": not errors,
        "expected_vector_count": len(expected),
        "actual_vector_count": len(rows),
        "errors": errors,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--actual", required=True, help="Future Godot engine parity output JSON")
    ap.add_argument("--vectors", default=str(DEFAULT_VECTORS.relative_to(ROOT)))
    ap.add_argument("--schema", default=str(DEFAULT_SCHEMA.relative_to(ROOT)))
    args = ap.parse_args()
    actual = json.loads((ROOT / args.actual).read_text())
    vectors = json.loads((ROOT / args.vectors).read_text())
    schema = json.loads((ROOT / args.schema).read_text())
    result = compare(actual, vectors, schema)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
