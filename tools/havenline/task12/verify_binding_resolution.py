#!/usr/bin/env python3
"""Verify T12 reconciliation of accepted T10/T11 public identifiers.

Default mode is a pre-activation guard: the resolution template must remain
unresolved/blank while T10 or T11 is unfinished. --require-resolved switches to
a future activation-time proof that verifies exact accepted dependency commits,
completion records and repository-backed JSON-pointer identity evidence.

This tool never edits upstream files and never promotes shipping data.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[3]
EXPECTED_TASKS = ("T10", "T11")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
FORBIDDEN_ID_MARKERS = ("provisional", "prepared", "example", "debug", "fixture", "test_only", "test-only")


def decode_pointer_token(token: str) -> str:
    return token.replace("~1", "/").replace("~0", "~")


def resolve_json_pointer(document: Any, pointer: str) -> Any:
    if pointer == "":
        return document
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ValueError("json_pointer must be empty or begin with /")
    current = document
    for raw in pointer.split("/")[1:]:
        token = decode_pointer_token(raw)
        if isinstance(current, list):
            if not token.isdigit():
                raise KeyError(token)
            index = int(token)
            current = current[index]
        elif isinstance(current, dict):
            current = current[token]
        else:
            raise KeyError(token)
    return current


def completion_source(record: dict[str, Any]) -> str | None:
    for key in ("integrated_source", "accepted_source", "accepted_integrated_source", "candidate_source"):
        value = record.get(key)
        if isinstance(value, str) and HEX40.fullmatch(value):
            return value
    return None


def completion_passes(record: dict[str, Any]) -> bool:
    status = str(record.get("status", "")).upper()
    return status in {"PASS", "APPROVED"}


def validate_resolution(resolution: dict[str, Any], *, require_resolved: bool, root: pathlib.Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    verified_ids = 0

    if resolution.get("task_id") != "T12":
        errors.append("task_id must be T12")
    dependencies = resolution.get("dependencies")
    if not isinstance(dependencies, dict):
        return {"passed": False, "verified_ids": 0, "errors": ["dependencies must be an object"]}

    for task in EXPECTED_TASKS:
        entry = dependencies.get(task)
        if not isinstance(entry, dict):
            errors.append(f"missing dependency resolution entry: {task}")
            continue
        source = entry.get("accepted_integrated_source")
        ids = entry.get("resolved_public_ids")
        completion_path = entry.get("verified_completion_path")

        if not isinstance(ids, list):
            errors.append(f"{task}.resolved_public_ids must be a list")
            ids = []

        if not require_resolved:
            if source not in ("", None):
                errors.append(f"{task} accepted_integrated_source must remain blank before activation reconciliation")
            if ids:
                errors.append(f"{task} resolved_public_ids must remain empty before activation reconciliation")
            continue

        if not isinstance(source, str) or not HEX40.fullmatch(source):
            errors.append(f"{task} accepted_integrated_source must be an exact 40-hex commit")
        if not isinstance(completion_path, str) or not completion_path:
            errors.append(f"{task} verified_completion_path must be set")
            continue
        completion_file = root / completion_path
        if not completion_file.is_file():
            errors.append(f"{task} completion record missing: {completion_path}")
            continue
        try:
            completion = json.loads(completion_file.read_text())
        except Exception as exc:
            errors.append(f"{task} completion record unreadable: {exc}")
            continue
        if not isinstance(completion, dict) or not completion_passes(completion):
            errors.append(f"{task} completion record is not PASS/APPROVED")
        accepted = completion_source(completion) if isinstance(completion, dict) else None
        if accepted is None:
            errors.append(f"{task} completion record has no recognized accepted/integrated commit field")
        elif source != accepted:
            errors.append(f"{task} resolution source {source!r} does not match completion source {accepted!r}")

        if not ids:
            errors.append(f"{task} must resolve at least one public ID before activation")
            continue

        seen: set[str] = set()
        for index, item in enumerate(ids):
            prefix = f"{task}.resolved_public_ids[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} must be an object")
                continue
            public_id = item.get("id")
            kind = item.get("kind")
            source_path = item.get("source_path")
            pointer = item.get("json_pointer")
            if not isinstance(public_id, str) or not public_id.strip():
                errors.append(f"{prefix}.id must be non-empty")
                continue
            normalized = public_id.lower()
            if any(marker in normalized for marker in FORBIDDEN_ID_MARKERS):
                errors.append(f"{prefix}.id looks provisional/test-only: {public_id}")
            if public_id in seen:
                errors.append(f"{task} duplicate resolved ID: {public_id}")
            seen.add(public_id)
            if not isinstance(kind, str) or not kind.strip():
                errors.append(f"{prefix}.kind must be non-empty")
            if not isinstance(source_path, str) or not source_path:
                errors.append(f"{prefix}.source_path must be non-empty")
                continue
            evidence_file = root / source_path
            if not evidence_file.is_file():
                errors.append(f"{prefix} source file missing: {source_path}")
                continue
            if evidence_file.suffix.lower() != ".json":
                errors.append(f"{prefix} source_path must point to JSON for exact pointer proof")
                continue
            try:
                document = json.loads(evidence_file.read_text())
                resolved = resolve_json_pointer(document, pointer)
            except Exception as exc:
                errors.append(f"{prefix} pointer proof failed: {exc}")
                continue
            if resolved != public_id:
                errors.append(f"{prefix} pointer resolves to {resolved!r}, expected {public_id!r}")
                continue
            verified_ids += 1

    expected_status = "RESOLVED_FOR_ACTIVATION" if require_resolved else "PREPARATION_TEMPLATE_UNRESOLVED"
    if resolution.get("status") != expected_status:
        errors.append(f"status must be {expected_status} in this mode")
    expected_promotion = True if require_resolved else False
    if resolution.get("promotion_allowed") is not expected_promotion:
        errors.append(f"promotion_allowed must be {expected_promotion} in this mode")

    return {"passed": not errors, "mode": "require_resolved" if require_resolved else "preactivation_blank", "verified_ids": verified_ids, "errors": errors}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resolution", default="Docs/Production/T12/BINDING_RESOLUTION_TEMPLATE.json")
    parser.add_argument("--require-resolved", action="store_true")
    args = parser.parse_args()
    resolution = json.loads(pathlib.Path(args.resolution).read_text())
    result = validate_resolution(resolution, require_resolved=args.require_resolved)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
