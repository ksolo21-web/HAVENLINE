#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from forward_execution import DOCS, ROOT

KB = DOCS / "FAILURE_INTELLIGENCE.json"
VALID_CLASSES = {"PRODUCT_DEFECT", "TOOLING_DEFECT", "GOVERNANCE_DEFECT", "EVIDENCE_DEFECT", "INFRASTRUCTURE_FAILURE", "SUPERSEDED", "MIXED"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9_+.-]+", text.lower()) if len(t) >= 3}


def validate() -> dict[str, Any]:
    data = load_json(KB); errors: list[str] = []; seen: set[str] = set()
    if data.get("schema_version") != 1: errors.append("failure intelligence schema_version must be 1")
    for row in data.get("records", []):
        rid = row.get("id")
        if not rid or rid in seen: errors.append("failure intelligence record ids must be unique/non-empty")
        seen.add(rid)
        for field in ("task_id", "scope", "gate", "classification", "signature_terms", "symptom", "root_cause", "causal_repair", "protected_files", "proof", "prevention_rule", "source"):
            if field not in row: errors.append(f"{rid or 'record'} missing {field}")
        if row.get("classification") not in VALID_CLASSES: errors.append(f"{rid} invalid classification")
        if not isinstance(row.get("signature_terms"), list) or not row.get("signature_terms"): errors.append(f"{rid} signature_terms must be non-empty list")
        source = str(row.get("source", "")).split("#", 1)[0]
        if source and not (ROOT / source).exists(): errors.append(f"{rid} source does not exist: {source}")
    return {"passed": not errors, "record_count": len(data.get("records", [])), "errors": errors}


def query(task_id: str | None, gate: str | None, text: str, limit: int = 5) -> dict[str, Any]:
    data = load_json(KB); text_tokens = _tokens(text); ranked: list[dict[str, Any]] = []
    for row in data.get("records", []):
        signature = _tokens(" ".join(row.get("signature_terms", [])))
        overlap = sorted(text_tokens.intersection(signature))
        score = len(overlap) * 5
        if task_id and row.get("task_id") == task_id.upper(): score += 4
        if gate and row.get("gate", "").lower() == gate.lower(): score += 4
        if row.get("scope") == "cross_task_reusable": score += 1
        if score <= 1: continue
        ranked.append({
            "id": row["id"], "score": score, "matched_terms": overlap,
            "task_id": row["task_id"], "gate": row["gate"], "classification": row["classification"],
            "symptom": row["symptom"], "root_cause": row["root_cause"], "causal_repair": row["causal_repair"],
            "protected_files": row["protected_files"], "proof": row["proof"], "prevention_rule": row["prevention_rule"], "source": row["source"],
            "advisory_only": True,
        })
    ranked.sort(key=lambda row: (-row["score"], row["id"]))
    return {"query_task": task_id, "query_gate": gate, "matches": ranked[:limit], "historical_match_is_advisory_only": True}


def query_packet(packet: dict[str, Any], limit: int = 5) -> dict[str, Any]:
    text = json.dumps({"steps": packet.get("steps", []), "changed_files": packet.get("changed_files", []), "run_conclusion": packet.get("run_conclusion"), "logs": packet.get("failure_excerpt", packet.get("failed_logs", packet.get("logs", "")))}, sort_keys=True)
    gate = packet.get("failed_gate") or packet.get("failed_step")
    return query(packet.get("task_id"), gate, text, limit=limit)


def main() -> int:
    ap = argparse.ArgumentParser(description="Havenline V3 cross-task failure intelligence")
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    q = sub.add_parser("query"); q.add_argument("--task"); q.add_argument("--gate"); q.add_argument("--text", required=True); q.add_argument("--limit", type=int, default=5)
    p = sub.add_parser("packet"); p.add_argument("packet"); p.add_argument("--limit", type=int, default=5)
    args = ap.parse_args()
    if args.command == "validate": report = validate()
    elif args.command == "query": report = query(args.task, args.gate, args.text, args.limit)
    else: report = query_packet(load_json((ROOT / args.packet).resolve()), args.limit)
    print(json.dumps(report, indent=2))
    return 0 if not report.get("errors") else 2


if __name__ == "__main__":
    raise SystemExit(main())
