#!/usr/bin/env python3
"""Project forward planning requirements; never certify gameplay or activate tasks."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = "Docs/Production/"
PACKAGE = DOCS + "GameplayDepth/2026-11-27/"
BASE = "9d10c45a8bd46aeb6ab1b4009e87538c4796ef1c"
LATEST_SOURCE = "3fad812b384335bd8ca9b5e47dc9d9557110eb4a"
TASKS = [f"T{i:02}" for i in range(1, 71)]
UNDEFINED = [f"T{i:02}" for i in range(71, 81)]
PETS = {"guardian_dog", "gray_wolf", "fox", "owl", "male_lion", "white_tiger", "brown_bear"}
HUMAN_FAMILIES = {"harvest_and_extract", "mixed_cargo_and_storage", "process_and_restock",
                  "service_and_cash_collection", "plot_purchase_and_upgrade", "construction_repair_and_recovery",
                  "defense_and_resupply", "rescue_escort_and_care", "transport_and_region_logistics", "scout_and_coordinate"}
MOTION_FAMILIES = {"human_locomotion", "human_work_actions", "cargo_and_transactions", "human_rescue_and_care",
                   "human_combat", "animal_motion_and_jobs", "owl_aerial", "production_equipment",
                   "conveyor_storage_service", "defensive_structures", "enemy_archetypes", "environment_and_feedback"}
# This dated audit has a fixed source universe; do not let omission yield a smaller passing audit.
SOURCE_UNIVERSE_SHA256 = "cdb6e04b85d2630fb72cf7812e7e9a330194c5de559ec642dd485f6e690ea066"


def read(root, relative):
    return json.loads((pathlib.Path(root) / relative).read_text(encoding="utf-8"))


def load(root=ROOT):
    return (read(root, DOCS + "GAMEPLAY_DEPTH_CONTRACT.json"),
            read(root, PACKAGE + "ACTORS_MOTION_REQUIREMENTS.json"),
            read(root, PACKAGE + "RESOURCE_VALUE_LEDGER.json"))


def source_bytes(root, commit, path):
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=root, stderr=subprocess.PIPE)


def validate_data(contract, actors, ledger):
    """Pure checks used by the CLI and negative integrity probes."""
    errors = []
    if contract.get("base_commit") != BASE or actors.get("base_commit") != BASE or ledger.get("pins", {}).get("plan") != BASE:
        errors.append("plan source pin changed")
    if contract.get("task_ids") != TASKS or contract.get("undefined_requested_task_ids") != UNDEFINED:
        errors.append("70 defined / 10 undefined task boundary changed")
    if contract.get("runtime_approval_allowed") is not False or contract.get("game_score") is not None:
        errors.append("planning contract must not approve or score gameplay")
    if actors.get("runtime_approval_allowed") is not False or actors.get("runtime_score") is not None:
        errors.append("actor audit must not approve or score gameplay")
    if ledger.get("boundaries", {}).get("playtest_claimed") is not False or ledger.get("boundaries", {}).get("proposed_design_approved") is not False:
        errors.append("resource audit cannot claim a playtest or approved proposed design")
    requirements = contract.get("requirements", [])
    if [x.get("id") for x in requirements] != [f"GD{i:02}" for i in range(1, 19)]:
        errors.append("18 distinct requirement IDs required")
    for row in requirements:
        ids = row.get("owner_tasks", []) + row.get("consumer_tasks", [])
        if not row.get("owner_tasks") or not set(ids) <= set(TASKS):
            errors.append(f"{row.get('id')}: missing owner or undefined task")
        if not row.get("required_evidence") or not row.get("obligation") or not row.get("origin"):
            errors.append(f"{row.get('id')}: incomplete requirement")
        if row.get("implementation_state") != "NOT_CERTIFIED_BY_THIS_PLAN_AUDIT":
            errors.append(f"{row.get('id')}: unsupported implementation certification")
    decisions = contract.get("design_decisions", [])
    if [x.get("id") for x in decisions] != [f"D{i:02}" for i in range(1, 6)]:
        errors.append("all five unresolved design decisions required")
    for row in decisions:
        if row.get("status") != "RECOMMENDED_PENDING_OWNER_FREEZE_AND_PLAYTEST":
            errors.append(f"{row.get('id')}: proposed tuning incorrectly approved")
        if not row.get("recommendation") or not row.get("must_freeze") or not row.get("owners") or not set(row.get("owners", [])) <= set(TASKS):
            errors.append(f"{row.get('id')}: incomplete decision contract")
    expected = {"canonical_registry": 6, "foundation_raw_inventory": 6,
                "foundation_processed_inventory": 3, "base_render_sheets": 13,
                "expansion_render_sheets": 20}
    for key, count in expected.items():
        rows = ledger.get(key, [])
        if len(rows) != count or len({x.get("id") for x in rows}) != count:
            errors.append(f"{key}: incomplete or duplicate inventory")
    for key, ids in {"canonical_registry": {"wood", "stone", "metal", "fuel", "fish", "wheat"},
                     "foundation_raw_inventory": {"wood", "stone", "meat", "coal", "slate", "metal"},
                     "foundation_processed_inventory": {"planks", "blocks", "meal"}}.items():
        if {x.get("id") for x in ledger.get(key, [])} != ids:
            errors.append(key + ": source identities changed")
    for key in ("foundation_raw_inventory", "foundation_processed_inventory"):
        for row in ledger.get(key, []):
            if not row.get("source_sink_status") or not row.get("proposal"):
                errors.append(f"{key}/{row.get('id')}: missing purpose/gap disposition")
    for key in ("base_render_sheets", "expansion_render_sheets"):
        for row in ledger.get(key, []):
            if row.get("runtime_approval_claimed") is not False or row.get("historical_score_is_current_approval") is not False:
                errors.append(f"{row.get('id')}: concept art cannot approve runtime")
            if len(row.get("render_sha256", "")) != 64 or not row.get("render_filename"):
                errors.append(f"{row.get('id')}: missing render identity")
    pets = actors.get("pet_roles", [])
    if len(pets) != 7 or {x.get("actor_id") for x in pets} != PETS:
        errors.append("seven distinct companions required")
    for pet in pets:
        if not pet.get("recommended_distinct_use") or not pet.get("recommended_play_scenario") or pet.get("runtime_evidence_state") != "UNVERIFIED":
            errors.append(f"{pet.get('actor_id')}: incomplete or falsely verified pet role")
    for key, ids, fields in [("human_task_families", HUMAN_FAMILIES, ["requirement"]),
                             ("animation_coverage_families", MOTION_FAMILIES, ["required_use_states", "proof_requirement"]),
                             ("ai_requirements", {f"AI{i:02}" for i in range(1, 15)}, ["requirement"])]:
        rows = actors.get(key, [])
        if len(rows) != len(ids) or {x.get("id") for x in rows} != ids:
            errors.append(key + ": specific identities/unique coverage incomplete")
        for row in rows:
            if any(not row.get(f) for f in fields) or row.get("runtime_evidence_state") != "UNVERIFIED":
                errors.append(f"{row.get('id')}: missing proof/behavior or false runtime state")
    if not set(actors.get("task_mapping", {})) <= set(TASKS):
        errors.append("actor routing includes an undefined task")
    scenarios = actors.get("acceptance_scenarios", [])
    if len(scenarios) != 12 or {x.get("id") for x in scenarios} != {f"AC{i:02}" for i in range(1, 13)} or any(x.get("status") != "NOT_RUN_AGAINST_ACTUAL_GAME" or not x.get("required_demonstration") for x in scenarios):
        errors.append("future gameplay scenarios must remain explicitly not run")
    return errors


def task_row(task_id, root=ROOT):
    task_id = task_id.upper()
    if task_id not in TASKS:
        raise ValueError(f"{task_id} has no defined gameplay-depth task")
    contract, actors, _ = load(root)
    graph = read(root, DOCS + "DEPENDENCY_GRAPH.json")["tasks"]
    selected = [r for r in contract["requirements"] if task_id in r["owner_tasks"] + r["consumer_tasks"]]
    return {"task_id": task_id, "name": graph[task_id]["name"],
            "dependencies_preserved": graph[task_id]["dependencies"],
            "requirements": [{**r, "role": "owner" if task_id in r["owner_tasks"] else "consumer"} for r in selected],
            "actor_motion_details": actors["task_mapping"].get(task_id, []),
            "decisions_owned": [d for d in contract["design_decisions"] if task_id in d["owners"]],
            "runtime_activation_allowed_by_this_addendum": False,
            "runtime_approval_allowed": False}


def validate_current_source(note):
    errors = []
    if note.get("observed_head") != LATEST_SOURCE or note.get("source_only") is not True:
        errors.append("newer source identity/scope changed")
    if any(note.get(k) is not False for k in ("runtime_tested", "runtime_approved", "balance_approved", "animation_approved")):
        errors.append("newer source note cannot certify gameplay or animation")
    census = note.get("current_identifier_census", {})
    for key, ids in {"raw_items": {"wood", "stone", "meat", "coal", "slate", "metal"},
                     "processed_item_ids": {"planks", "blocks", "meal"},
                     "goods_transfer_ids": {"planks", "blocks", "meal", "money"},
                     "goods_pack_ids": {"planks", "blocks", "meal", "money"},
                     "earned_currency_ids": {"money"}}.items():
        values = census.get(key, [])
        if len(values) != len(ids) or set(values) != ids:
            errors.append("newer source census incomplete: " + key)
    locations = census.get("cash_custody_locations", [])
    if len(locations) != 3 or {x.get("id") for x in locations} != {"till_balance()", "pocket_cash", "house_cash"} or census.get("cash_locations_are_separate_currencies") is not False:
        errors.append("cash custody must not create extra currencies")
    if len(note.get("source_hashes", [])) != 14:
        errors.append("newer source hash coverage incomplete")
    if not note.get("supersedes_historical_interpretation"):
        errors.append("newer source must identify superseded historical observations")
    return errors


def task_section(task_id, root=ROOT):
    row = task_row(task_id, root)
    text = "\n## Whole-game stakes, useful companions and resource value\n\n"
    text += "Forward requirements: `Docs/Production/GAMEPLAY_DEPTH_STANDARD.md` and `GAMEPLAY_DEPTH_CONTRACT.json`. "
    text += "This addendum does not reopen frozen historical scope, change dependencies/ownership, activate a task, or certify runtime behavior. "
    text += "Use the existing scope/change process for a changed approved component. Owner/consumer labels are responsibilities, not new dependency edges.\n\n"
    if not row["requirements"] and not row["actor_motion_details"]:
        return text + "No additional feature requirement is assigned to this task. Preserve its existing reference, render and acceptance obligations.\n"
    for req in row["requirements"]:
        text += f"- **{req['id']} — {req['title']} ({req['role']})**: {req['obligation']} Evidence: {'; '.join(req['required_evidence'])}.\n"
    if row["actor_motion_details"]:
        text += "\nTask-specific actor/motion details:\n\n" + "\n".join("- " + x for x in row["actor_motion_details"]) + "\n"
    if row["decisions_owned"]:
        text += "\nUnfrozen design decisions for this owner:\n\n"
        for decision in row["decisions_owned"]:
            text += f"- {decision['id']} — {decision['title']}: {decision['status']}. Freeze {'; '.join(decision['must_freeze'])}.\n"
    text += "\nUse the complete source-bound resource ledger and actor scenarios under `Docs/Production/GameplayDepth/2026-11-27/`. "
    text += "The introducing task freezes a useful resource contract before its own integration; T33 later reconciles it. Each pet proves standalone usefulness before T31 integration. "
    text += "All future play scenarios remain untested by this planning audit. Preserve the existing >=9.9 and stronger exact-10 reference rules.\n"
    return text


def crosswalk(root=ROOT):
    return {"schema_version": 1, "base_commit": BASE, "runtime_approval_allowed": False,
            "dependency_rule": "Responsibilities only; all existing dependencies and states preserved.",
            "rows": [task_row(t, root) for t in TASKS] + [
                {"task_id": t, "status": "SOURCE_NOT_FOUND", "requirements": [],
                 "runtime_activation_allowed_by_this_addendum": False, "runtime_approval_allowed": False} for t in UNDEFINED]}


def crosswalk_markdown(root=ROOT):
    lines = ["# Havenline T01–T80 gameplay-depth responsibility crosswalk", "",
             "Generated from the current 18-requirement contract and detailed actor requirements. All 70 real task definitions and their dependency lists are preserved; T71–T80 remain undefined. This crosswalk is a planning addendum, not an implementation, readiness or approval record.", "",
             "Read the [standard](../../GAMEPLAY_DEPTH_STANDARD.md), [source audit](README.md), [contract](../../GAMEPLAY_DEPTH_CONTRACT.json), and [reference/render crosswalk](../../ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md). A task owner resolves its own contract before integration; later T31/T33 integrations do not create backward dependencies.", ""]
    for row in crosswalk(root)["rows"]:
        task = row["task_id"]
        lines += [f"## {task}", ""]
        if row.get("status") == "SOURCE_NOT_FOUND":
            lines += ["**SOURCE_NOT_FOUND.** No name, runtime scope, dependency, owner or acceptance is invented.", ""]
            continue
        lines += [f"**{row['name']}**", "", "Existing required dependencies: " + (", ".join(row["dependencies_preserved"]) or "none") + ".", "",
                  task_section(task, root).split("\n", 2)[2]]
    return "\n".join(lines) + "\n"


def validate(root=ROOT):
    contract, actors, ledger = load(root)
    errors = validate_data(contract, actors, ledger)
    current = read(root, PACKAGE + "CURRENT_BRANCH_NOTE.json")
    errors.extend(validate_current_source(current))
    sources = read(root, PACKAGE + "SOURCE_BINDINGS.json")["sources"]
    identity = "\n".join(sorted(x["commit"] + ":" + x["path"] for x in sources)).encode()
    if hashlib.sha256(identity).hexdigest() != SOURCE_UNIVERSE_SHA256:
        errors.append("required source universe is incomplete, duplicated or changed")
    verified = 0
    for row in sources:
        try:
            content = source_bytes(root, row["commit"], row["path"])
            if hashlib.sha256(content).hexdigest() != row["sha256"] or len(content) != row["bytes"]:
                errors.append(f"source identity mismatch: {row['path']}")
            else:
                verified += 1
        except subprocess.CalledProcessError:
            errors.append(f"source unavailable: {row['commit']}:{row['path']}")
    try:
        registry = json.loads(source_bytes(root, BASE, DOCS + "RESOURCE_ACTION_REGISTRY.json"))["resources"]
        matrix = json.loads(source_bytes(root, BASE, DOCS + "ACTOR_CAPABILITY_MATRIX.json"))["actors"]
        if set(registry) != {x["id"] for x in ledger["canonical_registry"]}:
            errors.append("canonical registry identity mismatch")
        for pet in actors["pet_roles"]:
            if pet["actor_id"] not in matrix:
                errors.append("unknown companion " + pet["actor_id"])
        for key, manifest_key in [("base_render_sheets", "selected"), ("expansion_render_sheets", "sheets")]:
            first = ledger[key][0]["source"]
            manifest = json.loads(source_bytes(root, first["commit"], first["path"]))
            expected = {x["asset"]: x["sha256"] for x in manifest[manifest_key]}
            actual = {x["id"]: x["render_sha256"] for x in ledger[key]}
            if expected != actual:
                errors.append(key + ": render source identity mismatch")
        graph = read(root, DOCS + "DEPENDENCY_GRAPH.json")["tasks"]
        if set(graph) != set(TASKS):
            errors.append("task graph identity mismatch")
        expected = crosswalk(root)
        if read(root, PACKAGE + "TASK_GAMEPLAY_DEPTH_T01_T80.json") != expected:
            errors.append("saved task crosswalk is stale")
        if (pathlib.Path(root) / PACKAGE / "TASK_GAMEPLAY_DEPTH_T01_T80.md").read_text() != crosswalk_markdown(root):
            errors.append("saved readable task crosswalk is stale")
        for rel in contract["detail_documents"].values():
            if not (pathlib.Path(root) / rel).is_file():
                errors.append("missing detailed contract: " + rel)
    except (KeyError, ValueError, OSError, subprocess.CalledProcessError) as exc:
        errors.append("source reconciliation failed: " + str(exc))
    return {"passed": not errors, "scope": "Planning source identity, inventory coverage and task projection only",
            "runtime_approval_allowed": False, "game_score": None, "runtime_tested": False,
            "sources_verified": verified, "sources_required": len(sources),
            "latest_source_snapshot": current["observed_head"],
            "latest_source_runtime_tested": False,
            "defined_tasks": len(TASKS), "undefined_requested_tasks": len(UNDEFINED),
            "requirements": len(contract["requirements"]), "resource_render_concepts": 33,
            "companion_species": 7, "errors": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check", "task", "crosswalk", "crosswalk-markdown"])
    parser.add_argument("task_id", nargs="?")
    args = parser.parse_args()
    if args.command == "task":
        if not args.task_id:
            parser.error("task requires a defined T01-T70 ID")
        print(task_section(args.task_id))
    elif args.command == "crosswalk":
        print(json.dumps(crosswalk(), indent=2))
    elif args.command == "crosswalk-markdown":
        print(crosswalk_markdown(), end="")
    else:
        result = validate()
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
