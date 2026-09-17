#!/usr/bin/env python3
"""Fail-closed readiness validator for the first T13+ activation wave: T13 and T14 only.

This validator never activates a task and never writes runtime state. It proves that
T13/T14 are maximally prepared while dependency-locked: frozen scope, blueprint,
exact test/evidence plan, task-packet wiring, activation support artifacts, branch/
owner/dependency declarations, critic coverage, consumer binding, zero preparation
defects, and runtime-build prohibition.
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "Docs" / "Production"

EXPECTED = {
    "T13": {
        "branch": "havenline/T13-challenge-director",
        "owner": "challenge-director-builder",
        "dependencies": ["T12"],
        "critics": ["C2", "C3", "C4", "C6", "C7"],
        "required_markers": [
            "spend-blind",
            "deterministic",
            "bounded",
            "GM_CHALLENGE",
            "recovery",
        ],
    },
    "T14": {
        "branch": "havenline/T14-save-versioning",
        "owner": "save-versioning-builder",
        "dependencies": ["T08", "T10", "T12"],
        "critics": ["C2", "C9"],
        "required_markers": [
            "atomic",
            "migration",
            "corruption",
            "interruption",
            "round-trip",
        ],
    },
}

REQUIRED_FILES = (
    "FROZEN_SCOPE.md",
    "TASK_PACKET.md",
    "PREBUILD_CONTRACT.json",
    "ACTIVATION_CHECKLIST.json",
    "defect-ledger.json",
    "T12_CONSUMER_BINDING.json",
    "IMPLEMENTATION_BLUEPRINT.md",
    "TEST_EVIDENCE_PLAN.md",
)


def load_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def norm_list(values):
    return list(values or [])


def validate_task(task: str, cfg: dict) -> list[str]:
    errors: list[str] = []
    task_dir = DOCS / task

    for name in REQUIRED_FILES:
        path = task_dir / name
        if not path.exists():
            errors.append(f"{task}: missing {name}")

    if errors:
        return errors

    checklist = load_json(task_dir / "ACTIVATION_CHECKLIST.json")
    prebuild = load_json(task_dir / "PREBUILD_CONTRACT.json")
    ledger = load_json(task_dir / "defect-ledger.json")
    binding = load_json(task_dir / "T12_CONSUMER_BINDING.json")
    packet = (task_dir / "TASK_PACKET.md").read_text(encoding="utf-8")
    blueprint = (task_dir / "IMPLEMENTATION_BLUEPRINT.md").read_text(encoding="utf-8")
    test_plan = (task_dir / "TEST_EVIDENCE_PLAN.md").read_text(encoding="utf-8")
    scope = (task_dir / "FROZEN_SCOPE.md").read_text(encoding="utf-8")

    if checklist.get("task_id") != task:
        errors.append(f"{task}: checklist task_id mismatch")
    if prebuild.get("task_id") != task:
        errors.append(f"{task}: prebuild task_id mismatch")
    if checklist.get("future_builder_branch") != cfg["branch"]:
        errors.append(f"{task}: future builder branch mismatch")
    if prebuild.get("future_builder_branch") != cfg["branch"]:
        errors.append(f"{task}: prebuild future builder branch mismatch")
    if checklist.get("future_owner") != cfg["owner"]:
        errors.append(f"{task}: future owner mismatch")
    if prebuild.get("future_owner") != cfg["owner"]:
        errors.append(f"{task}: prebuild future owner mismatch")
    if norm_list(checklist.get("dependencies")) != cfg["dependencies"]:
        errors.append(f"{task}: checklist dependencies mismatch")
    if norm_list(prebuild.get("dependencies")) != cfg["dependencies"]:
        errors.append(f"{task}: prebuild dependencies mismatch")
    if sorted(norm_list(checklist.get("required_critics"))) != sorted(cfg["critics"]):
        errors.append(f"{task}: required critics mismatch")
    if checklist.get("runtime_build_allowed_before_activation") is not False:
        errors.append(f"{task}: runtime build must remain forbidden before activation")
    if checklist.get("runtime_status") != "LOCKED":
        errors.append(f"{task}: runtime status must remain LOCKED")
    if checklist.get("preparation_status") != "PREPARED_GOVERNANCE_ONLY":
        errors.append(f"{task}: preparation status drift")
    if prebuild.get("mode") != "dependency-independent governance/interface preparation only":
        errors.append(f"{task}: prebuild mode drift")

    unresolved = ledger.get("unresolved_preparation_defects")
    if unresolved != []:
        errors.append(f"{task}: unresolved preparation defects present: {unresolved}")

    if binding.get("consumer_task") != task:
        errors.append(f"{task}: T12 consumer binding mismatch")
    if not binding.get("prepared_contract_git_blob_sha"):
        errors.append(f"{task}: T12 consumer binding missing prepared contract blob SHA")
    if "Fail closed" not in str(binding.get("activation_rule", "")):
        errors.append(f"{task}: T12 consumer binding is not fail-closed")

    for required_path in (
        f"Docs/Production/{task}/IMPLEMENTATION_BLUEPRINT.md",
        f"Docs/Production/{task}/TEST_EVIDENCE_PLAN.md",
    ):
        support = norm_list(checklist.get("prepared_support_artifacts"))
        if required_path not in support:
            errors.append(f"{task}: checklist missing support artifact {required_path}")
        if required_path not in packet:
            errors.append(f"{task}: task packet does not reference {required_path}")

    if cfg["branch"] not in packet:
        errors.append(f"{task}: task packet branch mismatch")
    if cfg["owner"] not in packet:
        errors.append(f"{task}: task packet owner mismatch")
    if "runtime implementation may not begin" not in packet.lower():
        errors.append(f"{task}: task packet missing explicit no-runtime-before-activation rule")

    combined = "\n".join((scope, packet, blueprint, test_plan)).lower()
    for marker in cfg["required_markers"]:
        if marker.lower() not in combined:
            errors.append(f"{task}: handoff is missing required marker {marker!r}")

    if ">9.0" not in combined and '"threshold":9.0' not in (task_dir / "ACTIVATION_CHECKLIST.json").read_text(encoding="utf-8"):
        errors.append(f"{task}: strict >9.0 acceptance is not represented")
    if "10/10" not in combined and '"target":10.0' not in (task_dir / "ACTIVATION_CHECKLIST.json").read_text(encoding="utf-8"):
        errors.append(f"{task}: 10/10 target is not represented")

    return errors


def main() -> int:
    errors: list[str] = []
    for task, cfg in EXPECTED.items():
        errors.extend(validate_task(task, cfg))

    result = {
        "scope": "T13/T14 first-wave build-readiness handoff",
        "tasks": sorted(EXPECTED),
        "task_count": len(EXPECTED),
        "runtime_activation_performed": False,
        "errors": errors,
        "passed": not errors,
    }
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
