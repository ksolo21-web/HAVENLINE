#!/usr/bin/env python3
"""Validate T11 build-pending preparation and final integration promotion.

Default mode validates that an isolated T11 build may proceed against the frozen
T10 semantic contract while final integration remains dependency-gated.
`--activate --base <sha>` is the read-only final-promotion preflight and must
still fail until T10 is APPROVED/integrated on the authoritative branch.
`--write` stages coordination-file mutations only after every final-promotion
check passes. This tool never creates the builder branch or edits gameplay.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "Docs" / "Production"
CHECKLIST_PATH = DOCS / "T11" / "ACTIVATION_CHECKLIST.json"
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
    t11 = graph.get("tasks", {}).get("T11")
    if not t11:
        errors.append("T11 is missing from DEPENDENCY_GRAPH.json")
        t11 = {}

    expected_deps = checklist["dependencies"]
    if t11.get("dependencies") != expected_deps:
        errors.append(f"T11 dependency mismatch: graph={t11.get('dependencies')} checklist={expected_deps}")

    expected_critics = checklist["required_critics"]
    if t11.get("critics") != expected_critics:
        errors.append(f"T11 critic mismatch in dependency graph: {t11.get('critics')}")
    if critics.get("task_applicability", {}).get("T11") != expected_critics:
        errors.append(f"T11 critic mismatch in CRITIC_MATRIX.json: {critics.get('task_applicability', {}).get('T11')}")

    policy = checklist.get("build_pending_policy", {})
    if policy.get("isolated_build_allowed_before_t10_approval") is not True:
        errors.append("isolated build-pending policy must allow T11 build before T10 approval")
    if policy.get("maximum_state_before_t10_approval") != "BUILT_PENDING_DEPENDENCY":
        errors.append("maximum pre-T10 T11 state must be BUILT_PENDING_DEPENDENCY")
    if policy.get("may_claim_integration_ready") is not False or policy.get("may_integrate") is not False:
        errors.append("build-pending policy must keep INTEGRATION_READY/integration blocked")
    if checklist.get("runtime_build_allowed_before_final_activation") is not True:
        errors.append("runtime_build_allowed_before_final_activation must be true")
    if checklist.get("final_integration_allowed_before_dependencies") is not False:
        errors.append("final_integration_allowed_before_dependencies must remain false")

    planned = checklist["planned_owned_paths"]
    if len(planned) != len(set(planned)):
        errors.append("planned T11 reservation contains duplicate paths")

    protected = ownership.get("aliases", {}).get("@integration-only", [])
    for candidate in planned:
        for path in protected:
            if may_overlap(candidate, path):
                errors.append(f"planned T11 path collides with integration-only path: {candidate} <> {path}")

    t10_reserved = {
        "HavenlineGodot/scripts/world_transform.gd",
        "HavenlineGodot/scripts/world_transform_view.gd",
        "HavenlineGodot/data/world_transform_recipes.json",
        "HavenlineGodot/assets/world_transform_v1/**",
        "HavenlineGodot/tests/test_task10_world_transform.gd",
        "HavenlineGodot/tests/test_task10_integration.gd",
        "HavenlineGodot/tests/capture_task10_world_transform.gd",
        "Docs/Production/T10/**",
        "tools/havenline/task10/**",
        ".github/workflows/havenline-task10-*.yml",
    }
    prepared_t10 = DOCS / "T10" / "ACTIVATION_CHECKLIST.json"
    if prepared_t10.exists():
        t10_reserved = set(load(prepared_t10).get("planned_owned_paths", t10_reserved))
    t10_collisions = []
    for candidate in planned:
        for path in t10_reserved:
            if may_overlap(candidate, path):
                t10_collisions.append({"candidate": candidate, "t10": path})
    if t10_collisions:
        errors.append("planned T11 reservation collides with T10: " + json.dumps(t10_collisions))

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
        errors.append("planned T11 reservation collides with active ownership: " + json.dumps(active_collisions))

    for required in (DOCS / "T11" / "FROZEN_SCOPE.md", DOCS / "T11" / "TASK_PACKET.md", CHECKLIST_PATH):
        if not required.exists() or not required.read_text().strip():
            errors.append(f"missing/empty preparation artifact: {required.relative_to(ROOT)}")

    row = next((x for x in registry.get("workstreams", []) if x.get("task_id") == "T11"), None)
    if row and row.get("status") not in ("LOCKED", "PREPARED"):
        errors.append(f"canonical pre-promotion registry T11 status must be LOCKED/PREPARED, got {row.get('status')}")

    return {
        "task_id": "T11",
        "mode": "build-pending-preparation",
        "integration_branch": registry.get("integration_branch", "codex/havenline-sequential-task-01"),
        "prepared_from_branch": checklist.get("prepared_from_branch"),
        "prepared_from_commit": checklist.get("prepared_from_commit"),
        "builder_branch": checklist.get("builder_branch"),
        "t10_current_graph_status": graph.get("tasks", {}).get("T10", {}).get("status"),
        "planned_owned_path_count": len(planned),
        "t10_collision_count": len(t10_collisions),
        "active_ownership_collision_count": len(active_collisions),
        "required_critics": expected_critics,
        "isolated_build_allowed": True,
        "maximum_pre_dependency_state": "BUILT_PENDING_DEPENDENCY",
        "final_integration_allowed": False,
        "passed": not errors,
        "errors": errors,
    }


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
        reg_status = registry_status(registry, dep)
        if graph_status != "APPROVED":
            errors.append(f"dependency {dep} graph status is {graph_status}, not APPROVED")
        if reg_status != "APPROVED":
            errors.append(f"dependency {dep} registry status is {reg_status}, not APPROVED")
        if dep not in gates.get("approved_tasks", []):
            errors.append(f"dependency {dep} missing from task-gates approved_tasks")

    if "T10" not in gates.get("completed_task_records", {}):
        errors.append("T10 has no completed_task_records entry in task-gates")

    stale_t10_owner = [x for x in ownership.get("active_owners", []) if x.get("task_id") == "T10"]
    if stale_t10_owner:
        errors.append("T10 is still listed as an active owner; finish T10 closeout before T11 promotion")

    if graph.get("tasks", {}).get("T11", {}).get("status") not in ("LOCKED", "PREPARED"):
        errors.append(f"unexpected canonical pre-promotion T11 graph state: {graph.get('tasks', {}).get('T11', {}).get('status')}")

    return {
        "task_id": "T11",
        "mode": "integration-promotion-preflight",
        "base": base,
        "head": head,
        "dependencies": checklist["dependencies"],
        "builder_branch": checklist["builder_branch"],
        "owner": checklist["future_owner"],
        "owned_alias": checklist["planned_owned_alias"],
        "passed": not errors,
        "errors": errors,
    }


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
    branch = checklist["builder_branch"]
    critics = checklist["required_critics"]

    existing_alias = ownership.setdefault("aliases", {}).get(alias)
    if existing_alias is not None and existing_alias != paths:
        fail(f"existing {alias} differs from prepared reservation")
    ownership["aliases"][alias] = paths

    ownership["active_owners"] = [x for x in ownership.get("active_owners", []) if x.get("task_id") != "T11"]
    ownership["active_owners"].append({
        "workstream": "T11-camp-construction-builder",
        "task_id": "T11",
        "owner": owner,
        "branch": branch,
        "paths_alias": alias,
        "status": "ASSIGNED",
        "base_commit": base,
    })

    reservations = ownership.setdefault("future_wave1_reservations", [])
    if not any(x.get("task_id") == "T11" for x in reservations):
        reservations.append({"task_id": "T11", "branch": branch, "paths_alias": alias})

    graph["tasks"]["T11"]["status"] = "ASSIGNED"

    row = next((x for x in registry.get("workstreams", []) if x.get("task_id") == "T11"), None)
    new_row = {
        "task_id": "T11",
        "task_name": graph["tasks"]["T11"]["name"],
        "workstream_id": "T11-camp-construction-builder",
        "status": "ASSIGNED",
        "owner": owner,
        "branch": branch,
        "base_commit": base,
        "dependencies": graph["tasks"]["T11"]["dependencies"],
        "owned_paths": [alias],
        "protected_paths": ["@protected:approved", "@integration-only"],
        "candidate_commit": None,
        "candidate_hash_or_artifact": None,
        "tests": {},
        "evidence_path": "Docs/Production/Evidence/T11/",
        "critic_requirements": critics,
        "critic_status": {},
        "integration_status": "not integrated",
        "known_blockers": [],
        "next_action": "Reconcile the build-pending T11 candidate to the exact accepted T10 source, rerun dependency-sensitive tests/evidence, then advance to INTEGRATION_READY.",
    }
    if row:
        row.clear(); row.update(new_row)
    else:
        registry.setdefault("workstreams", []).append(new_row)

    notes = registry.setdefault("notes", [])
    activation_note = "T03-T10 are APPROVED. T11 build-pending candidate may now be reconciled and promoted toward integration under its frozen scope and disjoint reservation."
    if activation_note not in notes:
        notes.append(activation_note)

    gates["active_task"] = "T11"
    gates["active_task_title"] = graph["tasks"]["T11"]["name"]
    gates["active_status"] = "ASSIGNED"
    gates["active_frozen_scope"] = "Docs/Production/T11/FROZEN_SCOPE.md"
    gates["active_task_packet"] = "Docs/Production/T11/TASK_PACKET.md"
    gates["active_base_integration_commit"] = base
    gates["active_candidate_source"] = None
    gates["active_candidate_run"] = None
    gates["active_tests"] = None
    gates["active_evidence"] = "Docs/Production/Evidence/T11/"
    gates["active_critic_state"] = "PENDING_RECONCILIATION_BUILD_AND_INDEPENDENT_REVIEW"

    wave = gates.setdefault("next_post_t03_wave", [])
    wave[:] = [x for x in wave if x.get("task") != "T11"]
    wave.append({
        "task": "T11",
        "branch": branch,
        "state": "ASSIGNED",
        "owner": owner,
        "base_commit": base,
        "reason": "T05/T10 are approved; reconcile the existing build-pending T11 candidate to the exact T10 interface before integration readiness.",
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
            "Run production governance/migration tests.",
            "Commit promotion governance on the integration branch.",
            "Rebase/reconcile havenline/T11-camp-construction to that exact post-T10 governance commit.",
            "Require dependency-sensitive candidate guards, regression and fresh evidence before INTEGRATION_READY.",
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--activate", action="store_true", help="Require all T11 dependencies approved for final integration promotion")
    ap.add_argument("--base", help="Exact post-T10 integration head used for T11 promotion")
    ap.add_argument("--write", action="store_true", help="Stage T11 promotion coordination files after passing final preflight")
    args = ap.parse_args()

    if args.write and not args.activate:
        fail("--write requires --activate")
    if args.activate and not args.base:
        fail("--activate requires --base <exact integration head>")

    result = stage_activation(args.base) if args.write else (validate_activation(args.base) if args.activate else validate_preparation())
    print(json.dumps(result, indent=2))
    if not result.get("passed"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
