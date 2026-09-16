#!/usr/bin/env python3
"""Fail-closed semantic reconciliation between T11 camp content and accepted T10.

This tool never copies T10 costs into T11 and never mutates gameplay. It checks
that every T11 camp content transition still points at an existing T10 recipe
with the exact source/target semantic states T11 was authored against, and that
the T10 runtime still exposes the injected method surface T11 consumes.

Run this after T10 is integrated/rebased beneath T11. Before that point the
expected T10 files may be absent from the T11 isolated branch; absence is a
hard failure for the CLI, not permission to guess compatibility.
"""
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[3]
DEFAULT_T11_CATALOG = ROOT / "HavenlineGodot" / "data" / "camp_upgrade_recipes.json"
DEFAULT_T10_CATALOG = ROOT / "HavenlineGodot" / "data" / "world_transform_recipes.json"
DEFAULT_T10_SCRIPT = ROOT / "HavenlineGodot" / "scripts" / "world_transform.gd"
EXPECTED_T10_RECIPE_AUTHORITY = "T10-world-transform-recipes-v1"
REQUIRED_T10_METHODS = (
    "preview_transform",
    "commit_transform",
    "accept_authoritative_receipt",
)


def load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _recipe_map(catalog: dict[str, Any], id_field: str) -> tuple[dict[str, dict[str, Any]], list[str]]:
    errors: list[str] = []
    rows = catalog.get("recipes")
    if not isinstance(rows, list) or not rows:
        return {}, ["catalog recipes must be a non-empty array"]
    result: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(rows):
        if not isinstance(raw, dict):
            errors.append(f"recipe[{index}] must be an object")
            continue
        recipe_id = str(raw.get(id_field, ""))
        if not recipe_id:
            errors.append(f"recipe[{index}] missing {id_field}")
            continue
        if recipe_id in result:
            errors.append(f"duplicate {id_field}: {recipe_id}")
            continue
        result[recipe_id] = raw
    return result, errors


def reconcile(
    t11_catalog: dict[str, Any],
    t10_catalog: dict[str, Any],
    t10_script_text: str,
    *,
    mode: str = "semantic",
    expected_t10_source: str = "",
) -> dict[str, Any]:
    if mode not in {"semantic", "final"}:
        raise ValueError(f"unsupported mode: {mode}")

    errors: list[str] = []
    warnings: list[str] = []
    bindings: list[dict[str, Any]] = []

    if t11_catalog.get("authority_id") != "T11-camp-upgrade-recipes-build-pending-v1":
        errors.append(f"unexpected T11 catalog authority: {t11_catalog.get('authority_id')}")
    if t10_catalog.get("authority_id") != EXPECTED_T10_RECIPE_AUTHORITY:
        errors.append(f"unexpected T10 recipe authority: {t10_catalog.get('authority_id')}")

    if expected_t10_source and len(expected_t10_source) != 40:
        errors.append("expected_t10_source must be a 40-character commit SHA when supplied")

    for method in REQUIRED_T10_METHODS:
        marker = f"func {method}("
        if marker not in t10_script_text:
            errors.append(f"accepted T10 runtime missing required method: {method}")

    t11_rows, t11_errors = _recipe_map(t11_catalog, "camp_state_id")
    t10_rows, t10_errors = _recipe_map(t10_catalog, "recipe_id")
    errors.extend(f"T11: {value}" for value in t11_errors)
    errors.extend(f"T10: {value}" for value in t10_errors)

    seen_t10_ids: set[str] = set()
    for camp_state_id, row in t11_rows.items():
        if "costs" in row or "debits" in row:
            errors.append(f"T11 recipe {camp_state_id} illegally duplicates T10 cost/debit authority")

        t10_recipe_id = str(row.get("t10_recipe_id", ""))
        expected_source = str(row.get("t10_source_state", ""))
        expected_target = str(row.get("t10_target_state", ""))
        if not t10_recipe_id or not expected_source or not expected_target:
            errors.append(f"T11 recipe {camp_state_id} lacks a complete T10 semantic binding")
            continue
        if t10_recipe_id in seen_t10_ids:
            errors.append(f"duplicate T10 recipe binding in T11: {t10_recipe_id}")
        seen_t10_ids.add(t10_recipe_id)

        t10_row = t10_rows.get(t10_recipe_id)
        if t10_row is None:
            errors.append(f"T11 recipe {camp_state_id} references missing T10 recipe {t10_recipe_id}")
            continue

        actual_source = str(t10_row.get("source_state", ""))
        actual_target = str(t10_row.get("target_state", ""))
        source_match = actual_source == expected_source
        target_match = actual_target == expected_target
        if not source_match:
            errors.append(
                f"T10 source-state drift for {t10_recipe_id}: T11={expected_source} T10={actual_source}"
            )
        if not target_match:
            errors.append(
                f"T10 target-state drift for {t10_recipe_id}: T11={expected_target} T10={actual_target}"
            )

        costs = t10_row.get("costs", [])
        if not isinstance(costs, list) or not costs:
            errors.append(f"T10 recipe {t10_recipe_id} has no authoritative costs")

        bindings.append(
            {
                "camp_state_id": camp_state_id,
                "t10_recipe_id": t10_recipe_id,
                "source_state": actual_source,
                "target_state": actual_target,
                "source_match": source_match,
                "target_match": target_match,
                "t10_costs_present_authority_owned": isinstance(costs, list) and bool(costs),
                "t10_prerequisites": list(t10_row.get("prerequisites", [])) if isinstance(t10_row.get("prerequisites", []), list) else [],
                "t10_progression_tags": list(t10_row.get("progression_tags", [])) if isinstance(t10_row.get("progression_tags", []), list) else [],
                "t11_binding_status": str(row.get("binding_status", "")),
                "t11_shipping": bool(row.get("shipping", False)),
                "t11_test_only": bool(row.get("test_only", False)),
            }
        )

    semantic_compatible = not errors

    if bool(t10_catalog.get("prebuild_fixtures", False)):
        warnings.append("T10 catalog still declares prebuild_fixtures=true")
    if bool(t10_catalog.get("shipping_binding_required_after_t09", False)):
        warnings.append("T10 catalog still declares shipping_binding_required_after_t09=true")

    if mode == "final":
        if bool(t10_catalog.get("prebuild_fixtures", False)):
            errors.append("final reconciliation may not use a T10 catalog still marked prebuild_fixtures=true")
        if t11_catalog.get("final_t10_reconciliation_required") is not False:
            errors.append("final T11 catalog must clear final_t10_reconciliation_required after accepted reconciliation")
        for camp_state_id, row in t11_rows.items():
            if row.get("binding_status") == "t10_prebuild_fixture_unapproved":
                errors.append(f"final T11 recipe {camp_state_id} still has unapproved prebuild binding status")
            if bool(row.get("shipping", False)):
                provenance = row.get("price_source") or row.get("tuning_record")
                if not isinstance(provenance, str) or not provenance.strip():
                    errors.append(f"shipping T11 recipe {camp_state_id} lacks price/tuning provenance")

    return {
        "task_id": "T11",
        "mode": mode,
        "expected_t10_source": expected_t10_source or None,
        "t10_recipe_authority": t10_catalog.get("authority_id"),
        "required_t10_methods": list(REQUIRED_T10_METHODS),
        "binding_count": len(bindings),
        "bindings": bindings,
        "t11_local_cost_authority": False,
        "semantic_compatible": semantic_compatible,
        "final_reconciliation_passed": mode == "final" and not errors,
        "warnings": warnings,
        "errors": errors,
        "passed": not errors,
        "mutated": False,
        "task_approved": False,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--t11-catalog", default=str(DEFAULT_T11_CATALOG))
    ap.add_argument("--t10-catalog", default=str(DEFAULT_T10_CATALOG))
    ap.add_argument("--t10-script", default=str(DEFAULT_T10_SCRIPT))
    ap.add_argument("--t10-source", default="", help="Exact accepted T10 commit SHA for report binding")
    ap.add_argument("--mode", choices=("semantic", "final"), default="semantic")
    ap.add_argument("--output")
    args = ap.parse_args()

    t11_path = pathlib.Path(args.t11_catalog)
    t10_path = pathlib.Path(args.t10_catalog)
    script_path = pathlib.Path(args.t10_script)
    missing = [str(path) for path in (t11_path, t10_path, script_path) if not path.exists()]
    if missing:
        payload = {
            "task_id": "T11",
            "mode": args.mode,
            "passed": False,
            "errors": ["required reconciliation input unavailable: " + value for value in missing],
            "mutated": False,
            "task_approved": False,
        }
    else:
        try:
            payload = reconcile(
                load_json(t11_path),
                load_json(t10_path),
                script_path.read_text(),
                mode=args.mode,
                expected_t10_source=args.t10_source,
            )
        except Exception as exc:
            payload = {
                "task_id": "T11",
                "mode": args.mode,
                "passed": False,
                "errors": [f"reconciliation input error: {exc}"],
                "mutated": False,
                "task_approved": False,
            }

    text = json.dumps(payload, indent=2) + "\n"
    print(text, end="")
    if args.output:
        output = pathlib.Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text)
    raise SystemExit(0 if payload.get("passed") else 1)


if __name__ == "__main__":
    main()
