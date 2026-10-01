#!/usr/bin/env python3
"""Deterministic negative fuzz gate for the T12 progression contract.

Preparation only. Generates in-memory synthetic manifests and proves the static
validator rejects representative invalid topologies/eligibility mutations.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import random
import time
from typing import Any, Callable

ROOT = pathlib.Path(__file__).resolve().parents[3]
VALIDATOR_PATH = ROOT / "tools" / "havenline" / "task12" / "validate_progression_contract.py"
BUDGET_PATH = ROOT / "Docs" / "Production" / "T12" / "PREBUILD_PERFORMANCE_BUDGET.json"

spec = importlib.util.spec_from_file_location("t12_progression_validator", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validator)


def valid_manifest() -> dict[str, Any]:
    levels = []
    milestones = []
    for n in range(1, 101):
        level_id = f"t12.level.{n:03d}"
        visible = n % 10 in (0, 3, 6, 9)
        band_id = (
            "band_opening_frozen",
            "band_forest",
            "band_desert",
            "band_underwater",
            "band_sky",
            "band_volcanic",
            "band_swamp",
            "band_ruins",
            "band_underground",
            "band_alien",
        )[(n - 1) // 10]
        levels.append({
            "level": n,
            "level_id": level_id,
            "region_band_id": band_id,
            "prerequisite_level_ids": [] if n == 1 else [f"t12.level.{n - 1:03d}"],
            "required_fact_ids": [] if n == 1 else [f"t12.fact.slot.{n:03d}"],
            "progression_effects": [{"kind": "synthetic_fixture", "id": f"t12.effect.{n:03d}"}],
            "visible_progression_hook_ids": [f"t12.visible.{n:03d}"] if visible else [],
            "milestone_ids": [f"t12.milestone.{n:03d}"] if n % 10 == 0 else [],
            "one_time_event_ids": [f"t12.event.level.{n:03d}.completed"],
        })
        if n % 10 == 0:
            milestones.append({
                "milestone_id": f"t12.milestone.{n:03d}",
                "level": n,
                "kind": "major",
                "progression_hook_ids": [f"t12.visible.{n:03d}"],
                "visible_change_required": True,
                "owner_task": "PREPARED_FIXTURE_ONLY",
            })
    return {"schema_version": 1, "task_id": "T12", "levels": levels, "milestones": milestones}


def mutate_missing_level(m: dict[str, Any], rng: random.Random) -> None:
    del m["levels"][rng.randrange(100)]


def mutate_duplicate_level_id(m: dict[str, Any], rng: random.Random) -> None:
    idx = rng.randrange(1, 100)
    m["levels"][idx]["level_id"] = m["levels"][idx - 1]["level_id"]


def mutate_cycle(m: dict[str, Any], rng: random.Random) -> None:
    m["levels"][0]["prerequisite_level_ids"] = ["t12.level.100"]


def mutate_unreachable(m: dict[str, Any], rng: random.Random) -> None:
    idx = rng.randrange(1, 99)
    m["levels"][idx]["prerequisite_level_ids"] = []


def mutate_missing_prerequisite(m: dict[str, Any], rng: random.Random) -> None:
    idx = rng.randrange(1, 100)
    m["levels"][idx]["prerequisite_level_ids"] = ["t12.level.999"]


def mutate_empty_effect(m: dict[str, Any], rng: random.Random) -> None:
    m["levels"][rng.randrange(100)]["progression_effects"] = []


def mutate_visible_gap(m: dict[str, Any], rng: random.Random) -> None:
    band = rng.randrange(0, 10)
    for relative in (6, 9):
        n = band * 10 + relative
        if n <= 100:
            m["levels"][n - 1]["visible_progression_hook_ids"] = []


def mutate_missing_major_milestone(m: dict[str, Any], rng: random.Random) -> None:
    boundary = rng.choice(list(range(10, 101, 10)))
    m["milestones"] = [x for x in m["milestones"] if x["level"] != boundary]


def mutate_duplicate_event(m: dict[str, Any], rng: random.Random) -> None:
    idx = rng.randrange(1, 100)
    m["levels"][idx]["one_time_event_ids"] = list(m["levels"][idx - 1]["one_time_event_ids"])


def mutate_spend_gate(m: dict[str, Any], rng: random.Random) -> None:
    m["levels"][rng.randrange(100)]["purchase_history"] = {"minimum_usd": 1}


def mutate_energy_gate(m: dict[str, Any], rng: random.Random) -> None:
    m["levels"][rng.randrange(100)]["energy_required"] = 1


def mutate_provisional_id(m: dict[str, Any], rng: random.Random) -> None:
    m["levels"][rng.randrange(100)]["visible_progression_hook_ids"] = ["t10_provisional:should_never_ship"]


def mutate_noncanonical_level_id(m: dict[str, Any], rng: random.Random) -> None:
    idx = rng.randrange(100)
    m["levels"][idx]["level_id"] = f"level_{idx + 1:03d}"


def mutate_wrong_region_band(m: dict[str, Any], rng: random.Random) -> None:
    idx = rng.randrange(100)
    m["levels"][idx]["region_band_id"] = "band_wrong"


def mutate_missing_required_field(m: dict[str, Any], rng: random.Random) -> None:
    idx = rng.randrange(100)
    del m["levels"][idx]["required_fact_ids"]


def mutate_forward_prerequisite(m: dict[str, Any], rng: random.Random) -> None:
    idx = rng.randrange(1, 99)
    m["levels"][idx]["prerequisite_level_ids"] = [f"t12.level.{idx + 2:03d}"]


def mutate_duplicate_effect_payload(m: dict[str, Any], rng: random.Random) -> None:
    idx = rng.randrange(1, 100)
    m["levels"][idx]["progression_effects"] = json.loads(
        json.dumps(m["levels"][idx - 1]["progression_effects"])
    )


def mutate_unresolved_milestone_reference(m: dict[str, Any], rng: random.Random) -> None:
    boundary = rng.choice(list(range(10, 101, 10)))
    m["levels"][boundary - 1]["milestone_ids"] = ["t12.milestone.missing"]


def mutate_wrong_fact_slot(m: dict[str, Any], rng: random.Random) -> None:
    idx = rng.randrange(1, 100)
    level = idx + 1
    wrong = 2 if level != 2 else 3
    m["levels"][idx]["required_fact_ids"] = [f"t12.fact.slot.{wrong:03d}"]


def mutate_level1_fact_gate(m: dict[str, Any], rng: random.Random) -> None:
    m["levels"][0]["required_fact_ids"] = ["t12.fact.slot.001"]


def mutate_external_fact_id(m: dict[str, Any], rng: random.Random) -> None:
    idx = rng.randrange(1, 100)
    m["levels"][idx]["required_fact_ids"] = ["framework_anchor_seed_to_foundation"]


def mutate_invalid_milestone_shape(m: dict[str, Any], rng: random.Random) -> None:
    idx = rng.randrange(len(m["milestones"]))
    m["milestones"][idx]["visible_change_required"] = "yes"


def mutate_schema_version(m: dict[str, Any], rng: random.Random) -> None:
    m["schema_version"] = 2


def mutate_missing_completion_event(m: dict[str, Any], rng: random.Random) -> None:
    idx = rng.randrange(100)
    m["levels"][idx]["one_time_event_ids"] = [f"t12.event.other.{idx + 1:03d}"]


def mutate_prepared_required_fact(m: dict[str, Any], rng: random.Random) -> None:
    idx = rng.randrange(100)
    m["levels"][idx]["required_fact_ids"] = ["prepared.fact.should_never_ship"]


def mutate_duplicate_visible_hook(m: dict[str, Any], rng: random.Random) -> None:
    source = 2
    target = 5
    m["levels"][target]["visible_progression_hook_ids"] = list(
        m["levels"][source]["visible_progression_hook_ids"]
    )


def mutate_noncanonical_major_milestone(m: dict[str, Any], rng: random.Random) -> None:
    idx = rng.randrange(len(m["milestones"]))
    level = m["milestones"][idx]["level"]
    bad = f"t12.milestone.major_{level:03d}"
    m["milestones"][idx]["milestone_id"] = bad
    m["levels"][level - 1]["milestone_ids"] = [bad]


def mutate_global_spend_gate(m: dict[str, Any], rng: random.Random) -> None:
    m["purchase_history"] = {"minimum_usd": 1}


def mutate_extra_level_field(m: dict[str, Any], rng: random.Random) -> None:
    m["levels"][rng.randrange(100)]["unvalidated_bonus"] = 1


def mutate_extra_milestone_field(m: dict[str, Any], rng: random.Random) -> None:
    m["milestones"][rng.randrange(len(m["milestones"]))]["hidden_gate"] = True


MUTATIONS: dict[str, Callable[[dict[str, Any], random.Random], None]] = {
    "missing_level": mutate_missing_level,
    "duplicate_level_id": mutate_duplicate_level_id,
    "cycle": mutate_cycle,
    "unreachable_level": mutate_unreachable,
    "missing_prerequisite": mutate_missing_prerequisite,
    "empty_progression_effect": mutate_empty_effect,
    "visible_cadence_gap": mutate_visible_gap,
    "missing_major_milestone": mutate_missing_major_milestone,
    "duplicate_one_time_event": mutate_duplicate_event,
    "spend_gate": mutate_spend_gate,
    "energy_gate": mutate_energy_gate,
    "provisional_upstream_id": mutate_provisional_id,
    "noncanonical_level_id": mutate_noncanonical_level_id,
    "wrong_region_band": mutate_wrong_region_band,
    "missing_required_field": mutate_missing_required_field,
    "forward_prerequisite": mutate_forward_prerequisite,
    "duplicate_effect_payload": mutate_duplicate_effect_payload,
    "unresolved_milestone_reference": mutate_unresolved_milestone_reference,
    "wrong_fact_slot": mutate_wrong_fact_slot,
    "level1_fact_gate": mutate_level1_fact_gate,
    "external_fact_id": mutate_external_fact_id,
    "invalid_milestone_shape": mutate_invalid_milestone_shape,
    "schema_version": mutate_schema_version,
    "missing_completion_event": mutate_missing_completion_event,
    "prepared_required_fact": mutate_prepared_required_fact,
    "duplicate_visible_hook": mutate_duplicate_visible_hook,
    "noncanonical_major_milestone": mutate_noncanonical_major_milestone,
    "global_spend_gate": mutate_global_spend_gate,
    "extra_level_field": mutate_extra_level_field,
    "extra_milestone_field": mutate_extra_milestone_field,
}


def run_fuzz() -> dict[str, Any]:
    budget = json.loads(BUDGET_PATH.read_text())["fuzz_budget"]
    rng = random.Random(int(budget["deterministic_seed"]))
    cases = int(budget["cases"])
    expected_classes = set(budget["mutation_classes"])
    if expected_classes != set(MUTATIONS):
        return {"passed": False, "errors": ["fuzz mutation classes drifted from PREBUILD_PERFORMANCE_BUDGET.json"]}

    valid_result = validator.validate_manifest(valid_manifest())
    if not valid_result["passed"]:
        return {"passed": False, "errors": [f"baseline synthetic manifest is invalid: {valid_result['errors']}"]}

    rejected = 0
    escaped: list[dict[str, Any]] = []
    coverage = {name: 0 for name in MUTATIONS}
    names = sorted(MUTATIONS)
    started = time.perf_counter()
    for i in range(cases):
        name = names[i % len(names)] if i < len(names) else rng.choice(names)
        candidate = valid_manifest()
        MUTATIONS[name](candidate, rng)
        coverage[name] += 1
        result = validator.validate_manifest(candidate)
        if result["passed"]:
            escaped.append({"case": i, "mutation": name})
        else:
            rejected += 1
    elapsed = time.perf_counter() - started

    errors: list[str] = []
    if escaped:
        errors.append(f"invalid mutations escaped validation: {escaped[:10]}")
    if rejected < int(budget["minimum_rejected_mutations"]):
        errors.append(f"rejected mutations {rejected} below budget minimum {budget['minimum_rejected_mutations']}")
    if elapsed > float(budget["maximum_total_seconds"]):
        errors.append(f"fuzz elapsed {elapsed:.3f}s exceeds {budget['maximum_total_seconds']}s budget")
    uncovered = sorted(name for name, count in coverage.items() if count == 0)
    if uncovered:
        errors.append(f"mutation classes not exercised: {uncovered}")

    return {
        "passed": not errors,
        "cases": cases,
        "rejected": rejected,
        "escaped": len(escaped),
        "elapsed_seconds": round(elapsed, 6),
        "coverage": coverage,
        "errors": errors,
    }


def main() -> None:
    result = run_fuzz()
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
