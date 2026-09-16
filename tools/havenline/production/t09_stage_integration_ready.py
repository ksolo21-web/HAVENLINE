#!/usr/bin/env python3
"""Stage T09 INTEGRATION_READY governance after exact strict closeout proof.

Default mode is read-only and emits the exact mutation plan. `--write` updates
only governance coordination files in the current working tree. It can never
set APPROVED, merge runtime, close T09 ownership, or activate T10.
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "Docs" / "Production"
GRAPH = DOCS / "DEPENDENCY_GRAPH.json"
REGISTRY = DOCS / "WORKSTREAM_REGISTRY.json"
OWNERSHIP = DOCS / "PATH_OWNERSHIP.json"
GATES = DOCS / "task-gates.json"
REQUIRED_CRITICS = ["C2", "C3", "C4", "C5", "C6"]


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text())


def dump(path: pathlib.Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n")


def head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def minimum_model_score(review: dict) -> float:
    values: list[float] = []
    for critic in ("C2", "C3", "C4", "C5"):
        row = review["critics"][critic]
        values.extend(float(value) for value in row.get("scores", {}).values())
    if not values:
        raise SystemExit("strict review contains no model critic scores")
    return min(values)


def validate_inputs(closeout: dict, review: dict, current_head: str) -> tuple[str, str, list[str]]:
    errors: list[str] = []
    if closeout.get("task") != "T09" or closeout.get("mode") != "read-only-closeout-preflight":
        errors.append("closeout preflight identity/mode mismatch")
    if closeout.get("passed") is not True or closeout.get("ready_for_integration_owner_closeout") is not True:
        errors.append("closeout preflight did not pass")
    if closeout.get("approval_mutation_performed") is not False or closeout.get("integration_mutation_performed") is not False:
        errors.append("closeout artifact already claims a forbidden mutation")
    if closeout.get("integration_head") != current_head:
        errors.append(f"closeout was evaluated against stale integration head {closeout.get('integration_head')} != {current_head}")
    candidate = str(closeout.get("candidate", ""))
    source_run = str(closeout.get("source_run_id", ""))
    if len(candidate) != 40 or not source_run.isdigit():
        errors.append("invalid candidate/source-run identity")
    if review.get("task") != "T09" or review.get("candidate") != candidate:
        errors.append("strict review candidate mismatch")
    if str(review.get("source_run_id", "")) != source_run:
        errors.append("strict review source run mismatch")
    if review.get("required_critics") != REQUIRED_CRITICS or review.get("passed") is not True:
        errors.append("strict review did not pass the exact C2-C6 critic set")
    if review.get("task_approved") is not False:
        errors.append("strict review must not self-approve T09")
    if int(review.get("c5_full_cycle_groups", 0)) < 15:
        errors.append("strict review lacks full-cycle C5 coverage")
    for critic in REQUIRED_CRITICS:
        row = review.get("critics", {}).get(critic)
        if not isinstance(row, dict):
            errors.append(f"missing {critic} record")
            continue
        if row.get("passed") is not True:
            errors.append(f"{critic} did not pass")
        if critic != "C6":
            if row.get("defects"):
                errors.append(f"{critic} has unresolved defects")
            if row.get("coverage_complete") is not True or row.get("confidence") not in ("medium", "high"):
                errors.append(f"{critic} coverage/confidence invalid")
            if not row.get("scores") or any(float(v) <= 9.0 for v in row["scores"].values()):
                errors.append(f"{critic} has a raw score not strictly above 9.0")
        elif row.get("errors"):
            errors.append("C6 has performance errors")
    return candidate, source_run, errors


def mutate(graph: dict, registry: dict, ownership: dict, gates: dict, candidate: str, source_run: str, review: dict) -> dict:
    graph["tasks"]["T09"]["status"] = "INTEGRATION_READY"

    row = next((x for x in registry.get("workstreams", []) if x.get("task_id") == "T09"), None)
    if not row:
        raise SystemExit("T09 registry row missing")
    row["status"] = "INTEGRATION_READY"
    row["status_updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    row["candidate_commit"] = candidate
    row["candidate_hash_or_artifact"] = f"source-run:{source_run}; strict-review:PASS_C2_C3_C4_C5_C6; closeout-preflight:PASS"
    row["tests"] = {"source_run": int(source_run), "result": "PASS", "capture_reports": 71}
    row["critic_status"] = {
        critic: (
            f"PASS; minimum raw dimension {min(float(v) for v in review['critics'][critic]['scores'].values()):.4f}; zero defects"
            if critic != "C6" else "PASS; exact-base deterministic T09 performance delta"
        ) for critic in REQUIRED_CRITICS
    }
    row["integration_status"] = "INTEGRATION_READY; exact source/critics/closeout preflight passed; runtime not yet integrated"
    row["known_blockers"] = ["merge exact T09 candidate through integration owner and pass merged-candidate regression before APPROVED"]
    row["next_action"] = "Merge only the exact frozen T09 candidate through the integration owner, rerun merged-candidate regression, then stage APPROVED closeout if still clean."

    active = [x for x in ownership.get("active_owners", []) if x.get("task_id") == "T09"]
    if len(active) != 1:
        raise SystemExit(f"expected exactly one active T09 owner, found {len(active)}")
    active[0]["status"] = "INTEGRATION_READY"

    gates["active_task"] = "T09"
    gates["active_status"] = "INTEGRATION_READY"
    gates["active_candidate_source"] = candidate
    gates["active_candidate_run"] = int(source_run)
    gates["active_tests"] = {"source_run": int(source_run), "result": "PASS", "capture_reports": 71}
    gates["active_critic_state"] = "PASS_C2_C3_C4_C5_C6_PENDING_INTEGRATION"
    for item in gates.get("next_post_t03_wave", []):
        if item.get("task") == "T09":
            item["state"] = "INTEGRATION_READY"
            item["reason"] = "Exact T09 source run, 71-capture contact evidence, exact-base C6 performance, strict C2/C3/C4/C5 review, and read-only closeout preflight passed; exact-source integration regression remains before APPROVED."
            break
    else:
        raise SystemExit("T09 next_post_t03_wave row missing")

    # These must remain untouched until the later APPROVED closeout.
    if "T09" in gates.get("approved_tasks", []) or "T09" in gates.get("completed_task_records", {}):
        raise SystemExit("T09 is already recorded as APPROVED; integration-ready staging is invalid")
    return {
        "graph_status": graph["tasks"]["T09"]["status"],
        "registry_status": row["status"],
        "ownership_status": active[0]["status"],
        "task_gate_status": gates["active_status"],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--closeout", required=True)
    ap.add_argument("--strict-review", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    current_head = head()
    closeout = load(pathlib.Path(args.closeout))
    review = load(pathlib.Path(args.strict_review))
    candidate, source_run, errors = validate_inputs(closeout, review, current_head)

    graph = load(GRAPH); registry = load(REGISTRY); ownership = load(OWNERSHIP); gates = load(GATES)
    current_states = {
        "graph": graph.get("tasks", {}).get("T09", {}).get("status"),
        "registry": (next((x for x in registry.get("workstreams", []) if x.get("task_id") == "T09"), {}) or {}).get("status"),
        "ownership": (next((x for x in ownership.get("active_owners", []) if x.get("task_id") == "T09"), {}) or {}).get("status"),
        "task_gates": gates.get("active_status") if gates.get("active_task") == "T09" else None,
    }
    if any(value != "ASSIGNED" for value in current_states.values()):
        errors.append(f"T09 pre-promotion states must all be ASSIGNED: {current_states}")
    if graph.get("tasks", {}).get("T09", {}).get("critics") != REQUIRED_CRITICS:
        errors.append("dependency graph T09 critic set drift")
    if "T09" in gates.get("approved_tasks", []) or "T09" in gates.get("completed_task_records", {}):
        errors.append("T09 already appears in approval records")

    plan = {
        "task": "T09",
        "mode": "integration-ready-staging",
        "integration_head": current_head,
        "candidate": candidate,
        "source_run_id": source_run,
        "minimum_model_critic_score": minimum_model_score(review) if not errors else None,
        "required_critics": REQUIRED_CRITICS,
        "pre_states": current_states,
        "target_state": "INTEGRATION_READY",
        "approved_state_allowed": False,
        "runtime_merge_performed": False,
        "approval_mutation_performed": False,
        "mutated_files": [str(p.relative_to(ROOT)) for p in (GRAPH, REGISTRY, OWNERSHIP, GATES)],
        "write_requested": args.write,
        "errors": errors,
        "passed": not errors,
    }
    if errors:
        pathlib.Path(args.out).write_text(json.dumps(plan, indent=2) + "\n")
        print(json.dumps(plan, indent=2))
        raise SystemExit(1)

    graph2=json.loads(json.dumps(graph)); registry2=json.loads(json.dumps(registry)); ownership2=json.loads(json.dumps(ownership)); gates2=json.loads(json.dumps(gates))
    target_states = mutate(graph2, registry2, ownership2, gates2, candidate, source_run, review)
    plan["target_states"] = target_states
    if any(value != "INTEGRATION_READY" for value in target_states.values()):
        raise SystemExit("internal staging target-state mismatch")

    if args.write:
        dump(GRAPH, graph2); dump(REGISTRY, registry2); dump(OWNERSHIP, ownership2); dump(GATES, gates2)
        registry_check = subprocess.run(["python3", "tools/havenline/production/workstream.py", "validate-registry"], cwd=ROOT, text=True, capture_output=True)
        migration_check = subprocess.run(["python3", "tools/havenline/production/validate_migration.py"], cwd=ROOT, text=True, capture_output=True)
        plan["post_write_registry_validation"] = registry_check.returncode == 0
        plan["post_write_migration_validation"] = migration_check.returncode == 0
        if registry_check.returncode != 0 or migration_check.returncode != 0:
            plan["passed"] = False
            plan["errors"] = ["post-write governance validation failed", registry_check.stdout + registry_check.stderr, migration_check.stdout + migration_check.stderr]
            pathlib.Path(args.out).write_text(json.dumps(plan, indent=2) + "\n")
            print(json.dumps(plan, indent=2))
            raise SystemExit(1)
    pathlib.Path(args.out).write_text(json.dumps(plan, indent=2) + "\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
