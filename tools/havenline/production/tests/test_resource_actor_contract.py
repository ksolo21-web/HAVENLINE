#!/usr/bin/env python3
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
MODULE_PATH = ROOT / "tools" / "havenline" / "production" / "resource_actor_contract.py"
spec = importlib.util.spec_from_file_location("resource_actor_contract", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class ResourceActorContractTests(unittest.TestCase):
    def test_schema_is_internally_consistent(self):
        resources = mod.load(mod.RESOURCE_FILE)
        actors = mod.load(mod.ACTOR_FILE)
        animations = mod.load(mod.ANIMATION_FILE)
        self.assertEqual([], mod.validate_schema(resources, actors, animations))

    def test_t05_is_not_retroactively_expanded(self):
        result = mod.evaluate_task("T05", {"candidate_commit": "a" * 40})
        self.assertFalse(result["applicable"])
        self.assertTrue(result["passed"])

    def test_t09_frozen_registry_passes_with_complete_candidate_coverage(self):
        resources = mod.load(mod.RESOURCE_FILE)["resources"]
        expected = {
            "wood": ("RESOLVED_BASELINE", "natural", "chop", "axe", "human_player_chop", "human_helper_chop", "visible_wood_stack", "contextual_storage_furnace_build"),
            "stone": ("RESOLVED_BASELINE", "natural", "mine", "pickaxe", "human_player_mine", "human_helper_mine", "visible_stone_stack", "contextual_storage_furnace_build"),
            "metal": ("T09_FROZEN_ORE", "ore", "mine", "pickaxe", "human_player_mine", "human_helper_mine", "visible_metal_stack", "contextual_storage_processing_build"),
            "fuel": ("T09_FROZEN_SALVAGE", "fuel_salvage", "dismantle", "salvage_pry_tool", "human_player_dismantle", "human_helper_dismantle", "visible_fuel_stack", "contextual_furnace_storage"),
        }
        for resource_id, mapping in expected.items():
            row = resources[resource_id]
            self.assertTrue(row["production_ready"], resource_id)
            self.assertEqual(tuple(row[field] for field in ("status", "resource_class", "collection_method", "tool_profile", "player_animation_profile", "helper_animation_profile", "carry_visual", "delivery_destination")), mapping)
        manifest = {
            "candidate_commit": "b" * 40,
            "resource_actor_contract": {
                "introduced_resource_ids": [],
                "resource_ids_covered": ["wood", "stone", "metal", "fuel"],
                "actor_keys_covered": ["player_lead", "core_human_companion", "rescued_survivor_helper"],
                "animation_profiles_covered": ["human_player_chop", "human_player_mine", "human_player_dismantle"],
                "animation_delta": True
            }
        }
        result = mod.evaluate_task("T09", manifest)
        self.assertTrue(result["passed"], result["errors"])
        self.assertTrue(result["c5_required"])
        self.assertEqual(result["errors"], [])

    def test_t09_fails_closed_when_fuel_evidence_is_missing(self):
        manifest = {
            "candidate_commit": "e" * 40,
            "resource_actor_contract": {
                "introduced_resource_ids": [],
                "resource_ids_covered": ["wood", "stone", "metal"],
                "actor_keys_covered": ["player_lead", "core_human_companion", "rescued_survivor_helper"],
                "animation_profiles_covered": ["human_player_chop", "human_player_mine", "human_player_dismantle"],
                "animation_delta": True
            }
        }
        result = mod.evaluate_task("T09", manifest)
        self.assertFalse(result["passed"])
        self.assertTrue(any("fuel" in e for e in result["errors"]))

    def test_pet_task_requires_species_actor_and_animation_profiles(self):
        manifest = {
            "candidate_commit": "c" * 40,
            "resource_actor_contract": {
                "introduced_resource_ids": [],
                "resource_ids_covered": [],
                "actor_keys_covered": [],
                "animation_profiles_covered": [],
                "animation_delta": True
            }
        }
        result = mod.evaluate_task("T24", manifest)
        self.assertFalse(result["passed"])
        self.assertTrue(any("guardian_dog" in e for e in result["errors"]))
        self.assertTrue(any("dog_attack" in e for e in result["errors"]))
        self.assertTrue(any("dog_retrieve" in e for e in result["errors"]))

    def test_future_unregistered_resource_fails_closed(self):
        manifest = {
            "candidate_commit": "d" * 40,
            "resource_actor_contract": {
                "introduced_resource_ids": ["alien_crystal_unregistered"],
                "resource_ids_covered": ["alien_crystal_unregistered"],
                "actor_keys_covered": [],
                "animation_profiles_covered": [],
                "animation_delta": False
            }
        }
        result = mod.evaluate_task("T52", manifest)
        self.assertFalse(result["passed"])
        self.assertTrue(any("not registered" in e for e in result["errors"]))

if __name__ == "__main__":
    unittest.main()
