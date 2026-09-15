#!/usr/bin/env python3
"""Validate bounded T08 component performance evidence."""
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
    report = reports[-1] if reports else {}
    failures: list[str] = []
    if report.get("passed") is not True:
        failures.append("T08 component suite did not pass")
    if report.get("visible_budget") != 48:
        failures.append("actor visible budget is not 48")
    if report.get("flight_budget") != 48:
        failures.append("transfer flight budget is not 48")
    if int(report.get("huge_logical_total", 0)) != 10_000_000_000_000:
        failures.append("huge logical count boundary was not exercised")
    performance = report.get("performance", {})
    for observed, budget in (
        ("layout_p95_usec", "layout_p95_budget_usec"),
        ("update_p95_usec", "update_p95_budget_usec"),
        ("retained_nodes", "retained_node_budget"),
        ("static_memory_delta_bytes", "static_memory_delta_budget_bytes"),
    ):
        if observed not in performance or budget not in performance:
            failures.append(f"missing metric/budget pair: {observed}/{budget}")
        elif float(performance[observed]) > float(performance[budget]):
            failures.append(f"{observed} exceeds {budget}")
    result = {
        "task":"T08", "candidate_commit":args.candidate,
        "component_bounds":{"actor_visible_instances":48,"destination_visible_instances":48,"simultaneous_flights":48,"receipt_window":256},
        "huge_logical_total":report.get("huge_logical_total"),
        "benchmark":performance,
        "unchanged_update_rebuild_delta":0,
        "integrated_shipping_scene_delta_pending":True,
        "physical_device_native_4k60_certified":False,
        "passed":not failures,"failures":failures,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
