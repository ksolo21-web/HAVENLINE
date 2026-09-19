#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from forward_execution import DOCS, ROOT, resolve_task

MATRIX = DOCS / "TASK_CAPABILITY_MATRIX.json"
STATUS = DOCS / "CAPABILITY_STATUS.json"
READY = "READY"
VALID_EXTERNAL_STATES = {"READY", "UNVERIFIED", "UNAVAILABLE", "DEFERRED"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _requirements(task_id: str, plan: dict[str, Any], matrix: dict[str, Any]) -> list[str]:
    req: set[str] = set(matrix.get("base_requirements", []))
    req.update(matrix.get("mode_requirements", {}).get(plan["execution_mode"], []))
    req.update(matrix.get("archetype_requirements", {}).get(plan["archetype"], []))
    for critic in plan["critics"]:
        req.update(matrix.get("critic_requirements", {}).get(critic, []))
    req.update(matrix.get("task_overrides", {}).get(task_id, {}).get("required", []))
    return sorted(req)


def _probe_repository(row: dict[str, Any]) -> tuple[str, list[str]]:
    missing: list[str] = []
    for rel in row.get("probe_all", []):
        if not (ROOT / rel).exists():
            missing.append(rel)
    any_group = list(row.get("probe_any", []))
    if any_group and not any((ROOT / rel).exists() for rel in any_group):
        missing.append("ANY_OF:" + "|".join(any_group))
    return (READY if not missing else "MISSING_LOCAL"), missing


def resolve_capabilities(task_id: str) -> dict[str, Any]:
    task_id = task_id.upper()
    plan = resolve_task(task_id)
    matrix = load_json(MATRIX)
    status = load_json(STATUS)
    catalog = matrix.get("catalog", {})
    required = _requirements(task_id, plan, matrix)
    results: dict[str, Any] = {}
    errors: list[str] = []
    for capability in required:
        row = catalog.get(capability)
        if row is None:
            errors.append(f"unknown capability referenced by {task_id}: {capability}")
            continue
        kind = row.get("kind")
        if kind == "repository":
            state, missing = _probe_repository(row)
            results[capability] = {"kind": kind, "state": state, "missing": missing, "evidence": "repository probe"}
        elif kind in {"external", "hardware"}:
            key = row.get("status_key", capability)
            ext = status.get("external", {}).get(key)
            if not isinstance(ext, dict):
                errors.append(f"{capability} has no external status record {key}")
                results[capability] = {"kind": kind, "state": "UNVERIFIED", "evidence": None}
                continue
            state = ext.get("state")
            if state not in VALID_EXTERNAL_STATES:
                errors.append(f"{capability} invalid external state {state!r}")
            if state == READY and status.get("policy", {}).get("external_status_requires_evidence_reference") and not ext.get("evidence"):
                errors.append(f"{capability} cannot be READY without evidence reference")
                state = "UNVERIFIED"
            results[capability] = {"kind": kind, "state": state, "evidence": ext.get("evidence"), "note": ext.get("note")}
        else:
            errors.append(f"{capability} invalid capability kind {kind!r}")

    blockers = sorted(name for name, row in results.items() if row.get("state") != READY)
    capabilities_ready = not blockers and not errors
    if not plan["dependencies_approved"]:
        activation_state = "PREP_ONLY"
    elif not plan["canonical_packet_present"]:
        activation_state = "PREP_REQUIRED"
    elif not capabilities_ready:
        activation_state = "BLOCKED_CAPABILITY"
    else:
        activation_state = "READY_NOW"
    return {
        "task_id": task_id,
        "task_name": plan["task_name"],
        "execution_mode": plan["execution_mode"],
        "archetype": plan["archetype"],
        "dependencies_approved": plan["dependencies_approved"],
        "canonical_packet_present": plan["canonical_packet_present"],
        "required_capabilities": required,
        "capabilities": results,
        "capabilities_ready": capabilities_ready,
        "capability_blockers": blockers,
        "activation_state": activation_state,
        "runtime_activation_allowed": activation_state == "READY_NOW",
        "preparation_allowed": True,
        "errors": errors,
    }


def validate_all() -> dict[str, Any]:
    matrix = load_json(MATRIX)
    status = load_json(STATUS)
    errors: list[str] = []
    catalog = matrix.get("catalog", {})
    if matrix.get("scope") != "T10-T70":
        errors.append("capability matrix scope must be T10-T70")
    for name, row in catalog.items():
        if row.get("kind") not in {"repository", "external", "hardware"}:
            errors.append(f"capability {name} has invalid kind")
    for key, row in status.get("external", {}).items():
        if row.get("state") not in VALID_EXTERNAL_STATES:
            errors.append(f"external status {key} invalid state")
        if row.get("state") == READY and status.get("policy", {}).get("external_status_requires_evidence_reference") and not row.get("evidence"):
            errors.append(f"external status {key} READY without evidence")
    resolved: dict[str, str] = {}
    for i in range(10, 71):
        task_id = f"T{i:02d}"
        try:
            report = resolve_capabilities(task_id)
            resolved[task_id] = report["activation_state"]
            errors.extend(f"{task_id}: {x}" for x in report["errors"])
        except Exception as exc:
            errors.append(f"{task_id}: feasibility resolution failed: {exc}")
    return {"passed": not errors, "task_count": len(resolved), "activation_states": resolved, "errors": errors}


def main() -> int:
    ap = argparse.ArgumentParser(description="Resolve Havenline V3 task feasibility")
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    task = sub.add_parser("task")
    task.add_argument("task_id")
    task.add_argument("--output")
    args = ap.parse_args()
    report = validate_all() if args.command == "validate" else resolve_capabilities(args.task_id)
    text = json.dumps(report, indent=2) + "\n"
    if getattr(args, "output", None):
        out = (ROOT / args.output).resolve(); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(text)
    print(text, end="")
    return 0 if not report.get("errors") else 2


if __name__ == "__main__":
    raise SystemExit(main())
