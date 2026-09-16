#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
VALIDATOR_PATH = ROOT / "tools/havenline/task12/validate_runtime_interface.py"
CONTRACT_PATH = ROOT / "Docs/Production/T12/RUNTIME_INTERFACE_CONTRACT.json"

spec = importlib.util.spec_from_file_location("t12_runtime_validator", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validator)


class T12RuntimeInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT_PATH.read_text())

    def validate(self, mutator=None):
        candidate = copy.deepcopy(self.contract)
        if mutator:
            mutator(candidate)
        return validator.validate_contract(candidate)

    def test_prepared_runtime_contract_passes(self):
        result = self.validate()
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["runtime_api_count"], 7)

    def test_rejects_level_id_namespace_drift(self):
        def mutate(contract):
            contract["stable_id_namespaces"]["level"]["pattern"] = "level-NNN"
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("level" in error and "pattern" in error for error in result["errors"]))

    def test_rejects_missing_t13_boundary(self):
        def mutate(contract):
            contract["authority_model"]["T12_never_owns"] = [
                x for x in contract["authority_model"]["T12_never_owns"] if "T13" not in x
            ]
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("T13" in error for error in result["errors"]))

    def test_rejects_missing_idempotent_observation_api(self):
        def mutate(contract):
            del contract["runtime_api"]["observe_authoritative_fact"]
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("observe_authoritative_fact" in error for error in result["errors"]))

    def test_rejects_missing_world_transform_fact(self):
        def mutate(contract):
            contract["authoritative_fact_kinds"].remove("world_transform_completed")
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("world_transform_completed" in error for error in result["errors"]))

    def test_rejects_purchase_state_becoming_persisted_component_state(self):
        def mutate(contract):
            contract["component_state_contract"]["forbidden_fields"].remove("premium_spend")
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("forbidden fields" in error for error in result["errors"]))

    def test_rejects_missing_replay_rule(self):
        def mutate(contract):
            contract["progression_intent_contract"]["intent_id_rule"] = "deterministic identity"
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("replay" in error for error in result["errors"]))

    def test_rejects_per_frame_full_graph_policy(self):
        def mutate(contract):
            contract["performance_contract"]["evaluation"] = "evaluate all 100 levels every frame"
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("per-frame" in error for error in result["errors"]))

    def test_rejects_binding_resolution_gate_removal(self):
        def mutate(contract):
            contract["activation_rule"] = "Implement after activation."
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("activation rule" in error and "exact-resolution" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
