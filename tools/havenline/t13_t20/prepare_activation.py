#!/usr/bin/env python3
"""Validate T13-T20 parallel prep and perform read-only activation preflight."""
from __future__ import annotations
import argparse
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "Docs" / "Production"
TASKS = [f"T{i:02d}" for i in range(13, 21)]


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


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


def registry_status(registry: dict, task_id: str):
    if task_id in registry.get("legacy_approvals", {}):
        return "APPROVED"
    row = next((x for x in registry.get("workstreams", []) if x.get("task_id") == task_id), None)
    return (row or {}).get("status")


def collisions(paths: list[str], ownership: dict):
    protected = ownership.get("aliases", {}).get("@integration-only", [])
    integration = []
    active = []
    for candidate in paths:
        for path in protected:
            if may_overlap(candidate, path):
                integration.append({"candidate": candidate, "protected": path})
        for owner in ownership.get("active_owners", []):
            foreign = ownership.get("aliases", {}).get(owner.get("paths_alias"), [])
            for path in foreign:
                if may_overlap(candidate, path):
                    active.append({"task": owner.get("task_id"), "candidate": candidate, "foreign": path})
    return integration, active


def validate_prep(task_id: str):
    checklist_path = DOCS / task_id / "ACTIVATION_CHECKLIST.json"
    graph = load(DOCS / "DEPENDENCY_GRAPH.json")
    registry = load(DOCS / "WORKSTREAM_REGISTRY.json")
    ownership = load(DOCS / "PATH_OWNERSHIP.json")
    critic_matrix = load(DOCS / "CRITIC_MATRIX.json")
    errors = []
    required = [
        DOCS / task_id / "FROZEN_SCOPE.md",
        DOCS / task_id / "TASK_PACKET.md",
        DOCS / task_id / "PREBUILD_CONTRACT.json",
        DOCS / task_id / "defect-ledger.json",
        checklist_path,
    ]
    for path in required:
        if not path.exists() or not path.read_text(encoding="utf-8").strip():
            errors.append(f"missing/empty preparation artifact: {path.relative_to(ROOT)}")
    if errors:
        return {"task_id":task_id,"mode":"preparation","passed":False,"errors":errors}

    checklist = load(checklist_path)
    defect = load(DOCS / task_id / "defect-ledger.json")
    task = graph.get("tasks", {}).get(task_id, {})
    if checklist.get("dependencies") != task.get("dependencies"):
        errors.append(f"dependency mismatch: checklist={checklist.get('dependencies')} graph={task.get('dependencies')}")
    graph_critics = set(task.get("critics", []))
    planned_critics = set(checklist.get("required_critics", []))
    if not graph_critics.issubset(planned_critics):
        errors.append(f"planned critic set omits graph critics: {sorted(graph_critics - planned_critics)}")
    matrix_critics = set(critic_matrix.get("task_applicability", {}).get(task_id, []))
    if not matrix_critics.issubset(planned_critics):
        errors.append(f"planned critic set omits critic-matrix critics: {sorted(matrix_critics - planned_critics)}")
    if checklist.get("runtime_build_allowed_before_activation") is not False:
        errors.append("runtime_build_allowed_before_activation must be false")
    if checklist.get("runtime_status") != "LOCKED":
        errors.append("prepared runtime status must remain LOCKED")
    planned = checklist.get("planned_owned_paths", [])
    if not planned or len(planned) != len(set(planned)):
        errors.append("planned path reservation is empty or contains duplicates")
    integ, active = collisions(planned, ownership)
    if integ:
        errors.append("planned paths collide with integration-only ownership: " + json.dumps(integ))
    if active:
        errors.append("planned paths collide with an active workstream: " + json.dumps(active))
    if defect.get("unresolved_preparation_defects"):
        errors.append("unresolved preparation defects remain")
    return {
        "task_id": task_id,
        "mode": "preparation",
        "graph_status": task.get("status"),
        "registry_status": registry_status(registry, task_id),
        "planned_owned_alias": checklist.get("planned_owned_alias"),
        "planned_owned_path_count": len(planned),
        "required_critics": checklist.get("required_critics"),
        "integration_only_collision_count": len(integ),
        "active_ownership_collision_count": len(active),
        "runtime_build_allowed": False,
        "passed": not errors,
        "errors": errors,
    }


def git_head():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def validate_activation(task_id: str, base: str):
    prep = validate_prep(task_id)
    if not prep.get("passed"):
        return {**prep, "mode":"activation-preflight", "base":base, "passed":False}
    checklist = load(DOCS / task_id / "ACTIVATION_CHECKLIST.json")
    graph = load(DOCS / "DEPENDENCY_GRAPH.json")
    registry = load(DOCS / "WORKSTREAM_REGISTRY.json")
    gates = load(DOCS / "task-gates.json")
    ownership = load(DOCS / "PATH_OWNERSHIP.json")
    errors = []
    head = git_head()
    if head != base:
        errors.append(f"activation base must equal checked-out HEAD: head={head} base={base}")
    for dep in checklist.get("dependencies", []):
        if graph.get("tasks", {}).get(dep, {}).get("status") != "APPROVED":
            errors.append(f"dependency {dep} graph status is not APPROVED")
        if registry_status(registry, dep) != "APPROVED":
            errors.append(f"dependency {dep} registry status is not APPROVED")
        if dep not in gates.get("approved_tasks", []):
            errors.append(f"dependency {dep} missing from task-gates approved_tasks")
        if any(x.get("task_id") == dep for x in ownership.get("active_owners", [])):
            errors.append(f"dependency {dep} still has active path ownership")
    state = graph.get("tasks", {}).get(task_id, {}).get("status")
    if state not in ("LOCKED", "PREPARED"):
        errors.append(f"unexpected pre-activation graph status {state}")
    integ, active = collisions(checklist.get("planned_owned_paths", []), ownership)
    if integ or active:
        errors.append("planned ownership is no longer disjoint; refresh reservation before activation")
    claim = checklist.get("claim_template", "").replace("<EXACT_CURRENT_INTEGRATION_HEAD>", base)
    return {
        "task_id":task_id,
        "mode":"activation-preflight",
        "base":base,
        "head":head,
        "dependencies":checklist.get("dependencies", []),
        "future_branch":checklist.get("future_builder_branch"),
        "future_owner":checklist.get("future_owner"),
        "reservation_patch":{"alias":checklist.get("planned_owned_alias"),"paths":checklist.get("planned_owned_paths", [])},
        "claim_command":claim,
        "passed":not errors,
        "errors":errors,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--activate", action="store_true")
    ap.add_argument("--base")
    args = ap.parse_args()
    if args.all:
        if args.activate or args.base or args.task:
            raise SystemExit("--all is preparation validation only")
        results = [validate_prep(t) for t in TASKS]
        out = {"wave":"T13-T20","mode":"preparation","results":results,"passed":all(x["passed"] for x in results)}
    else:
        if not args.task:
            raise SystemExit("use --all or --task T13..T20")
        if args.activate and not args.base:
            raise SystemExit("--activate requires --base <exact integration head>")
        out = validate_activation(args.task, args.base) if args.activate else validate_prep(args.task)
    print(json.dumps(out, indent=2))
    if not out.get("passed"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
