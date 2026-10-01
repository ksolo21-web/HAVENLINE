#!/usr/bin/env python3
"""Materialize T12 shipping-shaped data from frozen non-shipping preparation.

Default behavior is a dry run for the level/milestone topology. Shipping writes
are fail-closed until T12 is claimed on the activation base, T10/T11 binding
proof is resolved, and a fully dispositioned 99-slot binding index is supplied.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import subprocess
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[3]
TASK = ROOT / "tools" / "havenline" / "task12"
DOCS = ROOT / "Docs" / "Production"
DEFAULT_BLUEPRINT = DOCS / "T12" / "AUTHORING_BLUEPRINT.json"
DEFAULT_BINDING_RESOLUTION = DOCS / "T12" / "BINDING_RESOLUTION.json"
DEFAULT_BINDING_CATALOG = DOCS / "T12" / "BINDING_SLOT_CATALOG.json"
LEVELS_OUT = ROOT / "HavenlineGodot" / "data" / "progression_levels_v1.json"
MILESTONES_OUT = ROOT / "HavenlineGodot" / "data" / "progression_milestones_v1.json"
BINDINGS_OUT = ROOT / "HavenlineGodot" / "data" / "progression_bindings_v1.json"
EXPECTED_BRANCH = "havenline/T12-progression-architecture"
EXPECTED_OWNER = "progression-architecture-builder"
ALLOWED_BUILD_STATES = {"ASSIGNED", "BUILDING_ISOLATED", "IN_REVIEW"}

def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, TASK / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

progression_validator = _load_module("t12_progression_validator", "validate_progression_contract.py")
binding_verifier = _load_module("t12_binding_verifier", "verify_binding_resolution.py")
binding_index_validator = _load_module("t12_binding_index_validator", "validate_fact_slot_binding_index.py")

def resolve_input_path(value: str | pathlib.Path) -> pathlib.Path:
    path = pathlib.Path(value)
    return path if path.is_absolute() else ROOT / path

def load_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text())

def materialize(blueprint: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if blueprint.get("schema_version") != 1 or blueprint.get("task_id") != "T12":
        raise ValueError("authoring blueprint identity must be schema_version=1 task_id=T12")
    if blueprint.get("status") != "PREPARATION_ONLY_AUTHORING_BLUEPRINT":
        raise ValueError("authoring blueprint status drifted")
    if blueprint.get("shipping_path_forbidden") is not True:
        raise ValueError("authoring blueprint must remain non-shipping")

    rows = blueprint.get("levels")
    milestones = blueprint.get("milestones")
    if not isinstance(rows, list) or not isinstance(milestones, list):
        raise ValueError("authoring blueprint levels/milestones must be lists")

    levels: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("authoring blueprint level row must be object")
        levels.append({
            "level": row["level"],
            "level_id": row["level_id"],
            "region_band_id": row["region_band_id"],
            "prerequisite_level_ids": list(row["prerequisite_level_ids"]),
            "required_fact_ids": list(row["materialized_required_fact_ids"]),
            "progression_effects": [dict(row["progression_effect_template"])],
            "visible_progression_hook_ids": list(row["visible_progression_hook_ids"]),
            "milestone_ids": list(row["milestone_ids"]),
            "one_time_event_ids": list(row["one_time_event_ids"]),
        })

    milestone_rows = [dict(row) for row in milestones]
    levels_doc = {"schema_version": 1, "task_id": "T12", "levels": levels}
    milestones_doc = {"schema_version": 1, "task_id": "T12", "milestones": milestone_rows}
    combined = {
        "schema_version": 1,
        "task_id": "T12",
        "levels": levels,
        "milestones": milestone_rows,
    }
    return levels_doc, milestones_doc, combined

def materialize_bindings(
    resolved_index: dict[str, Any],
    catalog: dict[str, Any],
) -> dict[str, Any]:
    resolved = binding_index_validator.validate(
        resolved_index,
        catalog,
        require_resolved=True,
    )
    if not resolved["passed"]:
        raise ValueError("resolved binding index invalid: " + json.dumps(resolved["errors"]))
    document = {
        "schema_version": 1,
        "task_id": "T12",
        "bindings": [dict(row["resolved_binding"]) for row in resolved_index["entries"]],
    }
    shipping = binding_index_validator.validate_shipping(document, catalog)
    if not shipping["passed"]:
        raise ValueError("shipping binding document invalid: " + json.dumps(shipping["errors"]))
    return document

def validate_materialized(blueprint: dict[str, Any]) -> dict[str, Any]:
    levels_doc, milestones_doc, combined = materialize(blueprint)
    result = progression_validator.validate_manifest(combined)
    return {
        "passed": result["passed"],
        "level_count": len(levels_doc["levels"]),
        "milestone_count": len(milestones_doc["milestones"]),
        "progression_validation": result,
    }

def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()

def validate_shipping_bindings_against_resolution(
    binding_doc: dict[str, Any],
    resolution: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    deps = resolution.get("dependencies")
    if not isinstance(deps, dict):
        return ["BINDING_RESOLUTION dependencies must be an object"]
    accepted: dict[str, dict[str, str]] = {}
    for task in ("T10", "T11"):
        row = deps.get(task)
        ids = row.get("resolved_public_ids") if isinstance(row, dict) else None
        if not isinstance(ids, list):
            errors.append(f"BINDING_RESOLUTION {task} resolved_public_ids must be a list")
            accepted[task] = {}
            continue
        accepted[task] = {
            item.get("id"): item.get("kind")
            for item in ids
            if isinstance(item, dict)
            and isinstance(item.get("id"), str)
            and item.get("id")
            and isinstance(item.get("kind"), str)
            and item.get("kind")
        }
    compatibility = (
        resolution.get("fact_kind_compatibility", {})
        if isinstance(resolution.get("fact_kind_compatibility"), dict)
        else {}
    )
    rows = binding_doc.get("bindings")
    if not isinstance(rows, list):
        return errors + ["shipping binding document bindings must be a list"]
    for row in rows:
        if not isinstance(row, dict) or row.get("resolution_state") != "RESOLVED":
            continue
        task = row.get("source_task")
        if task not in ("T10", "T11"):
            continue
        source_id = row.get("source_id")
        fact_kind = row.get("fact_kind")
        accepted_kind = accepted.get(task, {}).get(source_id)
        if accepted_kind is None:
            errors.append(
                f"shipping binding dataset uses {task} source IDs absent from BINDING_RESOLUTION: {[source_id]}"
            )
            continue
        fact_contract = compatibility.get(fact_kind)
        expected_task = fact_contract.get("source_task") if isinstance(fact_contract, dict) else None
        allowed_kinds = (
            set(fact_contract.get("accepted_id_kinds", []))
            if isinstance(fact_contract, dict)
            else set()
        )
        if expected_task != task or accepted_kind not in allowed_kinds:
            errors.append(
                f"shipping binding {row.get('slot_id')} uses {task} ID {source_id!r} "
                f"with accepted kind {accepted_kind!r}, incompatible with fact_kind {fact_kind!r}"
            )
    return errors


def validate_write_authority(
    activation_base: str,
    registry: dict[str, Any],
    ownership: dict[str, Any],
    resolution: dict[str, Any],
    *,
    root: pathlib.Path = ROOT,
) -> list[str]:
    errors: list[str] = []
    workstream = next(
        (row for row in registry.get("workstreams", []) if row.get("task_id") == "T12"),
        None,
    )
    if not isinstance(workstream, dict):
        errors.append("T12 workstream is not claimed")
    else:
        if workstream.get("status") not in ALLOWED_BUILD_STATES:
            errors.append(f"T12 workstream status is not build-authorized: {workstream.get('status')}")
        if workstream.get("owner") != EXPECTED_OWNER:
            errors.append("T12 workstream owner mismatch")
        if workstream.get("branch") != EXPECTED_BRANCH:
            errors.append("T12 builder branch mismatch")
        if workstream.get("base_commit") != activation_base:
            errors.append("T12 workstream base_commit does not match activation base")
        if "@reservation:T12" not in workstream.get("owned_paths", []):
            errors.append("T12 workstream does not own @reservation:T12")

    active = [
        row for row in ownership.get("active_owners", [])
        if row.get("task_id") == "T12"
    ]
    if len(active) != 1:
        errors.append("PATH_OWNERSHIP must contain exactly one active T12 owner")
    elif active[0].get("paths_alias") != "@reservation:T12":
        errors.append("active T12 owner is not bound to @reservation:T12")

    binding = binding_verifier.validate_resolution(
        resolution,
        require_resolved=True,
        root=root,
        activation_head=activation_base,
    )
    if not binding.get("passed"):
        errors.append("resolved binding proof failed: " + json.dumps(binding.get("errors", [])))
    return errors

def validate_actual_builder_branch(actual_branch: str) -> list[str]:
    if actual_branch != EXPECTED_BRANCH:
        return [
            f"shipping materialization must run on {EXPECTED_BRANCH}; actual branch is {actual_branch!r}"
        ]
    return []


def repository_write_authority_errors(
    activation_base: str,
    resolution_path: pathlib.Path,
    binding_doc: dict[str, Any] | None = None,
) -> list[str]:
    errors: list[str] = []
    try:
        actual_branch = _git("branch", "--show-current")
        errors.extend(validate_actual_builder_branch(actual_branch))
        head = _git("rev-parse", "HEAD")
        lineage = subprocess.run(
            ["git", "merge-base", "--is-ancestor", activation_base, head],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if lineage.returncode != 0:
            errors.append("activation base is not an ancestor of current HEAD")
    except Exception as exc:
        errors.append(f"git lineage proof failed: {exc}")

    if not resolution_path.is_file():
        errors.append(f"binding resolution is missing: {resolution_path.relative_to(ROOT)}")
        return errors

    try:
        registry = load_json(DOCS / "WORKSTREAM_REGISTRY.json")
        ownership = load_json(DOCS / "PATH_OWNERSHIP.json")
        resolution = load_json(resolution_path)
        errors.extend(
            validate_write_authority(
                activation_base,
                registry,
                ownership,
                resolution,
            )
        )
        if binding_doc is not None:
            errors.extend(validate_shipping_bindings_against_resolution(binding_doc, resolution))
    except Exception as exc:
        errors.append(f"write authority proof failed: {exc}")

    if LEVELS_OUT.exists() or MILESTONES_OUT.exists() or BINDINGS_OUT.exists():
        errors.append("shipping progression files already exist; materializer never overwrites them")
    return errors

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--blueprint", default=str(DEFAULT_BLUEPRINT.relative_to(ROOT)))
    ap.add_argument("--write-shipping", action="store_true")
    ap.add_argument("--activation-base")
    ap.add_argument("--binding-resolution", default=str(DEFAULT_BINDING_RESOLUTION.relative_to(ROOT)))
    ap.add_argument("--binding-index", help="Resolved 99-slot binding index; required for --write-shipping")
    ap.add_argument("--binding-catalog", default=str(DEFAULT_BINDING_CATALOG.relative_to(ROOT)))
    args = ap.parse_args()

    blueprint = load_json(resolve_input_path(args.blueprint))
    levels_doc, milestones_doc, combined = materialize(blueprint)
    validation = progression_validator.validate_manifest(combined)
    result: dict[str, Any] = {
        "task_id": "T12",
        "mode": "write_shipping" if args.write_shipping else "dry_run",
        "level_count": len(levels_doc["levels"]),
        "milestone_count": len(milestones_doc["milestones"]),
        "progression_validation_passed": validation["passed"],
        "binding_document_validation_passed": None,
        "errors": list(validation["errors"]),
        "shipping_files_written": False,
    }

    binding_doc = None
    if args.binding_index:
        try:
            binding_doc = materialize_bindings(
                load_json(resolve_input_path(args.binding_index)),
                load_json(resolve_input_path(args.binding_catalog)),
            )
            result["binding_document_validation_passed"] = True
        except Exception as exc:
            result["binding_document_validation_passed"] = False
            result["errors"].append(str(exc))

    if args.write_shipping:
        if not args.activation_base:
            result["errors"].append("--write-shipping requires --activation-base")
        if not args.binding_index:
            result["errors"].append("--write-shipping requires --binding-index")
        if args.activation_base:
            result["errors"].extend(
                repository_write_authority_errors(
                    args.activation_base,
                    resolve_input_path(args.binding_resolution),
                    binding_doc,
                )
            )
        if not result["errors"] and binding_doc is not None:
            LEVELS_OUT.parent.mkdir(parents=True, exist_ok=True)
            LEVELS_OUT.write_text(json.dumps(levels_doc, indent=2) + "\n")
            MILESTONES_OUT.write_text(json.dumps(milestones_doc, indent=2) + "\n")
            BINDINGS_OUT.write_text(json.dumps(binding_doc, indent=2) + "\n")
            result["shipping_files_written"] = True

    result["passed"] = not result["errors"]
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
