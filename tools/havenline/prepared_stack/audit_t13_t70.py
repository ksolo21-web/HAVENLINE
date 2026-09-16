#!/usr/bin/env python3
"""Cross-wave fail-closed audit for the prepared Havenline T13-T70 stack."""
from __future__ import annotations
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "Docs" / "Production"
TASKS = [f"T{i:02d}" for i in range(13, 71)]
BASE_ARTIFACTS = ("FROZEN_SCOPE.md", "TASK_PACKET.md", "PREBUILD_CONTRACT.json", "defect-ledger.json", "ACTIVATION_CHECKLIST.json")
EXTRA_C5 = {"T16", "T19", "T21", "T23"}
REGION_TASKS = {f"T{i:02d}" for i in range(44, 53)}
FINAL_ACCEPTANCE_TASKS = {f"T{i:02d}" for i in range(62, 71)}
MOTION_FINAL_TASKS = {"T59", "T60", "T61"}


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def blob_sha(path: pathlib.Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], cwd=ROOT, text=True).strip()


def prefix(pattern: str) -> str:
    cut = len(pattern)
    for token in ("*", "?", "["):
        pos = pattern.find(token)
        if pos >= 0:
            cut = min(cut, pos)
    return pattern[:cut].rstrip("/")


def overlap(a: str, b: str) -> bool:
    if a == b:
        return True
    pa, pb = prefix(a), prefix(b)
    if not pa or not pb:
        return True
    return pa == pb or pa.startswith(pb + "/") or pb.startswith(pa + "/")


def validate_t12_bindings(errors: list[str]) -> dict:
    contract_path = DOCS / "T12" / "DOWNSTREAM_CONSUMER_CONTRACT.json"
    contract = load(contract_path)
    current = blob_sha(contract_path)
    consumers = contract.get("consumers", {})
    results = {}

    individual = {
        "T13": DOCS / "T13" / "T12_CONSUMER_BINDING.json",
        "T14": DOCS / "T14" / "T12_CONSUMER_BINDING.json",
        "T32": DOCS / "T32" / "T12_CONSUMER_BINDING.json",
        "T62": DOCS / "T62" / "T12_CONSUMER_BINDING.json",
    }
    fields = {
        "T13": ("may_read", "must_not_require_from_T12", "boundary"),
        "T14": ("may_read", "must_not_require_from_T12", "boundary"),
        "T32": ("may_read", "owned_band", "owned_levels", "boundary"),
        "T62": ("may_read", "must_not_require_from_T12", "boundary"),
    }
    for tid, path in individual.items():
        if not path.exists():
            errors.append(f"{tid}: missing T12 consumer binding")
            continue
        binding = load(path)
        row = consumers.get(tid)
        local = []
        if binding.get("prepared_contract_git_blob_sha") != current:
            local.append("stale T12 contract blob binding")
        if row is None:
            local.append("consumer row missing from T12 contract")
        else:
            for key in fields[tid]:
                if binding.get(key) != row.get(key):
                    local.append(f"consumer field mismatch: {key}")
        errors.extend(f"{tid}: {x}" for x in local)
        results[tid] = {"passed": not local, "errors": local}

    region_path = DOCS / "T44_T52_T12_CONSUMER_BINDINGS.json"
    if not region_path.exists():
        errors.append("T44-T52: missing T12 region binding registry")
    else:
        registry = load(region_path)
        if registry.get("prepared_contract_git_blob_sha") != current:
            errors.append("T44-T52: stale T12 contract blob binding")
        bindings = registry.get("bindings", {})
        level_slots = []
        bands = []
        for tid in sorted(REGION_TASKS):
            row = consumers.get(tid)
            binding = bindings.get(tid)
            if row is None or binding is None:
                errors.append(f"{tid}: missing T12 region binding row")
                continue
            for key in ("owned_band", "owned_levels", "may_read", "boundary"):
                if binding.get(key) != row.get(key):
                    errors.append(f"{tid}: region consumer field mismatch: {key}")
            bands.append(binding.get("owned_band"))
            start, end = binding.get("owned_levels", [0, -1])
            level_slots.extend(range(start, end + 1))
        if len(bands) != len(set(bands)):
            errors.append("T44-T52: duplicate region band ownership")
        if sorted(level_slots) != list(range(11, 101)):
            errors.append("T44-T52: Levels 11-100 are not covered exactly once")
    return {"contract_blob_sha": current, "individual": results}


def main() -> int:
    errors: list[str] = []
    graph = load(DOCS / "DEPENDENCY_GRAPH.json")
    ownership = load(DOCS / "PATH_OWNERSHIP.json")
    gm = load(DOCS / "GAME_MASTER_POLICY.json")
    task_rows = graph.get("tasks", {})
    gm_flags = gm.get("task_policy", {}).get("required_proof_flags_by_task", {})
    active_owners = ownership.get("active_owners", [])
    aliases = ownership.get("aliases", {})
    task_results = []
    planned_paths: dict[str, list[str]] = {}

    for tid in TASKS:
        task_errors: list[str] = []
        d = DOCS / tid
        for name in BASE_ARTIFACTS:
            path = d / name
            if not path.exists() or not path.read_text(encoding="utf-8").strip():
                task_errors.append(f"missing/empty {name}")
        if task_errors:
            errors.extend(f"{tid}: {e}" for e in task_errors)
            task_results.append({"task_id": tid, "passed": False, "errors": task_errors})
            continue

        check = load(d / "ACTIVATION_CHECKLIST.json")
        prebuild = load(d / "PREBUILD_CONTRACT.json")
        defect = load(d / "defect-ledger.json")
        graph_row = task_rows.get(tid, {})
        if check.get("dependencies") != graph_row.get("dependencies"):
            task_errors.append("dependency mismatch vs graph")
        planned_critics = set(check.get("required_critics", []))
        graph_critics = set(graph_row.get("critics", []))
        if not graph_critics.issubset(planned_critics):
            task_errors.append(f"missing graph critics: {sorted(graph_critics - planned_critics)}")
        if tid in EXTRA_C5 and "C5" not in planned_critics:
            task_errors.append("C5 required by resource/tool/actor/animation overlay")
        if check.get("runtime_build_allowed_before_activation") is not False:
            task_errors.append("runtime build must remain disabled before activation")
        if check.get("runtime_status") != "LOCKED":
            task_errors.append(f"prepared runtime status must be LOCKED, got {check.get('runtime_status')}")
        if defect.get("unresolved_preparation_defects"):
            task_errors.append("unresolved preparation defects remain")

        required_gm = gm_flags.get(tid, [])
        supplied_gm = check.get("game_master_required_proof_flags", [])
        if supplied_gm != required_gm:
            task_errors.append(f"Game Master proof flags mismatch required={required_gm} supplied={supplied_gm}")
        if prebuild.get("game_master_required_proof_flags", []) != required_gm:
            if required_gm or prebuild.get("game_master_required_proof_flags"):
                task_errors.append("PREBUILD_CONTRACT Game Master proof flags mismatch")

        if tid in REGION_TASKS:
            if check.get("resource_actor_contract_required") is not True or prebuild.get("resource_actor_contract_required") is not True:
                task_errors.append("region resource/actor contract requirement missing")
            if prebuild.get("conditional_c5_on_animation_delta") is not True:
                task_errors.append("region conditional C5 rule missing")

        if tid == "T54" and (check.get("audio_playback_review_required") is not True or prebuild.get("audio_playback_review_required") is not True):
            task_errors.append("actual audio playback review requirement missing")
        if tid in MOTION_FINAL_TASKS:
            for key in ("full_motion_review_required", "tool_weapon_contact_compatibility_required", "feet_toes_knees_clipping_review_required", "protected_source_glb_change_requires_change_request"):
                if check.get(key) is not True or prebuild.get(key) is not True:
                    task_errors.append(f"motion acceptance requirement missing: {key}")
        if tid in FINAL_ACCEPTANCE_TASKS:
            if check.get("acceptance_only") is not True or prebuild.get("acceptance_only") is not True:
                task_errors.append("final-wave task must be acceptance-only")
            if check.get("production_patch_forbidden_during_acceptance") is not True or prebuild.get("production_patch_forbidden_during_acceptance") is not True:
                task_errors.append("production patch prohibition missing")
        if tid == "T63" and check.get("game_master_excluded_from_population") is not True:
            task_errors.append("T63 must exclude Game Master population")
        if tid in ("T68", "T69"):
            for key, value in (("physical_device_only", True), ("native_internal_min_width", 3840), ("native_internal_min_height", 2160), ("sustained_min_fps", 60), ("completed_game_load_required", True), ("emulator_software_renderer_cannot_certify", True)):
                if check.get(key) != value or prebuild.get(key) != value:
                    task_errors.append(f"physical certification rule mismatch: {key}")
        if tid == "T70":
            if check.get("owner_slot_count_required") != 2 or prebuild.get("owner_slot_count_required") != 2:
                task_errors.append("T70 must require exactly two Game Master owner slots")
            if check.get("physical_certifications_must_match_release_candidate") is not True:
                task_errors.append("T70 exact-candidate physical certification binding missing")

        paths = check.get("planned_owned_paths", [])
        if not paths or len(paths) != len(set(paths)):
            task_errors.append("planned owned paths empty or duplicated")
        planned_paths[tid] = paths
        for candidate in paths:
            for protected in aliases.get("@integration-only", []):
                if overlap(candidate, protected):
                    task_errors.append(f"planned path overlaps integration-only: {candidate} vs {protected}")
            for owner in active_owners:
                for foreign in aliases.get(owner.get("paths_alias"), []):
                    if overlap(candidate, foreign):
                        task_errors.append(f"planned path overlaps active {owner.get('task_id')}: {candidate} vs {foreign}")

        errors.extend(f"{tid}: {e}" for e in task_errors)
        task_results.append({"task_id": tid, "passed": not task_errors, "errors": task_errors})

    cross_collisions = []
    for i, a in enumerate(TASKS):
        for b in TASKS[i + 1:]:
            for pa in planned_paths.get(a, []):
                for pb in planned_paths.get(b, []):
                    if overlap(pa, pb):
                        cross_collisions.append({"task_a": a, "path_a": pa, "task_b": b, "path_b": pb})
    if cross_collisions:
        errors.append(f"cross-task planned path collisions: {len(cross_collisions)}")

    t12 = validate_t12_bindings(errors)

    approved = {tid for tid, row in task_rows.items() if row.get("status") == "APPROVED"}
    ready_now = []
    for tid in TASKS:
        row = task_rows.get(tid, {})
        if row.get("status") in ("LOCKED", "PREPARED") and all(dep in approved for dep in row.get("dependencies", [])):
            ready_now.append(tid)

    out = {
        "scope": "T13-T70 prepared stack",
        "task_count": len(TASKS),
        "task_results": task_results,
        "cross_task_path_collisions": cross_collisions,
        "t12_consumer_bindings": t12,
        "ready_now_from_graph_only": ready_now,
        "passed": not errors,
        "errors": errors,
    }
    print(json.dumps(out, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
