#!/usr/bin/env python3
"""Validate T10 parallel preparation and, after T09 approval, stage activation governance.

Default mode is read-only preparation validation. `--activate --base <sha>` is also
read-only and proves that T10 may be activated from the exact integration head.
`--write` stages the coordination-file mutations only after all activation checks
pass. It never creates the builder branch or edits gameplay runtime source.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from copy import deepcopy

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "Docs" / "Production"
CHECKLIST_PATH = DOCS / "T10" / "ACTIVATION_CHECKLIST.json"
GRAPH_PATH = DOCS / "DEPENDENCY_GRAPH.json"
REGISTRY_PATH = DOCS / "WORKSTREAM_REGISTRY.json"
OWNERSHIP_PATH = DOCS / "PATH_OWNERSHIP.json"
CRITICS_PATH = DOCS / "CRITIC_MATRIX.json"
GATES_PATH = DOCS / "task-gates.json"


def load(path: pathlib.Path):
    return json.loads(path.read_text())


def dump(path: pathlib.Path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def fail(message: str):
    raise SystemExit(message)


def prefix(pattern: str) -> str:
    cut = len(pattern)
    for token in ("*", "?", "["):
        pos = pattern.find(token)
        if pos >= 0:
            cut = min(cut, pos)
    return pattern[:cut].rstrip("/")


def may_overlap(a: str, b: str) -> bool:
    """Conservative path/glob collision test for Havenline reservation patterns."""
    if a == b:
        return True
    pa, pb = prefix(a), prefix(b)
    if not pa or not pb:
        return True
    return pa == pb or pa.startswith(pb + "/") or pb.startswith(pa + "/")


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def integration_branch_from_registry(registry) -> str:
    return registry.get("integration_branch", "codex/havenline-sequential-task-01")


def validate_preparation():
    checklist = load(CHECKLIST_PATH)
    graph = load(GRAPH_PATH)
    registry = load(REGISTRY_PATH)
    ownership = load(OWNERSHIP_PATH)
    critics = load(CRITICS_PATH)

    errors: list[str] = []
    t10 = graph.get("tasks", {}).get("T10")
    if not t10:
        errors.append("T10 is missing from DEPENDENCY_GRAPH.json")
        t10 = {}

    expected_deps = checklist["dependencies"]
    if t10.get("dependencies") != expected_deps:
        errors.append(f"T10 dependency mismatch: graph={t10.get('dependencies')} checklist={expected_deps}")

    expected_critics = checklist["required_critics"]
    if t10.get("critics") != expected_critics:
        errors.append(f"T10 critic mismatch in dependency graph: {t10.get('critics')}")
    if critics.get("task_applicability", {}).get("T10") != expected_critics:
        errors.append(f"T10 critic mismatch in CRITIC_MATRIX.json: {critics.get('task_applicability', {}).get('T10')}")

    if checklist.get("runtime_build_allowed_before_activation") is not False:
        errors.append("runtime_build_allowed_before_activation must remain false")

    planned = checklist["planned_owned_paths"]
    if len(planned) != len(set(planned)):
        errors.append("planned T10 reservation contains duplicate paths")

    protected = ownership.get("aliases", {}).get("@integration-only", [])
    for candidate in planned:
        for path in protected:
            if may_overlap(candidate, path):
                errors.append(f"planned T10 path collides with integration-only path: {candidate} <> {path}")

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
    if active_collisions:
        errors.append("planned T10 reservation collides with active ownership: " + json.dumps(active_collisions))

    for required in (DOCS / "T10" / "FROZEN_SCOPE.md", DOCS / "T10" / "TASK_PACKET.md", CHECKLIST_PATH):
        if not required.exists() or not required.read_text().strip():
            errors.append(f"missing/empty preparation artifact: {required.relative_to(ROOT)}")

    row = next((x for x in registry.get("workstreams", []) if x.get("task_id") == "T10"), None)
    if row and row.get("status") not in ("LOCKED", "PREPARED"):
        errors.append(f"pre-activation registry T10 status must be LOCKED/PREPARED, got {row.get('status')}")

    result = {
        "task_id": "T10",
        "mode": "preparation",
        "integration_branch": integration_branch_from_registry(registry),
        "prepared_from": checklist["prepared_from_integration_commit"],
        "t09_current_graph_status": graph.get("tasks", {}).get("T09", {}).get("status"),
        "planned_owned_path_count": len(planned),
        "active_ownership_collision_count": len(active_collisions),
        "required_critics": expected_critics,
        "runtime_build_allowed": False,
        "passed": not errors,
        "errors": errors,
    }
    return result


def validate_activation(base: str):
    prep = validate_preparation()
    if not prep["passed"]:
        fail(json.dumps(prep, indent=2))

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
        registry_row = next((x for x in registry.get("workstreams", []) if x.get("task_id") == dep), None)
        registry_status = "APPROVED" if dep in registry.get("legacy_approvals", {}) else (registry_row or {}).get("status")
        if graph_status != "APPROVED":
            errors.append(f"dependency {dep} graph status is {graph_status}, not APPROVED")
        if registry_status != "APPROVED":
            errors.append(f"dependency {dep} registry status is {registry_status}, not APPROVED")
        if dep not in gates.get("approved_tasks", []):
            errors.append(f"dependency {dep} missing from task-gates approved_tasks")

    if "T09" not in gates.get("completed_task_records", {}):
        errors.append("T09 has no completed_task_records entry in task-gates")

    stale_t09_owner = [x for x in ownership.get("active_owners", []) if x.get("task_id") == "T09"]
    if stale_t09_owner:
        errors.append("T09 is still listed as an active owner; finish T09 closeout before T10 activation")

    if graph.get("tasks", {}).get("T10", {}).get("status") not in ("LOCKED", "PREPARED"):
        errors.append(f"unexpected pre-activation T10 graph state: {graph.get('tasks', {}).get('T10', {}).get('status')}")

    result = {
        "task_id": "T10",
        "mode": "activation-preflight",
        "base": base,
        "head": head,
        "dependencies": checklist["dependencies"],
        "future_branch": checklist["future_builder_branch"],
        "owner": checklist["future_owner"],
        "owned_alias": checklist["planned_owned_alias"],
        "passed": not errors,
        "errors": errors,
    }
    return result


def stage_activation(base: str):
    result = validate_activation(base)
    if not result["passed"]:
        fail(json.dumps(result, indent=2))

    checklist = load(CHECKLIST_PATH)
    graph = load(GRAPH_PATH)
    registry = load(REGISTRY_PATH)
    ownership = load(OWNERSHIP_PATH)
    gates = load(GATES_PATH)

    alias = checklist["planned_owned_alias"]
    paths = checklist["planned_owned_paths"]
    owner = checklist["future_owner"]
    branch = checklist["future_builder_branch"]
    critics = checklist["required_critics"]

    # Idempotent ownership reservation.
    existing_alias = ownership.setdefault("aliases", {}).get(alias)
    if existing_alias is not None and existing_alias != paths:
        fail(f"existing {alias} differs from prepared reservation")
    ownership["aliases"][alias] = paths

    ownership["active_owners"] = [x for x in ownership.get("active_owners", []) if x.get("task_id") != "T10"]
    ownership["active_owners"].append({
        "workstream": "T10-world-transformation-builder",
        "task_id": "T10",
        "owner": owner,
        "branch": branch,
        "paths_alias": alias,
        "status": "ASSIGNED",
        "base_commit": base,
    })
    reservations = ownership.setdefault("future_wave1_reservations", [])
    if not any(x.get("task_id") == "T10" for x in reservations):
        reservations.append({"task_id": "T10", "branch": branch, "paths_alias": alias})

    graph["tasks"]["T10"]["status"] = "ASSIGNED"

    row = next((x for x in registry.get("workstreams", []) if x.get("task_id") == "T10"), None)
    new_row = {
        "task_id": "T10",
        "task_name": graph["tasks"]["T10"]["name"],
        "workstream_id": "T10-world-transformation-builder",
        "status": "ASSIGNED",
        "owner": owner,
        "branch": branch,
        "base_commit": base,
        "dependencies": graph["tasks"]["T10"]["dependencies"],
        "owned_paths": [alias],
        "protected_paths": ["@protected:approved", "@integration-only"],
        "candidate_commit": None,
        "candidate_hash_or_artifact": None,
        "tests": {},
        "evidence_path": "Docs/Production/Evidence/T10/",
        "critic_requirements": critics,
        "critic_status": {},
        "integration_status": "not integrated",
        "known_blockers": [],
        "next_action": "Create the isolated T10 builder branch from the activation governance checkpoint and begin the frozen World Transformation Framework candidate.",
    }
    if row:
        row.clear(); row.update(new_row)
    else:
        registry.setdefault("workstreams", []).append(new_row)

    notes = registry.setdefault("notes", [])
    activation_note = "T03-T09 are APPROVED. T10 is ASSIGNED with frozen scope, owner and disjoint reservation; T11+ runtime remains dependency-gated."
    notes[:] = [n for n in notes if not ("T09 is ASSIGNED" in n or "T10+ runtime work remains locked" in n)]
    if activation_note not in notes:
        notes.append(activation_note)

    gates["active_task"] = "T10"
    gates["active_task_title"] = graph["tasks"]["T10"]["name"]
    gates["active_status"] = "ASSIGNED"
    gates["active_frozen_scope"] = "Docs/Production/T10/FROZEN_SCOPE.md"
    gates["active_task_packet"] = "Docs/Production/T10/TASK_PACKET.md"
    gates["active_base_integration_commit"] = base
    gates["active_candidate_source"] = None
    gates["active_candidate_run"] = None
    gates["active_tests"] = None
    gates["active_evidence"] = "Docs/Production/Evidence/T10/"
    gates["active_critic_state"] = "PENDING_BUILD_AND_INDEPENDENT_REVIEW"
    gates["task10_plus_runtime_locked"] = False
    wave = gates.setdefault("next_post_t03_wave", [])
    wave[:] = [x for x in wave if x.get("task") != "T10"]
    wave.append({
        "task": "T10",
        "branch": branch,
        "state": "ASSIGNED",
        "owner": owner,
        "base_commit": base,
        "reason": "T05/T08/T09 are approved; T10 frozen scope, activation preflight and disjoint reservation are complete. Build and independent C1/C2/C3/C4/C6/C7 review remain pending.",
    })

    dump(OWNERSHIP_PATH, ownership)
    dump(GRAPH_PATH, graph)
    dump(REGISTRY_PATH, registry)
    dump(GATES_PATH, gates)

    return {
        **result,
        "written": True,
        "mutated_files": [
            str(OWNERSHIP_PATH.relative_to(ROOT)),
            str(GRAPH_PATH.relative_to(ROOT)),
            str(REGISTRY_PATH.relative_to(ROOT)),
            str(GATES_PATH.relative_to(ROOT)),
        ],
        "next_actions": [
            "Run: python3 tools/havenline/production/workstream.py validate-registry",
            "Run the production governance/migration tests.",
            "Commit these governance mutations on the integration branch.",
            "Create havenline/T10-world-transformation from that resulting integration governance commit.",
            "Require candidate guard PASS before T10 runtime implementation expands.",
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--activate", action="store_true", help="Require all T10 dependencies approved and exact base/head match")
    ap.add_argument("--base", help="Exact post-T09 integration head used for T10 activation")
    ap.add_argument("--write", action="store_true", help="Stage T10 ASSIGNED coordination files after a passing activation preflight")
    args = ap.parse_args()

    if args.write and not args.activate:
        fail("--write requires --activate")
    if args.activate and not args.base:
        fail("--activate requires --base <exact integration head>")

    if args.activate:
        result = stage_activation(args.base) if args.write else validate_activation(args.base)
    else:
        result = validate_preparation()

    print(json.dumps(result, indent=2))
    if not result.get("passed"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
