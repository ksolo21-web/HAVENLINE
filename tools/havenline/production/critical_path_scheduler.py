#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from forward_execution import DOCS, ROOT, resolve_task
from preactivation_feasibility import resolve_capabilities

POLICY = DOCS / "PRODUCTION_SCHEDULER_POLICY.json"
GRAPH = DOCS / "DEPENDENCY_GRAPH.json"
REGISTRY = DOCS / "WORKSTREAM_REGISTRY.json"
CRITICS = DOCS / "CRITIC_MATRIX.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _metrics(graph: dict[str, Any]) -> tuple[dict[str, set[str]], Any, Any]:
    tasks = graph["tasks"]
    children: dict[str, set[str]] = {task: set() for task in tasks}
    for task, row in tasks.items():
        for dep in row.get("dependencies", []):
            children.setdefault(dep, set()).add(task)

    @lru_cache(maxsize=None)
    def descendants(task: str) -> frozenset[str]:
        out: set[str] = set()
        for child in children.get(task, set()):
            out.add(child); out.update(descendants(child))
        return frozenset(out)

    @lru_cache(maxsize=None)
    def depth(task: str) -> int:
        kids = children.get(task, set())
        return 0 if not kids else 1 + max(depth(child) for child in kids)

    return children, descendants, depth


def _workstream_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {w["task_id"]: w for w in registry.get("workstreams", []) if str(w.get("task_id", "")).startswith("T")}


def schedule() -> dict[str, Any]:
    policy = load_json(POLICY)
    graph = load_json(GRAPH)
    registry = load_json(REGISTRY)
    matrix = load_json(CRITICS)
    ws = _workstream_map(registry)
    children, descendants, depth = _metrics(graph)
    weights = policy["priority_weights"]
    independent = set(policy["resource_classes"]["independent_critic"])
    rows: list[dict[str, Any]] = []

    for i in range(10, 71):
        task_id = f"T{i:02d}"
        node = graph["tasks"][task_id]
        if node["status"] == "APPROVED":
            continue
        plan = resolve_task(task_id)
        feasibility = resolve_capabilities(task_id)
        workstream = ws.get(task_id, {})
        current_status = workstream.get("status", node["status"])
        direct = len(children.get(task_id, set()))
        transitive = len(descendants(task_id))
        critical_depth = depth(task_id)
        score = direct * weights["direct_downstream_count"] + transitive * weights["transitive_downstream_count"] + critical_depth * weights["critical_path_depth"]
        if feasibility["activation_state"] == "READY_NOW": score += weights["ready_now_bonus"]
        if current_status == "INTEGRATION_READY": score += weights["integration_ready_bonus"]
        if direct >= 2: score += weights["unblocks_multiple_tasks_bonus"]
        if feasibility["activation_state"] == "BLOCKED_CAPABILITY": score -= weights["external_block_penalty"]
        if not plan["canonical_packet_present"]: score -= weights["missing_packet_penalty"]

        if current_status in {"INTEGRATION_READY", "INTEGRATING"}:
            classification = "INTEGRATION_QUEUE"
        elif feasibility["activation_state"] == "READY_NOW":
            classification = "READY_NOW"
        elif feasibility["activation_state"] == "BLOCKED_CAPABILITY" and plan["dependencies_approved"]:
            classification = "BLOCKED_CAPABILITY"
        else:
            classification = "PREP_ONLY"
        critics = matrix["task_applicability"].get(task_id, [])
        rows.append({
            "task_id": task_id,
            "name": node["name"],
            "status": current_status,
            "classification": classification,
            "priority_score": score,
            "direct_downstream_count": direct,
            "transitive_downstream_count": transitive,
            "critical_path_depth": critical_depth,
            "dependencies": plan["dependencies"],
            "dependency_status": plan["dependency_status"],
            "missing_packet": not plan["canonical_packet_present"],
            "capability_blockers": feasibility["capability_blockers"],
            "execution_mode": plan["execution_mode"],
            "needs_independent_critic": bool(independent.intersection(critics)),
            "critics": critics,
        })

    rows.sort(key=lambda row: (-row["priority_score"], int(row["task_id"][1:])))
    by_class = {name: [row for row in rows if row["classification"] == name] for name in ("READY_NOW", "PREP_ONLY", "BLOCKED_CAPABILITY", "INTEGRATION_QUEUE")}
    active_build_states = {"ASSIGNED", "BUILDING_ISOLATED", "BUILT_PENDING_DEPENDENCY"}
    active_builds = [row for row in rows if row["status"] in active_build_states and row["execution_mode"] == "build"]
    wip = policy["wip"]
    build_slots = max(0, int(wip["max_parallel_runtime_builds"]) - len(active_builds))
    prep_slots = int(wip["max_parallel_prep_tasks"])
    suggested_start = by_class["READY_NOW"][:build_slots]
    suggested_prep = by_class["PREP_ONLY"][:prep_slots]
    integration_queue = sorted(by_class["INTEGRATION_QUEUE"], key=lambda row: (-row["priority_score"], int(row["task_id"][1:])))
    return {
        "schema_version": 1,
        "policy": "Docs/Production/PRODUCTION_SCHEDULER_POLICY.json",
        "scheduler_is_advisory": True,
        "integration_owner_slots": wip["integration_owner_slots"],
        "independent_critic_runtime_slots": wip["independent_critic_runtime_slots"],
        "active_runtime_builds": [row["task_id"] for row in active_builds],
        "available_runtime_build_slots": build_slots,
        "suggested_start_now": [row["task_id"] for row in suggested_start],
        "suggested_prepare_now": [row["task_id"] for row in suggested_prep],
        "integration_queue": [row["task_id"] for row in integration_queue],
        "classes": by_class,
        "all_unapproved": rows,
    }


def validate() -> dict[str, Any]:
    policy = load_json(POLICY)
    errors: list[str] = []
    if policy.get("policy", {}).get("single_integration_authority") is not True:
        errors.append("scheduler must preserve a single integration authority")
    if policy.get("policy", {}).get("do_not_auto_start") is not True:
        errors.append("scheduler must remain advisory and may not auto-start tasks")
    for key in ("max_parallel_runtime_builds", "max_parallel_prep_tasks", "max_integration_ready_queue", "integration_owner_slots", "independent_critic_runtime_slots", "physical_certification_slots"):
        value = policy.get("wip", {}).get(key)
        if not isinstance(value, int) or value < 1:
            errors.append(f"invalid WIP value {key}={value!r}")
    try:
        report = schedule()
        ids = [row["task_id"] for row in report["all_unapproved"]]
        if len(ids) != len(set(ids)):
            errors.append("scheduler emitted duplicate tasks")
    except Exception as exc:
        errors.append(f"scheduler resolution failed: {exc}")
        report = {}
    return {"passed": not errors, "errors": errors, "summary": report}


def main() -> int:
    ap = argparse.ArgumentParser(description="Havenline V3 critical path/WIP scheduler")
    ap.add_argument("command", choices=["plan", "validate"])
    ap.add_argument("--output")
    args = ap.parse_args()
    report = schedule() if args.command == "plan" else validate()
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        out = (ROOT / args.output).resolve(); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(text)
    print(text, end="")
    return 0 if not report.get("errors") else 2


if __name__ == "__main__":
    raise SystemExit(main())
