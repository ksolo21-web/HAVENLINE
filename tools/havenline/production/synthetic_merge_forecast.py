#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from typing import Any

from change_impact import calculate
from contract_compatibility import affected_contracts
from forward_execution import ROOT


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=check)


def _resolve(ref: str) -> str:
    result = _git("rev-parse", "--verify", f"{ref}^{{commit}}", check=False)
    if result.returncode != 0:
        raise ValueError(f"unresolvable git ref {ref}: {result.stderr.strip()}")
    return result.stdout.strip()


def _changed(base: str, head: str) -> list[str]:
    result = _git("diff", "--name-only", f"{base}..{head}")
    return sorted(x for x in result.stdout.splitlines() if x.strip())


def _merge_tree(integration: str, candidate: str) -> dict[str, Any]:
    modern = _git("merge-tree", "--write-tree", integration, candidate, check=False)
    if modern.returncode in (0, 1):
        return {"supported": True, "clean": modern.returncode == 0, "returncode": modern.returncode, "output": (modern.stdout + modern.stderr)[-12000:]}
    base = _git("merge-base", integration, candidate).stdout.strip()
    legacy = _git("merge-tree", base, integration, candidate, check=False)
    text = legacy.stdout + legacy.stderr
    conflict_markers = ("changed in both", "CONFLICT", "<<<<<<<")
    return {"supported": False, "clean": not any(token in text for token in conflict_markers), "returncode": legacy.returncode, "output": text[-12000:]}


def forecast(candidate_ref: str, integration_ref: str) -> dict[str, Any]:
    candidate = _resolve(candidate_ref); integration = _resolve(integration_ref)
    base = _git("merge-base", candidate, integration).stdout.strip()
    if len(base) != 40:
        raise RuntimeError("git merge-base did not produce exact commit")
    candidate_files = _changed(base, candidate)
    integration_files = _changed(base, integration)
    overlap = sorted(set(candidate_files).intersection(integration_files))
    drift_impact = calculate(integration_files)
    candidate_impact = calculate(candidate_files)
    merge = _merge_tree(integration, candidate)
    contracts = affected_contracts(sorted(set(candidate_files + integration_files)))
    governance_only_drift = bool(integration_files) and drift_impact.get("governance_only") is True and drift_impact.get("unknown_production_fallback") is False
    production_drift = bool(integration_files) and not governance_only_drift
    requires_reconcile = production_drift or not merge["clean"]
    if not merge["clean"]: risk = "CONFLICT"
    elif overlap: risk = "OVERLAPPING_CHANGES"
    elif governance_only_drift: risk = "GOVERNANCE_ONLY_DRIFT"
    elif integration_files: risk = "PRODUCTION_DRIFT"
    else: risk = "NO_DRIFT"
    return {
        "schema_version": 1,
        "candidate": candidate,
        "integration_head": integration,
        "merge_base": base,
        "risk": risk,
        "requires_reconcile": requires_reconcile,
        "candidate_files": candidate_files,
        "integration_drift_files": integration_files,
        "overlap_files": overlap,
        "candidate_change_impact": candidate_impact,
        "integration_drift_impact": drift_impact,
        "affected_contracts": contracts,
        "merge_tree": merge,
        "rule": "A clean forecast never replaces integration-owner review or fresh post-integration regression. Governance-only drift may avoid a rebase; production drift requires reconciliation before integration."
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Havenline V3 non-mutating synthetic merge forecast")
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--integration", required=True)
    ap.add_argument("--output")
    args = ap.parse_args()
    try:
        report = forecast(args.candidate, args.integration)
        code = 0
    except Exception as exc:
        report = {"schema_version": 1, "risk": "FORECAST_ERROR", "requires_reconcile": True, "errors": [str(exc)]}
        code = 2
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        out = (ROOT / args.output).resolve(); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(text)
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
