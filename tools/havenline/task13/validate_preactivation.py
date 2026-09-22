#!/usr/bin/env python3
"""Fail-closed T13 preactivation readiness validator.

This validator proves that the T13 preparation package is coherent on the
authoritative integration lineage while runtime implementation remains locked.
It does not activate T13 and does not modify repository state.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "Docs" / "Production"
T13 = DOCS / "T13"

REQUIRED_DOCS = (
    "FROZEN_SCOPE.md",
    "TASK_PACKET.md",
    "PREBUILD_CONTRACT.json",
    "ACTIVATION_CHECKLIST.json",
    "IMPLEMENTATION_BLUEPRINT.md",
    "TEST_EVIDENCE_PLAN.md",
    "T12_CONSUMER_BINDING.json",
    "defect-ledger.json",
)

SHIPPING_PATHS = (
    ROOT / "HavenlineGodot/scripts/challenge_director.gd",
    ROOT / "HavenlineGodot/data/challenge_director_v1.json",
    ROOT / "HavenlineGodot/tests/test_task13_challenge_director.gd",
    ROOT / "HavenlineGodot/tests/test_task13_integration.gd",
    ROOT / "HavenlineGodot/tests/capture_task13_challenge.gd",
)

EXPECTED_BRANCH = "havenline/T13-challenge-director"
EXPECTED_OWNER = "challenge-director-builder"
EXPECTED_DEPENDENCIES = ["T12"]
EXPECTED_GM_FLAGS = [
    "gm_challenge_profile_implemented",
    "gm_challenge_spend_blind",
    "gm_challenge_elevated_envelope_proven",
]

def load_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))

def git_blob_sha(path: pathlib.Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()

def main() -> int:
    errors: list[str] = []
    for name in REQUIRED_DOCS:
        p = T13 / name
        if not p.exists() or not p.read_text(encoding="utf-8").strip():
            errors.append(f"missing/empty T13 artifact: {p.relative_to(ROOT)}")

    if errors:
        print(json.dumps({"task_id":"T13","passed":False,"errors":errors}, indent=2))
        return 1

    prebuild = load_json(T13 / "PREBUILD_CONTRACT.json")
    checklist = load_json(T13 / "ACTIVATION_CHECKLIST.json")
    binding = load_json(T13 / "T12_CONSUMER_BINDING.json")
    ledger = load_json(T13 / "defect-ledger.json")
    graph = load_json(DOCS / "DEPENDENCY_GRAPH.json")
    gates = load_json(DOCS / "task-gates.json")
    gm_policy = load_json(DOCS / "GAME_MASTER_POLICY.json")
    t12_contract_path = DOCS / "T12" / "DOWNSTREAM_CONSUMER_CONTRACT.json"

    if prebuild.get("task_id") != "T13" or checklist.get("task_id") != "T13":
        errors.append("task identity mismatch")
    if checklist.get("dependencies") != EXPECTED_DEPENDENCIES:
        errors.append("activation checklist dependency mismatch")
    if prebuild.get("dependencies") != EXPECTED_DEPENDENCIES:
        errors.append("prebuild dependency mismatch")
    if checklist.get("future_builder_branch") != EXPECTED_BRANCH:
        errors.append("future builder branch mismatch")
    if checklist.get("future_owner") != EXPECTED_OWNER:
        errors.append("future owner mismatch")
    if checklist.get("runtime_status") != "LOCKED":
        errors.append("T13 runtime status must remain LOCKED before activation")
    if checklist.get("runtime_build_allowed_before_activation") is not False:
        errors.append("runtime build must remain forbidden before activation")
    if ledger.get("unresolved_preparation_defects"):
        errors.append("unresolved preparation defects remain")

    task = graph.get("tasks", {}).get("T13", {})
    if task.get("dependencies") != EXPECTED_DEPENDENCIES:
        errors.append("dependency graph T13 dependency mismatch")
    if task.get("status") not in ("LOCKED", "PREPARED"):
        errors.append(f"unexpected T13 graph status before activation: {task.get('status')}")
    if "T13" in gates.get("approved_tasks", []):
        errors.append("T13 may not be approved during preactivation")

    existing_shipping = [str(p.relative_to(ROOT)) for p in SHIPPING_PATHS if p.exists()]
    if existing_shipping:
        errors.append("T13 shipping/runtime files exist before activation: " + ", ".join(existing_shipping))

    if not t12_contract_path.exists():
        errors.append("missing authoritative T12 downstream consumer contract")
        current_contract_sha = None
    else:
        current_contract_sha = git_blob_sha(t12_contract_path)
        if binding.get("prepared_contract_git_blob_sha") != current_contract_sha:
            errors.append(
                "T12 consumer contract blob drift: prepared="
                + str(binding.get("prepared_contract_git_blob_sha"))
                + " current=" + current_contract_sha
            )
        contract = load_json(t12_contract_path)
        row = contract.get("consumers", {}).get("T13")
        if not row:
            errors.append("T13 missing from T12 downstream consumer contract")
        else:
            for key in ("may_read", "must_not_require_from_T12", "boundary"):
                if binding.get(key) != row.get(key):
                    errors.append(f"T12 consumer field mismatch: {key}")

    gm_flags = (
        gm_policy.get("task_policy", {})
        .get("required_proof_flags_by_task", {})
        .get("T13")
    )
    if gm_flags != EXPECTED_GM_FLAGS:
        errors.append("Game Master T13 proof-flag contract drift")
    if checklist.get("game_master_required_proof_flags") != EXPECTED_GM_FLAGS:
        errors.append("activation checklist Game Master proof flags drift")
    if prebuild.get("game_master_required_proof_flags") != EXPECTED_GM_FLAGS:
        errors.append("prebuild Game Master proof flags drift")

    t12_status = graph.get("tasks", {}).get("T12", {}).get("status")
    t12_approved = (
        t12_status == "APPROVED"
        and "T12" in gates.get("approved_tasks", [])
    )

    result = {
        "task_id": "T13",
        "passed": not errors,
        "runtime_activation_performed": False,
        "runtime_files_present": len(existing_shipping),
        "t12_graph_status": t12_status,
        "t12_approved_in_task_gates": "T12" in gates.get("approved_tasks", []),
        "activation_dependency_satisfied": t12_approved,
        "t12_consumer_contract_blob_sha": current_contract_sha,
        "gm_required_flags": gm_flags,
        "unresolved_preparation_defects": len(ledger.get("unresolved_preparation_defects", [])),
        "errors": errors,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
