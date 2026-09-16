#!/usr/bin/env python3
"""Read-only activation frontier report for prepared Havenline tasks T13-T70.

This tool never activates a task, creates a builder branch, or edits governance.
It reports the exact blockers that must clear before each prepared task can be
claimed from the then-current integration head.
"""
from __future__ import annotations

import json
import os
import pathlib
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "Docs" / "Production"
TASKS = [f"T{i:02d}" for i in range(13, 71)]
TASK_SET = set(TASKS)
PREACTIVATION_STATES = {"LOCKED", "PREPARED"}


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def registry_status(registry: dict, task_id: str):
    if task_id in registry.get("legacy_approvals", {}):
        return "APPROVED"
    row = next(
        (item for item in registry.get("workstreams", []) if item.get("task_id") == task_id),
        None,
    )
    return (row or {}).get("status")


def dependency_state(task_id: str, graph: dict, registry: dict, gates: dict, ownership: dict):
    graph_row = graph.get("tasks", {}).get(task_id)
    graph_status = (graph_row or {}).get("status")
    reg_status = registry_status(registry, task_id)
    gate_approved = task_id in gates.get("approved_tasks", [])
    active_owner = next(
        (owner for owner in ownership.get("active_owners", []) if owner.get("task_id") == task_id),
        None,
    )

    blockers = []
    if graph_row is None:
        blockers.append("missing_dependency_graph_row")
    elif graph_status != "APPROVED":
        blockers.append(f"graph_status:{graph_status or 'MISSING'}")
    if reg_status != "APPROVED":
        blockers.append(f"registry_status:{reg_status or 'MISSING'}")
    if not gate_approved:
        blockers.append("task_gate_not_approved")
    if active_owner is not None:
        blockers.append(f"active_path_owner:{active_owner.get('owner') or active_owner.get('paths_alias') or 'present'}")

    return {
        "task_id": task_id,
        "graph_status": graph_status,
        "registry_status": reg_status,
        "task_gate_approved": gate_approved,
        "active_path_owner": active_owner is not None,
        "approved": not blockers,
        "blockers": blockers,
    }


def validate_prepared_task(task_id: str, graph: dict):
    errors = []
    task_dir = DOCS / task_id
    checklist_path = task_dir / "ACTIVATION_CHECKLIST.json"
    prebuild_path = task_dir / "PREBUILD_CONTRACT.json"
    if not checklist_path.exists():
        return None, None, ["missing ACTIVATION_CHECKLIST.json"]
    if not prebuild_path.exists():
        return None, None, ["missing PREBUILD_CONTRACT.json"]

    checklist = load(checklist_path)
    prebuild = load(prebuild_path)
    graph_row = graph.get("tasks", {}).get(task_id, {})

    if checklist.get("task_id") != task_id:
        errors.append("checklist task_id mismatch")
    if prebuild.get("task_id") != task_id:
        errors.append("prebuild task_id mismatch")
    if checklist.get("preparation_status") != "PREPARED_GOVERNANCE_ONLY":
        errors.append("preparation_status must remain PREPARED_GOVERNANCE_ONLY")
    if checklist.get("runtime_status") != "LOCKED":
        errors.append("runtime_status must remain LOCKED")
    if checklist.get("runtime_build_allowed_before_activation") is not False:
        errors.append("runtime build must remain disabled before activation")
    if checklist.get("dependencies") != graph_row.get("dependencies"):
        errors.append("checklist dependencies differ from dependency graph")
    if prebuild.get("dependencies") != graph_row.get("dependencies"):
        errors.append("prebuild dependencies differ from dependency graph")
    if checklist.get("future_builder_branch") != prebuild.get("future_builder_branch"):
        errors.append("future builder branch differs between checklist and prebuild")
    if checklist.get("future_owner") != prebuild.get("future_owner"):
        errors.append("future owner differs between checklist and prebuild")
    if checklist.get("planned_owned_paths") != prebuild.get("planned_owned_paths"):
        errors.append("planned owned paths differ between checklist and prebuild")
    if not checklist.get("future_builder_branch"):
        errors.append("future builder branch missing")
    if not checklist.get("future_owner"):
        errors.append("future owner missing")
    if not checklist.get("planned_owned_paths"):
        errors.append("planned owned paths missing")

    return checklist, prebuild, errors


def hypothetical_internal_waves(graph: dict):
    """Layer T13-T70 assuming all dependencies outside this range have cleared.

    This is ordering information only. It is explicitly not current approval.
    """
    approved = {
        task_id
        for task_id, row in graph.get("tasks", {}).items()
        if row.get("status") == "APPROVED"
    }
    approved.update(task_id for task_id in graph.get("tasks", {}) if task_id not in TASK_SET)

    remaining = {
        task_id
        for task_id in TASKS
        if graph.get("tasks", {}).get(task_id, {}).get("status") != "APPROVED"
    }
    waves = []
    while remaining:
        wave = sorted(
            task_id
            for task_id in remaining
            if all(dep in approved for dep in graph.get("tasks", {}).get(task_id, {}).get("dependencies", []))
        )
        if not wave:
            break
        waves.append(wave)
        approved.update(wave)
        remaining.difference_update(wave)
    return waves, sorted(remaining)


def build_report():
    graph = load(DOCS / "DEPENDENCY_GRAPH.json")
    registry = load(DOCS / "WORKSTREAM_REGISTRY.json")
    gates = load(DOCS / "task-gates.json")
    ownership = load(DOCS / "PATH_OWNERSHIP.json")

    structural_errors = []
    rows = []
    frontier_now = []
    already_approved = []
    already_active = []
    blocker_counts = Counter()

    for task_id in TASKS:
        checklist, _prebuild, prep_errors = validate_prepared_task(task_id, graph)
        if prep_errors:
            structural_errors.extend(f"{task_id}: {error}" for error in prep_errors)

        graph_row = graph.get("tasks", {}).get(task_id, {})
        graph_status = graph_row.get("status")
        dependencies = graph_row.get("dependencies", [])
        dep_states = [dependency_state(dep, graph, registry, gates, ownership) for dep in dependencies]
        blockers = [
            {"dependency": state["task_id"], "reasons": state["blockers"]}
            for state in dep_states
            if not state["approved"]
        ]
        for blocker in blockers:
            for reason in blocker["reasons"]:
                blocker_counts[reason.split(":", 1)[0]] += 1

        own_active = any(
            owner.get("task_id") == task_id for owner in ownership.get("active_owners", [])
        )
        if graph_status == "APPROVED":
            state = "APPROVED"
            already_approved.append(task_id)
        elif own_active or graph_status in {"ASSIGNED", "ACTIVE", "IN_PROGRESS"}:
            state = "ACTIVE_OR_ASSIGNED"
            already_active.append(task_id)
        elif prep_errors:
            state = "PREPARATION_DEFECT"
        elif graph_status not in PREACTIVATION_STATES:
            state = "UNEXPECTED_GRAPH_STATE"
            structural_errors.append(f"{task_id}: unexpected preactivation graph status {graph_status!r}")
        elif blockers:
            state = "BLOCKED_BY_DEPENDENCIES"
        else:
            state = "ACTIVATABLE_NOW"
            frontier_now.append(task_id)

        rows.append(
            {
                "task_id": task_id,
                "state": state,
                "graph_status": graph_status,
                "dependencies": dependencies,
                "dependency_blockers": blockers,
                "future_builder_branch": (checklist or {}).get("future_builder_branch"),
                "future_owner": (checklist or {}).get("future_owner"),
                "activation_rule": "Create/claim only from the exact current integration head after every dependency is approved and released from active ownership.",
            }
        )

    waves, unresolved = hypothetical_internal_waves(graph)
    return {
        "scope": "T13-T70 activation frontier",
        "mode": "READ_ONLY_REPORT",
        "task_count": len(TASKS),
        "activation_frontier_now": frontier_now,
        "activation_frontier_count": len(frontier_now),
        "already_approved": already_approved,
        "already_active_or_assigned": already_active,
        "blocker_reason_counts": dict(sorted(blocker_counts.items())),
        "hypothetical_internal_unlock_waves_after_all_external_dependencies_clear": [
            {"wave": index + 1, "tasks": wave} for index, wave in enumerate(waves)
        ],
        "hypothetical_unresolved_after_external_clearance": unresolved,
        "tasks": rows,
        "structural_errors": structural_errors,
        "passed": not structural_errors,
        "important": "Hypothetical waves are sequencing guidance only; they do not grant approval or authorize branch creation.",
    }


def write_step_summary(report: dict):
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    frontier = report["activation_frontier_now"]
    waves = report["hypothetical_internal_unlock_waves_after_all_external_dependencies_clear"]
    lines = [
        "# Havenline T13-T70 Activation Frontier",
        "",
        f"- Structural audit: **{'PASS' if report['passed'] else 'FAIL'}**",
        f"- T13+ tasks legal to activate now: **{len(frontier)}**",
        f"- Current frontier: `{', '.join(frontier) if frontier else 'none'}`",
        "- This report is read-only and never creates task branches.",
        "",
        "## Hypothetical internal order after all external dependencies clear",
        "",
    ]
    for wave in waves:
        lines.append(f"- Wave {wave['wave']}: {', '.join(wave['tasks'])}")
    if report["hypothetical_unresolved_after_external_clearance"]:
        lines.extend([
            "",
            "## Unresolved graph nodes",
            "",
            ", ".join(report["hypothetical_unresolved_after_external_clearance"]),
        ])
    pathlib.Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    report = build_report()
    print(json.dumps(report, indent=2))
    write_step_summary(report)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
