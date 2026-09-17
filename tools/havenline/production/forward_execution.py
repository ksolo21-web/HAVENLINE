#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "Docs" / "Production"
PROFILE_PATH = DOCS / "FORWARD_EXECUTION_PROFILES.json"
GRAPH_PATH = DOCS / "DEPENDENCY_GRAPH.json"
CRITIC_PATH = DOCS / "CRITIC_MATRIX.json"
RUNNER_PATH = DOCS / "FORWARD_GATE_RUNNERS.json"
VALID_MODES = {"build", "validation_only", "certification_only", "release_only"}
EXPENSIVE_GATES = {"performance", "visual_evidence", "physical_device", "critic_review"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def authorities() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    return load_json(PROFILE_PATH), load_json(GRAPH_PATH), load_json(CRITIC_PATH), load_json(RUNNER_PATH)


def _critic_gates(critics: list[str], profile: dict[str, Any], mode: str) -> set[str]:
    required: set[str] = set()
    rules = profile["critic_gate_requirements"]
    for critic in critics:
        rule = rules.get(critic, {})
        required.update(rule.get("all_of", []))
        any_of = list(rule.get("any_of", []))
        if any_of:
            # Resolve the cheapest valid proof for this execution mode. C6/C11
            # physical certification must remain physical; normal build/review
            # work uses performance/device matrices instead.
            if critic == "C6":
                required.add("physical_device" if mode == "certification_only" else "performance")
            elif critic == "C11":
                required.add("physical_device" if mode == "certification_only" else "device_matrix")
            elif critic == "C1":
                # Reference fidelity is protected at both ends: lock the
                # authority before building and prove source-bound pixels later.
                required.update({"reference_lock", "visual_evidence"})
            else:
                required.add(any_of[0])
    return required


def resolve_task(task_id: str) -> dict[str, Any]:
    profile, graph, matrix, runner_registry = authorities()
    task_id = task_id.upper()
    if task_id not in profile["tasks"]:
        raise ValueError(f"no forward execution profile for {task_id}")
    graph_task = graph["tasks"].get(task_id)
    critics = matrix["task_applicability"].get(task_id)
    if not graph_task or critics is None:
        raise ValueError(f"{task_id} missing from dependency or critic authority")
    row = profile["tasks"][task_id]
    archetype = profile["archetypes"].get(row["archetype"])
    if archetype is None:
        raise ValueError(f"{task_id} references unknown archetype {row['archetype']}")
    mode = row["mode"]
    gates: set[str] = {
        "scope_dependency", "ownership", "source_contract", "task_sentinel", "critic_review", "closeout"
    }
    if mode not in {"certification_only", "release_only"}:
        gates.add("focused_unit")
    gates.update(archetype.get("base_gates", []))
    gates.update(row.get("extra_gates", []))
    gates.update(_critic_gates(list(critics), profile, mode))
    if mode == "build":
        gates.update({"impacted_regression", "integration", "post_integration_regression"})
    elif mode == "validation_only":
        gates.add("impacted_regression")
    elif mode == "certification_only":
        gates.add("physical_device")
    elif mode == "release_only":
        gates.add("release_manifest")
    order = {name: idx for idx, name in enumerate(profile["gate_order"])}
    unknown = sorted(gates - set(order))
    if unknown:
        raise ValueError(f"{task_id} uses unknown gates: {unknown}")
    missing_runners = sorted(gates - set(runner_registry.get("gates", {})))
    if missing_runners:
        raise ValueError(f"{task_id} gates lack execution contracts: {missing_runners}")
    ordered = sorted(gates, key=order.__getitem__)
    dependencies = list(graph_task.get("dependencies", []))
    dependency_status = {dep: graph["tasks"][dep]["status"] for dep in dependencies}
    packet_dir = DOCS / task_id
    packet_present = packet_dir.is_dir() and (packet_dir / "TASK_PACKET.md").is_file()
    dependencies_approved = all(status == "APPROVED" for status in dependency_status.values())
    gate_execution = {
        gate: {
            "execution": runner_registry["gates"][gate]["execution"],
            "runner": runner_registry["gates"][gate]["runner"],
            "rule": runner_registry["gates"][gate]["rule"],
        }
        for gate in ordered
    }
    return {
        "task_id": task_id,
        "task_name": graph_task["name"],
        "status": graph_task["status"],
        "archetype": row["archetype"],
        "execution_mode": mode,
        "dependencies": dependencies,
        "dependency_status": dependency_status,
        "dependencies_approved": dependencies_approved,
        "critics": list(critics),
        "early_sentinel": row["sentinel"],
        "ordered_gates": ordered,
        "gate_execution": gate_execution,
        "canonical_packet_present": packet_present,
        "activation_ready": dependencies_approved and packet_present,
        "failure_disposition": (
            "C0 -> bounded builder repair plan" if mode == "build" else
            "C0 -> change request to owning build task; this task may not repair runtime"
        ),
    }


def validate_all() -> dict[str, Any]:
    profile, graph, matrix, runner_registry = authorities()
    errors: list[str] = []
    expected = {f"T{i:02d}" for i in range(10, 71)}
    actual = set(profile.get("tasks", {}))
    if actual != expected:
        errors.append(f"profile task coverage mismatch missing={sorted(expected-actual)} extra={sorted(actual-expected)}")
    global_rules = profile.get("global", {})
    required_globals = {
        "freeze_exact_sha": True,
        "finish_running_sha": True,
        "ci_cancel_in_progress": False,
        "candidate_guard_before_broad_build": True,
        "stop_after_failed_preflight": True,
        "automatic_c0_on_terminal_failure": True,
        "c0_non_voting": True,
        "repair_requires_c0_and_plan": True,
        "threshold_relaxation_is_not_repair": True,
    }
    for key, expected_value in required_globals.items():
        if global_rules.get(key) != expected_value:
            errors.append(f"global rule {key} must be {expected_value!r}")
    if global_rules.get("same_failure_fingerprint_max") != 1:
        errors.append("same failure fingerprint must block after one repeated occurrence")
    if global_rules.get("infra_retry_without_code_change_max") != 1:
        errors.append("infrastructure retry budget must be exactly one no-code retry")

    gate_order = list(profile.get("gate_order", []))
    gate_contracts = runner_registry.get("gates", {})
    missing_gate_contracts = sorted(set(gate_order) - set(gate_contracts))
    extra_gate_contracts = sorted(set(gate_contracts) - set(gate_order))
    if missing_gate_contracts:
        errors.append(f"forward gates without runner contracts: {missing_gate_contracts}")
    if extra_gate_contracts:
        errors.append(f"runner contracts reference unknown forward gates: {extra_gate_contracts}")
    for gate in gate_order:
        row = gate_contracts.get(gate, {})
        for field in ("execution", "runner", "rule"):
            if not str(row.get(field, "")).strip():
                errors.append(f"gate {gate} missing runner-contract field {field}")
    if gate_contracts.get("task_sentinel", {}).get("execution") != "task_adapter_required":
        errors.append("task_sentinel must require a task-owned adapter before broad build")
    if gate_contracts.get("physical_device", {}).get("execution") != "physical_hardware_only":
        errors.append("physical_device gate must remain physical_hardware_only")

    mode_counts = {mode: 0 for mode in VALID_MODES}
    archetype_counts: dict[str, int] = {}
    plans: dict[str, Any] = {}
    for task_id in sorted(expected):
        row = profile.get("tasks", {}).get(task_id)
        if not row:
            continue
        mode = row.get("mode")
        if mode not in VALID_MODES:
            errors.append(f"{task_id} invalid execution mode {mode!r}")
            continue
        mode_counts[mode] += 1
        archetype = row.get("archetype")
        if archetype not in profile.get("archetypes", {}):
            errors.append(f"{task_id} unknown archetype {archetype!r}")
            continue
        archetype_counts[archetype] = archetype_counts.get(archetype, 0) + 1
        if not str(row.get("sentinel", "")).strip():
            errors.append(f"{task_id} missing early sentinel")
        graph_task = graph.get("tasks", {}).get(task_id)
        matrix_critics = matrix.get("task_applicability", {}).get(task_id)
        if graph_task is None or matrix_critics is None:
            errors.append(f"{task_id} missing graph/critic authority")
            continue
        if set(graph_task.get("critics", [])) != set(matrix_critics):
            errors.append(f"{task_id} dependency-graph critics disagree with CRITIC_MATRIX")
        try:
            plan = resolve_task(task_id)
            plans[task_id] = plan
        except Exception as exc:
            errors.append(f"{task_id} plan resolution failed: {exc}")
            continue
        gates = plan["ordered_gates"]
        gate_set = set(gates)
        if set(plan["gate_execution"]) != gate_set:
            errors.append(f"{task_id} gate execution mapping incomplete")
        # Critic-specific proof gates are mandatory and cannot be silently
        # omitted by a task packet or builder workflow.
        if "C1" in matrix_critics and not {"reference_lock", "visual_evidence"} <= gate_set:
            errors.append(f"{task_id} C1 requires reference lock + visual evidence")
        if "C5" in matrix_critics and "motion_preflight" not in gate_set:
            errors.append(f"{task_id} C5 missing motion preflight")
        if "C6" in matrix_critics and not ({"performance", "physical_device"} & gate_set):
            errors.append(f"{task_id} C6 missing performance/physical proof")
        if "C7" in matrix_critics and "progression_sim" not in gate_set:
            errors.append(f"{task_id} C7 missing progression simulation")
        if "C8" in matrix_critics and "economy_sim" not in gate_set:
            errors.append(f"{task_id} C8 missing economy simulation")
        if "C9" in matrix_critics and "security_attack" not in gate_set:
            errors.append(f"{task_id} C9 missing security attack phase")
        if "C10" in matrix_critics and "liveops_sim" not in gate_set:
            errors.append(f"{task_id} C10 missing LiveOps simulation")
        if "C11" in matrix_critics and not ({"device_matrix", "physical_device"} & gate_set):
            errors.append(f"{task_id} C11 missing device/accessibility evidence")
        # Cheap decisive work must finish before costly fan-out.
        if "task_sentinel" in gates:
            sentinel_idx = gates.index("task_sentinel")
            for expensive in EXPENSIVE_GATES:
                if expensive in gates and sentinel_idx > gates.index(expensive):
                    errors.append(f"{task_id} expensive gate {expensive} occurs before task sentinel")
        if mode == "build":
            if "integration" not in gate_set or "post_integration_regression" not in gate_set:
                errors.append(f"{task_id} build mode missing integration/post-integration gates")
        else:
            if "integration" in gate_set or "post_integration_regression" in gate_set:
                errors.append(f"{task_id} {mode} must not perform runtime integration")
        if mode == "certification_only" and "physical_device" not in gate_set:
            errors.append(f"{task_id} certification cannot substitute non-physical evidence")
        if mode == "release_only" and "release_manifest" not in gate_set:
            errors.append(f"{task_id} release handoff missing release manifest closure")

    expected_validation = {"T58", "T62", "T63", "T64", "T65", "T66", "T67"}
    expected_cert = {"T68", "T69"}
    expected_release = {"T70"}
    for task_id in expected_validation:
        if profile["tasks"][task_id]["mode"] != "validation_only":
            errors.append(f"{task_id} must be validation_only")
    for task_id in expected_cert:
        if profile["tasks"][task_id]["mode"] != "certification_only":
            errors.append(f"{task_id} must be certification_only")
    for task_id in expected_release:
        if profile["tasks"][task_id]["mode"] != "release_only":
            errors.append(f"{task_id} must be release_only")

    return {
        "passed": not errors,
        "task_count": len(actual),
        "expected_task_count": 61,
        "gate_runner_contract_count": len(gate_contracts),
        "expected_gate_runner_contract_count": len(gate_order),
        "archetype_counts": dict(sorted(archetype_counts.items())),
        "mode_counts": mode_counts,
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve/validate Havenline forward execution plans")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    plan = sub.add_parser("plan")
    plan.add_argument("task_id")
    plan.add_argument("--output")
    args = parser.parse_args()
    if args.command == "validate":
        result = validate_all()
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result["passed"] else 2)
    result = resolve_task(args.task_id)
    text = json.dumps(result, indent=2) + "\n"
    if args.output:
        path = (ROOT / args.output).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    print(text, end="")


if __name__ == "__main__":
    main()
