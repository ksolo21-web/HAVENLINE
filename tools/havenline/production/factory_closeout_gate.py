#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from lib import ROOT


def validate(task_id: str, candidate: str, observation: dict) -> dict:
    task_id = task_id.upper()
    errors: list[str] = []
    if not re.fullmatch(r"T[0-9]{2}", task_id) or int(task_id[1:]) < 10:
        errors.append("factory closeout gate is forward-only for T10+")
    if not re.fullmatch(r"[0-9a-f]{40}", candidate):
        errors.append("candidate must be exact 40-character SHA")
    if observation.get("schema_version") != 1:
        errors.append("factory observation schema_version must be 1")
    if observation.get("passed") is not True:
        errors.append("factory observation did not pass")
    if observation.get("task_id") != task_id:
        errors.append("factory observation task mismatch")
    if observation.get("source_sha") != candidate:
        errors.append("factory observation candidate mismatch")
    if observation.get("bundle_is_observation_not_authority") is not True:
        errors.append("factory observation authority boundary missing")
    if observation.get("quality_thresholds_unchanged") is not True:
        errors.append("factory observation may not alter quality thresholds")
    if observation.get("environment_exact") is not True or not observation.get("environment_fingerprint"):
        errors.append("forward closeout requires exact runner/toolchain environment provenance")
    telemetry = observation.get("telemetry")
    if not isinstance(telemetry, dict):
        errors.append("factory telemetry missing")
    else:
        required = {"queue_seconds","run_seconds","gate_durations","rerun_count","c0_cycles","proof_cache_hits","artifact_bytes","terminal_gate","terminal_class"}
        missing = sorted(required - set(telemetry))
        if missing:
            errors.append("factory telemetry missing fields: " + ", ".join(missing))
        if telemetry.get("terminal_class") != "SUCCESS":
            errors.append("forward closeout requires successful terminal run")
        if telemetry.get("source_sha") != candidate or telemetry.get("task_id") != task_id:
            errors.append("factory telemetry source/task mismatch")
    state = observation.get("task_state")
    if not isinstance(state, dict):
        errors.append("factory observation task-state snapshot missing")
    else:
        if state.get("task_id") != task_id or state.get("candidate_commit") != candidate:
            errors.append("factory task-state source/task mismatch")
        if state.get("snapshot_is_derived_not_authority") is not True:
            errors.append("factory task-state must remain derived")
    for index, row in enumerate(observation.get("runtime_dependency_traces", []) or []):
        validation = row.get("validation", {}) if isinstance(row, dict) else {}
        if validation.get("passed") is not True:
            errors.append(f"runtime dependency trace {index} not validated")
        if row.get("trace", {}).get("source_sha") != candidate:
            errors.append(f"runtime dependency trace {index} source mismatch")
    return {
        "schema_version": 1,
        "passed": not errors,
        "task_id": task_id,
        "candidate": candidate,
        "factory_observation_required": True,
        "approval_authority_granted": False,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate T10+ terminal V3.1 factory observation before forward closeout")
    parser.add_argument("--task", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--observation", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    path = Path(args.observation)
    if not path.is_absolute():
        path = ROOT / path
    try:
        observation = json.loads(path.read_text())
        report = validate(args.task, args.candidate, observation)
    except Exception as exc:
        report = {"schema_version": 1, "passed": False, "task_id": args.task.upper(), "candidate": args.candidate, "factory_observation_required": True, "approval_authority_granted": False, "errors": [str(exc)]}
    text = json.dumps(report, indent=2) + "\n"
    print(text, end="")
    if args.output:
        out = Path(args.output)
        if not out.is_absolute():out = ROOT / out
        out.parent.mkdir(parents=True, exist_ok=True);out.write_text(text)
    return 0 if report.get("passed") else 2


if __name__ == "__main__":
    raise SystemExit(main())
