"""Integrity probes: incomplete plans must not look complete or approve gameplay."""
import copy
import importlib.util
import pathlib
import unittest
from unittest.mock import patch

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "gameplay_depth.py"
SPEC = importlib.util.spec_from_file_location("gameplay_depth", SCRIPT)
gd = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gd)


class GameplayDepthIntegrity(unittest.TestCase):
    def test_source_bound_complete_projection(self):
        result = gd.validate()
        self.assertEqual(result["errors"], [])
        self.assertFalse(result["runtime_approval_allowed"])
        self.assertIsNone(result["game_score"])
        rows = gd.crosswalk()["rows"]
        self.assertEqual([x["task_id"] for x in rows], gd.TASKS + gd.UNDEFINED)
        for row in rows[70:]:
            self.assertEqual(row["status"], "SOURCE_NOT_FOUND")
            self.assertFalse(row["runtime_activation_allowed_by_this_addendum"])

    def test_critical_task_projection_preserves_obligations(self):
        for task, ids in {"T10": ["GD04"], "T23": ["GD03", "GD04", "GD05", "GD06"],
                          "T24": ["GD07"], "T33": ["GD13", "GD15", "GD16"],
                          "T54": ["GD12"], "T70": ["GD18"]}.items():
            text = gd.task_section(task)
            for identity in ids:
                self.assertIn(identity, text)
            self.assertIn("not new dependency edges", text)
        with self.assertRaises(ValueError):
            gd.task_section("T71")

    def test_independent_review_omission_and_substitution_regressions(self):
        probes = [
            ("AI omitted", lambda c, a, l: a.update(ai_requirements=[])),
            ("decisions omitted", lambda c, a, l: c.update(design_decisions=[])),
            ("human replaces dog", lambda c, a, l: a["pet_roles"][0].update(actor_id="player_lead")),
            ("unknown material", lambda c, a, l: l["foundation_raw_inventory"][0].update(id="invented_unknown_resource")),
            ("duplicate human work", lambda c, a, l: a.update(human_task_families=[a["human_task_families"][0]] * 10)),
            ("duplicate motion", lambda c, a, l: a.update(animation_coverage_families=[a["animation_coverage_families"][0]] * 12)),
            ("false runtime approval", lambda c, a, l: c.update(runtime_approval_allowed=True)),
            ("missing render", lambda c, a, l: l["base_render_sheets"].pop()),
            ("false play result", lambda c, a, l: a["acceptance_scenarios"][0].update(status="PASS")),
        ]
        for name, mutate in probes:
            with self.subTest(name=name):
                c, a, l = copy.deepcopy(gd.load())
                mutate(c, a, l)
                self.assertTrue(gd.validate_data(c, a, l), name)

    def test_missing_source_universe_fails_closed(self):
        original = gd.read
        def missing(root, rel):
            if rel.endswith("SOURCE_BINDINGS.json"):
                return {"sources": []}
            return original(root, rel)
        with patch.object(gd, "read", side_effect=missing):
            result = gd.validate()
        self.assertFalse(result["passed"])
        self.assertIn("required source universe is incomplete, duplicated or changed", result["errors"])

    def test_latest_source_supersession_is_honest_and_complete(self):
        note = gd.read(gd.ROOT, gd.PACKAGE + "CURRENT_BRANCH_NOTE.json")
        self.assertEqual(gd.validate_current_source(note), [])
        for field, value in [("runtime_approved", True), ("observed_head", gd.BASE)]:
            changed = copy.deepcopy(note)
            changed[field] = value
            self.assertTrue(gd.validate_current_source(changed))
        changed = copy.deepcopy(note)
        changed["current_identifier_census"]["earned_currency_ids"] = ["pocket_cash", "house_cash", "till"]
        self.assertTrue(gd.validate_current_source(changed))


if __name__ == "__main__":
    unittest.main()
