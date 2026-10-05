#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
ORACLE_PATH = ROOT / "tools/havenline/task12/reference_progression_oracle.py"
VECTORS_PATH = ROOT / "Docs/Production/T12/ENGINE_TEST_VECTORS.json"

spec = importlib.util.spec_from_file_location("t12_reference_oracle", ORACLE_PATH)
oracle = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(oracle)


class T12ReferenceOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vectors = json.loads(VECTORS_PATH.read_text())

    def test_authoritative_vectors_pass(self):
        result = oracle.run_vectors(self.vectors)
        self.assertTrue(result["passed"], result["errors"])
        self.assertGreaterEqual(result["vector_count"], 9)

    def test_rejects_expected_output_drift(self):
        data = copy.deepcopy(self.vectors)
        data["vectors"][0]["expected"]["eligible_level_ids"] = []
        result = oracle.run_vectors(data)
        self.assertFalse(result["passed"])
        self.assertTrue(any("first-level-eligible" in error for error in result["errors"]))

    def test_duplicate_observed_fact_is_idempotent(self):
        levels = [{
            "level": 2,
            "level_id": "t12.level.002",
            "prerequisite_level_ids": ["t12.level.001"],
            "required_fact_ids": ["synthetic.fact.ready"],
            "one_time_event_ids": ["t12.event.level.002.completed"],
        }]
        once = oracle.evaluate(levels, {
            "completed_level_ids": ["t12.level.001"],
            "observed_fact_ids": ["synthetic.fact.ready"],
            "emitted_event_ids": [],
        })
        twice = oracle.evaluate(levels, {
            "completed_level_ids": ["t12.level.001"],
            "observed_fact_ids": ["synthetic.fact.ready", "synthetic.fact.ready"],
            "emitted_event_ids": [],
        })
        self.assertEqual(once, twice)

    def test_replayed_event_is_suppressed_without_hiding_eligibility(self):
        result = oracle.evaluate([{
            "level": 2,
            "level_id": "t12.level.002",
            "prerequisite_level_ids": ["t12.level.001"],
            "required_fact_ids": [],
            "one_time_event_ids": ["t12.event.level.002.completed"],
        }], {
            "completed_level_ids": ["t12.level.001"],
            "observed_fact_ids": [],
            "emitted_event_ids": ["t12.event.level.002.completed"],
        })
        self.assertEqual(result["eligible_level_ids"], ["t12.level.002"])
        self.assertEqual(result["new_one_time_event_ids"], [])

    def test_duplicate_level_identity_fails_closed(self):
        with self.assertRaises(ValueError):
            oracle.evaluate([
                {"level": 1, "level_id": "t12.level.001", "prerequisite_level_ids": [], "required_fact_ids": [], "one_time_event_ids": []},
                {"level": 2, "level_id": "t12.level.001", "prerequisite_level_ids": [], "required_fact_ids": [], "one_time_event_ids": []},
            ], {"completed_level_ids": [], "observed_fact_ids": [], "emitted_event_ids": []})


    def test_rejects_schema_version_drift(self):
        data = copy.deepcopy(self.vectors)
        data["schema_version"] = 2
        result = oracle.run_vectors(data)
        self.assertFalse(result["passed"])
        self.assertTrue(any("schema_version" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
