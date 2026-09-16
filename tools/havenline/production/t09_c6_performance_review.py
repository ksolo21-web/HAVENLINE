#!/usr/bin/env python3
"""Deterministic T09 C6 review over the exact-base performance delta artifact."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--record", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    perf = json.loads(Path(args.record).read_text())
    errors: list[str] = []
    if perf.get("task") != "T09": errors.append("task mismatch")
    if perf.get("candidate") != args.candidate: errors.append("candidate mismatch")
    if perf.get("passed") is not True: errors.append("source performance gate did not pass")
    if perf.get("physical_4k60_verified") is not False: errors.append("T09 may not claim physical 4K60 certification")
    if perf.get("thermal_certified") is not False: errors.append("T09 may not claim thermal certification")
    delta = perf.get("delta", {})
    limits = perf.get("limits", {})
    checks = {
        "p95_ms": ("p95_ms", 10.0),
        "draw_calls": ("average_draw_calls", 12.0),
        "primitives": ("average_primitives", 5000.0),
        "memory_mb": ("process_static_memory_mb", 32.0),
        "materials": ("materials_visible", 6.0),
        "shaders": ("unique_shader_resources", 0.0),
        "physics_bodies": ("physics_active_bodies", 0.0),
        "animation_players": ("animation_players", 0.0),
    }
    measured = {}
    for limit_key, (delta_key, expected_limit) in checks.items():
        source_limit = limits.get(limit_key)
        value = delta.get(delta_key)
        if source_limit is None or float(source_limit) != expected_limit:
            errors.append(f"{limit_key} source limit drift: {source_limit} != {expected_limit}")
            continue
        if value is None:
            errors.append("missing delta " + delta_key)
            continue
        measured[delta_key] = value
        if float(value) > expected_limit:
            errors.append(f"{delta_key} {value} exceeds {expected_limit}")
    for key in ("active_animations",):
        value = delta.get(key)
        measured[key] = value
        if value is None or float(value) > 0:
            errors.append(f"{key} regression: {value}")
    result = {
        "critic_id": "C6", "task": "T09", "candidate": args.candidate,
        "execution_type": "quantitative_specialist_gate", "exact_base": perf.get("exact_base"),
        "method": perf.get("method"), "measured_delta": measured, "limits": limits,
        "passed": not errors, "errors": errors, "task_approved": False,
        "note": "Development-task C6 delta gate only; not T68/T69 physical 4K60 certification.",
    }
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
