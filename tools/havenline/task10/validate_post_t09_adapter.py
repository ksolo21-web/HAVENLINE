#!/usr/bin/env python3
"""Validate the prepared T10->simulation authority adapter contract.

Before T09 approval this validates only the prepared contract and reports the shared
runtime as intentionally unbound. After the integration owner applies the authorized
simulation.gd change, --require-bound validates source markers needed by the real T10
integration suite. It never edits shared runtime.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = ROOT / "Docs" / "Production" / "T10" / "POST_T09_ADAPTER_CONTRACT.json"
SIMULATION_PATH = ROOT / "HavenlineGodot" / "scripts" / "simulation.gd"

REQUIRED_CONTRACT_RULES = {
    "resource_owner": "simulation",
    "affordability_balance": "stored",
    "carried_balance": "inventory",
    "t10_must_use": "stored",
    "t10_must_not_debit": "inventory",
    "t09_harvest_receipt_is_direct_t10_authority": False,
}

BOUND_SOURCE_MARKERS = [
    "world_transform_debit_receipts",
    "commit_world_transform_debit",
    'authority_source',
    'authority_applied',
    'simulation_replayed',
    'stored',
    'target_revision',
    'authority_transaction_key',
]


def fail(message: str) -> None:
    raise AssertionError(message)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--require-bound", action="store_true")
    ap.add_argument("--output")
    args = ap.parse_args()

    contract = json.loads(CONTRACT_PATH.read_text())
    errors: list[str] = []

    if contract.get("task_id") != "T10":
        errors.append("adapter contract task_id is not T10")
    if contract.get("integration_owner_required") is not True:
        errors.append("shared runtime change must remain integration-owner-only")
    if contract.get("shared_runtime_path") != "HavenlineGodot/scripts/simulation.gd":
        errors.append("unexpected shared runtime path")

    authority = contract.get("authority", {})
    for key, expected in REQUIRED_CONTRACT_RULES.items():
        if authority.get(key) != expected:
            errors.append(f"authority contract mismatch: {key}={authority.get(key)!r}, expected {expected!r}")

    api = contract.get("proposed_api", {})
    if api.get("method") != "commit_world_transform_debit":
        errors.append("prepared adapter method name mismatch")
    required_fields = set(api.get("input_required_fields", []))
    expected_fields = {
        "transaction_id", "authority_transaction_key", "request_identity", "recipe_id",
        "target_id", "source_state", "target_state", "debits", "progression_tags",
        "presentation_key", "target_revision",
    }
    if required_fields != expected_fields:
        errors.append("prepared intent field set does not match T10 authoritative intent")

    bounded = contract.get("bounded_idempotency", {})
    if bounded.get("proposed_simulation_field") != "world_transform_debit_receipts":
        errors.append("bounded simulation receipt field mismatch")
    if bounded.get("key") != "target_id":
        errors.append("bounded receipt ledger must remain target-keyed")

    persistence = contract.get("persistence", {})
    if persistence.get("required") is not True or persistence.get("global_versioning_owner") != "T14":
        errors.append("adapter persistence/T14 boundary mismatch")
    if persistence.get("does_not_define_global_save_version") is not True:
        errors.append("T10 adapter must not define global save versioning")

    shared = contract.get("shared_runtime_change_scope", {})
    if shared.get("required_paths") != ["HavenlineGodot/scripts/simulation.gd"]:
        errors.append("prepared shared runtime scope expanded unexpectedly")
    if shared.get("main_gd_change_required_for_t10_framework_integration") is not False:
        errors.append("T10 framework integration must not require main.gd shipping-content wiring")
    if shared.get("t11_later_owns_shipping_content_binding") is not True:
        errors.append("T11 final content boundary is not preserved")

    source = SIMULATION_PATH.read_text()
    present = [marker for marker in BOUND_SOURCE_MARKERS if marker in source]
    missing = [marker for marker in BOUND_SOURCE_MARKERS if marker not in source]
    bound = not missing

    if args.require_bound and not bound:
        errors.append("real adapter is not bound; missing simulation.gd markers: " + ", ".join(missing))

    report = {
        "task": "T10",
        "mode": "post-t09-adapter-bound-validation" if args.require_bound else "prepared-adapter-contract-validation",
        "contract": str(CONTRACT_PATH.relative_to(ROOT)),
        "shared_runtime": str(SIMULATION_PATH.relative_to(ROOT)),
        "prepared_contract_valid": not [e for e in errors if not e.startswith("real adapter is not bound")],
        "real_adapter_bound": bound,
        "required_bound_markers": BOUND_SOURCE_MARKERS,
        "present_bound_markers": present,
        "missing_bound_markers": missing,
        "require_bound": args.require_bound,
        "integration_allowed": False if not bound else None,
        "errors": errors,
        "passed": not errors,
    }
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(text)
    print(text, end="")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
