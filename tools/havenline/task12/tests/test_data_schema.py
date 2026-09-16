#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
VALIDATOR_PATH = ROOT / "tools/havenline/task12/validate_data_schema.py"
SCHEMA_PATH = ROOT / "Docs/Production/T12/PROGRESSION_DATA_SCHEMA.json"

spec = importlib.util.spec_from_file_location("t12_schema_validator", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validator)


class T12ProgressionSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(SCHEMA_PATH.read_text())

    def validate(self, mutator=None):
        candidate = copy.deepcopy(self.schema)
        if mutator:
            mutator(candidate)
        return validator.validate_schema(candidate)

    def test_prepared_schema_passes(self):
        result = self.validate()
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["level_field_count"], 9)
        self.assertEqual(result["milestone_field_count"], 6)

    def test_rejects_missing_required_fact_ids(self):
        def mutate(data):
            data["level_record"]["required_fields"].remove("required_fact_ids")
        result = self.validate(mutate)
        self.assertFalse(result["passed"])

    def test_rejects_namespace_drift(self):
        def mutate(data):
            data["level_record"]["field_contracts"]["level_id"] = "any string"
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("namespace" in error for error in result["errors"]))

    def test_rejects_loss_of_spend_guard(self):
        def mutate(data):
            data["level_record"]["forbidden_eligibility_fields"].remove("premium_spend")
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("spend/energy" in error for error in result["errors"]))

    def test_rejects_t10_authority_creep(self):
        def mutate(data):
            data["level_record"]["authority_rules"] = [
                x for x in data["level_record"]["authority_rules"] if "T10" not in x
            ]
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("t10" in error.lower() for error in result["errors"]))

    def test_rejects_relaxed_level_count(self):
        def mutate(data):
            data["shipping_manifest"]["exact_level_count"] = 99
        result = self.validate(mutate)
        self.assertFalse(result["passed"])

    def test_rejects_activation_binding_gate_removal(self):
        def mutate(data):
            data["shipping_manifest"]["promotion_requires"] = [
                x for x in data["shipping_manifest"]["promotion_requires"] if "BINDING_RESOLUTION.json" not in x
            ]
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("binding_resolution.json" in error.lower() for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
