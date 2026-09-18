#!/usr/bin/env python3
"""Execute T10's mandatory C7 transaction-state proof at one frozen source."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
REQUIRED = {
    "test_task10_world_transform": {
        "undeclared two-state progression cycle is rejected",
        "undeclared multi-state progression cycle is rejected",
        "nonreciprocal inverse declaration is rejected",
        "explicit reciprocal reversible pair configures",
        "required upstream prerequisite is enforced",
        "neutral branching recipes can diverge from one source without semantic changes",
        "completed JSON recovery is canonical and exact",
        "4096 model targets register and overflow rejects",
        "malformed import preserves populated component atomically",
        "pending record cannot claim completed authority",
        "completed receipt enforces accepted_by_world_transform",
    },
    "test_task10_integration": {
        "real carried harvest cannot pay T10",
        "real deposit conserves delivered resources",
        "real simulation exact stored debit",
        "real snapshot restores after debit before acceptance",
        "real pending component restores",
        "real crash retry does not debit again",
        "real recovered receipt advances once",
        "real duplicate acceptance is idempotent",
        "real malformed receipt restore is atomic",
        "real insufficient stock cannot partially charge",
        "real exact next revision succeeds",
        "real older revision remains rejected",
        "real maximum target stress retains bounded receipts",
        "real target overflow rejects without mutation",
    },
}


def validate_report(suite, report):
    errors = []
    checks = report.get("checks", [])
    if not isinstance(checks, list) or not checks:
        return ["missing executable checks"]
    names = [row.get("name") for row in checks if isinstance(row, dict)]
    if len(names) != len(checks) or len(names) != len(set(names)):
        errors.append("malformed or duplicate checks")
    if report.get("passed") is not True or report.get("failures") or any(row.get("passed") is not True for row in checks if isinstance(row, dict)):
        errors.append("failed suite or check")
    missing = REQUIRED[suite] - set(names)
    if missing:
        errors.append("missing required checks: " + ", ".join(sorted(missing)))
    if suite == "test_task10_integration" and (report.get("real_t09_adapter_bound") is not True or report.get("fixture_simulation_only") is not False):
        errors.append("real simulation authority required")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--godot", default=os.environ.get("GODOT_BIN", "Godot_v4.7.2-stable_linux.x86_64"))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    candidate = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", args.candidate) or args.candidate != candidate:
        raise SystemExit("C7 proof requires exact checked-out candidate")
    paths = ["HavenlineGodot/scripts", "HavenlineGodot/tests", "HavenlineGodot/data", "tools/havenline/task10"]
    subprocess.run(["git", "diff", "--exit-code", "HEAD", "--", *paths], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    godot = shutil.which(args.godot)
    if not godot:
        raise SystemExit("Pinned Godot executable is required")
    version = subprocess.check_output([godot, "--version"], text=True).strip()
    if version != "4.7.2.stable.official.ed1daf0bf":
        raise SystemExit("Godot version differs from locked toolchain")
    output = Path(args.output).resolve()
    logs = output.parent / "progression-logs"
    logs.mkdir(parents=True, exist_ok=True)
    results, errors = [], []
    for suite in REQUIRED:
        run = subprocess.run([godot, "--headless", "--audio-driver", "Dummy", "--path", str(ROOT / "HavenlineGodot"), "--script", "res://tests/" + suite + ".gd"], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
        raw = run.stdout
        log = logs / (suite + ".log")
        log.write_text(raw)
        reports = [json.loads(line) for line in raw.splitlines() if line.startswith("{")]
        report = reports[-1] if len(reports) == 1 else {}
        suite_errors = validate_report(suite, report)
        if run.returncode or any(marker in raw for marker in ("SCRIPT ERROR", "Parse Error", "ERROR:", "ObjectDB instances were leaked")):
            suite_errors.append("runtime error")
        errors.extend(suite + ": " + error for error in suite_errors)
        results.append({"suite": suite, "checks": len(report.get("checks", [])), "required_checks": sorted(REQUIRED[suite]), "passed": not suite_errors, "log": str(log), "sha256": hashlib.sha256(log.read_bytes()).hexdigest()})
    hashes = {}
    tracked = subprocess.check_output(["git", "ls-files", *paths], cwd=ROOT, text=True).splitlines()
    for name in tracked:
        hashes[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    record = {"task_id": "T10", "candidate_commit": candidate, "profile": "T10_transaction_state_integrity_v1", "gate": "progression_sim", "critic_id": "C7", "engine": version, "executed": True, "suites": results, "source_sha256": hashes, "passed": not errors, "errors": errors, "independent_critic": False, "task_approved": False}
    output.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"passed": record["passed"], "candidate_commit": candidate, "checks": sum(row["checks"] for row in results), "errors": errors}))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
