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

    def test_rejects_required_fact_slot_contract_drift(self):
        def mutate(data):
            data["level_record"]["field_contracts"]["required_fact_ids"] = "any stable string"
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("required_fact_ids contract" in error for error in result["errors"]))

    def test_rejects_missing_fact_slot_contract(self):
        def mutate(data):
            del data["fact_slot_contract"]
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("fact_slot_contract must be an object" in error for error in result["errors"]))

    def test_rejects_later_owner_unlocking_without_trusted_integration(self):
        def mutate(data):
            data["fact_slot_contract"]["later_owner_behavior"] = "later tasks can unlock directly"
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("later-owner behavior" in error for error in result["errors"]))

    def test_rejects_presentation_requirement_authority_drift(self):
        def mutate(data):
            data["fact_slot_contract"]["presentation_requirement_rule"] = "milestone may bind source"
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("presentation rule" in error for error in result["errors"]))

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

    def test_rejects_completion_event_namespace_drift(self):
        def mutate(data):
            data["level_record"]["field_contracts"]["one_time_event_ids"] = "replay safe arbitrary IDs"
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("completion event identity" in error for error in result["errors"]))

    def test_rejects_major_milestone_namespace_drift(self):
        def mutate(data):
            data["milestone_record"]["field_contracts"]["milestone_id"] = "stable ^t12\\.milestone\\..+$ IDs"
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("canonical major milestone" in error for error in result["errors"]))

    def test_rejects_missing_split_shipping_file_contract(self):
        def mutate(data):
            del data["shipping_files"]["progression_milestones_v1"]
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("progression_milestones_v1" in error for error in result["errors"]))

    def test_rejects_missing_binding_shipping_file_contract(self):
        def mutate(data):
            del data["shipping_files"]["progression_bindings_v1"]
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("progression_bindings_v1" in error for error in result["errors"]))

    def test_rejects_binding_count_drift(self):
        def mutate(data):
            data["shipping_files"]["progression_bindings_v1"]["exact_binding_count"] = 98
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("exact_binding_count" in error for error in result["errors"]))

    def test_rejects_split_file_identity_drift(self):
        def mutate(data):
            data["shipping_files"]["progression_levels_v1"]["task_id"] = "T13"
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("schema_version=1 and task_id=T12" in error for error in result["errors"]))

    def test_rejects_missing_cross_file_validation_rule(self):
        def mutate(data):
            data["shipping_files"]["cross_file_rule"] = "hash files"
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("cross-file rule" in error for error in result["errors"]))


    def test_rejects_schema_version_drift(self):
        result = self.validate(lambda data: data.__setitem__("schema_version", 2))
        self.assertFalse(result["passed"])
        self.assertTrue(any("schema_version" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
