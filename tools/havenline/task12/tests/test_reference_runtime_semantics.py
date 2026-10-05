#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
TOOL_PATH = ROOT / "tools/havenline/task12/validate_reference_runtime_semantics.py"
SEMANTICS_PATH = ROOT / "Docs/Production/T12/REFERENCE_RUNTIME_SEMANTICS.json"
RUNTIME_PATH = ROOT / "Docs/Production/T12/RUNTIME_INTERFACE_CONTRACT.json"

spec = importlib.util.spec_from_file_location("t12_reference_semantics_validator", TOOL_PATH)
validator = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(validator)

class T12ReferenceRuntimeSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.semantics = json.loads(SEMANTICS_PATH.read_text())
        cls.runtime = json.loads(RUNTIME_PATH.read_text())

    def validate(self, semantics=None, runtime=None):
        return validator.validate(
            copy.deepcopy(semantics if semantics is not None else self.semantics),
            copy.deepcopy(runtime if runtime is not None else self.runtime),
        )

    def test_reference_semantics_match_runtime_contract(self):
        result = self.validate()
        self.assertTrue(result["passed"], result["errors"])

    def test_out_of_order_retention_rule_is_mandatory(self):
        semantics = copy.deepcopy(self.semantics)
        semantics["authoritative_fact_observation"]["out_of_order_rule"] = "reject everything"
        result = self.validate(semantics=semantics)
        self.assertFalse(result["passed"])
        self.assertTrue(any("out-of-order" in error or "retained" in error for error in result["errors"]))

    def test_state_field_drift_fails(self):
        semantics = copy.deepcopy(self.semantics)
        del semantics["initial_state"]["fact_slot_source_keys"]
        result = self.validate(semantics=semantics)
        self.assertFalse(result["passed"])
        self.assertTrue(any("initial_state fields" in error for error in result["errors"]))

    def test_runtime_observe_identity_drift_fails(self):
        runtime = copy.deepcopy(self.runtime)
        runtime["runtime_api"]["observe_authoritative_fact"]["inputs"].remove("source_task")
        result = self.validate(runtime=runtime)
        self.assertFalse(result["passed"])
        self.assertTrue(any("fact identity fields drifted" in error for error in result["errors"]))

    def test_snapshot_exact_causality_rule_is_mandatory(self):
        semantics = copy.deepcopy(self.semantics)
        semantics["snapshot_restore"]["causality_rule"] = "state is approximately related"
        semantics["snapshot_restore"]["reject"] = [
            rule for rule in semantics["snapshot_restore"]["reject"]
            if "consumed fact key" not in rule and "completion event" not in rule
        ]
        result = self.validate(semantics=semantics)
        self.assertFalse(result["passed"])
        self.assertTrue(any("snapshot/restore semantics" in error for error in result["errors"]))

    def test_snapshot_replay_rule_is_mandatory(self):
        semantics = copy.deepcopy(self.semantics)
        semantics["snapshot_restore"]["recovery"] = "restore arbitrary state"
        result = self.validate(semantics=semantics)
        self.assertFalse(result["passed"])
        self.assertTrue(any("snapshot/restore semantics" in error for error in result["errors"]))

if __name__ == "__main__":
    unittest.main()
