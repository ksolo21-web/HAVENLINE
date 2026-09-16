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
BUILD_PENDING_PATH = DOCS / "T11" / "BUILD_PENDING_CANDIDATE.json"
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


def checkpoint_source(checkpoint: dict) -> str:
    return str(
        checkpoint.get("runtime_and_evidence_candidate_source")
        or checkpoint.get("runtime_candidate_source")
        or ""
    )


def validate_build_pending_checkpoint(errors: list[str]) -> dict:
    if not BUILD_PENDING_PATH.exists() or not BUILD_PENDING_PATH.read_text().strip():
        errors.append("missing/empty T11 BUILD_PENDING_CANDIDATE.json")
        return {}
    try:
        checkpoint = load(BUILD_PENDING_PATH)
    except Exception as exc:
        errors.append(f"T11 BUILD_PENDING_CANDIDATE.json is invalid JSON: {exc}")
        return {}

    if checkpoint.get("task_id") != "T11":
        errors.append("build-pending checkpoint task_id must be T11")
    if checkpoint.get("state") != "BUILT_PENDING_DEPENDENCY":
        errors.append(f"build-pending checkpoint state must be BUILT_PENDING_DEPENDENCY, got {checkpoint.get('state')}")
    if checkpoint.get("final_integration_ready") is not False:
        errors.append("build-pending checkpoint must not claim final integration readiness")
    if checkpoint.get("task_approved") is not False:
        errors.append("build-pending checkpoint must not claim task approval")
    if checkpoint.get("unresolved_mandatory_build_defects") != []:
        errors.append("build-pending checkpoint must have zero unresolved mandatory build defects")

    source = checkpoint_source(checkpoint)
    if len(source) != 40:
        errors.append(f"build-pending checkpoint needs an exact 40-char candidate source SHA, got {source!r}")

    run = checkpoint.get("build_pending_test_run", {})
    if not isinstance(run, dict):
        errors.append("build_pending_test_run must be an object")
        run = {}
    if run.get("source") != source:
        errors.append(f"build-pending run source does not match candidate source: run={run.get('source')} candidate={source}")
    if run.get("conclusion") != "success":
        errors.append(f"build-pending test run conclusion must be success, got {run.get('conclusion')}")
    if not isinstance(run.get("workflow_run"), int) or int(run.get("workflow_run", 0)) <= 0:
        errors.append("build-pending checkpoint must record a workflow_run id")
    if not isinstance(run.get("artifact_id"), int) or int(run.get("artifact_id", 0)) <= 0:
        errors.append("build-pending checkpoint must record an artifact_id")
    artifact_sha = str(run.get("artifact_sha256", ""))
    if len(artifact_sha) != 64:
        errors.append("build-pending checkpoint must record a 64-char artifact_sha256")

    tests = checkpoint.get("build_pending_tests", {})
    if not isinstance(tests, dict):
        errors.append("build_pending_tests must be an object")
        tests = {}
    if tests.get("all_passed") is not True:
        errors.append("build-pending checkpoint tests must all pass")
    if int(tests.get("suite_count", 0)) < 1 or int(tests.get("check_count", 0)) < 1:
        errors.append("build-pending checkpoint must record non-zero suite/check counts")
    for key in ("godot_import", "source_contract", "production_governance_regression", "rendered_evidence_gate"):
        if tests.get(key) != "PASS":
            errors.append(f"build-pending checkpoint {key} must be PASS, got {tests.get(key)}")

    evidence = checkpoint.get("rendered_evidence", {})
    if not isinstance(evidence, dict):
        errors.append("rendered_evidence must be an object")
        evidence = {}
    if int(evidence.get("standard_frame_count", 0)) < 1 or int(evidence.get("native_4k_frame_count", 0)) < 1:
        errors.append("build-pending checkpoint must include standard and native-4K rendered evidence")
    if evidence.get("approved_t03_boundary_rendered") is not True:
        errors.append("build-pending rendered evidence must include approved T03 boundary context")
    if evidence.get("lifecycle_beacon_readable_at_gameplay_scale") is not True:
        errors.append("build-pending rendered evidence must record gameplay-scale lifecycle readability")
    if evidence.get("final_visual_critic_evidence") is not False:
        errors.append("build-pending checkpoint must not claim final visual critic evidence")
    if evidence.get("physical_4k60_verified") is not False:
        errors.append("build-pending checkpoint must not claim physical 4K60 verification")

    blockers = checkpoint.get("blocked_before_integration_ready")
    if not isinstance(blockers, list) or not blockers:
        errors.append("build-pending checkpoint must preserve blockers before INTEGRATION_READY")

    return checkpoint


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

    checkpoint = validate_build_pending_checkpoint(errors)
    candidate_source = checkpoint_source(checkpoint)
    run = checkpoint.get("build_pending_test_run", {}) if checkpoint else {}

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
        "build_pending_candidate_source": candidate_source,
        "build_pending_workflow_run": run.get("workflow_run"),
        "build_pending_artifact_id": run.get("artifact_id"),
        "fresh_reconciliation_required": True,
        "passed": not errors,
        "errors": errors,
    }


def stage_activation(base: str):
    result = validate_activation(base)
    if not result["passed"]:
        fail(json.dumps(result, indent=2))

    checklist = load(CHECKLIST_PATH)
    checkpoint = load(BUILD_PENDING_PATH)
    graph = load(GRAPH_PATH)
    registry = load(REGISTRY_PATH)
    ownership = load(OWNERSHIP_PATH)
    gates = load(GATES_PATH)

    alias = checklist["planned_owned_alias"]
    paths = checklist["planned_owned_paths"]
    owner = checklist["future_owner"]
    branch = checklist["builder_branch"]
    critics = checklist["required_critics"]
    candidate_source = checkpoint_source(checkpoint)
    run = checkpoint["build_pending_test_run"]
    tests = checkpoint["build_pending_tests"]
    blockers = list(checkpoint.get("blocked_before_integration_ready", []))
    artifact_identity = f"github-actions:{run['artifact_id']}:sha256:{run['artifact_sha256']}"

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
        "candidate_commit": candidate_source,
        "candidate_hash_or_artifact": artifact_identity,
        "tests": tests,
        "evidence_path": "Docs/Production/Evidence/T11/",
        "critic_requirements": critics,
        "critic_status": {},
        "integration_status": "not integrated; reconciliation required",
        "known_blockers": blockers,
        "next_action": "Reconcile the preserved build-pending T11 candidate to the exact accepted T10 source, rerun dependency-sensitive tests/evidence, then advance to INTEGRATION_READY.",
    }
    if row:
        row.clear(); row.update(new_row)
    else:
        registry.setdefault("workstreams", []).append(new_row)

    notes = registry.setdefault("notes", [])
    activation_note = "T03-T10 are APPROVED. Preserve the tested T11 build-pending candidate, reconcile it to the exact accepted T10 source, and require fresh dependency-sensitive evidence before INTEGRATION_READY."
    if activation_note not in notes:
        notes.append(activation_note)

    gates["active_task"] = "T11"
    gates["active_task_title"] = graph["tasks"]["T11"]["name"]
    gates["active_status"] = "ASSIGNED"
    gates["active_frozen_scope"] = "Docs/Production/T11/FROZEN_SCOPE.md"
    gates["active_task_packet"] = "Docs/Production/T11/TASK_PACKET.md"
    gates["active_base_integration_commit"] = base
    gates["active_candidate_source"] = candidate_source
    gates["active_candidate_run"] = run.get("workflow_run")
    gates["active_tests"] = tests
    gates["active_evidence"] = "Docs/Production/Evidence/T11/"
    gates["active_critic_state"] = "PENDING_EXACT_T10_RECONCILIATION_AND_INDEPENDENT_REVIEW"

    wave = gates.setdefault("next_post_t03_wave", [])
    wave[:] = [x for x in wave if x.get("task") != "T11"]
    wave.append({
        "task": "T11",
        "branch": branch,
        "state": "ASSIGNED",
        "owner": owner,
        "base_commit": base,
        "candidate_commit": candidate_source,
        "reason": "T05/T10 are approved; preserve and reconcile the existing build-pending T11 candidate to the exact accepted T10 interface before integration readiness.",
    })

    dump(OWNERSHIP_PATH, ownership)
    dump(GRAPH_PATH, graph)
    dump(REGISTRY_PATH, registry)
    dump(GATES_PATH, gates)

    return {
        **result,
        "written": True,
        "preserved_candidate_source": candidate_source,
        "preserved_workflow_run": run.get("workflow_run"),
        "preserved_artifact_id": run.get("artifact_id"),
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
            "Rebase/reconcile havenline/T11-camp-construction to that exact post-T10 governance commit while preserving the tested build-pending source as the comparison anchor.",
            "Require exact accepted-T10 contract diff, dependency-sensitive candidate guards, regression and fresh evidence before INTEGRATION_READY.",
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
