#!/usr/bin/env python3
"""Benchmark the complete T12 preparation validation surface.

This is a prebuild hygiene gate only. It cannot satisfy shipping C6. Timing and
memory instrumentation are intentionally separate so tracemalloc overhead is not
misreported as validator latency.
"""
from __future__ import annotations

import gc
import importlib.util
import json
import pathlib
import statistics
import time
import tracemalloc
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[3]
TASK = ROOT / "tools" / "havenline" / "task12"
DOCS = ROOT / "Docs" / "Production" / "T12"


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, TASK / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


progression = load_module("t12_progression", "validate_progression_contract.py")
matrix_validator = load_module("t12_matrix", "validate_level_matrix.py")
schema_validator = load_module("t12_schema", "validate_data_schema.py")
runtime_validator = load_module("t12_runtime", "validate_runtime_interface.py")
trace_validator = load_module("t12_trace", "validate_traceability.py")
downstream_validator = load_module("t12_downstream", "validate_downstream_contract.py")
candidate_validator = load_module("t12_candidate_evidence", "validate_candidate_evidence.py")
critic_validator = load_module("t12_critic_reviews", "validate_critic_review_records.py")
fuzz_module = load_module("t12_fuzz", "fuzz_progression_contract.py")

MATRIX = json.loads((DOCS / "LEVEL_1_100_MATRIX.json").read_text())
SCHEMA = json.loads((DOCS / "PROGRESSION_DATA_SCHEMA.json").read_text())
RUNTIME = json.loads((DOCS / "RUNTIME_INTERFACE_CONTRACT.json").read_text())
TRACE = json.loads((DOCS / "ACCEPTANCE_TRACEABILITY.json").read_text())
DOWNSTREAM = json.loads((DOCS / "DOWNSTREAM_CONSUMER_CONTRACT.json").read_text())
CANDIDATE_TEMPLATE = json.loads((DOCS / "CANDIDATE_EVIDENCE_TEMPLATE.json").read_text())
CRITIC_TEMPLATE = json.loads((DOCS / "CRITIC_REVIEW_RECORD_TEMPLATE.json").read_text())
BUDGET = json.loads((DOCS / "PREBUILD_PERFORMANCE_BUDGET.json").read_text())["static_validation_budget"]
SYNTHETIC_MANIFEST = fuzz_module.valid_manifest()


def validate_once() -> list[dict[str, Any]]:
    return [
        progression.validate_manifest(SYNTHETIC_MANIFEST),
        matrix_validator.validate_matrix(MATRIX),
        schema_validator.validate_schema(SCHEMA),
        runtime_validator.validate_contract(RUNTIME),
        trace_validator.validate_traceability(TRACE),
        downstream_validator.validate_contract(DOWNSTREAM),
        candidate_validator.validate_packet(CANDIDATE_TEMPLATE, require_resolved=False),
        critic_validator.validate_record(CRITIC_TEMPLATE, require_resolved=False),
    ]


def percentile95(values: list[float]) -> float:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * 0.95)))
    return ordered[index]


def all_pass(results: list[dict[str, Any]]) -> bool:
    return all(result.get("passed") for result in results)


def main() -> None:
    initial = validate_once()
    initial_errors = [result.get("errors", []) for result in initial if not result.get("passed")]
    if initial_errors:
        print(json.dumps({"passed": False, "errors": [f"baseline validator failure: {initial_errors}"]}, indent=2))
        raise SystemExit(1)

    iterations = int(BUDGET["iterations"])
    memory_iterations = int(BUDGET["memory_iterations"])
    durations_ms: list[float] = []
    errors: list[str] = []

    # Latency pass: no tracemalloc instrumentation.
    gc.collect()
    for _ in range(iterations):
        started = time.perf_counter_ns()
        results = validate_once()
        elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000.0
        durations_ms.append(elapsed_ms)
        if not all_pass(results):
            errors.append("validator returned failure during timing benchmark")
            break

    mean_ms = statistics.fmean(durations_ms) if durations_ms else float("inf")
    p95_ms = percentile95(durations_ms) if durations_ms else float("inf")
    maximum_ms = max(durations_ms) if durations_ms else float("inf")

    # Separate memory pass under tracemalloc. Its runtime is intentionally not
    # mixed into the latency metrics above.
    gc.collect()
    tracemalloc.start()
    baseline_current, _ = tracemalloc.get_traced_memory()
    for _ in range(memory_iterations):
        results = validate_once()
        if not all_pass(results):
            errors.append("validator returned failure during memory benchmark")
            break
    gc.collect()
    final_current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    retained_growth_kib = max(0.0, (final_current - baseline_current) / 1024.0)
    peak_kib = peak / 1024.0

    if mean_ms >= float(BUDGET["maximum_mean_ms"]):
        errors.append(f"mean {mean_ms:.3f}ms exceeds budget {BUDGET['maximum_mean_ms']}ms")
    if p95_ms >= float(BUDGET["maximum_p95_ms"]):
        errors.append(f"p95 {p95_ms:.3f}ms exceeds budget {BUDGET['maximum_p95_ms']}ms")
    if maximum_ms >= float(BUDGET["maximum_single_ms"]):
        errors.append(f"max {maximum_ms:.3f}ms exceeds budget {BUDGET['maximum_single_ms']}ms")
    if retained_growth_kib >= float(BUDGET["maximum_retained_growth_kib"]):
        errors.append(
            f"retained growth {retained_growth_kib:.1f}KiB exceeds budget {BUDGET['maximum_retained_growth_kib']}KiB"
        )

    result = {
        "passed": not errors,
        "shipping_c6_satisfied": False,
        "timing_instrumentation": "perf_counter_ns without tracemalloc",
        "memory_instrumentation": "separate tracemalloc pass",
        "iterations": len(durations_ms),
        "memory_iterations": memory_iterations,
        "validators_per_iteration": 8,
        "mean_ms": round(mean_ms, 6),
        "p95_ms": round(p95_ms, 6),
        "maximum_ms": round(maximum_ms, 6),
        "retained_growth_kib": round(retained_growth_kib, 3),
        "peak_traced_kib": round(peak_kib, 3),
        "errors": errors,
    }
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
