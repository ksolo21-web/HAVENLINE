#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from lib import DOCS, ROOT


def validate() -> dict:
    errors: list[str] = []
    required_files = [
        "tools/havenline/production/factory_observer.py",
        "tools/havenline/production/factory_closeout_gate.py",
        "tools/havenline/production/flake_intelligence.py",
        "tools/havenline/production/pipeline_telemetry.py",
        "tools/havenline/production/runtime_dependency_learning.py",
        "tools/havenline/production/proof_invalidation.py",
    ]
    for rel in required_files:
        if not (ROOT / rel).is_file():
            errors.append("missing factory-control file: " + rel)

    try:
        runners = json.loads((DOCS / "FORWARD_GATE_RUNNERS.json").read_text())
        closeout = runners.get("gates", {}).get("closeout", {})
        closeout_runner = str(closeout.get("runner", ""))
        closeout_rule = str(closeout.get("rule", ""))
        for token in ("factory_observer.py", "factory_closeout_gate.py", "evidence_retention.py", "task_state_snapshot.py"):
            if token not in closeout_runner:
                errors.append("forward closeout runner missing " + token)
        if "factory-observation.json" not in closeout_rule:
            errors.append("forward closeout rule does not require factory-observation.json")
        if "T10+" not in closeout_rule:
            errors.append("forward closeout rule must remain forward-only for T10+")
        release = runners.get("gates", {}).get("release_manifest", {})
        release_text = str(release.get("runner", "")) + " " + str(release.get("rule", ""))
        if "factory_closeout_gate.py" not in release_text or "contract-diff" not in release_text:
            errors.append("release manifest contract is missing V3.1 factory closeout/invalidation controls")
    except Exception as exc:
        errors.append("unable to validate forward gate runners: " + str(exc))

    c0_path = ROOT / ".github/workflows/havenline-c0-root-cause.yml"
    if c0_path.is_file():
        c0 = c0_path.read_text()
        for token in ("factory_observer.py", "c0-output/factory-observation", "/artifacts?per_page=100"):
            if token not in c0:
                errors.append("C0 workflow missing automatic factory observation token: " + token)
    else:
        errors.append("C0 workflow missing")

    packet_path = ROOT / "tools/havenline/production/task_packet.py"
    if packet_path.is_file():
        packet = packet_path.read_text()
        for token in ("factory_observer.py", "factory-observation.json"):
            if token not in packet:
                errors.append("future task packet generator missing " + token)
    else:
        errors.append("task packet generator missing")

    observer_path = ROOT / "tools/havenline/production/factory_observer.py"
    if observer_path.is_file():
        observer = observer_path.read_text()
        for token in ("bundle_is_observation_not_authority", "quality_thresholds_unchanged", "validate_trace"):
            if token not in observer:
                errors.append("factory observer safety boundary missing " + token)

    return {
        "schema_version": 1,
        "passed": not errors,
        "automatic_failure_observation": True,
        "forward_closeout_observation_required": True,
        "factory_observation_is_not_authority": True,
        "quality_thresholds_unchanged": True,
        "errors": errors,
    }


def main() -> int:
    report = validate()
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
