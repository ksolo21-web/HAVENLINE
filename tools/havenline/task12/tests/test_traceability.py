#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
VALIDATOR_PATH = ROOT / "tools/havenline/task12/validate_traceability.py"
TRACE_PATH = ROOT / "Docs/Production/T12/ACCEPTANCE_TRACEABILITY.json"

spec = importlib.util.spec_from_file_location("t12_trace_validator", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validator)


class T12TraceabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trace = json.loads(TRACE_PATH.read_text())

    def validate(self, mutator=None):
        candidate = copy.deepcopy(self.trace)
        if mutator:
            mutator(candidate)
        return validator.validate_traceability(candidate)

    def test_full_traceability_plan_passes(self):
        result = self.validate()
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["requirement_count"], 16)

    def test_rejects_missing_requirement(self):
        result = self.validate(lambda t: t["requirements"].pop(9))
        self.assertFalse(result["passed"])
        self.assertTrue(any("exactly once" in error for error in result["errors"]))

    def test_rejects_empty_evidence(self):
        def mutate(trace):
            trace["requirements"][0]["required_evidence"] = []
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("required_evidence" in error for error in result["errors"]))

    def test_rejects_unknown_critic(self):
        def mutate(trace):
            trace["requirements"][1]["critics"].append("C99")
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("unknown critics" in error for error in result["errors"]))

    def test_rejects_missing_visual_critic_for_cadence(self):
        def mutate(trace):
            trace["requirements"][2]["critics"].remove("C3")
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("T12-R03" in error and "C3" in error for error in result["errors"]))

    def test_rejects_missing_c6_performance_coverage(self):
        def mutate(trace):
            trace["requirements"][11]["critics"] = ["C2"]
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("T12-R12" in error and "C6" in error for error in result["errors"]))

    def test_rejects_incomplete_final_critic_set(self):
        def mutate(trace):
            trace["requirements"][15]["critics"].remove("C7")
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("T12-R16" in error and "C7" in error for error in result["errors"]))

    def test_rejects_missing_frozen_scope_traceability(self):
        def mutate(trace):
            row = trace["requirements"][14]
            for key in ("prepared_checks", "shipping_tests", "required_evidence"):
                row[key] = [item for item in row[key] if "six" not in item.lower()]
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("T12-R15" in error and "'six'" in error for error in result["errors"]))

    def test_rejects_missing_validator_identity_traceability(self):
        def mutate(trace):
            row = trace["requirements"][15]
            for key in ("prepared_checks", "shipping_tests", "required_evidence"):
                row[key] = [item for item in row[key] if "validator" not in item.lower()]
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("T12-R16" in error and "'validator'" in error for error in result["errors"]))

    def test_rejects_relaxed_score_rule(self):
        def mutate(trace):
            trace["acceptance_rule"]["operator"] = ">="
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("strictly >9.0" in error for error in result["errors"]))


    def test_rejects_schema_version_drift(self):
        result = self.validate(lambda trace: trace.__setitem__("schema_version", 2))
        self.assertFalse(result["passed"])
        self.assertTrue(any("schema_version" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
