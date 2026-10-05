#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Any

from contract_compatibility import contracts_for_task, validate_registry
from critical_path_scheduler import schedule, validate as validate_scheduler
from failure_intelligence import validate as validate_failure_intelligence
from forward_execution import resolve_task
from gate_fingerprint import validate_policy as validate_fingerprints
from preactivation_feasibility import resolve_capabilities, validate_all as validate_feasibility


def task_readiness(task_id: str) -> dict[str, Any]:
    task_id = task_id.upper()
    forward = resolve_task(task_id)
    feasibility = resolve_capabilities(task_id)
    scheduler = schedule()
    scheduler_row = next((row for row in scheduler["all_unapproved"] if row["task_id"] == task_id), None)
    contracts = contracts_for_task(task_id)
    return {
        "schema_version": 1,
        "task_id": task_id,
        "forward": forward,
        "feasibility": feasibility,
        "scheduler": scheduler_row,
        "contracts": contracts,
        "runtime_activation_allowed": feasibility["runtime_activation_allowed"],
        "activation_decision": feasibility["activation_state"],
        "commands": {
            "forward_plan": f"python3 tools/havenline/production/forward_execution.py plan {task_id}",
            "feasibility": f"python3 tools/havenline/production/preactivation_feasibility.py task {task_id}",
            "scheduler": "python3 tools/havenline/production/critical_path_scheduler.py plan",
            "contracts": f"python3 tools/havenline/production/contract_compatibility.py task {task_id}"
        }
    }


def validate() -> dict[str, Any]:
    checks = {
        "feasibility": validate_feasibility(),
        "scheduler": validate_scheduler(),
        "gate_fingerprints": validate_fingerprints(),
        "contracts": validate_registry(),
        "failure_intelligence": validate_failure_intelligence(),
    }
    errors: list[str] = []
    for name, report in checks.items():
        for error in report.get("errors", []):
            errors.append(f"{name}: {error}")
    for i in range(10, 71):
        task_id = f"T{i:02d}"
        try:
            task_readiness(task_id)
        except Exception as exc:
            errors.append(f"{task_id}: V3 readiness resolution failed: {exc}")
    return {"passed": not errors, "task_count": 61, "systems": checks, "errors": errors}


def main() -> int:
    ap = argparse.ArgumentParser(description="Havenline Production Architecture V3")
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    task = sub.add_parser("readiness"); task.add_argument("task_id")
    args = ap.parse_args()
    report = validate() if args.command == "validate" else task_readiness(args.task_id)
    print(json.dumps(report, indent=2))
    return 0 if not report.get("errors") else 2


if __name__ == "__main__":
    raise SystemExit(main())
