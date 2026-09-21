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
        level_id = f"level_{level:03d}"
        levels.append({
            "level": level,
            "level_id": level_id,
            "region_band_id": f"band_{band_start:03d}_{band_start + 9:03d}",
            "prerequisite_level_ids": [] if level == 1 else [f"level_{level - 1:03d}"],
            "progression_effects": [{"kind": "practical_hook", "owner_task": "future-owner"}],
            "visible_progression_hook_ids": [f"visible_{level:03d}"] if visible else [],
            "milestone_ids": [f"major_{level:03d}"] if relative == 10 else [],
            "one_time_event_ids": [f"event_{level:03d}"],
        })
        if relative == 10:
            milestones.append({
                "milestone_id": f"major_{level:03d}",
                "level": level,
                "kind": "major",
                "progression_hook_ids": [f"visible_{level:03d}"],
                "visible_change_required": True,
                "owner_task": "future-owner",
            })
    return {"schema_version": 1, "levels": levels, "milestones": milestones}


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
        manifest["levels"][1]["prerequisite_level_ids"] = ["level_003"]
        manifest["levels"][2]["prerequisite_level_ids"] = ["level_002"]
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
