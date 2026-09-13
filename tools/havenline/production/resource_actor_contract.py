#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[3]
DOCS = ROOT / "Docs" / "Production"

RESOURCE_FILE = DOCS / "RESOURCE_ACTION_REGISTRY.json"
ACTOR_FILE = DOCS / "ACTOR_CAPABILITY_MATRIX.json"
ANIMATION_FILE = DOCS / "ANIMATION_ACTION_MATRIX.json"

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
        return any(token in value for token in tokens)
    if isinstance(value, list):
        return any(contains_placeholder(v, tokens) for v in value)
    if isinstance(value, dict):
        return any(contains_placeholder(v, tokens) for v in value.values())
    return False

def validate_schema(resources, actors, animations):
    errors = []
    required_resource_fields = resources["future_resource_rule"]["required_fields"]
    tokens = resources.get("placeholder_tokens", [])
    for rid, row in resources.get("resources", {}).items():
        for field in required_resource_fields:
            if field not in row:
                errors.append(f"resource {rid} missing field {field}")
        if row.get("production_ready") is True and contains_placeholder(row, tokens):
            errors.append(f"resource {rid} marked production_ready with unresolved placeholder")
    for actor_key, row in actors.get("actors", {}).items():
        if row.get("attack_allowed") and not any(
            p.get("actor") == actor_key and p.get("action") == "attack"
            for p in animations.get("profiles", {}).values()
        ):
            errors.append(f"attack-capable actor {actor_key} has no explicit attack animation profile")
        if row.get("direct_resource_extraction_allowed") and "gather_with_tools" not in row.get("capabilities", []):
            errors.append(f"direct-gather actor {actor_key} lacks gather_with_tools capability")
        if row.get("actor_class", "").startswith("animal_") and row.get("tool_use") != "none":
            errors.append(f"animal actor {actor_key} may not use human tool fallback")
    for profile_id, row in animations.get("profiles", {}).items():
        actor = row.get("actor")
        if actor not in actors.get("actors", {}):
            errors.append(f"animation profile {profile_id} references unknown actor {actor}")
        if not row.get("action"):
            errors.append(f"animation profile {profile_id} missing action")
    return errors

def evaluate_task(task_id, manifest=None):
    manifest = manifest or {}
    resources = load(RESOURCE_FILE)
    actors = load(ACTOR_FILE)
    animations = load(ANIMATION_FILE)
    errors = validate_schema(resources, actors, animations)

    policy = resources.get("task_policy", {})
    applicable = task_id in policy.get("applicable_tasks", [])
    result = {
        "task_id": task_id,
        "candidate_commit": manifest.get("candidate_commit"),
        "applicable": applicable,
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
    introduced = set(contract.get("introduced_resource_ids", []))
    covered_resources = set(contract.get("resource_ids_covered", []))
    covered_actors = set(contract.get("actor_keys_covered", []))
    covered_profiles = set(contract.get("animation_profiles_covered", []))

    required_resources = set(policy.get("resource_resolution_tasks", {}).get(task_id, []))
    for rid in sorted(required_resources | introduced):
        row = resources.get("resources", {}).get(rid)
        if not row:
            errors.append(f"resource {rid} is not registered")
            continue
        if row.get("production_ready") is not True:
            errors.append(f"resource {rid} is not production_ready")
        if contains_placeholder(row, resources.get("placeholder_tokens", [])):
            errors.append(f"resource {rid} still contains unresolved placeholder")
        if rid not in covered_resources:
            errors.append(f"resource {rid} missing from candidate resource coverage")

    required_actors = set(actors.get("required_actor_keys_by_task", {}).get(task_id, []))
    for actor_key in sorted(required_actors):
        if actor_key not in covered_actors:
            errors.append(f"required actor capability not proven: {actor_key}")

    required_profiles = set(animations.get("required_profiles_by_task", {}).get(task_id, []))
    for profile_id in sorted(required_profiles):
        if profile_id not in covered_profiles:
            errors.append(f"required animation profile not proven: {profile_id}")

    animation_delta = bool(contract.get("animation_delta"))
    always_c5 = task_id in policy.get("always_motion_critic_tasks", [])
    conditional_c5 = task_id in policy.get("conditional_motion_critic_tasks", []) and animation_delta
    result["c5_required"] = always_c5 or conditional_c5
    result["required_resources"] = sorted(required_resources)
    result["required_actors"] = sorted(required_actors)
    result["required_animation_profiles"] = sorted(required_profiles)
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
        result = {"task_id": args.task.upper(), "schema_only": True, "passed": not errors, "errors": errors}
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
