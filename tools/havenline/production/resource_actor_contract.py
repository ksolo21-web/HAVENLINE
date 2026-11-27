#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[3]
DOCS = ROOT / "Docs" / "Production"

RESOURCE_FILE = DOCS / "RESOURCE_ACTION_REGISTRY.json"
ACTOR_FILE = DOCS / "ACTOR_CAPABILITY_MATRIX.json"
ANIMATION_FILE = DOCS / "ANIMATION_ACTION_MATRIX.json"
CRITIC_FILE = DOCS / "CRITIC_MATRIX.json"
GRAPH_FILE = DOCS / "DEPENDENCY_GRAPH.json"

# User-required roster. Removing a registry row or weakening its own task lists
# must not silently turn a combat companion into a support-only animal.
PET_ATTACKS = {
    "guardian_dog": ("T24", "animal_dog", "attack", "dog_attack"),
    "gray_wolf": ("T25", "animal_wolf", "attack", "wolf_attack"),
    "fox": ("T26", "animal_fox", "attack", "fox_attack"),
    "owl": ("T27", "animal_owl", "aerial_attack", "owl_attack"),
    "male_lion": ("T28", "animal_lion", "attack", "lion_attack"),
    "white_tiger": ("T29", "animal_tiger", "attack", "tiger_attack"),
    "brown_bear": ("T30", "animal_bear", "attack", "bear_attack"),
}
PET_INTEGRATION_TASKS = {"T31", "T32", "T62", "T67", "T70"}
REGION_TASKS = {f"T{n}" for n in range(44, 53)}
SURVIVOR_PROFILE_TASKS = {"T23", *PET_INTEGRATION_TASKS, *REGION_TASKS}
FULL_RESOURCE_TASKS = {"T62", "T67", "T70"}
SURVIVOR_DEFERRED_PROFILE = "T23_FREEZE_REQUIRED"
RESOURCE_PROFILE_ACTORS = {
    "player_animation_profile": "player_lead",
    "helper_animation_profile": "core_human_companion",
    "survivor_animation_profile": "rescued_survivor_helper",
}
RESOURCE_METHOD_ACTIONS = {
    "chop": "gather_wood", "mine": "mine", "dismantle": "dismantle",
    "fishing": "fishing", "crop_harvest": "crop_harvest",
}
VALIDATION_KIND = "DECLARED_RESOURCE_ACTOR_COVERAGE"

def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))

def sha256_file(path: pathlib.Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def contains_placeholder(value, tokens):
    if isinstance(value, str):
        # Task-owned placeholders remain placeholders even when a token was
        # accidentally omitted from the configurable list (notably T23).
        return (any(token in value for token in tokens) or "UNRESOLVED" in value or
                re.search(r"(?:T\d{2}|TASK)_FREEZE_REQUIRED\b", value) is not None)
    if isinstance(value, list):
        return any(contains_placeholder(v, tokens) for v in value)
    if isinstance(value, dict):
        return any(contains_placeholder(v, tokens) for v in value.values())
    return False

def resource_phase_view(row, *, defer_survivor):
    """Only the exact future T23 survivor field may be deferred.

    T09/T16/T19 author acquisition before T23; no backward task dependency is
    introduced. A different owner, another field, or an unknown profile is not
    a valid deferral. T23 and integrated survivor scopes must resolve it.
    """
    return {key: value for key, value in row.items()
            if not (defer_survivor and key == "survivor_animation_profile" and
                    value == SURVIVOR_DEFERRED_PROFILE)}

def validate_pet_attacks(actors, animations):
    errors = []
    profiles = animations.get("profiles", {})
    for actor_key, (task, actor_class, capability, profile_id) in PET_ATTACKS.items():
        row = actors.get("actors", {}).get(actor_key)
        if not isinstance(row, dict):
            errors.append(f"required pet {actor_key} is missing")
            continue
        if row.get("attack_allowed") is not True:
            errors.append(f"required pet {actor_key} must retain attack_allowed=true")
        if row.get("actor_class") != actor_class:
            errors.append(f"required pet {actor_key} has wrong species class")
        capabilities = row.get("capabilities")
        if not isinstance(capabilities, list) or any(not isinstance(item, str) for item in capabilities):
            errors.append(f"required pet {actor_key} has invalid capabilities list")
        elif capability not in capabilities:
            errors.append(f"required pet {actor_key} lacks {capability} capability")
        profile = profiles.get(profile_id)
        allowed_actions = {"attack", "aerial_attack"} if actor_key == "owl" else {"attack"}
        if not isinstance(profile, dict):
            errors.append(f"required pet {actor_key} missing named attack profile {profile_id}")
        elif (profile.get("actor") != actor_key or profile.get("action") not in allowed_actions or
              not isinstance(profile.get("motion_language"), str) or
              not profile["motion_language"].strip() or
              contains_placeholder(profile["motion_language"], [])):
            errors.append(f"required pet {actor_key} has invalid species attack profile {profile_id}")
        for name in ("required_profiles_by_task", "required_attack_profiles_by_task"):
            required = animations.get(name, {}).get(task, [])
            if not isinstance(required, list) or profile_id not in required:
                errors.append(f"{task} must require {profile_id} in {name}")
        required = actors.get("required_actor_keys_by_task", {}).get(task, [])
        if not isinstance(required, list) or actor_key not in required:
            errors.append(f"{task} must require pet actor {actor_key}")
    return errors

def validate_schema(resources, actors, animations):
    """Validate declarations; a pass does not prove a clip, contact or runtime."""
    errors = validate_pet_attacks(actors, animations)
    required_resource_fields = resources["future_resource_rule"]["required_fields"]
    tokens = resources.get("placeholder_tokens", [])
    profiles = animations.get("profiles", {})
    for rid, row in resources.get("resources", {}).items():
        for field in required_resource_fields:
            if field not in row:
                errors.append(f"resource {rid} missing field {field}")
        if row.get("production_ready") is True and contains_placeholder(
                resource_phase_view(row, defer_survivor=True), tokens):
            errors.append(f"resource {rid} marked production_ready with unresolved placeholder")
        for field, actor_key in RESOURCE_PROFILE_ACTORS.items():
            profile_id = row.get(field)
            if not isinstance(profile_id, str) or not profile_id.strip():
                errors.append(f"resource {rid} has empty/invalid {field}")
                continue
            if field == "survivor_animation_profile" and profile_id == SURVIVOR_DEFERRED_PROFILE:
                continue  # Explicitly pending the T23 owner, never proof of motion.
            if contains_placeholder(profile_id, tokens):
                continue  # Unready resources may declare their future task freeze.
            profile = profiles.get(profile_id)
            if not isinstance(profile, dict):
                errors.append(f"resource {rid} {field} references unknown profile {profile_id}")
            elif profile.get("actor") != actor_key:
                errors.append(f"resource {rid} {field} references wrong actor in {profile_id}")
            elif (row.get("collection_method") in RESOURCE_METHOD_ACTIONS and
                  profile.get("action") != RESOURCE_METHOD_ACTIONS[row["collection_method"]]):
                errors.append(f"resource {rid} {field} references wrong acquisition action in {profile_id}")
    for actor_key, row in actors.get("actors", {}).items():
        if row.get("attack_allowed") and not any(
            p.get("actor") == actor_key and p.get("action") in {"attack", "aerial_attack"}
            for p in profiles.values()
        ):
            errors.append(f"attack-capable actor {actor_key} has no explicit attack animation profile")
        if row.get("direct_resource_extraction_allowed") and "gather_with_tools" not in row.get("capabilities", []):
            errors.append(f"direct-gather actor {actor_key} lacks gather_with_tools capability")
        if row.get("actor_class", "").startswith("animal_") and row.get("tool_use") != "none":
            errors.append(f"animal actor {actor_key} may not use human tool fallback")
    for profile_id, row in profiles.items():
        actor = row.get("actor")
        if actor not in actors.get("actors", {}):
            errors.append(f"animation profile {profile_id} references unknown actor {actor}")
        if not row.get("action"):
            errors.append(f"animation profile {profile_id} missing action")
    for name in ("required_profiles_by_task", "required_attack_profiles_by_task"):
        for task, required in animations.get(name, {}).items():
            for profile_id in required:
                if profile_id not in profiles:
                    errors.append(f"{task} {name} references unknown profile {profile_id}")
    return errors

def coverage_set(contract, key, errors):
    values = contract.get(key, [])
    if (not isinstance(values, list) or
            any(not isinstance(value, str) or not value for value in values)):
        errors.append(f"resource_actor_contract {key} must be a list of nonempty IDs")
        return set()
    if len(values) != len(set(values)):
        errors.append(f"resource_actor_contract {key} contains duplicate IDs")
    return set(values)

def upstream_tasks(task_id, graph):
    """Read existing dependency edges without creating new prerequisites."""
    found = set()
    pending = list(graph.get("tasks", {}).get(task_id, {}).get("dependencies", []))
    while pending:
        task = pending.pop()
        if task in found:
            continue
        found.add(task)
        pending.extend(graph.get("tasks", {}).get(task, {}).get("dependencies", []))
    return found

def evaluate_task(task_id, manifest=None):
    manifest = manifest or {}
    resources = load(RESOURCE_FILE)
    actors = load(ACTOR_FILE)
    animations = load(ANIMATION_FILE)
    errors = validate_schema(resources, actors, animations)

    policy = resources.get("task_policy", {})
    graph = load(GRAPH_FILE)
    pet_tasks = {row[0] for row in PET_ATTACKS.values()}
    applicable = (task_id in policy.get("applicable_tasks", []) or
                  task_id in pet_tasks | SURVIVOR_PROFILE_TASKS)
    result = {
        "task_id": task_id,
        "candidate_commit": manifest.get("candidate_commit"),
        "applicable": applicable,
        "validation_kind": VALIDATION_KIND,
        "validator_sha256": sha256_file(HERE),
        "approval_allowed": False,
        "runtime_approval_allowed": False,
        "motion_evidence_verified": False,
        "registry_hashes": {
            "resource_action_registry": sha256_file(RESOURCE_FILE),
            "actor_capability_matrix": sha256_file(ACTOR_FILE),
            "animation_action_matrix": sha256_file(ANIMATION_FILE)
        },
        "errors": errors
    }
    if not applicable:
        result["passed"] = not errors
        return result

    contract = manifest.get("resource_actor_contract", {})
    if not isinstance(contract, dict):
        errors.append("resource_actor_contract must be an object")
        contract = {}
    introduced = coverage_set(contract, "introduced_resource_ids", errors)
    covered_resources = coverage_set(contract, "resource_ids_covered", errors)
    covered_actors = coverage_set(contract, "actor_keys_covered", errors)
    covered_profiles = coverage_set(contract, "animation_profiles_covered", errors)
    for label, declared, registered in (
            ("resource", covered_resources, resources.get("resources", {})),
            ("actor", covered_actors, actors.get("actors", {})),
            ("animation profile", covered_profiles, animations.get("profiles", {}))):
        for value in sorted(declared - set(registered)):
            errors.append(f"covered {label} {value} is not registered")
    # The evaluator emits the current hashes on first use. If a caller already
    # supplies a binding, accepting a stale one would misrepresent its coverage.
    if "registry_hashes" in contract and contract["registry_hashes"] != result["registry_hashes"]:
        errors.append("candidate registry_hashes do not match current registries")

    required_resources = set(policy.get("resource_resolution_tasks", {}).get(task_id, []))
    required_resources.update(rid for rid, row in resources.get("resources", {}).items()
                              if task_id in row.get("required_by_tasks", []))
    survivor_scope = task_id in SURVIVOR_PROFILE_TASKS
    if survivor_scope:
        required_resources.update(rid for rid, row in resources.get("resources", {}).items()
                                  if row.get("production_ready") is True)
        # T23 already depends on opening acquisition, but not on T16/T19.
        # An upstream resource cannot evade survivor resolution by changing its
        # ready flag to false. Unready future resources do not create a cycle.
        for owner in upstream_tasks(task_id, graph):
            required_resources.update(policy.get("resource_resolution_tasks", {}).get(owner, []))
    if task_id in FULL_RESOURCE_TASKS:
        required_resources.update(resources.get("resources", {}))
    resource_profiles = set()
    resource_actors = set()
    task_profile_actors = {
        animations.get("profiles", {}).get(profile_id, {}).get("actor")
        for profile_id in animations.get("required_profiles_by_task", {}).get(task_id, [])
    }
    deferred = []
    for rid in sorted(required_resources | introduced | covered_resources):
        row = resources.get("resources", {}).get(rid)
        if not row:
            errors.append(f"resource {rid} is not registered")
            continue
        if row.get("production_ready") is not True:
            errors.append(f"resource {rid} is not production_ready")
        if contains_placeholder(resource_phase_view(row, defer_survivor=not survivor_scope),
                                resources.get("placeholder_tokens", [])):
            errors.append(f"resource {rid} still contains unresolved placeholder")
        survivor_profile = row.get("survivor_animation_profile")
        if survivor_profile == SURVIVOR_DEFERRED_PROFILE:
            if survivor_scope:
                errors.append(f"resource {rid} survivor profile remains deferred to T23 in {task_id}")
            else:
                deferred.append({"resource_id": rid, "field": "survivor_animation_profile",
                                 "owner_task": "T23", "placeholder": SURVIVOR_DEFERRED_PROFILE,
                                 "motion_proven": False})
        fields = {"survivor_animation_profile"} if survivor_scope else set()
        if rid in introduced:
            fields.add("player_animation_profile")
            # Early producers keep their frozen role phases. A T09 resource
            # introduction cannot manufacture a dependency on T31 helper motion.
            fields.update(field for field, actor in RESOURCE_PROFILE_ACTORS.items()
                          if actor in task_profile_actors)
        if task_id in REGION_TASKS | FULL_RESOURCE_TASKS | {"T32"}:
            fields.update({"player_animation_profile", "helper_animation_profile"})
        for field in fields:
            profile_id = row.get(field)
            if isinstance(profile_id, str) and not contains_placeholder(profile_id, resources.get("placeholder_tokens", [])):
                resource_profiles.add(profile_id)
                resource_actors.add(RESOURCE_PROFILE_ACTORS[field])
        if rid not in covered_resources:
            errors.append(f"resource {rid} missing from candidate resource coverage")

    required_actors = set(actors.get("required_actor_keys_by_task", {}).get(task_id, []))
    required_actors.update(resource_actors)
    required_profiles = set(animations.get("required_profiles_by_task", {}).get(task_id, []))
    required_profiles.update(animations.get("required_attack_profiles_by_task", {}).get(task_id, []))
    required_profiles.update(resource_profiles)
    for actor_key, (owner, _, _, profile_id) in PET_ATTACKS.items():
        if (task_id == owner or task_id in PET_INTEGRATION_TASKS or
                actor_key in covered_actors or profile_id in covered_profiles):
            required_actors.add(actor_key)
            required_profiles.add(profile_id)
    if survivor_scope:
        required_actors.add("rescued_survivor_helper")
    for actor_key in sorted(required_actors):
        if actor_key not in actors.get("actors", {}):
            errors.append(f"required actor {actor_key} is not registered")
        if actor_key not in covered_actors:
            errors.append(f"required actor capability not proven: {actor_key}")

    for profile_id in sorted(required_profiles):
        if profile_id not in animations.get("profiles", {}):
            errors.append(f"required animation profile {profile_id} is not registered")
        if profile_id not in covered_profiles:
            errors.append(f"required animation profile not proven: {profile_id}")

    animation_delta = contract.get("animation_delta", False)
    if not isinstance(animation_delta, bool):
        errors.append("resource_actor_contract animation_delta must be boolean")
    always_c5 = task_id in policy.get("always_motion_critic_tasks", [])
    conditional_c5 = task_id in policy.get("conditional_motion_critic_tasks", []) and animation_delta is True
    critics = load(CRITIC_FILE).get("task_applicability", {}).get(task_id, [])
    graph_critics = graph.get("tasks", {}).get(task_id, {}).get("critics", [])
    pet_motion = bool(required_actors & set(PET_ATTACKS))
    # Regional resource actions need contact/use-state review against the new
    # environment even when they reuse existing clips. This is a forward C5
    # floor, not a claim of newly authored animation. Neither a false delta nor
    # an omitted introduction list can waive actual required action coverage.
    regional_contact_review = task_id in REGION_TASKS and bool(resource_profiles)
    result["c5_required"] = (always_c5 or conditional_c5 or pet_motion or regional_contact_review or
                             "C5" in critics or "C5" in graph_critics)
    result["c5_reasons"] = [reason for reason, applies in (
        ("resource_policy_always", always_c5), ("regional_animation_delta", conditional_c5),
        ("required_pet_attack", pet_motion), ("regional_resource_contact", regional_contact_review),
        ("critic_matrix_or_task_graph", "C5" in critics or "C5" in graph_critics)) if applies]
    result["required_motion_critics"] = ["C5"] if result["c5_required"] else []
    result["required_resources"] = sorted(required_resources)
    result["required_actors"] = sorted(required_actors)
    result["required_animation_profiles"] = sorted(required_profiles)
    result["deferred_resource_profiles"] = deferred
    result["passed"] = not errors
    return result

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--manifest")
    ap.add_argument("--output")
    ap.add_argument("--schema-only", action="store_true")
    args = ap.parse_args()

    manifest = {}
    if args.manifest:
        p = pathlib.Path(args.manifest)
        if not p.is_absolute():
            p = ROOT / p
        manifest = load(p)

    if args.schema_only:
        resources = load(RESOURCE_FILE)
        actors = load(ACTOR_FILE)
        animations = load(ANIMATION_FILE)
        errors = validate_schema(resources, actors, animations)
        result = {"task_id": args.task.upper(), "schema_only": True, "passed": not errors,
                  "validation_kind": "REGISTRY_SCHEMA_ONLY", "approval_allowed": False,
                  "runtime_approval_allowed": False, "motion_evidence_verified": False,
                  "errors": errors}
    else:
        result = evaluate_task(args.task.upper(), manifest)

    text = json.dumps(result, indent=2) + "\n"
    if args.output:
        out = pathlib.Path(args.output)
        if not out.is_absolute():
            out = ROOT / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(text, end="")
    if not result.get("passed"):
        raise SystemExit(1)

if __name__ == "__main__":
    main()
