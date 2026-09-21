#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
from pathlib import Path

from control_plane_lineage import assess as assess_control_plane_lineage
from lib import DOCS, ROOT, json_dump, load_json
from task_graduation_gate import evaluate as graduation
from workstream import claim as legacy_claim

FORWARD_TASK = re.compile(r"^T(?:1[1-9]|[2-6][0-9]|70)$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def remote_branch_head(branch: str) -> str | None:
    try:
        output = subprocess.check_output(
            ["git", "ls-remote", "origin", f"refs/heads/{branch}"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None
    rows = [line.split() for line in output.splitlines() if line.strip()]
    if len(rows) != 1 or len(rows[0]) < 2:
        return None
    sha, ref = rows[0][0], rows[0][1]
    if ref != f"refs/heads/{branch}" or not SHA40.fullmatch(sha):
        return None
    return sha


def validate_assignment(task_id: str, branch: str, builder_head: str, integration_head: str, verify_remote: bool = True) -> dict:
    errors: list[str] = []
    task_id = task_id.upper()
    registry = load_json(DOCS / "WORKSTREAM_REGISTRY.json")
    graph = load_json(DOCS / "DEPENDENCY_GRAPH.json")
    row = next((w for w in registry["workstreams"] if w.get("task_id") == task_id), None)

    if not FORWARD_TASK.fullmatch(task_id):
        errors.append("V3.2 assignment claim is only for T11-T70")
    if task_id not in graph.get("tasks", {}):
        errors.append("task is missing from dependency graph")
    if not row:
        errors.append("task must already have a PREPARED registered workstream")
    elif row.get("branch") != branch:
        errors.append(f"builder branch mismatch: registry={row.get('branch')} supplied={branch}")
    if not SHA40.fullmatch(str(builder_head or "")):
        errors.append("exact builder head is required")
    if not SHA40.fullmatch(str(integration_head or "")):
        errors.append("exact integration head is required")

    integration_branch = registry.get("integration_branch")
    if verify_remote and not errors:
        actual_builder = remote_branch_head(branch)
        actual_integration = remote_branch_head(integration_branch) if integration_branch else None
        if actual_builder != builder_head:
            errors.append(f"builder head does not match remote {branch}: remote={actual_builder} supplied={builder_head}")
        if actual_integration != integration_head:
            errors.append(
                f"integration head does not match remote {integration_branch}: "
                f"remote={actual_integration} supplied={integration_head}"
            )

    lineage = assess_control_plane_lineage(builder_head, integration_head)
    if not lineage.get("passed"):
        errors.append("control-plane lineage is not synchronized: " + str(lineage.get("reason") or lineage.get("errors")))

    grad = graduation(task_id, "ASSIGNED", builder_head, integration_head)
    if not grad.get("passed"):
        errors.extend("graduation: " + x for x in grad.get("errors", []))

    return {
        "passed": not errors,
        "task_id": task_id,
        "builder_branch": branch,
        "builder_head": builder_head,
        "integration_branch": integration_branch,
        "integration_head": integration_head,
        "remote_identity_verified": verify_remote and not any("remote" in x for x in errors),
        "lineage": lineage,
        "graduation": grad,
        "errors": errors,
    }


def apply_assignment(task_id: str, owner: str, branch: str, base: str, owned_alias: str, builder_head: str, integration_head: str) -> dict:
    report = validate_assignment(task_id, branch, builder_head, integration_head, verify_remote=True)
    if not report["passed"]:
        return report

    legacy_claim(task_id, owner, branch, base, owned_alias, "ASSIGNED")

    registry = load_json(DOCS / "WORKSTREAM_REGISTRY.json")
    row = next(w for w in registry["workstreams"] if w.get("task_id") == task_id.upper())
    row["assignment_integration_commit"] = integration_head
    row["assignment_branch_head"] = builder_head
    row["assignment_lineage_state"] = "SYNCHRONIZED"
    row["assignment_claimed_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    row["next_action"] = (
        "Create/validate the V3.2 graduation package, pass BUILDING_ISOLATED on the exact candidate, "
        "then begin bounded task-owned runtime construction."
    )
    json_dump(DOCS / "WORKSTREAM_REGISTRY.json", registry)

    report["assignment_record"] = {
        "assignment_integration_commit": integration_head,
        "assignment_branch_head": builder_head,
        "assignment_lineage_state": "SYNCHRONIZED",
    }
    report["registry_updated"] = True
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="V3.2 fail-closed assignment authority for T11-T70")
    ap.add_argument("task_id")
    ap.add_argument("--owner", required=True)
    ap.add_argument("--branch", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--owned-alias", required=True)
    ap.add_argument("--builder-head", required=True)
    ap.add_argument("--integration-head", required=True)
    ap.add_argument("--validate-only", action="store_true")
    args = ap.parse_args()

    result = (
        validate_assignment(args.task_id, args.branch, args.builder_head, args.integration_head, verify_remote=True)
        if args.validate_only
        else apply_assignment(
            args.task_id,
            args.owner,
            args.branch,
            args.base,
            args.owned_alias,
            args.builder_head,
            args.integration_head,
        )
    )
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
