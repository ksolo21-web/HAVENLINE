"""Run the completion, restart and failed-grant scenarios in guarded private homes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile


def hash_file(path):
    with path.open("rb") as contents:
        return hashlib.file_digest(contents, "sha256").hexdigest()


def verify_manifest(project, manifest, source):
    receipt = json.loads(manifest.read_text())
    assert receipt["commit"] == source
    for name, expected in receipt["files"].items():
        if hash_file(project / name) != expected:
            raise RuntimeError("Source changed: " + name)
    return {"sha256": hash_file(manifest), "checked_files": len(receipt["files"])}


def run_phase(project, fixture, profile, user_home, phase, output):
    env = os.environ.copy()
    for name in ("data", "config", "cache"):
        env["XDG_" + name.upper() + "_HOME"] = str(user_home / name)
    env.update(LP_NUM_THREADS="1", OMP_NUM_THREADS="1")
    command = [
        "godot", "--headless", "--audio-driver", "Dummy", "--fixed-fps", "60",
        "--audio-output-latency", "5", "--frame-delay", "3", "--path", str(project),
        "--script", str(fixture), "--", "--l1-disposable-profile=" + str(profile),
        "--settlement-qa=" + phase,
    ]
    result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=150)
    log = result.stdout + result.stderr
    filename = output / (phase + ".log")
    filename.write_text(log)
    lines = log.splitlines()
    data = [json.loads(line[len("SETTLEMENT_QA "):]) for line in lines if line.startswith("SETTLEMENT_QA ")]
    messages = [line for line in lines if any(prefix in line for prefix in ("WARNING:", "ERROR:", "SCRIPT ERROR:"))]
    if result.returncode or len(data) != 1 or data[0]["failures"] or messages:
        raise RuntimeError(f"{phase} failed; inspect {filename}")
    save = profile / "field-inventory-v1.json"
    receipt = dict(phase=phase, exit_code=result.returncode, warnings_and_errors=messages,
                   log=filename.name, checks=data[0]["checks"], observed=data[0].get("observed", {}),
                   log_sha256=hashlib.sha256(filename.read_bytes()).hexdigest())
    if save.exists():
        envelope = json.loads(save.read_text())
        payload = envelope["payload"]
        assert hashlib.sha256(payload.encode()).hexdigest() == envelope["sha256"]
        receipt["durable_payload"] = json.loads(payload)
        receipt["durable_payload_sha256"] = envelope["sha256"]
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--baseline-project", type=Path,
                        help="Use the prior build to author a genuine version-3 save.")
    parser.add_argument("--baseline-manifest", type=Path,
                        help="Validate the reviewed old build used to write the migration fixture.")
    parser.add_argument("--source", default="working-tree")
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    project = args.project.resolve()
    fixture = project / "tests/qa_level1_completion.gd"
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    binding = verify_manifest(project, args.manifest, args.source) if args.manifest else {}
    baseline_binding = None
    if args.baseline_manifest:
        assert args.baseline_project
        baseline = json.loads(args.baseline_manifest.read_text())["commit"]
        baseline_binding = verify_manifest(args.baseline_project, args.baseline_manifest, baseline)
        baseline_binding["commit"] = baseline
    with tempfile.TemporaryDirectory(prefix="havenline-l1-v3-finish-") as path:
        profile = Path(path)
        (profile / "L1-DISPOSABLE").write_text("HAVENLINE-ALFRED-V3-DISPOSABLE\n")
        private = profile / "xdg"
        cases = ["ledger-edges", "legacy", "layout", "plot-partial", "claim", "delivery-interrupted", "load-cooker", "cook-interrupted", "cook", "pickup-roast",
                 "interrupted", "serve", "machines-and-owl", "handoff-interrupted", "handoff", "second-launch"]
        for phase in cases:
            build = args.baseline_project.resolve() if phase == "legacy" and args.baseline_project else project
            try:
                row = run_phase(build, fixture, profile, private, phase, out)
            except (RuntimeError, subprocess.TimeoutExpired):
                summary = {"source":args.source, "passed":False, "failed_phase":phase, "completed":rows}
                (out / "Completion-results.json").write_text(json.dumps(summary,indent=2) + "\n")
                raise
            rows.append(row)
            print(phase, len(row["checks"]), "checks", flush=True)
        assert (profile / "opening-v3.json").exists() is False
        by_phase = {row["phase"]: row for row in rows}
        for checkpoint, failed in [("claim","delivery-interrupted"), ("load-cooker","cook-interrupted"), ("pickup-roast","interrupted"), ("machines-and-owl","handoff-interrupted")]:
            assert by_phase[checkpoint]["durable_payload_sha256"] == by_phase[failed]["durable_payload_sha256"], "Interrupted attempt changed durable bytes"
    summary = dict(source=args.source, engine=subprocess.check_output(["godot", "--version"], text=True).strip(),
                   actual_processes=len(rows), private_profile=True,
                   clean_legacy_opening_slot=True, passed=True, rows=rows)
    if baseline_binding:
        baseline_again = verify_manifest(args.baseline_project, args.baseline_manifest, baseline)
        assert baseline_again["sha256"] == baseline_binding["sha256"]
        summary["legacy_source_before_and_after"] = baseline_binding
    if args.manifest:
        assert verify_manifest(project,args.manifest,args.source)==binding
        summary["verified_source_before_and_after"] = binding
    (out / "Completion-results.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
