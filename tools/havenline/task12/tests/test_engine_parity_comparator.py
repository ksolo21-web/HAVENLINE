#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
COMPARATOR_PATH = ROOT / "tools/havenline/task12/compare_engine_parity.py"
VECTORS_PATH = ROOT / "Docs/Production/T12/ENGINE_TEST_VECTORS.json"
SCHEMA_PATH = ROOT / "Docs/Production/T12/ENGINE_PARITY_OUTPUT_SCHEMA.json"

spec = importlib.util.spec_from_file_location("t12_engine_parity", COMPARATOR_PATH)
comparator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(comparator)


class T12EngineParityComparatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vectors = json.loads(VECTORS_PATH.read_text())
        cls.schema = json.loads(SCHEMA_PATH.read_text())

    def valid_actual(self):
        rows = []
        for case in self.vectors["vectors"]:
            rows.append({
                "vector_id": case["id"],
                "eligible_level_ids": list(case["expected"]["eligible_level_ids"]),
                "new_one_time_event_ids": list(case["expected"]["new_one_time_event_ids"]),
                "state_hash_before": f"state-{case['id']}",
                "state_hash_after": f"state-{case['id']}",
                "repeat_output_hashes": [f"output-{case['id']}", f"output-{case['id']}"],
            })
        return {
            "task_id": "T12",
            "candidate_source": "a" * 40,
            "vector_results": rows,
        }

    def compare(self, actual=None, vectors=None, schema=None):
        return comparator.compare(
            actual if actual is not None else self.valid_actual(),
            vectors if vectors is not None else self.vectors,
            schema if schema is not None else self.schema,
        )

    def test_synthetic_engine_output_passes(self):
        result = self.compare()
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["expected_vector_count"], len(self.vectors["vectors"]))

    def test_rejects_missing_vector(self):
        actual = self.valid_actual()
        actual["vector_results"].pop()
        result = self.compare(actual=actual)
        self.assertFalse(result["passed"])
        self.assertTrue(any("missing engine vector results" in error for error in result["errors"]))

    def test_rejects_output_drift(self):
        actual = self.valid_actual()
        actual["vector_results"][0]["eligible_level_ids"] = []
        result = self.compare(actual=actual)
        self.assertFalse(result["passed"])
        self.assertTrue(any("differs" in error for error in result["errors"]))

    def test_rejects_query_state_mutation(self):
        actual = self.valid_actual()
        actual["vector_results"][0]["state_hash_after"] = "changed-state"
        result = self.compare(actual=actual)
        self.assertFalse(result["passed"])
        self.assertTrue(any("mutated state" in error for error in result["errors"]))

    def test_rejects_nondeterministic_repeat_output(self):
        actual = self.valid_actual()
        actual["vector_results"][0]["repeat_output_hashes"] = ["one", "two"]
        result = self.compare(actual=actual)
        self.assertFalse(result["passed"])
        self.assertTrue(any("not deterministic" in error for error in result["errors"]))

    def test_rejects_non_exact_candidate_source(self):
        actual = self.valid_actual()
        actual["candidate_source"] = "prepared-branch"
        result = self.compare(actual=actual)
        self.assertFalse(result["passed"])
        self.assertTrue(any("40-hex" in error for error in result["errors"]))

    def test_rejects_schema_field_drift(self):
        schema = copy.deepcopy(self.schema)
        schema["vector_result_required_fields"].remove("state_hash_after")
        result = self.compare(schema=schema)
        self.assertFalse(result["passed"])
        self.assertTrue(any("required vector fields drifted" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
