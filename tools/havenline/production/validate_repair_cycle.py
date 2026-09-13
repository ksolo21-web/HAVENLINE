#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
from typing import Any

ALLOWED_STATUSES = {
    "OPEN", "DIAGNOSING", "PRODUCTION_FIX_REQUIRED",
    "PRODUCTION_FIX_IMPLEMENTED", "READY_FOR_VERIFICATION", "RESOLVED",
    "REJECTED_AS_INVALID_FINDING",
}
ALLOWED_CLASSIFICATIONS = {
    "PRODUCTION_FIX", "EVIDENCE_FIX", "TOOLING_FIX", "DIAGNOSTIC_ONLY", "TEST_FIX"
}
IMPLEMENTED_STATUSES = {"PRODUCTION_FIX_IMPLEMENTED", "READY_FOR_VERIFICATION", "RESOLVED"}


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def validate_ledger(
    ledger: dict[str, Any],
    changed_files: set[str],
    evidence_capture: dict[str, Any] | None = None,
    matched_capture_unchanged: bool | None = None,
) -> list[str]:
    errors: list[str] = []
    required_top = {
        "schema_version", "task_id", "task_status", "rejected_candidates",
        "repair_range", "defects", "same_object_before_after",
    }
    missing = sorted(required_top - set(ledger))
    if missing:
        errors.append("ledger missing fields: " + ",".join(missing))
        return errors

    rejected = ledger.get("rejected_candidates", [])
    if not rejected or any(x.get("status") != "REJECTED" for x in rejected):
        errors.append("every failed candidate must remain explicitly REJECTED")

    repair = ledger.get("repair_range", {})
    labels = set(repair.get("classifications", []))
    if not labels or not labels <= ALLOWED_CLASSIFICATIONS:
        errors.append("repair classifications are missing or invalid")

    defects = ledger.get("defects", [])
    if not defects:
        errors.append("defect ledger is empty")
    for defect in defects:
        defect_id = str(defect.get("defect_id", "<missing>"))
        status = defect.get("status")
        if status not in ALLOWED_STATUSES:
            errors.append(f"{defect_id}: invalid status")
        required = {
            "defect_id", "critic_source", "visible_symptom", "triage",
            "affected_production_object", "probable_root_cause",
            "production_files_likely_implicated", "production_change",
            "expected_visible_result", "required_proof", "status", "counters",
        }
        absent = sorted(required - set(defect))
        if absent:
            errors.append(f"{defect_id}: missing fields {','.join(absent)}")
            continue
        if defect.get("triage") == "VALID_PRODUCTION_DEFECT":
            if status not in IMPLEMENTED_STATUSES:
                errors.append(f"{defect_id}: production defect is not implemented")
            implicated = set(defect.get("production_files_likely_implicated", []))
            if not implicated & changed_files:
                errors.append(f"{defect_id}: no implicated production file changed")
            if "PRODUCTION_FIX" not in labels:
                errors.append(f"{defect_id}: repair range lacks PRODUCTION_FIX")
            if any(not str(defect.get(k, "")).strip() for k in (
                "visible_symptom", "probable_root_cause", "production_change",
                "expected_visible_result",
            )):
                errors.append(f"{defect_id}: causal chain is incomplete")
            counters = defect.get("counters", {})
            if int(counters.get("evidence_only_attempt_count", 0)) >= 2 and not implicated & changed_files:
                errors.append(f"{defect_id}: two-strike rule blocks evidence-only rerun")

    proof = ledger.get("same_object_before_after", {})
    if proof.get("same_camera_required") is not True:
        errors.append("matched before/after camera is not required")
    if matched_capture_unchanged is False:
        errors.append("capture camera source changed from the rejected baseline")

    if evidence_capture is not None:
        rows = evidence_capture.get("captures", [])
        ids = {row.get("evidence_id") for row in rows if row.get("evidence_id")}
        required_ids = set(proof.get("required_gameplay_evidence_ids", []))
        if not required_ids or not required_ids <= ids:
            errors.append("fresh gameplay-scale proof is missing")
        by_id = {row.get("evidence_id"): row for row in rows}
        for evidence_id in required_ids:
            row = by_id.get(evidence_id, {})
            if row.get("evidence_kind") != "gameplay-scale":
                errors.append("non-gameplay proof substituted for " + str(evidence_id))
            if row.get("gameplay_camera_position_and_scale_preserved") is not True:
                errors.append("shipping gameplay scale not preserved for " + str(evidence_id))
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--evidence-root")
    parser.add_argument("--output")
    args = parser.parse_args()

    ledger_path = pathlib.Path(args.ledger)
    ledger = json.loads(ledger_path.read_text())
    changed = set(_git("diff", "--name-only", args.base, args.head).splitlines())
    capture_path = str(ledger["same_object_before_after"]["capture_source_file"])
    matched = subprocess.run(
        ["git", "diff", "--quiet", args.base, args.head, "--", capture_path],
        check=False,
    ).returncode == 0
    capture = None
    if args.evidence_root:
        capture = json.loads((pathlib.Path(args.evidence_root) / "gallery" / "capture.json").read_text())
    errors = validate_ledger(ledger, changed, capture, matched)
    result = {
        "task": ledger.get("task_id"),
        "base": args.base,
        "head": _git("rev-parse", args.head),
        "passed": not errors,
        "changed_files": sorted(changed),
        "matched_capture_source_unchanged": matched,
        "production_fix_present": "PRODUCTION_FIX" in set(ledger.get("repair_range", {}).get("classifications", [])),
        "critic_execution_allowed": not errors,
        "errors": errors,
    }
    rendered = json.dumps(result, indent=2)
    print(rendered)
    if args.output:
        output = pathlib.Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

