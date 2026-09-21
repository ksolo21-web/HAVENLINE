from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
VALIDATOR_PATH = ROOT / "tools" / "havenline" / "task12" / "validate_progression_contract.py"
SPEC = importlib.util.spec_from_file_location("t12_progression_validator", VALIDATOR_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)
validate_manifest = MODULE.validate_manifest


def make_valid_manifest():
    levels = []
    milestones = []
    for level in range(1, 101):
        band_start = ((level - 1) // 10) * 10 + 1
        relative = (level - 1) % 10 + 1
        visible = relative in (3, 6, 9, 10)
        level_id = f"t12.level.{level:03d}"
        band_id = {
            1: "band_opening_frozen",
            11: "band_forest",
            21: "band_desert",
            31: "band_underwater",
            41: "band_sky",
            51: "band_volcanic",
            61: "band_swamp",
            71: "band_ruins",
            81: "band_underground",
            91: "band_alien",
        }[band_start]
        visible_id = f"t12.visible.{level:03d}"
        milestone_id = f"t12.milestone.major_{level:03d}"
        levels.append({
            "level": level,
            "level_id": level_id,
            "region_band_id": band_id,
            "prerequisite_level_ids": [] if level == 1 else [f"t12.level.{level - 1:03d}"],
            "required_fact_ids": [f"t12.fact.level_{level:03d}"],
            "progression_effects": [{
                "kind": "practical_hook",
                "effect_id": f"t12.effect.level_{level:03d}",
                "owner_task": "future-owner",
            }],
            "visible_progression_hook_ids": [visible_id] if visible else [],
            "milestone_ids": [milestone_id] if relative == 10 else [],
            "one_time_event_ids": [f"t12.event.level_{level:03d}"],
        })
        if relative == 10:
            milestones.append({
                "milestone_id": milestone_id,
                "level": level,
                "kind": "major",
                "progression_hook_ids": [visible_id],
                "visible_change_required": True,
                "owner_task": "future-owner",
            })
    return {"schema_version": 1, "task_id": "T12", "levels": levels, "milestones": milestones}


class ProgressionContractTests(unittest.TestCase):
    def test_valid_100_level_contract_passes(self):
        result = validate_manifest(make_valid_manifest())
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["level_record_count"], 100)
        self.assertEqual(result["unique_level_ids"], 100)
        self.assertEqual(result["major_milestone_count"], 10)

    def test_missing_level_fails(self):
        manifest = make_valid_manifest()
        manifest["levels"].pop(49)
        result = validate_manifest(manifest)
        self.assertFalse(result["passed"])
        self.assertTrue(any("exactly 100" in error for error in result["errors"]))
        self.assertTrue(any("missing level numbers" in error for error in result["errors"]))

    def test_duplicate_level_and_id_fail(self):
        manifest = make_valid_manifest()
        manifest["levels"][49] = copy.deepcopy(manifest["levels"][48])
        result = validate_manifest(manifest)
        self.assertFalse(result["passed"])
        self.assertTrue(any("duplicate level numbers" in error for error in result["errors"]))
        self.assertTrue(any("duplicate level IDs" in error for error in result["errors"]))

    def test_cycle_fails(self):
        manifest = make_valid_manifest()
        manifest["levels"][1]["prerequisite_level_ids"] = ["t12.level.003"]
        manifest["levels"][2]["prerequisite_level_ids"] = ["t12.level.002"]
        result = validate_manifest(manifest)
        self.assertFalse(result["passed"])
        self.assertTrue(any("cycle" in error for error in result["errors"]))

    def test_spend_and_energy_gates_fail(self):
        manifest = make_valid_manifest()
        manifest["levels"][19]["eligibility"] = {"vip_status": "gold", "energy_required": 4}
        result = validate_manifest(manifest)
        self.assertFalse(result["passed"])
        self.assertGreaterEqual(sum("forbidden spend/energy" in error for error in result["errors"]), 2)

    def test_visible_progression_gap_fails(self):
        manifest = make_valid_manifest()
        for level in range(11, 17):
            manifest["levels"][level - 1]["visible_progression_hook_ids"] = []
        manifest["milestones"] = [m for m in manifest["milestones"] if m["level"] != 10]
        result = validate_manifest(manifest)
        self.assertFalse(result["passed"])
        self.assertTrue(any("visible progression gap" in error for error in result["errors"]))

    def test_missing_major_milestone_fails(self):
        manifest = make_valid_manifest()
        manifest["milestones"] = [m for m in manifest["milestones"] if m["level"] != 50]
        result = validate_manifest(manifest)
        self.assertFalse(result["passed"])
        self.assertTrue(any("level 50" in error for error in result["errors"]))

    def test_duplicate_one_time_event_fails(self):
        manifest = make_valid_manifest()
        manifest["levels"][1]["one_time_event_ids"] = [manifest["levels"][0]["one_time_event_ids"][0]]
        result = validate_manifest(manifest)
        self.assertFalse(result["passed"])
        self.assertTrue(any("duplicate one-time event ID" in error for error in result["errors"]))

    def test_provisional_t10_t11_hook_cannot_ship(self):
        manifest = make_valid_manifest()
        manifest["levels"][2]["visible_progression_hook_ids"] = ["t11_provisional:camp_stage_1"]
        result = validate_manifest(manifest)
        self.assertFalse(result["passed"])
        self.assertTrue(any("provisional hook/event ID" in error for error in result["errors"]))

    def test_noncanonical_level_id_fails(self):
        manifest = make_valid_manifest()
        manifest["levels"][11]["level_id"] = "level_012"
        result = validate_manifest(manifest)
        self.assertFalse(result["passed"])
        self.assertTrue(any("level_id must be canonical" in error for error in result["errors"]))

    def test_missing_required_fact_field_fails(self):
        manifest = make_valid_manifest()
        del manifest["levels"][20]["required_fact_ids"]
        result = validate_manifest(manifest)
        self.assertFalse(result["passed"])
        self.assertTrue(any("missing required fields" in error for error in result["errors"]))

    def test_wrong_region_band_fails(self):
        manifest = make_valid_manifest()
        manifest["levels"][24]["region_band_id"] = "band_forest"
        result = validate_manifest(manifest)
        self.assertFalse(result["passed"])
        self.assertTrue(any("region_band_id must be band_desert" in error for error in result["errors"]))

    def test_forward_prerequisite_fails(self):
        manifest = make_valid_manifest()
        manifest["levels"][1]["prerequisite_level_ids"] = ["t12.level.003"]
        manifest["levels"][2]["prerequisite_level_ids"] = ["t12.level.001"]
        result = validate_manifest(manifest)
        self.assertFalse(result["passed"])
        self.assertTrue(any("not earlier in the ordered progression" in error for error in result["errors"]))

    def test_duplicate_adjacent_effect_payload_fails(self):
        manifest = make_valid_manifest()
        manifest["levels"][9]["progression_effects"] = copy.deepcopy(manifest["levels"][8]["progression_effects"])
        result = validate_manifest(manifest)
        self.assertFalse(result["passed"])
        self.assertTrue(any("duplicate progression_effects payload" in error for error in result["errors"]))

    def test_unresolved_milestone_reference_fails(self):
        manifest = make_valid_manifest()
        manifest["levels"][9]["milestone_ids"] = ["t12.milestone.missing"]
        result = validate_manifest(manifest)
        self.assertFalse(result["passed"])
        self.assertTrue(any("milestone reference does not resolve" in error for error in result["errors"]))

    def test_milestone_schema_fails_closed(self):
        manifest = make_valid_manifest()
        manifest["milestones"][0]["visible_change_required"] = "yes"
        result = validate_manifest(manifest)
        self.assertFalse(result["passed"])
        self.assertTrue(any("visible_change_required must be boolean" in error for error in result["errors"]))


class PreparationBindingTests(unittest.TestCase):
    def test_upstream_binding_states_are_truthful(self):
        path = ROOT / "Docs" / "Production" / "T12" / "UPSTREAM_BINDINGS.json"
        data = json.loads(path.read_text())
        self.assertEqual(data["bindings"]["T07"]["status"], "APPROVED")
        self.assertEqual(data["bindings"]["T07"]["integrated_source"], "94b3f6c5097356a3857ebd13a77fb1e316eb06ae")
        self.assertEqual(data["bindings"]["T08"]["status"], "APPROVED")
        self.assertEqual(data["bindings"]["T08"]["integrated_source"], "9d56ea8ae972d0a0705ff8b985e13fab31dde493")
        self.assertTrue(data["bindings"]["T10"]["reconcile_at_activation"])
        self.assertTrue(data["bindings"]["T11"]["reconcile_at_activation"])
        self.assertEqual(data["bindings"]["T10"]["status"], "APPROVED")
        self.assertEqual(
            data["bindings"]["T10"]["integrated_source"],
            "eba0107def258824549fb10d81785290d0c81d97",
        )
        self.assertEqual(data["bindings"]["T11"]["status"], "ASSIGNED_PROVISIONAL_CONTRACT")
        self.assertNotIn("APPROVED", data["bindings"]["T11"]["status"])

    def test_shipping_t12_runtime_is_not_prebuilt(self):
        forbidden = [
            ROOT / "HavenlineGodot" / "scripts" / "progression_architecture.gd",
            ROOT / "HavenlineGodot" / "data" / "progression_levels_v1.json",
            ROOT / "HavenlineGodot" / "data" / "progression_milestones_v1.json",
        ]
        self.assertEqual([str(path.relative_to(ROOT)) for path in forbidden if path.exists()], [])


if __name__ == "__main__":
    unittest.main()
