#!/usr/bin/env python3
import importlib.util
import copy
import pathlib
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[4]
MODULE_PATH = ROOT / "tools" / "havenline" / "production" / "resource_actor_contract.py"
spec = importlib.util.spec_from_file_location("resource_actor_contract", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class ResourceActorContractTests(unittest.TestCase):
    def registries(self):
        return (mod.load(mod.RESOURCE_FILE), mod.load(mod.ACTOR_FILE),
                mod.load(mod.ANIMATION_FILE))

    def evaluate_with(self, task, manifest, registries):
        real_load = mod.load
        replacements = dict(zip((mod.RESOURCE_FILE, mod.ACTOR_FILE, mod.ANIMATION_FILE), registries))
        with patch.object(mod, "load", side_effect=lambda path: copy.deepcopy(replacements[path])
                          if path in replacements else real_load(path)):
            return mod.evaluate_task(task, manifest)

    def declared_manifest(self, task, registries=None):
        resources, actors, animations = registries or self.registries()
        return {"candidate_commit": "a" * 40, "resource_actor_contract": {
            "introduced_resource_ids": [],
            "resource_ids_covered": [rid for rid, row in resources["resources"].items()
                                     if row.get("production_ready") is True]
                                    if task in mod.SURVIVOR_PROFILE_TASKS or task == "T09" else [],
            "actor_keys_covered": list(actors["actors"]),
            "animation_profiles_covered": list(animations["profiles"]),
            "animation_delta": False}}

    def resolve_test_survivor_fields(self, resources):
        # Synthetic declaration-only fixtures; no actual asset or production
        # registry is changed and a pass never claims playback/contact proof.
        resources["resources"]["metal"]["survivor_animation_profile"] = "human_survivor_mine"
        resources["resources"]["fuel"]["survivor_animation_profile"] = "human_survivor_dismantle"

    def resolved_region_fixture(self, *, new_profiles):
        registries = self.registries()
        self.resolve_test_survivor_fields(registries[0])
        resources = registries[0]["resources"]
        for rid, action in (("fish", "fish"), ("wheat", "crop_harvest")):
            resources[rid].update({"production_ready": True, "status": "TEST_DECLARATION_ONLY",
                                  "tool_profile": "test_tool", "carry_visual": "test_stack"})
            for role in ("player", "helper", "survivor"):
                resources[rid][role + "_animation_profile"] = f"human_{role}_{action}"
        resources["regional_test_wood"] = copy.deepcopy(resources["wood"])
        resources["regional_test_wood"]["required_by_tasks"] = ["T44"]
        if new_profiles:
            for role in ("player", "helper", "survivor"):
                profile = f"regional_test_{role}_gather"
                registries[2]["profiles"][profile] = copy.deepcopy(registries[2]["profiles"][f"human_{role}_chop"])
                resources["regional_test_wood"][role + "_animation_profile"] = profile
        manifest = self.declared_manifest("T44", registries)
        manifest["resource_actor_contract"].update({
            "introduced_resource_ids": ["regional_test_wood"],
            "actor_keys_covered": ["player_lead", "core_human_companion", "rescued_survivor_helper"],
            "animation_profiles_covered": [profile for profile, row in registries[2]["profiles"].items()
                                           if row["actor"] in {"player_lead", "core_human_companion", "rescued_survivor_helper"}]})
        return registries, manifest

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

    def test_roster_cannot_omit_any_of_the_seven_species(self):
        expected = {"guardian_dog", "gray_wolf", "fox", "owl", "male_lion", "white_tiger", "brown_bear"}
        self.assertEqual(expected, set(mod.PET_ATTACKS))
        for actor in expected:
            with self.subTest(actor=actor):
                resources, actors, animations = self.registries()
                del actors["actors"][actor]
                errors = mod.validate_schema(resources, actors, animations)
                self.assertTrue(any(f"required pet {actor} is missing" in e for e in errors))

    def test_all_pet_attack_permissions_are_strictly_required(self):
        for actor in mod.PET_ATTACKS:
            for value in (False, None, 1):
                with self.subTest(actor=actor, value=value):
                    resources, actors, animations = self.registries()
                    actors["actors"][actor]["attack_allowed"] = value
                    self.assertTrue(any("must retain attack_allowed=true" in e
                                        for e in mod.validate_schema(resources, actors, animations)))

    def test_every_pet_keeps_its_attack_capability_and_owl_is_aerial(self):
        for actor, (_, _, capability, _) in mod.PET_ATTACKS.items():
            with self.subTest(actor=actor):
                resources, actors, animations = self.registries()
                actors["actors"][actor]["capabilities"].remove(capability)
                self.assertTrue(any(f"lacks {capability}" in e
                                    for e in mod.validate_schema(resources, actors, animations)))
        resources, actors, animations = self.registries()
        self.assertNotIn("attack", actors["actors"]["owl"]["capabilities"])
        animations["profiles"]["owl_attack"]["action"] = "aerial_attack"
        self.assertEqual([], mod.validate_schema(resources, actors, animations))

    def test_an_alternative_attack_does_not_replace_named_species_profile(self):
        for actor, (_, _, _, profile) in mod.PET_ATTACKS.items():
            with self.subTest(actor=actor):
                resources, actors, animations = self.registries()
                animations["profiles"]["generic_replacement"] = animations["profiles"].pop(profile)
                errors = mod.validate_schema(resources, actors, animations)
                self.assertTrue(any(f"missing named attack profile {profile}" in e for e in errors))

    def test_wrong_actor_action_or_missing_motion_language_is_invalid(self):
        for field, value in (("actor", "player_lead"), ("action", "follow"),
                             ("motion_language", ""), ("motion_language", "TASK_FREEZE_REQUIRED")):
            with self.subTest(field=field, value=value):
                resources, actors, animations = self.registries()
                animations["profiles"]["fox_attack"][field] = value
                self.assertTrue(any("invalid species attack profile fox_attack" in e
                                    for e in mod.validate_schema(resources, actors, animations)))

    def test_erasing_task_requirements_cannot_waive_pet_attacks(self):
        for key in ("required_profiles_by_task", "required_attack_profiles_by_task"):
            with self.subTest(key=key):
                resources, actors, animations = self.registries()
                animations[key]["T26"] = []
                self.assertTrue(any(f"must require fox_attack in {key}" in e
                                    for e in mod.validate_schema(resources, actors, animations)))
        resources, actors, animations = self.registries()
        actors["required_actor_keys_by_task"]["T26"] = []
        self.assertTrue(any("must require pet actor fox" in e
                            for e in mod.validate_schema(resources, actors, animations)))

    def test_pet_capability_and_requirement_lists_cannot_be_substring_strings(self):
        resources, actors, animations = self.registries()
        actors["actors"]["fox"]["capabilities"] = "scout_attack_retrieve"
        self.assertTrue(any("invalid capabilities list" in e for e in mod.validate_schema(resources, actors, animations)))
        resources, actors, animations = self.registries()
        animations["required_attack_profiles_by_task"]["T26"] = "fox_attack"
        self.assertTrue(any("must require fox_attack" in e for e in mod.validate_schema(resources, actors, animations)))

    def test_seven_pet_tasks_require_motion_critic_even_without_delta_flag(self):
        for _, (task, _, _, _) in mod.PET_ATTACKS.items():
            with self.subTest(task=task):
                result = mod.evaluate_task(task, self.declared_manifest(task))
                self.assertTrue(result["passed"], result["errors"])
                self.assertTrue(result["c5_required"])
                self.assertEqual(["C5"], result["required_motion_critics"])

    def test_integrated_pet_coverage_requires_each_attack(self):
        registries = self.registries()
        self.resolve_test_survivor_fields(registries[0])
        complete = self.declared_manifest("T31", registries)
        self.assertTrue(self.evaluate_with("T31", complete, registries)["passed"])
        for _, (_, _, _, profile) in mod.PET_ATTACKS.items():
            with self.subTest(profile=profile):
                manifest = copy.deepcopy(complete)
                manifest["resource_actor_contract"]["animation_profiles_covered"].remove(profile)
                result = self.evaluate_with("T31", manifest, registries)
                self.assertFalse(result["passed"])
                self.assertIn(f"required animation profile not proven: {profile}", result["errors"])

    def test_T09_deferral_is_reported_without_claiming_survivor_motion(self):
        result = mod.evaluate_task("T09", self.declared_manifest("T09"))
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual({"metal", "fuel"}, {x["resource_id"] for x in result["deferred_resource_profiles"]})
        self.assertTrue(all(x["owner_task"] == "T23" and x["motion_proven"] is False
                            for x in result["deferred_resource_profiles"]))

    def test_T09_introduction_does_not_require_future_helper_or_survivor_motion(self):
        registries = self.registries()
        row = copy.deepcopy(registries[0]["resources"]["wood"])
        row.update(player_animation_profile="test_player_new_wood", survivor_animation_profile="T23_FREEZE_REQUIRED")
        registries[0]["resources"]["test_new_wood"] = row
        registries[2]["profiles"]["test_player_new_wood"] = copy.deepcopy(registries[2]["profiles"]["human_player_chop"])
        manifest = self.declared_manifest("T09", registries)
        manifest["resource_actor_contract"].update({
            "introduced_resource_ids": ["test_new_wood"],
            "actor_keys_covered": ["player_lead", "core_human_companion", "rescued_survivor_helper"],
            "animation_profiles_covered": ["human_player_chop", "human_player_mine", "human_player_dismantle", "test_player_new_wood"]})
        result = self.evaluate_with("T09", manifest, registries)
        self.assertTrue(result["passed"], result["errors"])
        self.assertNotIn("human_helper_chop", result["required_animation_profiles"])
        self.assertNotIn("human_survivor_chop", result["required_animation_profiles"])

    def test_T23_and_integrations_reject_current_survivor_placeholders(self):
        for task in ("T23", "T31", "T32", "T44", "T52", "T62", "T67", "T70"):
            with self.subTest(task=task):
                result = mod.evaluate_task(task, self.declared_manifest(task))
                self.assertFalse(result["passed"])
                for resource in ("metal", "fuel"):
                    self.assertTrue(any(f"resource {resource} survivor profile remains deferred to T23" in e
                                        for e in result["errors"]), result["errors"])

    def test_T23_does_not_freeze_future_fish_or_crop_resources(self):
        registries = self.registries()
        self.resolve_test_survivor_fields(registries[0])
        result = self.evaluate_with("T23", self.declared_manifest("T23", registries), registries)
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual({"wood", "stone", "metal", "fuel"}, set(result["required_resources"]))
        self.assertNotIn("fish", result["required_resources"])
        self.assertNotIn("wheat", result["required_resources"])

    def test_upstream_resource_cannot_evade_T23_by_clearing_ready_flag(self):
        registries = self.registries()
        self.resolve_test_survivor_fields(registries[0])
        registries[0]["resources"]["metal"]["production_ready"] = False
        result = self.evaluate_with("T23", self.declared_manifest("T23", registries), registries)
        self.assertFalse(result["passed"])
        self.assertIn("resource metal is not production_ready", result["errors"])

    def test_T32_does_not_add_backward_dependency_on_unready_later_region_resource(self):
        registries = self.registries()
        resources = registries[0]["resources"]
        self.resolve_test_survivor_fields(registries[0])
        resources["future_region_item"] = copy.deepcopy(resources["fish"])
        resources["future_region_item"]["required_by_tasks"] = ["T52"]
        for rid, action in (("fish", "fish"), ("wheat", "crop_harvest")):
            resources[rid].update({"production_ready": True, "status": "TEST_DECLARATION_ONLY",
                                   "tool_profile": "test_tool", "carry_visual": "test_stack"})
            for role, field in (("player", "player_animation_profile"), ("helper", "helper_animation_profile"),
                                ("survivor", "survivor_animation_profile")):
                resources[rid][field] = f"human_{role}_{action}"
        result = self.evaluate_with("T32", self.declared_manifest("T32", registries), registries)
        self.assertTrue(result["passed"], result["errors"])
        self.assertNotIn("future_region_item", result["required_resources"])

    def test_deferral_cannot_move_to_another_field_or_owner(self):
        for field, value in (("tool_profile", "T23_FREEZE_REQUIRED"),
                             ("survivor_animation_profile", "T24_FREEZE_REQUIRED"),
                             ("survivor_animation_profile", "")):
            with self.subTest(field=field, value=value):
                registries = self.registries()
                registries[0]["resources"]["metal"][field] = value
                result = self.evaluate_with("T09", self.declared_manifest("T09", registries), registries)
                self.assertFalse(result["passed"])
                self.assertTrue(any("metal" in e for e in result["errors"]))

    def test_resource_profile_references_must_exist_and_match_actor(self):
        for value in ("unknown_profile", "dog_attack", "human_helper_mine"):
            with self.subTest(value=value):
                registries = self.registries()
                registries[0]["resources"]["metal"]["survivor_animation_profile"] = value
                self.assertTrue(any("survivor_animation_profile" in e
                                    for e in mod.validate_schema(*registries)))

    def test_survivor_freeze_cannot_be_faked_with_an_unrelated_survivor_action(self):
        registries = self.registries()
        registries[0]["resources"]["metal"]["survivor_animation_profile"] = "human_survivor_attack"
        self.assertTrue(any("wrong acquisition action" in e for e in mod.validate_schema(*registries)))

    def test_unknown_coverage_and_supplied_stale_hashes_fail(self):
        for field in ("resource_ids_covered", "actor_keys_covered", "animation_profiles_covered"):
            with self.subTest(field=field):
                manifest = self.declared_manifest("T24")
                manifest["resource_actor_contract"][field].append("not_registered")
                result = mod.evaluate_task("T24", manifest)
                self.assertFalse(result["passed"])
                self.assertTrue(any("not_registered is not registered" in e for e in result["errors"]))
        manifest = self.declared_manifest("T24")
        manifest["resource_actor_contract"]["registry_hashes"] = {"actor_capability_matrix": "0" * 64}
        self.assertIn("candidate registry_hashes do not match current registries", mod.evaluate_task("T24", manifest)["errors"])

    def test_region_resource_requires_all_three_actual_human_profile_declarations(self):
        registries, manifest = self.resolved_region_fixture(new_profiles=True)
        result = self.evaluate_with("T44", manifest, registries)
        self.assertTrue(result["passed"], result["errors"])
        for role in ("player", "helper", "survivor"):
            with self.subTest(role=role):
                incomplete = copy.deepcopy(manifest)
                profile = f"regional_test_{role}_gather"
                incomplete["resource_actor_contract"]["animation_profiles_covered"].remove(profile)
                result = self.evaluate_with("T44", incomplete, registries)
                self.assertFalse(result["passed"])
                self.assertIn(f"required animation profile not proven: {profile}", result["errors"])

    def test_region_cannot_omit_new_profile_coverage_by_omitting_introduced_list(self):
        registries, manifest = self.resolved_region_fixture(new_profiles=True)
        manifest["resource_actor_contract"]["introduced_resource_ids"] = []
        manifest["resource_actor_contract"]["animation_profiles_covered"].remove("regional_test_player_gather")
        result = self.evaluate_with("T44", manifest, registries)
        self.assertFalse(result["passed"])
        self.assertIn("required animation profile not proven: regional_test_player_gather", result["errors"])

    def test_region_contact_review_cannot_be_waived_by_false_delta_or_clip_reuse(self):
        for new_profiles in (True, False):
            for declared_introduction in (True, False):
                with self.subTest(new_profiles=new_profiles, declared_introduction=declared_introduction):
                    registries, manifest = self.resolved_region_fixture(new_profiles=new_profiles)
                    if not declared_introduction:
                        manifest["resource_actor_contract"]["introduced_resource_ids"] = []
                    self.assertFalse(manifest["resource_actor_contract"]["animation_delta"])
                    result = self.evaluate_with("T44", manifest, registries)
                    self.assertTrue(result["passed"], result["errors"])
                    self.assertTrue(result["c5_required"])
                    self.assertIn("regional_resource_contact", result["c5_reasons"])

    def test_pass_is_declared_coverage_not_motion_or_game_approval(self):
        result = mod.evaluate_task("T27", self.declared_manifest("T27"))
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual("DECLARED_RESOURCE_ACTOR_COVERAGE", result["validation_kind"])
        self.assertFalse(result["approval_allowed"])
        self.assertFalse(result["runtime_approval_allowed"])
        self.assertFalse(result["motion_evidence_verified"])

    def test_malformed_coverage_or_delta_cannot_be_truthy_proof(self):
        for field, value in (("actor_keys_covered", "guardian_dog"),
                             ("animation_profiles_covered", [None]), ("animation_delta", "false")):
            with self.subTest(field=field):
                manifest = self.declared_manifest("T24")
                manifest["resource_actor_contract"][field] = value
                self.assertFalse(mod.evaluate_task("T24", manifest)["passed"])

if __name__ == "__main__":
    unittest.main()
