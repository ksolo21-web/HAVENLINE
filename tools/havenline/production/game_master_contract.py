#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[3]
DOCS = ROOT / "Docs" / "Production"
POLICY_FILE = DOCS / "GAME_MASTER_POLICY.json"


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_schema(policy: dict) -> list[str]:
    errors: list[str] = []
    if policy.get("role_id") != "GAME_MASTER":
        errors.append("role_id must be GAME_MASTER")
    if policy.get("owner_slot_count") != 2:
        errors.append("exactly two owner slots required")
    slots = policy.get("owner_slots", [])
    if len(slots) != 2 or len(set(slots)) != 2:
        errors.append("owner slot list invalid")
    identity = policy.get("identity_policy", {})
    if identity.get("provider") != "Google Sign-In":
        errors.append("Google Sign-In required")
    if identity.get("server_authoritative_role") is not True:
        errors.append("role authority setting invalid")
    if identity.get("release_oauth_identity_test_required") is not True:
        errors.append("release identity test must be required")
    if identity.get("public_source_contains_owner_account_identifiers") is not False:
        errors.append("public source identifier policy invalid")
    vip = policy.get("vip_policy", {})
    if vip.get("tier_id") != "GAME_MASTER" or vip.get("above_public_max_vip") is not True:
        errors.append("Game Master VIP tier invalid")
    if vip.get("permanent") is not True or vip.get("purchasable") is not False:
        errors.append("Game Master VIP permanence/availability invalid")
    if vip.get("inherits_all_public_vip_perks_at_maximum") is not True:
        errors.append("VIP inheritance requirement missing")
    shop = policy.get("shop_policy", {})
    if shop.get("all_approved_skus_zero_cost_for_game_master") is not True:
        errors.append("zero-cost shop rule missing")
    if shop.get("real_money_checkout_used_for_game_master_claim") is not False:
        errors.append("Game Master checkout rule invalid")
    if shop.get("normal_player_prices_unchanged") is not True:
        errors.append("normal price isolation missing")
    challenge = policy.get("challenge_policy", {})
    if challenge.get("profile_id") != "GM_CHALLENGE":
        errors.append("GM_CHALLENGE missing")
    if challenge.get("vip_or_spend_signals_used") is not False:
        errors.append("challenge profile must remain spend-blind")
    mn = challenge.get("threat_budget_min_multiplier")
    target = challenge.get("threat_budget_target_multiplier")
    mx = challenge.get("threat_budget_max_multiplier")
    if not all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in (mn, target, mx)):
        errors.append("challenge multipliers must be numeric")
    elif not (1.0 < mn <= target <= mx):
        errors.append("challenge multiplier envelope invalid")
    task_policy = policy.get("task_policy", {})
    applicable = set(task_policy.get("applicable_tasks", []))
    required_map = task_policy.get("required_proof_flags_by_task", {})
    if not applicable or set(required_map) != applicable:
        errors.append("task proof coverage mismatch")
    return errors


def evaluate_task(task_id: str, manifest: dict | None = None) -> dict:
    manifest = manifest or {}
    policy = load(POLICY_FILE)
    errors = validate_schema(policy)
    task_policy = policy.get("task_policy", {})
    applicable = task_id in task_policy.get("applicable_tasks", [])
    required_flags = task_policy.get("required_proof_flags_by_task", {}).get(task_id, [])
    result = {
        "task_id": task_id,
        "candidate_commit": manifest.get("candidate_commit"),
        "applicable": applicable,
        "policy_sha256": sha256_file(POLICY_FILE),
        "required_proof_flags": required_flags,
        "errors": errors,
    }
    if not applicable:
        result["passed"] = not errors
        return result
    contract = manifest.get("game_master_contract", {})
    proven = contract.get("proof_flags", {})
    for flag in required_flags:
        if proven.get(flag) is not True:
            errors.append(f"missing Game Master proof flag: {flag}")
    if task_id in task_policy.get("owner_binding_tasks", []):
        if contract.get("owner_slots_bound_count") != 2:
            errors.append("two owner-slot bindings must be proven")
        if not contract.get("server_binding_proof_hash"):
            errors.append("owner binding proof hash missing")
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
        policy = load(POLICY_FILE)
        errors = validate_schema(policy)
        result = {"task_id": args.task.upper(), "schema_only": True, "passed": not errors, "policy_sha256": sha256_file(POLICY_FILE), "errors": errors}
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
