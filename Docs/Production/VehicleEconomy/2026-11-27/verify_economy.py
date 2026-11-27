#!/usr/bin/env python3
"""Validate the authored material graph, not the live game or economic balance."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
economy = json.loads((ROOT / "RESOURCE_CHAINS.json").read_text())
worlds = json.loads((ROOT / "WORLD_VEHICLES.json").read_text())
checks = []


def check(identifier, condition, evidence):
    checks.append({"id": identifier, "passed": bool(condition), "evidence": evidence})
    if not condition:
        raise ValueError(identifier + ": " + str(evidence))


def quantity(value):
    if not isinstance(value, str) or not re.fullmatch(r"[1-9][0-9]*", value):
        raise ValueError("positive canonical decimal count required")
    return int(value)


catalogue = {item["id"]: item for item in economy["resources"]}
check("unique_catalogue", len(catalogue) == len(economy["resources"]), sorted(catalogue))
check("unique_recipe_ids", len({r["id"] for r in economy["recipes"]}) == len(economy["recipes"]), [r["id"] for r in economy["recipes"]])
check("unique_producer_ids", len({p["id"] for p in economy["producers_in_bootstrap_order"]}) == len(economy["producers_in_bootstrap_order"]), [p["id"] for p in economy["producers_in_bootstrap_order"]])
recipe_by_output = {}
for recipe in economy["recipes"]:
    check("recipe_fuel_free_" + recipe["id"], recipe["vehicle_fuel_required"] is False, recipe["vehicle_fuel_required"])
    check("one_output_" + recipe["id"], len(recipe["output"]) == 1, recipe["output"])
    output = next(iter(recipe["output"]))
    check("unique_output_" + output, output not in recipe_by_output, recipe["id"])
    for item, amount in dict(recipe["inputs"], **recipe["output"]).items():
        quantity(amount)
        if item not in catalogue:
            raise ValueError("unknown recipe resource " + item)
    recipe_by_output[output] = recipe


def depths(recipes):
    memo = {}

    def depth(item, visiting):
        if item in visiting:
            raise ValueError("recipe cycle at " + item)
        if item in memo:
            return memo[item]
        if item not in recipes:
            memo[item] = 0
        else:
            memo[item] = 1 + max(depth(i, visiting | {item}) for i in recipes[item]["inputs"])
        return memo[item]

    for item in catalogue:
        depth(item, set())
    return memo


depth = depths(recipe_by_output)
check("acyclic_recipes", max(depth.values()) == 3, depth)


def expand(bill, available_producers=None, available_raw=None):
    wanted = Counter({k: quantity(v) for k, v in bill.items()})
    if any(k not in catalogue for k in wanted):
        raise ValueError("unknown bill resource")
    batches, surplus = {}, {}
    for item in sorted(depth, key=lambda k: (-depth[k], k)):
        if not wanted[item] or item not in recipe_by_output:
            continue
        recipe = recipe_by_output[item]
        if available_producers is not None and recipe["producer"] not in available_producers:
            raise ValueError("producer unavailable: " + recipe["producer"])
        output = quantity(recipe["output"][item])
        n = (wanted[item] + output - 1) // output
        batches[recipe["id"]] = str(n)
        excess = n * output - wanted[item]
        if excess:
            surplus[item] = str(excess)
        wanted[item] = 0
        for raw, amount in recipe["inputs"].items():
            wanted[raw] += n * quantity(amount)
    leaves = {k: str(v) for k, v in sorted(wanted.items()) if v}
    if available_raw is not None and not set(leaves).issubset(available_raw):
        raise ValueError("raw source unavailable")
    return {"raw_inputs": leaves, "recipe_batches": batches, "remaining_batch_outputs": surplus}


built = set()
raw = set(economy["bootstrap"]["initial_manually_reachable_raw"])
infrastructure = Counter()
for producer in economy["producers_in_bootstrap_order"]:
    identifier = producer["id"]
    check("producer_dependency_" + identifier,
          set(producer["requires_producers"]).issubset(built), sorted(built))
    result = expand(producer["construction_bill"], built, raw)
    check("fuel_free_bootstrap_" + identifier,
          "fuel" not in producer["construction_bill"] and
          not producer["construction_vehicle_fuel_required"] and
          not producer["operation_vehicle_fuel_required"], result)
    infrastructure.update({k: quantity(v) for k, v in producer["construction_bill"].items()})
    built.add(identifier)
    raw.update(producer["unlocks_resource_sources"])
check("all_recipe_producers_available", all(r["producer"] in built for r in recipe_by_output.values()), sorted(built))
check("crude_pump_unlock", "crude_oil" in raw and "crude_oil" not in economy["bootstrap"]["initial_manually_reachable_raw"], sorted(raw))
pump = next(p for p in economy["producers_in_bootstrap_order"] if p["id"] == "manual_oil_pump")
check("pump_outside_camp", pump["site"] == "outside_camp_reachable_manual_oil_site", pump["site"])
check("pump_authorizes_crude", pump["unlocks_resource_sources"] == ["crude_oil"], pump["unlocks_resource_sources"])
check("refinery_explicit_coal_and_crude", set(recipe_by_output["fuel"]["inputs"]) == {"coal", "crude_oil"}, recipe_by_output["fuel"]["inputs"])

profiles = {p["id"]: p for p in economy["build_profiles"]}
check("unique_profiles", len(profiles) == len(economy["build_profiles"]), sorted(profiles))
check("known_profile_kinds", all(p["kind"] in {"vehicle", "garage"} for p in profiles.values()), {k: p["kind"] for k, p in profiles.items()})
check("snow_truck_is_vehicle", profiles["snow_truck_v2"]["kind"] == "vehicle", profiles["snow_truck_v2"]["kind"])
costs = {}
for identifier, profile in profiles.items():
    costs[identifier] = expand(profile["bill"], built, raw)
    if profile["kind"] == "vehicle":
        starter = quantity(profile["initial_tank_fuel_units"])
        check("funded_tank_" + identifier,
              starter == quantity(profile["bill"].get("fuel", "0")) and starter == 60,
              {"bill_fuel": profile["bill"]["fuel"], "tank_units": str(starter)})
check("eight_truck_inputs", len(profiles["snow_truck_v2"]["bill"]) == 8, profiles["snow_truck_v2"]["bill"])
for component in ["mechanical_parts", "drive_assembly", "traction_kit"]:
    uses = {"recipe:" + r["id"] for r in economy["recipes"] if component in r["inputs"]}
    uses |= {"build:" + p["id"] for p in economy["build_profiles"] if component in p["bill"]}
    uses |= {"producer:" + p["id"] for p in economy["producers_in_bootstrap_order"] if component in p["construction_bill"]}
    check("multiple_real_uses_" + component, len(uses) >= 2, sorted(uses))
check("no_speculative_feedstock", not ({"rubber", "copper", "electronics"} & set(catalogue)), sorted(catalogue))
check("worlds_2_to_10", sorted(v["world"] for v in worlds["vehicles"]) == list(range(2, 11)), [v["display_name"] for v in worlds["vehicles"]])
check("unique_world_vehicle_ids", len({v["vehicle_id"] for v in worlds["vehicles"]}) == len(worlds["vehicles"]), [v["vehicle_id"] for v in worlds["vehicles"]])
check("authentic_world_task_binding", all(v["authentic_task"] == "T" + str(v["world"] + 42) for v in worlds["vehicles"]), {str(v["world"]): v["authentic_task"] for v in worlds["vehicles"]})
check("world_profile_bindings", all(v["build_profile"] in profiles and profiles[v["build_profile"]]["kind"] == "vehicle" for v in worlds["vehicles"]), [v["build_profile"] for v in worlds["vehicles"]])
check("recurring_jobs", all(len(v["recurring_useful_jobs"]) >= 2 for v in worlds["vehicles"]), "Each of nine vehicles has at least two recurring jobs.")
check("finite_parts_not_payment", all("relay_component" not in p["bill"] for p in profiles.values()), "No vehicle or garage bill contains relay_component.")
check("retained_metal_id", "metal" in catalogue and "iron_ore" not in catalogue, "Display migration never creates a duplicate ore balance.")
check("tank_denominations", int(economy["fuel_contract"]["subunits_per_fuel_unit"]) * 60 == int(economy["fuel_contract"]["tank_capacity_subunits"]), economy["fuel_contract"]["tank_capacity_subunits"])

# Deliberately invalid examples exercise the safety boundary of this proof.
invalid = json.loads(json.dumps(recipe_by_output))
invalid["iron_bars"]["inputs"] = {"sheet_metal": "1"}
try:
    depths(invalid)
except ValueError:
    rejected_cycle = True
else:
    rejected_cycle = False
check("reject_circular_recipe", rejected_cycle, "iron_bars -> sheet_metal -> iron_bars rejected")
for identifier, bill, producer_set, raw_set in [
    ("reject_missing_first_smelter", {"iron_bars": "2"}, {"saw_bench"}, raw),
    ("reject_missing_oil_source", {"fuel": "10"}, built, raw - {"crude_oil"}),
    ("reject_unknown_item", {"unregistered_part": "1"}, built, raw),
]:
    try:
        expand(bill, producer_set, raw_set)
    except ValueError:
        rejected = True
    else:
        rejected = False
    check(identifier, rejected, bill)

all_bill = infrastructure.copy()
all_bill.update({k: quantity(v) for k, v in profiles["garage_v2"]["bill"].items()})
all_bill.update({k: quantity(v) for k, v in profiles["snow_truck_v2"]["bill"].items()})
report = {
    "schema_version": 1,
    "scope": "Authored identifier, dependency, batch arithmetic and funded-tank checks only; not navigation, producer/runtime, balance, media or device approval.",
    "input_sha256": {p: sha256((ROOT / p).read_bytes()).hexdigest() for p in ["RESOURCE_CHAINS.json", "WORLD_VEHICLES.json", "verify_economy.py"]},
    "passed": all(c["passed"] for c in checks),
    "checks_passed": len(checks),
    "checks_required": len(checks),
    "checks": checks,
    "profile_expansions": costs,
    "producer_infrastructure_expansion": expand({k: str(v) for k, v in infrastructure.items()}, built, raw),
    "new_producers_plus_garage_plus_truck_expansion": expand({k: str(v) for k, v in all_bill.items()}, built, raw),
    "subtotal_exclusions": economy["bootstrap"]["existing_progression_excluded_from_subtotal"],
}
(ROOT / "evidence").mkdir(exist_ok=True)
(ROOT / "evidence/economy_checks.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"passed": report["passed"], "checks_passed": len(checks), "truck_raw": costs["snow_truck_v2"]["raw_inputs"], "garage_raw": costs["garage_v2"]["raw_inputs"], "full_subtotal_raw": report["new_producers_plus_garage_plus_truck_expansion"]["raw_inputs"]}, indent=2))
