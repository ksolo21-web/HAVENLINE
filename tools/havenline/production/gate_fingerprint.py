#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from forward_execution import DOCS, ROOT, resolve_task

POLICY = DOCS / "GATE_FINGERPRINT_POLICY.json"
INDEX = DOCS / "GATE_RESULT_INDEX.json"
REGISTRY = DOCS / "WORKSTREAM_REGISTRY.json"
RUNNERS = DOCS / "FORWARD_GATE_RUNNERS.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=check)


def _assert_commit(commit: str) -> None:
    if len(commit) != 40 or any(c not in "0123456789abcdefABCDEF" for c in commit):
        raise ValueError("candidate must be an exact 40-character commit")
    result = _git("cat-file", "-e", f"{commit}^{{commit}}", check=False)
    if result.returncode != 0:
        raise ValueError(f"candidate commit unavailable locally: {commit}")


def _tree_entries(commit: str, rel: str) -> list[str]:
    result = _git("ls-tree", "-r", "--full-tree", commit, "--", rel, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git ls-tree failed for {rel}")
    entries = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        meta, path = line.split("\t", 1)
        parts = meta.split()
        if len(parts) < 3:
            continue
        entries.append(f"{parts[2]} {path}")
    return sorted(entries)


def _accepted_dependency_sources(task_id: str) -> dict[str, str]:
    plan = resolve_task(task_id)
    registry = load_json(REGISTRY)
    workstreams = {w.get("task_id"): w for w in registry.get("workstreams", [])}
    legacy = registry.get("legacy_approvals", {})
    out: dict[str, str] = {}
    for dep in plan["dependencies"]:
        ws = workstreams.get(dep, {})
        source = ws.get("candidate_commit") or ws.get("integrated_source") or legacy.get(dep, {}).get("accepted_source")
        if not source:
            raise ValueError(f"approved dependency {dep} lacks accepted source identity")
        out[dep] = source
    return out


def fingerprint(task_id: str, gate: str, candidate: str) -> dict[str, Any]:
    task_id = task_id.upper(); gate = gate.strip()
    _assert_commit(candidate)
    plan = resolve_task(task_id)
    if gate not in plan["ordered_gates"]:
        raise ValueError(f"gate {gate} is not selected for {task_id}")
    policy = load_json(POLICY)
    row = policy.get("gates", {}).get(gate)
    if not row:
        raise ValueError(f"gate fingerprint policy missing {gate}")
    runner_row = load_json(RUNNERS)["gates"].get(gate)
    if not runner_row:
        raise ValueError(f"runner contract missing {gate}")

    rels: list[str] = []
    rels.extend(policy.get("global_inputs", []))
    for template in policy.get("task_inputs", []):
        rels.append(template.format(task=task_id, task_lower=task_id.lower()))
    rels.extend(row.get("extra_inputs", []))
    # Avoid duplicate work while preserving deterministic ordering.
    rels = sorted(dict.fromkeys(rels))
    manifest: dict[str, list[str]] = {}
    missing: list[str] = []
    for rel in rels:
        entries = _tree_entries(candidate, rel)
        if entries:
            manifest[rel] = entries
        else:
            # Optional task-specific folders may not exist until activation;
            # frozen scope, runtime and authorities are mandatory.
            optional = rel == f"tools/havenline/{task_id.lower()}"
            if not optional:
                missing.append(rel)
    if missing:
        raise ValueError("fingerprint inputs missing: " + ", ".join(missing))

    material = {
        "schema_version": 1,
        "task_id": task_id,
        "gate": gate,
        "reuse_class": row["reuse"],
        "runtime_and_input_manifest": manifest,
        "runner_contract": runner_row,
        "accepted_dependency_sources": _accepted_dependency_sources(task_id),
        "task_archetype": plan["archetype"],
        "execution_mode": plan["execution_mode"],
        "critics": plan["critics"],
    }
    canonical = json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(canonical).hexdigest()
    return {
        "task_id": task_id,
        "gate": gate,
        "candidate": candidate,
        "fingerprint": digest,
        "reuse_class": row["reuse"],
        "input_count": sum(len(v) for v in manifest.values()),
        "accepted_dependency_sources": material["accepted_dependency_sources"],
        "material": material,
    }


def lookup(task_id: str, gate: str, candidate: str) -> dict[str, Any]:
    current = fingerprint(task_id, gate, candidate)
    index = load_json(INDEX)
    matches = [r for r in index.get("records", []) if r.get("task_id") == task_id.upper() and r.get("gate") == gate and r.get("fingerprint") == current["fingerprint"] and r.get("result") == "PASS"]
    matches.sort(key=lambda row: str(row.get("recorded_at", "")), reverse=True)
    reuse = current["reuse_class"]
    decision = "RUN_FRESH"
    reason = "no matching prior PASS fingerprint"
    prior = matches[0] if matches else None
    if prior:
        if reuse == "exact_source_required":
            if prior.get("candidate") == candidate:
                decision, reason = "REUSE_EXACT_SOURCE", "same exact candidate and fingerprint"
            else:
                decision, reason = "RUN_FRESH", "gate requires exact source even though logical inputs match"
        elif reuse == "deterministic_reusable":
            decision, reason = "REUSE_PASS", "complete gate-input fingerprint matches prior deterministic PASS"
        elif reuse == "rebind_with_provenance":
            decision, reason = "REUSE_WITH_PROVENANCE_BRIDGE", "heavy evidence inputs match; bind prior immutable evidence to this SHA with a bridge record"
    return {"current": current, "decision": decision, "reason": reason, "prior_record": prior}


def provenance_bridge(task_id: str, gate: str, candidate: str) -> dict[str, Any]:
    result = lookup(task_id, gate, candidate)
    if result["decision"] != "REUSE_WITH_PROVENANCE_BRIDGE":
        raise ValueError("provenance bridge is only valid for a matching rebind_with_provenance PASS")
    prior = result["prior_record"]
    return {
        "schema_version": 1,
        "task_id": task_id.upper(),
        "gate": gate,
        "new_candidate": candidate,
        "fingerprint": result["current"]["fingerprint"],
        "prior_candidate": prior["candidate"],
        "prior_evidence": prior.get("evidence"),
        "prior_result": prior["result"],
        "statement": "Relevant runtime, harness, authority and accepted-dependency inputs are content-identical under the V3 gate fingerprint policy. Evidence bytes may be reused, but current-source critic/closure gates remain fresh where required."
    }


def validate_policy() -> dict[str, Any]:
    policy = load_json(POLICY); runners = load_json(RUNNERS)
    errors: list[str] = []
    allowed = set(policy.get("allowed_reuse_values", []))
    gate_order = load_json(DOCS / "FORWARD_EXECUTION_PROFILES.json").get("gate_order", [])
    if set(policy.get("gates", {})) != set(gate_order):
        errors.append("fingerprint policy must cover every forward gate exactly")
    for gate, row in policy.get("gates", {}).items():
        if row.get("reuse") not in allowed:
            errors.append(f"{gate} invalid reuse class")
        if gate not in runners.get("gates", {}):
            errors.append(f"{gate} missing runner contract")
    for gate in ("physical_device", "critic_review", "integration", "post_integration_regression", "closeout", "release_manifest"):
        if policy.get("gates", {}).get(gate, {}).get("reuse") != "exact_source_required":
            errors.append(f"{gate} must remain exact_source_required")
    if policy.get("fail_result_reuse") != "forbidden":
        errors.append("failed results must never be reused as PASS")
    index = load_json(INDEX)
    if not isinstance(index.get("records"), list):
        errors.append("gate result index records must be a list")
    return {"passed": not errors, "gate_count": len(policy.get("gates", {})), "errors": errors}


def main() -> int:
    ap = argparse.ArgumentParser(description="Havenline V3 content-addressed gate proof")
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    for command in ("fingerprint", "lookup", "bridge"):
        p = sub.add_parser(command); p.add_argument("task_id"); p.add_argument("gate"); p.add_argument("candidate"); p.add_argument("--output")
    args = ap.parse_args()
    if args.command == "validate":
        report = validate_policy()
    elif args.command == "fingerprint": report = fingerprint(args.task_id, args.gate, args.candidate)
    elif args.command == "lookup": report = lookup(args.task_id, args.gate, args.candidate)
    else: report = provenance_bridge(args.task_id, args.gate, args.candidate)
    text = json.dumps(report, indent=2) + "\n"
    if getattr(args, "output", None):
        out = (ROOT / args.output).resolve(); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(text)
    print(text, end="")
    return 0 if not report.get("errors") else 2


if __name__ == "__main__":
    raise SystemExit(main())
