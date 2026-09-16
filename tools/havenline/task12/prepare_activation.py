#!/usr/bin/env python3
"""Validate T12 parallel preparation and activation readiness after T11 approval.

Default mode validates governance preparation only. `--activate --base <sha>`
is read-only and proves that T12 may be activated from the exact integration
head. This tool never creates the builder branch, mutates governance files, or
edits gameplay/runtime.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "Docs" / "Production"
CHECKLIST_PATH = DOCS / "T12" / "ACTIVATION_CHECKLIST.json"
GRAPH_PATH = DOCS / "DEPENDENCY_GRAPH.json"
REGISTRY_PATH = DOCS / "WORKSTREAM_REGISTRY.json"
OWNERSHIP_PATH = DOCS / "PATH_OWNERSHIP.json"
CRITICS_PATH = DOCS / "CRITIC_MATRIX.json"
GATES_PATH = DOCS / "task-gates.json"


def load(path: pathlib.Path):
    return json.loads(path.read_text())


def prefix(pattern: str) -> str:
    cut = len(pattern)
    for token in ("*", "?", "["):
        pos = pattern.find(token)
        if pos >= 0:
            cut = min(cut, pos)
    return pattern[:cut].rstrip("/")


def may_overlap(a: str, b: str) -> bool:
    if a == b:
        return True
    pa, pb = prefix(a), prefix(b)
    if not pa or not pb:
        return True
    return pa == pb or pa.startswith(pb + "/") or pb.startswith(pa + "/")


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def registry_status(registry, task_id: str):
    if task_id in registry.get("legacy_approvals", {}):
        return "APPROVED"
    row = next((x for x in registry.get("workstreams", []) if x.get("task_id") == task_id), None)
    return (row or {}).get("status")


def validate_preparation():
    checklist = load(CHECKLIST_PATH)
    graph = load(GRAPH_PATH)
    registry = load(REGISTRY_PATH)
    ownership = load(OWNERSHIP_PATH)
    critics = load(CRITICS_PATH)
    errors: list[str] = []

    t12 = graph.get("tasks", {}).get("T12")
    if not t12:
        errors.append("T12 is missing from DEPENDENCY_GRAPH.json")
        t12 = {}

    expected_deps = checklist["dependencies"]
    if t12.get("dependencies") != expected_deps:
        errors.append(f"T12 dependency mismatch: graph={t12.get('dependencies')} checklist={expected_deps}")

    expected_critics = checklist["required_critics"]
    if t12.get("critics") != expected_critics:
        errors.append(f"T12 critic mismatch in dependency graph: {t12.get('critics')}")
    if critics.get("task_applicability", {}).get("T12") != expected_critics:
        errors.append(f"T12 critic mismatch in CRITIC_MATRIX.json: {critics.get('task_applicability', {}).get('T12')}")

    if checklist.get("runtime_build_allowed_before_activation") is not False:
        errors.append("runtime_build_allowed_before_activation must remain false")

    planned = checklist["planned_owned_paths"]
    if len(planned) != len(set(planned)):
        errors.append("planned T12 reservation contains duplicate paths")

    protected = ownership.get("aliases", {}).get("@integration-only", [])
    collisions = []
    for candidate in planned:
        for path in protected:
            if may_overlap(candidate, path):
                collisions.append({"candidate": candidate, "protected": path})

    active_collisions = []
    for active in ownership.get("active_owners", []):
        alias = active.get("paths_alias")
        foreign = ownership.get("aliases", {}).get(alias, [])
        for candidate in planned:
            for path in foreign:
                if may_overlap(candidate, path):
                    active_collisions.append({
                        "task": active.get("task_id"),
                        "candidate": candidate,
                        "foreign": path,
                    })

    t11_checklist = DOCS / "T11" / "ACTIVATION_CHECKLIST.json"
    t11_collisions = []
    if t11_checklist.exists():
        t11_paths = load(t11_checklist).get("planned_owned_paths", [])
        for candidate in planned:
            for path in t11_paths:
                if may_overlap(candidate, path):
                    t11_collisions.append({"candidate": candidate, "t11": path})

    if collisions:
        errors.append("planned T12 reservation collides with integration-only paths: " + json.dumps(collisions))
    if active_collisions:
        errors.append("planned T12 reservation collides with active ownership: " + json.dumps(active_collisions))
    if t11_collisions:
        errors.append("planned T12 reservation collides with T11: " + json.dumps(t11_collisions))

    required = [
        DOCS / "T12" / "FROZEN_SCOPE.md",
        DOCS / "T12" / "TASK_PACKET.md",
        DOCS / "T12" / "PREBUILD_CONTRACT.json",
        DOCS / "T12" / "defect-ledger.json",
        CHECKLIST_PATH,
    ]
    for path in required:
        if not path.exists() or not path.read_text().strip():
            errors.append(f"missing/empty preparation artifact: {path.relative_to(ROOT)}")

    shipping_paths = [
        ROOT / "HavenlineGodot" / "scripts" / "progression_architecture.gd",
        ROOT / "HavenlineGodot" / "data" / "progression_levels_v1.json",
        ROOT / "HavenlineGodot" / "data" / "progression_milestones_v1.json",
    ]
    for path in shipping_paths:
        if path.exists():
            errors.append(f"shipping T12 path exists before activation: {path.relative_to(ROOT)}")

    row = next((x for x in registry.get("workstreams", []) if x.get("task_id") == "T12"), None)
    if row and row.get("status") not in ("LOCKED", "PREPARED"):
        errors.append(f"pre-activation registry T12 status must be LOCKED/PREPARED, got {row.get('status')}")

    return {
        "task_id": "T12",
        "mode": "preparation",
        "integration_branch": registry.get("integration_branch", "codex/havenline-sequential-task-01"),
        "prepared_from_branch": checklist.get("prepared_from_branch"),
        "prepared_from_commit": checklist.get("prepared_from_commit"),
        "t10_current_graph_status": graph.get("tasks", {}).get("T10", {}).get("status"),
        "t11_current_graph_status": graph.get("tasks", {}).get("T11", {}).get("status"),
        "planned_owned_path_count": len(planned),
        "integration_only_collision_count": len(collisions),
        "active_ownership_collision_count": len(active_collisions),
        "t11_collision_count": len(t11_collisions),
        "required_critics": expected_critics,
        "runtime_build_allowed": False,
        "passed": not errors,
        "errors": errors,
    }


def validate_activation(base: str):
    prep = validate_preparation()
    if not prep["passed"]:
        return {**prep, "mode": "activation-preflight", "base": base, "passed": False}

    checklist = load(CHECKLIST_PATH)
    graph = load(GRAPH_PATH)
    registry = load(REGISTRY_PATH)
    ownership = load(OWNERSHIP_PATH)
    gates = load(GATES_PATH)
    errors: list[str] = []

    head = git_head()
    if head != base:
        errors.append(f"activation base must equal checked-out HEAD: head={head} base={base}")

    for dep in checklist["dependencies"]:
        graph_status = graph.get("tasks", {}).get(dep, {}).get("status")
        reg_status = registry_status(registry, dep)
        if graph_status != "APPROVED":
            errors.append(f"dependency {dep} graph status is {graph_status}, not APPROVED")
        if reg_status != "APPROVED":
            errors.append(f"dependency {dep} registry status is {reg_status}, not APPROVED")
        if dep not in gates.get("approved_tasks", []):
            errors.append(f"dependency {dep} missing from task-gates approved_tasks")

    completed = gates.get("completed_task_records", {})
    for dep in ("T10", "T11"):
        if dep not in completed:
            errors.append(f"{dep} has no completed_task_records entry in task-gates")

    stale_owners = [x for x in ownership.get("active_owners", []) if x.get("task_id") in ("T10", "T11")]
    if stale_owners:
        errors.append("T10/T11 still listed as active owners; finish closeout before T12 activation")

    if graph.get("tasks", {}).get("T12", {}).get("status") not in ("LOCKED", "PREPARED"):
        errors.append(f"unexpected pre-activation T12 graph state: {graph.get('tasks', {}).get('T12', {}).get('status')}")

    return {
        "task_id": "T12",
        "mode": "activation-preflight",
        "base": base,
        "head": head,
        "dependencies": checklist["dependencies"],
        "future_branch": checklist["future_builder_branch"],
        "owner": checklist["future_owner"],
        "owned_alias": checklist["planned_owned_alias"],
        "reservation_patch": {
            "alias": checklist["planned_owned_alias"],
            "paths": checklist["planned_owned_paths"]
        },
        "claim_command": checklist["claim_template"].replace("<POST_T11_INTEGRATION_SHA>", base),
        "passed": not errors,
        "errors": errors,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--activate", action="store_true", help="Require all T12 dependencies approved and exact base/head match")
    ap.add_argument("--base", help="Exact post-T11 integration head used for T12 activation")
    args = ap.parse_args()

    if args.activate and not args.base:
        raise SystemExit("--activate requires --base <exact integration head>")

    result = validate_activation(args.base) if args.activate else validate_preparation()
    print(json.dumps(result, indent=2))
    if not result.get("passed"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
