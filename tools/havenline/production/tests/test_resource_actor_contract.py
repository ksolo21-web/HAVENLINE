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

    def test_t09_fails_closed_until_metal_and_fuel_are_frozen(self):
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
        self.assertFalse(result["passed"])
        self.assertTrue(result["c5_required"])
        self.assertTrue(any("metal" in e for e in result["errors"]))
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
