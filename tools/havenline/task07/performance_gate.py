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
    if perf.get("iterations") != 2000 or perf.get("input_candidates") != 128:
        failures.append("benchmark did not exercise the frozen worst-population case")
    observed = float(perf.get("microseconds_per_evaluation", float("inf")))
    budget = float(perf.get("budget_microseconds", 2500.0))
    if observed >= budget:
        failures.append(f"selection cost {observed:.3f} us exceeds {budget:.3f} us budget")
    required_bounded_metrics = {
        "p95_microseconds": "p95_budget_microseconds",
        "maximum_microseconds": "maximum_budget_microseconds",
        "switch_frequency_hz": "switch_frequency_budget_hz",
        "retained_object_delta": "retained_object_budget",
        "memory_static_delta_bytes": "memory_static_delta_budget_bytes",
    }
    for observed_key, budget_key in required_bounded_metrics.items():
        if observed_key not in perf or budget_key not in perf:
            failures.append(f"missing C6 metric/budget pair: {observed_key}/{budget_key}")
            continue
        if float(perf[observed_key]) > float(perf[budget_key]):
            failures.append(f"{observed_key} {perf[observed_key]} exceeds {budget_key} {perf[budget_key]}")
    rss_delta = int(perf.get("process_rss_delta_kib", -1))
    rss_budget = int(perf.get("process_rss_delta_budget_kib", -1))
    if rss_delta < 0 or rss_budget < 0:
        failures.append("process RSS measurement is unavailable")
    elif rss_delta > rss_budget:
        failures.append(f"process RSS delta {rss_delta} KiB exceeds {rss_budget} KiB")
    if perf.get("shipping_scene_frame_submission_delta") != "required_after_integration":
        failures.append("isolated C6 record did not preserve the integrated scene-delta requirement")
    output = {
        "task": "T07",
        "candidate_commit": args.candidate,
        "benchmark": perf,
        "bounded_input": report.get("contract", {}).get("maximum_input_candidates") == 128,
        "bounded_eligible": report.get("contract", {}).get("maximum_eligible_candidates") == 96,
        "physical_device_native_4k60_certified": False,
        "integrated_shipping_scene_delta_pending": True,
        "passed": not failures,
        "failures": failures,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))
    raise SystemExit(0 if output["passed"] else 1)


if __name__ == "__main__":
    main()
