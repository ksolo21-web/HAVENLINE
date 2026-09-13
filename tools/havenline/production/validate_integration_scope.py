#!/usr/bin/env python3
"""Validate commit-local integration ownership without freezing governance to one task."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from lib import DOCS, any_match, changed_files, expand_alias, load_json
from workstream import approved_change_requests

INTEGRATION_STATES = {"INTEGRATION_READY", "INTEGRATING", "UNDER_REVIEW", "FIX_REQUIRED", "APPROVED"}


def evaluate(files: list[str], registry: dict, ownership: dict, authorized: dict[str, set[str]] | None = None) -> dict:
    authorized = authorized or {}
    qa_patterns = ownership["aliases"].get("@ownership:QA-GOV", [])
    integration_only = ownership["aliases"].get("@integration-only", [])
    workstreams = [w for w in registry["workstreams"] if w.get("task_id", "").startswith("T")]
    errors: list[str] = []
    task_files: dict[str, list[str]] = {}
    integration_files: list[str] = []
    governance_files: list[str] = []

    for path in files:
        if any_match(path, qa_patterns):
            governance_files.append(path)
            continue
        if any_match(path, integration_only):
            integration_files.append(path)
            continue
        matches = []
        for ws in workstreams:
            patterns = expand_alias(ws.get("owned_paths", []), ownership)
            if any_match(path, patterns):
                matches.append(ws)
        if len(matches) != 1:
            errors.append(f"integration path must have exactly one registered task owner: {path} ({len(matches)} matches)")
            continue
        ws = matches[0]
        task_id = ws["task_id"]
        if ws.get("status") not in INTEGRATION_STATES:
            errors.append(f"{task_id} runtime path changed while task state is {ws.get('status')}, not integration-ready: {path}")
        task_files.setdefault(task_id, []).append(path)

    task_ids = sorted(task_files)
    if len(task_ids) > 1:
        errors.append(f"sequential integration commit spans multiple task owners: {task_ids}")

    for path in integration_files:
        if len(task_ids) != 1:
            errors.append(f"integration-only path requires exactly one task-scoped runtime change: {path}")
            continue
        task_id = task_ids[0]
        if path not in authorized.get(task_id, set()):
            errors.append(f"integration-only path lacks authorized change request for {task_id}: {path}")

    task_id = task_ids[0] if len(task_ids) == 1 else None
    task_status = None
    if task_id:
        task_status = next(w["status"] for w in workstreams if w["task_id"] == task_id)
    return {
        "passed": not errors,
        "classification": "GOVERNANCE_ONLY" if not task_files and not integration_files and not errors else "TASK_INTEGRATION",
        "task_id": task_id,
        "task_status": task_status,
        "changed_files": files,
        "governance_files": governance_files,
        "task_files": task_files,
        "integration_only_files": integration_files,
        "errors": errors,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    registry = load_json(DOCS / "WORKSTREAM_REGISTRY.json")
    ownership = load_json(DOCS / "PATH_OWNERSHIP.json")
    authorizations = {
        w["task_id"]: approved_change_requests(w["task_id"])
        for w in registry["workstreams"] if w.get("task_id", "").startswith("T")
    }
    report = evaluate(changed_files(args.base, args.head), registry, ownership, authorizations)
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text, end="")
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
