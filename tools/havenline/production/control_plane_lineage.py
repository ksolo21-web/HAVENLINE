#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess

from change_impact import calculate as calculate_impact
from forward_execution import ROOT

SHA40 = re.compile(r"^[0-9a-f]{40}$")


def _available(sha: str) -> bool:
    if not SHA40.fullmatch(str(sha or "")):
        return False
    return subprocess.run(
        ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def _is_ancestor(ancestor: str, descendant: str) -> bool:
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def _merge_base(left: str, right: str) -> str:
    return subprocess.check_output(
        ["git", "merge-base", left, right],
        cwd=ROOT,
        text=True,
        stderr=subprocess.DEVNULL,
    ).strip()


def _changed(base: str, head: str) -> list[str]:
    output = subprocess.check_output(
        ["git", "diff", "--name-only", f"{base}..{head}"],
        cwd=ROOT,
        text=True,
        stderr=subprocess.DEVNULL,
    )
    return sorted(x for x in output.splitlines() if x.strip())


def assess(builder_head: str | None, integration_head: str | None) -> dict:
    errors: list[str] = []
    if not SHA40.fullmatch(str(builder_head or "")):
        errors.append("exact 40-character builder head is required")
    if not SHA40.fullmatch(str(integration_head or "")):
        errors.append("exact 40-character integration head is required")
    if errors:
        return {
            "passed": False,
            "state": "INVALID_BINDING",
            "builder_head": builder_head,
            "integration_head": integration_head,
            "control_plane_sync_required": True,
            "runtime_reset_required": False,
            "errors": errors,
        }

    assert builder_head is not None and integration_head is not None
    if not _available(builder_head):
        errors.append("builder head commit is unavailable")
    if not _available(integration_head):
        errors.append("integration head commit is unavailable")
    if errors:
        return {
            "passed": False,
            "state": "UNAVAILABLE_BINDING",
            "builder_head": builder_head,
            "integration_head": integration_head,
            "control_plane_sync_required": True,
            "runtime_reset_required": False,
            "errors": errors,
        }

    if _is_ancestor(integration_head, builder_head):
        return {
            "passed": True,
            "state": "SYNCHRONIZED",
            "builder_head": builder_head,
            "integration_head": integration_head,
            "merge_base": integration_head,
            "builder_contains_integration": True,
            "integration_contains_builder": _is_ancestor(builder_head, integration_head),
            "integration_drift_files": [],
            "integration_drift_impact": None,
            "governance_only_drift": True,
            "control_plane_sync_required": False,
            "runtime_reset_required": False,
            "reconcile_mode": "NONE",
            "reason": "builder history contains the exact authoritative integration/control-plane head",
            "errors": [],
        }

    merge_base = _merge_base(builder_head, integration_head)
    integration_contains_builder = _is_ancestor(builder_head, integration_head)
    drift_files = _changed(merge_base, integration_head)
    impact = calculate_impact(drift_files)
    governance_only = (
        bool(drift_files)
        and impact.get("governance_only") is True
        and impact.get("unknown_production_fallback") is False
    )

    if governance_only and integration_contains_builder:
        state = "STALE_GOVERNANCE_ONLY"
        reconcile_mode = "FAST_FORWARD_CONTROL_PLANE"
        reason = (
            "builder is behind only governance/control-plane material; preserve task scope and "
            "prepared work, but synchronize the branch before ownership/build authority"
        )
    elif governance_only:
        state = "DIVERGED_GOVERNANCE_ONLY"
        reconcile_mode = "MERGE_OR_REBASE_CONTROL_PLANE"
        reason = (
            "builder diverged while integration drift is governance-only; preserve task runtime "
            "work, but reconcile control-plane lineage before ownership/build authority"
        )
    else:
        state = "STALE_RUNTIME_OR_CONTRACT" if integration_contains_builder else "DIVERGED_RUNTIME_OR_CONTRACT"
        reconcile_mode = "RUNTIME_OR_CONTRACT_RECONCILIATION"
        reason = "integration drift includes runtime/contract material and must be reconciled before authority"

    return {
        "passed": False,
        "state": state,
        "builder_head": builder_head,
        "integration_head": integration_head,
        "merge_base": merge_base,
        "builder_contains_integration": False,
        "integration_contains_builder": integration_contains_builder,
        "integration_drift_files": drift_files,
        "integration_drift_impact": impact,
        "governance_only_drift": governance_only,
        "control_plane_sync_required": True,
        "runtime_reset_required": not governance_only,
        "reconcile_mode": reconcile_mode,
        "reason": reason,
        "errors": [reason],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Prove builder/control-plane lineage before task authority")
    ap.add_argument("--builder-head", required=True)
    ap.add_argument("--integration-head", required=True)
    args = ap.parse_args()
    result = assess(args.builder_head, args.integration_head)
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
