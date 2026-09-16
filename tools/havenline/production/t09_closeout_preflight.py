#!/usr/bin/env python3
"""Read-only T09 production closeout preflight.

This tool proves that an exact T09 candidate has a complete source build/evidence
packet, a strict C2-C6 review decision, and a still-valid registered integration
scope. It NEVER changes task status, ownership, task gates, or integration refs.
Approval remains a separate integration-owner action after this report passes.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "Docs" / "Production"
REQUIRED_CRITICS = ["C2", "C3", "C4", "C5", "C6"]


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text())


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def show_json(ref: str, path: str) -> dict:
    return json.loads(git("show", f"{ref}:{path}"))


def registry_row(registry: dict, task: str) -> dict | None:
    return next((x for x in registry.get("workstreams", []) if x.get("task_id") == task), None)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--source-run-id", required=True)
    ap.add_argument("--evidence-root", required=True)
    ap.add_argument("--strict-review", required=True)
    ap.add_argument("--integration-head", default="HEAD")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    candidate = git("rev-parse", f"{args.candidate}^{{commit}}")
    integration = git("rev-parse", f"{args.integration_head}^{{commit}}")
    evidence = pathlib.Path(args.evidence_root)
    review = load(pathlib.Path(args.strict_review))
    errors: list[str] = []

    required_evidence = {
        "candidate_manifest": evidence / "candidate-manifest.json",
        "tests": evidence / "tests.json",
        "capture": evidence / "capture-summary.json",
        "performance": evidence / "performance" / "delta.json",
        "resource_actor_contract": evidence / "resource-actor-contract.json",
        "candidate_scope": evidence / "candidate-scope.json",
    }
    missing = [name for name, path in required_evidence.items() if not path.is_file()]
    if missing:
        errors.append("missing build evidence: " + ", ".join(missing))

    packet = {}
    if not missing:
        packet = {name: load(path) for name, path in required_evidence.items()}
        identities = {
            packet["candidate_manifest"].get("candidate_commit"),
            packet["tests"].get("source"),
            packet["capture"].get("candidate"),
            packet["performance"].get("candidate"),
        }
        if identities != {candidate}:
            errors.append(f"build evidence candidate mismatch: {sorted(str(x) for x in identities)}")
        if packet["tests"].get("all_passed") is not True:
            errors.append("source regression suite did not pass")
        if packet["capture"].get("passed") is not True:
            errors.append("source capture/evidence gate did not pass")
        if packet["capture"].get("reports") != 71:
            errors.append("source capture report count is not 71")
        if packet["performance"].get("passed") is not True:
            errors.append("source exact-base performance gate did not pass")
        if packet["performance"].get("physical_4k60_verified") is not False:
            errors.append("T09 source evidence improperly claims physical 4K60 certification")
        if packet["resource_actor_contract"].get("passed") is not True:
            errors.append("T09 resource/actor contract did not pass")
        if packet["candidate_scope"].get("passed") is not True:
            errors.append("T09 candidate scope gate did not pass")

    if review.get("task") != "T09" or review.get("candidate") != candidate:
        errors.append("strict review is not bound to exact T09 candidate")
    if str(review.get("source_run_id", "")) != str(args.source_run_id):
        errors.append("strict review source run id mismatch")
    if review.get("required_critics") != REQUIRED_CRITICS:
        errors.append(f"strict review critic set mismatch: {review.get('required_critics')}")
    if review.get("passed") is not True:
        errors.append("strict review gate did not pass")
    if review.get("task_approved") is not False:
        errors.append("review artifact must not self-approve the task")
    if int(review.get("c5_full_cycle_groups", 0)) < 15:
        errors.append("C5 full-cycle coverage is incomplete")

    critic_rows = review.get("critics", {})
    if set(critic_rows) != set(REQUIRED_CRITICS):
        errors.append("strict review does not contain exactly C2-C6 records")
    else:
        for critic in REQUIRED_CRITICS:
            row = critic_rows[critic]
            if critic == "C6":
                if row.get("candidate") != candidate or row.get("passed") is not True or row.get("errors"):
                    errors.append("C6 exact-source deterministic gate is not clean")
                continue
            if row.get("critic_id") != critic or row.get("candidate_hash") != candidate:
                errors.append(f"{critic} exact-source identity mismatch")
            if row.get("passed") is not True or row.get("coverage_complete") is not True:
                errors.append(f"{critic} did not pass complete coverage")
            if row.get("defects"):
                errors.append(f"{critic} has unresolved defects")
            if row.get("confidence") not in ("medium", "high"):
                errors.append(f"{critic} confidence is insufficient")
            scores = row.get("scores", {})
            if not scores or any(float(value) <= 9.0 for value in scores.values()):
                errors.append(f"{critic} has a raw score not strictly above 9.0")

    graph = load(DOCS / "DEPENDENCY_GRAPH.json")
    registry = load(DOCS / "WORKSTREAM_REGISTRY.json")
    ownership = load(DOCS / "PATH_OWNERSHIP.json")
    gates = load(DOCS / "task-gates.json")
    t09 = graph.get("tasks", {}).get("T09", {})
    row = registry_row(registry, "T09")
    active = [x for x in ownership.get("active_owners", []) if x.get("task_id") == "T09"]

    if t09.get("status") not in ("ASSIGNED", "BUILDING", "INTEGRATION_READY"):
        errors.append(f"unexpected pre-closeout T09 graph state: {t09.get('status')}")
    if not row or row.get("status") not in ("ASSIGNED", "BUILDING", "INTEGRATION_READY"):
        errors.append(f"unexpected/missing pre-closeout T09 registry state: {(row or {}).get('status')}")
    if not row or row.get("branch") != "havenline/T09-harvesting":
        errors.append("T09 registry branch is not the frozen builder branch")
    if len(active) != 1 or active[0].get("branch") != "havenline/T09-harvesting":
        errors.append("T09 must have exactly one active owner on the frozen builder branch")
    if gates.get("active_task") != "T09":
        errors.append(f"task-gates active_task is {gates.get('active_task')}, not T09")

    candidate_ledger = show_json(candidate, "Docs/Production/T09/defect-ledger.json")
    if candidate_ledger.get("defects"):
        errors.append("candidate T09 defect ledger is not empty")

    validation = subprocess.run(
        [
            "python3", "tools/havenline/production/workstream.py", "validate-candidate", "T09",
            "--base", row.get("base_commit", "") if row else "",
            "--head", candidate,
            "--integration-head", integration,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    ) if row and row.get("base_commit") else None
    scope_validation = None
    if validation is None:
        errors.append("T09 registry has no base_commit for closeout validation")
    else:
        try:
            scope_validation = json.loads(validation.stdout)
        except Exception:
            scope_validation = {"passed": False, "stdout": validation.stdout, "stderr": validation.stderr}
        if validation.returncode != 0 or scope_validation.get("passed") is not True:
            errors.append("current integration drift invalidates the registered T09 candidate scope")

    report = {
        "task": "T09",
        "mode": "read-only-closeout-preflight",
        "candidate": candidate,
        "source_run_id": str(args.source_run_id),
        "integration_head": integration,
        "required_critics": REQUIRED_CRITICS,
        "source_build_complete": not missing and packet.get("tests", {}).get("all_passed") is True and packet.get("capture", {}).get("passed") is True and packet.get("performance", {}).get("passed") is True,
        "strict_review_passed": review.get("passed") is True,
        "registered_scope_validation": scope_validation,
        "approval_mutation_performed": False,
        "integration_mutation_performed": False,
        "ready_for_integration_owner_closeout": not errors,
        "errors": errors,
        "passed": not errors,
        "next_action": "integration owner may stage exact-source T09 merge/approval closeout" if not errors else "do not approve or integrate T09; repair listed blockers and rerun exact-source preflight",
    }
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
