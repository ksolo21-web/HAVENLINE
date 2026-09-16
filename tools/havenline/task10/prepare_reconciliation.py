#!/usr/bin/env python3
"""Read-only T10 isolated-candidate -> post-T09 integration reconciliation preflight.

This tool never mutates refs/files. It inspects an exact integration base and exact
isolated candidate, validates dependency closure from the base itself, verifies T10
changed-path ownership, detects base drift that overlaps T10-owned paths, and emits a
machine-readable handoff plan. It is useful before rebasing/cherry-picking the already-
built T10 candidate after T09 closes.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
INTEGRATION_BRANCH = "codex/havenline-sequential-task-01"
T10_ALLOWED_EXACT = {
    "HavenlineGodot/scripts/world_transform.gd",
    "HavenlineGodot/scripts/world_transform_view.gd",
    "HavenlineGodot/data/world_transform_recipes.json",
    "HavenlineGodot/tests/test_task10_world_transform.gd",
    "HavenlineGodot/tests/test_task10_integration.gd",
    "HavenlineGodot/tests/capture_task10_world_transform.gd",
    ".github/workflows/havenline-task10-prebuild.yml",
    ".github/workflows/havenline-task10-isolated.yml",
    ".github/workflows/havenline-task10-adapter-preflight.yml",
}
T10_ALLOWED_PREFIXES = (
    "HavenlineGodot/assets/world_transform_v1/",
    "Docs/Production/T10/",
    "tools/havenline/task10/",
)
T10_RUNTIME_PREFIXES = (
    "HavenlineGodot/scripts/world_transform.gd",
    "HavenlineGodot/scripts/world_transform_view.gd",
    "HavenlineGodot/data/world_transform_recipes.json",
    "HavenlineGodot/assets/world_transform_v1/",
    "HavenlineGodot/tests/test_task10_",
    "HavenlineGodot/tests/capture_task10_world_transform.gd",
)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def git_lines(*args: str) -> list[str]:
    text = git(*args)
    return [line for line in text.splitlines() if line]


def show_json(ref: str, path: str) -> dict:
    return json.loads(git("show", f"{ref}:{path}"))


def allowed_t10_path(path: str) -> bool:
    return path in T10_ALLOWED_EXACT or path.startswith(T10_ALLOWED_PREFIXES)


def overlaps_t10_runtime(path: str) -> bool:
    return any(path == prefix or path.startswith(prefix) for prefix in T10_RUNTIME_PREFIXES)


def registry_status(registry: dict, task: str) -> str | None:
    if task in registry.get("legacy_approvals", {}):
        return "APPROVED"
    row = next((x for x in registry.get("workstreams", []) if x.get("task_id") == task), None)
    return None if row is None else row.get("status")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--integration-base", required=True, help="Exact post-T09 integration commit")
    ap.add_argument("--isolated-candidate", required=True, help="Exact isolated T10 candidate commit")
    ap.add_argument("--require-dependencies-approved", action="store_true")
    ap.add_argument("--output")
    args = ap.parse_args()

    base = git("rev-parse", f"{args.integration_base}^{{commit}}")
    candidate = git("rev-parse", f"{args.isolated_candidate}^{{commit}}")
    merge_base = git("merge-base", base, candidate)

    graph = show_json(base, "Docs/Production/DEPENDENCY_GRAPH.json")
    registry = show_json(base, "Docs/Production/WORKSTREAM_REGISTRY.json")
    gates = show_json(base, "Docs/Production/task-gates.json")
    ownership = show_json(base, "Docs/Production/PATH_OWNERSHIP.json")

    dependency_state = {}
    dependency_errors: list[str] = []
    for dep in ["T05", "T08", "T09"]:
        graph_status = graph.get("tasks", {}).get(dep, {}).get("status")
        reg_status = registry_status(registry, dep)
        gate_approved = dep in gates.get("approved_tasks", [])
        dependency_state[dep] = {
            "graph": graph_status,
            "registry": reg_status,
            "task_gate_approved": gate_approved,
        }
        if graph_status != "APPROVED" or reg_status != "APPROVED" or not gate_approved:
            dependency_errors.append(f"{dep} not fully approved at integration base")

    if "T09" not in gates.get("completed_task_records", {}):
        dependency_errors.append("T09 completion record missing at integration base")
    if any(x.get("task_id") == "T09" for x in ownership.get("active_owners", [])):
        dependency_errors.append("T09 still active owner at integration base")

    candidate_changes = git_lines("diff", "--name-only", merge_base, candidate)
    unauthorized = [path for path in candidate_changes if not allowed_t10_path(path)]

    base_drift = git_lines("diff", "--name-only", merge_base, base)
    overlapping_drift = [path for path in base_drift if allowed_t10_path(path) or overlaps_t10_runtime(path)]
    shared_integration_drift = [
        path for path in base_drift
        if path in {
            "HavenlineGodot/scripts/simulation.gd",
            "HavenlineGodot/scripts/main.gd",
            "Docs/Production/DEPENDENCY_GRAPH.json",
            "Docs/Production/WORKSTREAM_REGISTRY.json",
            "Docs/Production/PATH_OWNERSHIP.json",
            "Docs/Production/task-gates.json",
        }
    ]

    errors: list[str] = []
    if unauthorized:
        errors.append("isolated candidate contains unauthorized paths: " + ", ".join(unauthorized))
    if overlapping_drift:
        errors.append("integration base drift overlaps T10-owned/runtime paths; manual reconciliation required: " + ", ".join(overlapping_drift))
    if args.require_dependencies_approved:
        errors.extend(dependency_errors)

    deps_ready = not dependency_errors
    path_reconcile_clean = not unauthorized and not overlapping_drift
    handoff_ready = deps_ready and path_reconcile_clean

    report = {
        "task": "T10",
        "integration_branch": INTEGRATION_BRANCH,
        "integration_base": base,
        "isolated_candidate": candidate,
        "merge_base": merge_base,
        "dependency_state": dependency_state,
        "dependencies_fully_approved": deps_ready,
        "dependency_errors": dependency_errors,
        "isolated_changed_file_count": len(candidate_changes),
        "isolated_changed_files": candidate_changes,
        "unauthorized_isolated_paths": unauthorized,
        "integration_drift_file_count": len(base_drift),
        "integration_drift_files": base_drift,
        "overlapping_t10_drift": overlapping_drift,
        "shared_integration_drift": shared_integration_drift,
        "path_reconciliation_clean": path_reconcile_clean,
        "handoff_ready_for_reconcile": handoff_ready,
        "real_adapter_required_after_reconcile": True,
        "integration_allowed": False,
        "task_approved": False,
        "suggested_next_steps": (
            [
                "Run prepare_activation.py --activate --base <exact integration base> on the integration branch.",
                "Commit activation governance through the integration owner.",
                "Reconcile the isolated candidate onto that activation commit.",
                "Integration owner applies POST_T09_CHANGE_REQUEST_TEMPLATE.json if the shared simulation contract still matches.",
                "Run validate_post_t09_adapter.py --require-bound and the full T10 real-integration/regression/evidence/critic chain.",
            ] if handoff_ready else [
                "Do not integrate T10 yet.",
                "Resolve dependency closure and/or reported overlapping drift, then rerun this exact preflight.",
            ]
        ),
        "errors": errors,
        "passed": not errors,
    }
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        pathlib.Path(args.output).write_text(text)
    print(text, end="")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
