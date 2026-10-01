#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
VALIDATOR_PATH = ROOT / "tools/havenline/task12/validate_level_matrix.py"
MATRIX_PATH = ROOT / "Docs/Production/T12/LEVEL_1_100_MATRIX.json"

spec = importlib.util.spec_from_file_location("t12_matrix_validator", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validator)


class T12LevelMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads(MATRIX_PATH.read_text())

    def validate(self, mutator=None):
        candidate = copy.deepcopy(self.matrix)
        if mutator:
            mutator(candidate)
        return validator.validate_matrix(candidate)

    def test_authoritative_preparation_matrix_passes(self):
        result = self.validate()
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["level_count"], 100)
        self.assertEqual(result["visible_level_count"], 40)
        self.assertEqual(result["major_level_count"], 10)
        self.assertEqual(result["concrete_t10_binding_count"], 0)
        self.assertEqual(result["concrete_t11_binding_count"], 0)

    def test_rejects_missing_level(self):
        result = self.validate(lambda m: m["levels"].pop(49))
        self.assertFalse(result["passed"])
        self.assertTrue(any("exactly 100" in error or "missing levels" in error for error in result["errors"]))

    def test_rejects_wrong_band_owner(self):
        def mutate(matrix):
            matrix["levels"][20]["owner"] = "T44"
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("expected content owner T45" in error for error in result["errors"]))

    def test_rejects_broken_predecessor(self):
        def mutate(matrix):
            matrix["levels"][36]["requires"] = ["t12.level.001"]
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("baseline prerequisite" in error for error in result["errors"]))

    def test_rejects_visible_cadence_drift(self):
        def mutate(matrix):
            matrix["levels"][32]["visible"] = False
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("visible must be True" in error or "visible cadence" in error for error in result["errors"]))

    def test_rejects_missing_major_milestone(self):
        def mutate(matrix):
            matrix["levels"][59]["major"] = False
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("major must be True" in error or "major milestones" in error for error in result["errors"]))

    def test_rejects_concrete_t10_binding_before_activation(self):
        def mutate(matrix):
            matrix["concrete_binding_ids"]["T10"].append("t10.world_transform.example")
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("concrete T10/T11 binding IDs" in error for error in result["errors"]))

    def test_rejects_concrete_t11_binding_before_activation(self):
        def mutate(matrix):
            matrix["concrete_binding_ids"]["T11"].append("t11.camp_state.example")
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("concrete T10/T11 binding IDs" in error for error in result["errors"]))

    def test_rejects_missing_spend_blind_guard(self):
        def mutate(matrix):
            matrix["forbidden_eligibility_inputs"].remove("premium_spend")
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("missing forbidden eligibility inputs" in error for error in result["errors"]))

    def test_rejects_shipping_status_flip(self):
        def mutate(matrix):
            matrix["status"] = "SHIPPING"
            matrix["shipping_path_forbidden"] = False
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("PREPARATION_ONLY_NON_SHIPPING" in error for error in result["errors"]))


    def test_rejects_schema_version_drift(self):
        result = self.validate(lambda matrix: matrix.__setitem__("schema_version", 2))
        self.assertFalse(result["passed"])
        self.assertTrue(any("schema_version" in error for error in result["errors"]))


    def test_rejects_frozen_invariant_drift(self):
        def mutate(matrix):
            matrix["invariants"]["max_visible_gap"] = 4
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("matrix invariants drifted" in error for error in result["errors"]))



if __name__ == "__main__":
    unittest.main()
