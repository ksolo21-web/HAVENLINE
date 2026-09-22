#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
TOOL_PATH = ROOT / "tools/havenline/task12/validate_authoring_blueprint.py"
BLUEPRINT_PATH = ROOT / "Docs/Production/T12/AUTHORING_BLUEPRINT.json"
CATALOG_PATH = ROOT / "Docs/Production/T12/BINDING_SLOT_CATALOG.json"
MATRIX_PATH = ROOT / "Docs/Production/T12/LEVEL_1_100_MATRIX.json"
T10_PATH = ROOT / "HavenlineGodot/data/world_transform_recipes.json"

spec = importlib.util.spec_from_file_location("t12_authoring_blueprint", TOOL_PATH)
validator = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(validator)

class T12AuthoringBlueprintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.blueprint = json.loads(BLUEPRINT_PATH.read_text())
        cls.catalog = json.loads(CATALOG_PATH.read_text())
        cls.matrix = json.loads(MATRIX_PATH.read_text())
        cls.t10 = json.loads(T10_PATH.read_text())

    def validate(self, blueprint=None, catalog=None, matrix=None, t10=None):
        return validator.validate(
            copy.deepcopy(blueprint if blueprint is not None else self.blueprint),
            copy.deepcopy(catalog if catalog is not None else self.catalog),
            copy.deepcopy(matrix if matrix is not None else self.matrix),
            copy.deepcopy(t10 if t10 is not None else self.t10),
        )

    def test_authoring_blueprint_passes(self):
        result = self.validate()
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["blueprint_level_count"], 100)
        self.assertEqual(result["binding_slot_count"], 100)
        self.assertEqual(result["milestone_count"], 10)
        self.assertTrue(result["materialized_progression_passed"])

    def test_binding_output_path_drift_fails(self):
        blueprint = copy.deepcopy(self.blueprint)
        blueprint["materialization_contract"]["output_files"].remove(
            "HavenlineGodot/data/progression_bindings_v1.json"
        )
        result = self.validate(blueprint=blueprint)
        self.assertFalse(result["passed"])
        self.assertTrue(any("three canonical shipping datasets" in error for error in result["errors"]))

    def test_fact_slot_identity_drift_fails(self):
        blueprint = copy.deepcopy(self.blueprint)
        blueprint["levels"][11]["fact_slot_id"] = "t12.fact.slot.013"
        result = self.validate(blueprint=blueprint)
        self.assertFalse(result["passed"])
        self.assertTrue(any("level 12" in error and "fact_slot_id" in error for error in result["errors"]))

    def test_materialized_fact_rule_drift_fails(self):
        blueprint = copy.deepcopy(self.blueprint)
        blueprint["levels"][20]["materialized_required_fact_ids"] = ["external.fact"]
        result = self.validate(blueprint=blueprint)
        self.assertFalse(result["passed"])
        self.assertTrue(any("level 21" in error and "materialized_required_fact_ids" in error for error in result["errors"]))

    def test_internal_presentation_requirement_cannot_be_allowed_fact(self):
        blueprint = copy.deepcopy(self.blueprint)
        blueprint["levels"][2]["allowed_fact_kinds"].append("visible_progression_required")
        result = self.validate(blueprint=blueprint)
        self.assertFalse(result["passed"])
        self.assertTrue(any("allowed_fact_kinds" in error or "internal presentation requirements leaked" in error for error in result["errors"]))

    def test_t11_invented_public_id_fails(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["authority_classes"]["T11_CAMP"]["current_public_ids"] = ["invented.camp.id"]
        result = self.validate(catalog=catalog)
        self.assertFalse(result["passed"])
        self.assertTrue(any("invented/future public IDs" in error for error in result["errors"]))

    def test_t10_hint_drift_fails(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["authority_classes"]["T10_TRANSFORM"]["current_public_id_hints"][0]["recipe_id"] = "wrong"
        result = self.validate(catalog=catalog)
        self.assertFalse(result["passed"])
        self.assertTrue(any("T10_TRANSFORM public ID hints drifted" in error for error in result["errors"]))

    def test_matrix_role_drift_fails(self):
        blueprint = copy.deepcopy(self.blueprint)
        blueprint["levels"][5]["role"] = "fake_role"
        result = self.validate(blueprint=blueprint)
        self.assertFalse(result["passed"])
        self.assertTrue(any("level 6" in error and "role" in error for error in result["errors"]))

    def test_progression_effect_semantic_drift_fails(self):
        blueprint = copy.deepcopy(self.blueprint)
        blueprint["levels"][8]["progression_effect_template"]["semantic"] = "counter only"
        result = self.validate(blueprint=blueprint)
        self.assertFalse(result["passed"])
        self.assertTrue(any("level 9" in error and "effect template" in error for error in result["errors"]))

if __name__ == "__main__":
    unittest.main()
