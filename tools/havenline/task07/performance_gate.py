#!/usr/bin/env python3
"""Validate the deterministic T07 benchmark emitted by the Godot suite."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    reports = [json.loads(line) for line in args.log.read_text().splitlines() if line.startswith("{")]
    failures: list[str] = []
    if not reports:
        failures.append("test log has no machine-readable report")
        report: dict = {}
    else:
        report = reports[-1]
    perf = report.get("performance", {})
    if report.get("passed") is not True:
        failures.append("T07 engine suite did not pass")
    if perf.get("iterations") != 2000 or perf.get("input_candidates") != 160:
        failures.append("benchmark did not exercise the frozen worst-population case")
    observed = float(perf.get("microseconds_per_evaluation", float("inf")))
    budget = float(perf.get("budget_microseconds", 2500.0))
    if observed >= budget:
        failures.append(f"selection cost {observed:.3f} us exceeds {budget:.3f} us budget")
    output = {
        "task": "T07",
        "candidate_commit": args.candidate,
        "benchmark": perf,
        "bounded_input": report.get("contract", {}).get("maximum_input_candidates") == 128,
        "bounded_eligible": report.get("contract", {}).get("maximum_eligible_candidates") == 96,
        "physical_device_native_4k60_certified": False,
        "passed": not failures,
        "failures": failures,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))
    raise SystemExit(0 if output["passed"] else 1)


if __name__ == "__main__":
    main()
