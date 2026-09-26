#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from forward_execution import DOCS, ROOT

REGISTRY = DOCS / "CONTRACT_REGISTRY.json"
GRAPH = DOCS / "DEPENDENCY_GRAPH.json"
VALID_COMPAT = {"strict", "backward_compatible", "migration_required"}
VALID_CHANGE = {"compatible", "breaking"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _num(task_id: str) -> int:
    if len(task_id) != 3 or not task_id.startswith("T") or not task_id[1:].isdigit():
        raise ValueError(f"invalid task id {task_id}")
    return int(task_id[1:])


def expand_consumers(row: dict[str, Any]) -> list[str]:
    out = set(row.get("consumers", []))
    for start, end in row.get("consumer_ranges", []):
        a, b = _num(start), _num(end)
        if a > b:
            raise ValueError(f"invalid consumer range {start}-{end}")
        out.update(f"T{i:02d}" for i in range(a, b + 1))
    return sorted(out, key=_num)


def contracts_for_task(task_id: str) -> dict[str, list[dict[str, Any]]]:
    task_id = task_id.upper(); data = load_json(REGISTRY)
    produced: list[dict[str, Any]] = []; consumed: list[dict[str, Any]] = []
    for cid, row in data.get("contracts", {}).items():
        item = {"contract_id": cid, "version": row["version"], "compatibility": row["compatibility"], "owner": row["owner"], "description": row.get("description", "")}
        if row["owner"] == task_id: produced.append(item)
        if task_id in expand_consumers(row): consumed.append(item)
    return {"produces": produced, "consumes": consumed}


def affected_contracts(changed_files: list[str]) -> list[str]:
    data = load_json(REGISTRY); affected = []
    for cid, row in data.get("contracts", {}).items():
        for watched in row.get("watch_paths", []):
            if any(path == watched or path.startswith(watched.rstrip("/") + "/") for path in changed_files):
                affected.append(cid); break
    return sorted(set(affected))


def validate_registry() -> dict[str, Any]:
    data = load_json(REGISTRY); graph = load_json(GRAPH); errors: list[str] = []
    tasks = set(graph.get("tasks", {}))
    if data.get("schema_version") != 1: errors.append("contract registry schema_version must be 1")
    contracts = data.get("contracts", {})
    if not contracts: errors.append("contract registry must not be empty")
    for cid, row in contracts.items():
        owner = row.get("owner")
        if owner not in tasks:
            errors.append(f"{cid} owner {owner!r} is not a numbered task")
        if not isinstance(row.get("version"), int) or row.get("version", 0) < 1:
            errors.append(f"{cid} version must be positive integer")
        if row.get("compatibility") not in VALID_COMPAT:
            errors.append(f"{cid} invalid compatibility policy")
        try: consumers = expand_consumers(row)
        except Exception as exc:
            errors.append(f"{cid} consumer expansion failed: {exc}"); consumers = []
        unknown = sorted(set(consumers) - tasks)
        if unknown: errors.append(f"{cid} unknown consumers {unknown}")
        if owner in consumers: errors.append(f"{cid} owner cannot also be consumer")
        if not str(row.get("description", "")).strip(): errors.append(f"{cid} missing description")
        if not isinstance(row.get("watch_paths", []), list): errors.append(f"{cid} watch_paths must be list")
    return {"passed": not errors, "contract_count": len(contracts), "errors": errors}


def evaluate_change(descriptor: dict[str, Any]) -> dict[str, Any]:
    data = load_json(REGISTRY); graph = load_json(GRAPH); errors: list[str] = []
    cid = descriptor.get("contract_id"); row = data.get("contracts", {}).get(cid)
    if not row:
        return {"passed": False, "errors": [f"unknown contract {cid!r}"]}
    kind = descriptor.get("change_kind")
    if kind not in VALID_CHANGE: errors.append("change_kind must be compatible or breaking")
    before = descriptor.get("from_version"); after = descriptor.get("to_version")
    if before != row["version"]: errors.append(f"from_version must equal registered version {row['version']}")
    if not isinstance(after, int) or after < before: errors.append("to_version must be integer >= from_version")
    consumers = expand_consumers(row)
    active_consumers = [task for task in consumers if graph["tasks"][task]["status"] != "LOCKED"]
    revalidated = set(descriptor.get("consumer_revalidation", []))
    if kind == "breaking":
        if not isinstance(after, int) or after <= before: errors.append("breaking change requires version bump")
        if not str(descriptor.get("migration_plan", "")).strip(): errors.append("breaking change requires migration_plan")
        missing = sorted(set(active_consumers) - revalidated, key=_num)
        if missing: errors.append(f"breaking change missing active consumer revalidation: {missing}")
    if kind == "compatible" and descriptor.get("migration_plan") and row["compatibility"] == "strict":
        # Not an error; keep diagnostic so callers can audit why migration text exists.
        note = "strict contract declared compatible change with migration note"
    else: note = None
    return {
        "passed": not errors,
        "contract_id": cid,
        "owner": row["owner"],
        "registered_version": row["version"],
        "proposed_version": after,
        "change_kind": kind,
        "active_consumers": active_consumers,
        "all_consumers": consumers,
        "note": note,
        "errors": errors,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Havenline V3 cross-task contract compatibility")
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    task = sub.add_parser("task"); task.add_argument("task_id")
    paths = sub.add_parser("paths"); paths.add_argument("files", nargs="+")
    change = sub.add_parser("change"); change.add_argument("descriptor")
    args = ap.parse_args()
    if args.command == "validate": report = validate_registry()
    elif args.command == "task": report = contracts_for_task(args.task_id)
    elif args.command == "paths": report = {"affected_contracts": affected_contracts(args.files)}
    else: report = evaluate_change(load_json((ROOT / args.descriptor).resolve()))
    print(json.dumps(report, indent=2))
    return 0 if not report.get("errors") else 2


if __name__ == "__main__":
    raise SystemExit(main())
