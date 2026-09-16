#!/usr/bin/env python3
"""Focused regression tests for activation_frontier.py."""
from __future__ import annotations

import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "tools/havenline/prepared_stack/activation_frontier.py"


def load_module():
    spec = importlib.util.spec_from_file_location("activation_frontier", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load activation_frontier.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    m = load_module()
    failures = []

    registry = {
        "legacy_approvals": {"T10": {}},
        "workstreams": [
            {"task_id": "T11", "status": "APPROVED"},
            {"task_id": "T12", "status": "LOCKED"},
        ],
    }
    if m.registry_status(registry, "T10") != "APPROVED":
        failures.append("legacy approval lookup failed")
    if m.registry_status(registry, "T11") != "APPROVED":
        failures.append("workstream approval lookup failed")
    if m.registry_status(registry, "T12") != "LOCKED":
        failures.append("locked workstream lookup failed")

    graph = {
        "tasks": {
            "T12": {"status": "APPROVED", "dependencies": []},
            "T13": {"status": "LOCKED", "dependencies": ["T12"]},
            "T14": {"status": "LOCKED", "dependencies": ["T13"]},
            "T15": {"status": "LOCKED", "dependencies": ["T13", "T14"]},
        }
    }
    waves, unresolved = m.hypothetical_internal_waves(graph)
    expected_prefix = [["T13"], ["T14"], ["T15"]]
    if waves[:3] != expected_prefix:
        failures.append(f"unexpected synthetic wave order: {waves[:3]}")
    # The production TASKS constant includes T16-T70, which are intentionally
    # unresolved in this tiny synthetic graph. The test verifies that the
    # function reports them instead of silently pretending they were ordered.
    if not unresolved:
        failures.append("synthetic missing graph nodes were not reported unresolved")

    dep_graph = {"tasks": {"T12": {"status": "APPROVED", "dependencies": []}}}
    dep_registry = {"legacy_approvals": {"T12": {}}}
    dep_gates = {"approved_tasks": ["T12"]}
    dep_ownership = {"active_owners": []}
    good = m.dependency_state("T12", dep_graph, dep_registry, dep_gates, dep_ownership)
    if not good["approved"] or good["blockers"]:
        failures.append(f"fully approved dependency was blocked: {good}")

    dep_ownership = {"active_owners": [{"task_id": "T12", "owner": "still-active"}]}
    blocked = m.dependency_state("T12", dep_graph, dep_registry, dep_gates, dep_ownership)
    if blocked["approved"] or not any(x.startswith("active_path_owner:") for x in blocked["blockers"]):
        failures.append(f"active dependency ownership was not fail-closed: {blocked}")

    print({"scope": "activation frontier regression tests", "passed": not failures, "failures": failures})
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
