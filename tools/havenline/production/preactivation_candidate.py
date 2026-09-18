#!/usr/bin/env python3
"""Validate an explicitly authorized pre-activation isolated build.

This is deliberately narrower than workstream.py validate-candidate. It exists for
Txx builder branches whose frozen activation checklist explicitly permits isolated
construction up to BUILT_PENDING_DEPENDENCY before upstream approval/registry
claim. It never authorizes integration or approval.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "Docs" / "Production"


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def matches(path: str, pattern: str) -> bool:
    return fnmatch.fnmatchcase(path, pattern)


def explicit_build_pending_permission(checklist: dict) -> tuple[bool, str]:
    if (
        checklist.get("isolated_build_allowed_before_all_dependencies_approved") is True
        and checklist.get("built_pending_dependency_allowed") is True
        and checklist.get("integration_allowed_before_activation") is False
    ):
        return True, "generic_build_pending_policy"

    pending = checklist.get("build_pending_policy", {})
    if (
        pending.get("isolated_build_allowed_before_t10_approval") is True
        and pending.get("maximum_state_before_t10_approval") == "BUILT_PENDING_DEPENDENCY"
        and pending.get("may_integrate") is False
        and pending.get("may_claim_integration_ready") is False
    ):
        return True, "task_specific_build_pending_policy"

    return False, "none"


def validate(task_id: str, branch: str, head: str) -> dict:
    errors: list[str] = []
    checklist_path = DOCS / task_id / "ACTIVATION_CHECKLIST.json"
    if not checklist_path.exists():
        return {"task_id": task_id, "passed": False, "errors": [f"missing {checklist_path.relative_to(ROOT)}"]}

    checklist = load(checklist_path)
    graph = load(DOCS / "DEPENDENCY_GRAPH.json")
    gates = load(DOCS / "task-gates.json")
    ownership = load(DOCS / "PATH_OWNERSHIP.json")

    if checklist.get("task_id") != task_id:
        errors.append(f"activation checklist task mismatch: {checklist.get('task_id')}")

    expected_branch = checklist.get("builder_branch") or checklist.get("future_builder_branch")
    if expected_branch != branch:
        errors.append(f"builder branch mismatch: expected={expected_branch} actual={branch}")

    allowed, policy = explicit_build_pending_permission(checklist)
    if not allowed:
        errors.append("activation checklist does not explicitly authorize pre-activation BUILT_PENDING_DEPENDENCY construction")

    graph_row = graph.get("tasks", {}).get(task_id)
    if not graph_row:
        errors.append(f"{task_id} missing from dependency graph")
        graph_row = {}
    if graph_row.get("status") not in ("LOCKED", "PREPARED"):
        errors.append(f"pre-activation graph status must be LOCKED/PREPARED, got {graph_row.get('status')}")

    dependencies = checklist.get("dependencies", [])
    if graph_row.get("dependencies") != dependencies:
        errors.append(f"dependency mismatch: checklist={dependencies} graph={graph_row.get('dependencies')}")
    approved_tasks = set(gates.get("approved_tasks", []))
    unresolved = [dep for dep in dependencies if dep not in approved_tasks]
    if not unresolved:
        errors.append("all dependencies are approved; task must use normal activation/registry claim rather than pre-activation mode")

    prepared_branch = checklist.get("prepared_branch")
    if not prepared_branch:
        errors.append("activation checklist has no prepared_branch")
        base = None
    else:
        remote_ref = f"refs/remotes/origin/{prepared_branch}"
        try:
            git("rev-parse", "--verify", remote_ref)
            base = git("merge-base", remote_ref, head)
        except subprocess.CalledProcessError:
            base = None
            errors.append(f"prepared branch not resolvable: {prepared_branch}")

    planned = checklist.get("planned_owned_paths", [])
    if not planned:
        errors.append("planned_owned_paths is empty")

    changed: list[str] = []
    foreign: list[str] = []
    active_collisions: list[dict] = []
    integration_collisions: list[dict] = []
    if base:
        changed = [line for line in git("diff", "--name-only", f"{base}..{head}").splitlines() if line]
        foreign = [path for path in changed if not any(matches(path, pattern) for pattern in planned)]
        if foreign:
            errors.append(f"changed paths outside frozen reservation: {foreign}")

        aliases = ownership.get("aliases", {})
        integration_only = aliases.get("@integration-only", [])
        for path in changed:
            for pattern in integration_only:
                if matches(path, pattern):
                    integration_collisions.append({"path": path, "integration_only": pattern})
            for owner in ownership.get("active_owners", []):
                if owner.get("task_id") == task_id:
                    continue
                for pattern in aliases.get(owner.get("paths_alias"), []):
                    if matches(path, pattern):
                        active_collisions.append({"path": path, "active_task": owner.get("task_id"), "owned_pattern": pattern})
        if integration_collisions:
            errors.append(f"integration-only paths changed: {integration_collisions}")
        if active_collisions:
            errors.append(f"active foreign ownership collision: {active_collisions}")

    return {
        "task_id": task_id,
        "mode": "preactivation-build-pending",
        "branch": branch,
        "head": head,
        "prepared_branch": prepared_branch,
        "base": base,
        "permission_policy": policy,
        "graph_status": graph_row.get("status"),
        "unresolved_dependencies": unresolved,
        "changed_files": changed,
        "foreign_paths": foreign,
        "integration_only_collisions": integration_collisions,
        "active_owner_collisions": active_collisions,
        "maximum_state": "BUILT_PENDING_DEPENDENCY",
        "integration_allowed": False,
        "task_approved": False,
        "passed": not errors,
        "errors": errors,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--branch", required=True)
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--output")
    args = ap.parse_args()
    result = validate(args.task.upper(), args.branch, args.head)
    text = json.dumps(result, indent=2)
    print(text)
    if args.output:
        path = pathlib.Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
