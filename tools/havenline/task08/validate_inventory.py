#!/usr/bin/env python3
"""Fail-closed static contract gate for T08 physical inventory presentation."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CARRY = ROOT / "HavenlineGodot/scripts/carry_stack.gd"
STOCKPILE = ROOT / "HavenlineGodot/scripts/storage_stockpile.gd"
TRANSFER = ROOT / "HavenlineGodot/scripts/transfer_feedback.gd"
UNIT = ROOT / "HavenlineGodot/tests/test_task08_inventory.gd"
INTEGRATION = ROOT / "HavenlineGodot/tests/test_task08_integration.gd"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(candidate: str) -> dict:
    sources = {"carry": CARRY.read_text(), "stockpile": STOCKPILE.read_text(), "transfer": TRANSFER.read_text()}
    tests = UNIT.read_text() + "\n" + INTEGRATION.read_text()
    checks: list[dict] = []
    failures: list[str] = []

    def check(name: str, passed: bool, detail: object = None) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})
        if not passed:
            failures.append(name)

    combined = "\n".join(sources.values())
    assets = {
        "wood": "res://assets/stations_v2/wood_stack.glb",
        "stone": "res://assets/stations_v2/stone_stack.glb",
        "metal": "res://assets/stations_v2/metal_stack.glb",
        "fuel": "res://assets/stations_v2/fuel_canister.glb",
    }
    check("exact component identities", all(token in combined for token in (
        "class_name HavenlineCarryStack", "class_name HavenlineStorageStockpile", "class_name HavenlineTransferFeedback")))
    check("all production resources use approved authored assets", all(f'"{kind}": "{path}"' in sources["carry"] for kind, path in assets.items()), assets)
    check("logical inventory is explicitly unlimited", '"unlimited_logical_inventory": true' in sources["carry"])
    check("presentation cannot mutate inventory", combined.count('"mutates_inventory": false') >= 3)
    check("presentation adds no save fields", '"adds_save_fields": false' in sources["carry"] and "FileAccess" not in combined)
    check("visual budgets are explicit", "VISIBLE_BUDGET := 48" in sources["carry"] and "MAX_FLIGHTS := 48" in sources["transfer"])
    check("small and compressed layouts are deterministic", "allocate_visible" in sources["carry"] and "represented_count" in sources["carry"])
    check("actor loads use a raised readable rack", "CARRY_BASE_HEIGHT :=" in sources["carry"] and "CARRY_TIER_HEIGHT :=" in sources["carry"])
    check("unchanged actor stacks avoid rebuilds", "if next_signature == signature:" in sources["carry"])
    check("authored nodes are pooled", "pools" in sources["carry"] and "pools" in sources["transfer"])
    check("future resources have no generic primitive fallback", not re.search(r"\b(BoxMesh|SphereMesh|CylinderMesh|CSGBox3D)\b", combined))
    check("transfer directions are exact", '["source_to_actor", "actor_to_destination"]' in sources["transfer"])
    check("transfer flights expose readability geometry", "FLIGHT_SCALE_MULTIPLIER :=" in sources["transfer"] and "ARC_HEIGHT :=" in sources["transfer"] and "DURATION_SECONDS := 0.72" in sources["transfer"])
    check("receipt replay is rejected", "if receipts.has(receipt_id):" in sources["transfer"] and "RECEIPT_WINDOW := 256" in sources["transfer"])
    check("invalid and zero-length routes fail closed", "valid_point" in sources["transfer"] and "distance_squared_to(finish) <= 0.000001" in sources["transfer"])
    check("destination display derives from stored counts", "return stack.update_inventory(stored)" in sources["stockpile"])
    check("no inventory UI or manual transfer control", not re.search(r"\b(Button|TouchScreenButton|ItemList|GridContainer|drag_data)\b", combined))
    check("tests cover maximum-scale logical counts", "10000000000000" in tests and "900000000000" in tests)
    check("tests cover conservation and visual non-authority", "cannot mutate caller inventory" in tests and "cannot duplicate logical value" in tests)
    check("tests cover save-derived reconstruction", "rebuild without saved presentation state" in tests and "T08 adds no save field" in tests)
    check("tests preserve T07 one-joystick context", "one-joystick action contract remains intact" in tests)
    check("tests cover build repair helper and actor visibility", all(token in tests for token in ("routes committed build", "routes committed repair", "lead switch cannot duplicate", "hidden actor stack fails closed")))

    return {
        "task": "T08", "candidate_commit": candidate,
        "sources": {str(path.relative_to(ROOT)): digest(path) for path in (CARRY, STOCKPILE, TRANSFER)},
        "tests": {str(path.relative_to(ROOT)): digest(path) for path in (UNIT, INTEGRATION)},
        "checks": checks, "check_count": len(checks), "passed": not failures,
        "failures": failures, "future_scope_implemented": [],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", default="local-working-tree")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(args.candidate)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(rendered, end="")
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
