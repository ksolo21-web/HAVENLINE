#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
ORACLE_PATH = ROOT / "tools/havenline/task12/reference_progression_oracle.py"
CORPUS_PATH = ROOT / "Docs/Production/T12/FULL_ENGINE_VECTOR_CORPUS.json"

spec = importlib.util.spec_from_file_location("t12_reference_oracle_full", ORACLE_PATH)
oracle = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(oracle)

class T12FullEngineVectorCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = json.loads(CORPUS_PATH.read_text())

    def test_full_corpus_passes(self):
        result = oracle.run_vectors(self.corpus)
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["vector_count"], 398)
        self.assertEqual(self.corpus["coverage"]["ready_vectors"], 100)
        self.assertEqual(self.corpus["coverage"]["missing_fact_vectors"], 99)
        self.assertEqual(self.corpus["coverage"]["missing_prerequisite_vectors"], 99)
        self.assertEqual(self.corpus["coverage"]["replay_suppression_vectors"], 100)

    def test_every_level_has_ready_vector(self):
        ids = {row["id"] for row in self.corpus["vectors"]}
        for level in range(1, 101):
            self.assertIn(f"full-l{level:03d}-ready", ids)

    def test_every_noninitial_level_has_lock_and_replay_vectors(self):
        ids = {row["id"] for row in self.corpus["vectors"]}
        for level in range(2, 101):
            prefix = f"full-l{level:03d}"
            self.assertIn(prefix + "-missing-fact", ids)
            self.assertIn(prefix + "-missing-prerequisite", ids)
            self.assertIn(prefix + "-replay-suppressed", ids)

    def test_wrong_ready_expectation_fails(self):
        data = copy.deepcopy(self.corpus)
        target = next(row for row in data["vectors"] if row["id"] == "full-l050-ready")
        target["expected"]["eligible_level_ids"] = []
        result = oracle.run_vectors(data)
        self.assertFalse(result["passed"])
        self.assertTrue(any("full-l050-ready" in error for error in result["errors"]))

    def test_wrong_fact_slot_keeps_level_locked(self):
        level = 73
        row = {
            "level": level,
            "level_id": f"t12.level.{level:03d}",
            "prerequisite_level_ids": [f"t12.level.{level - 1:03d}"],
            "required_fact_ids": [f"t12.fact.slot.{level:03d}"],
            "one_time_event_ids": [f"t12.event.level.{level:03d}.completed"],
        }
        result = oracle.evaluate([row], {
            "completed_level_ids": [f"t12.level.{level - 1:03d}"],
            "observed_fact_ids": [f"t12.fact.slot.{level + 1:03d}"],
            "emitted_event_ids": [],
        })
        self.assertEqual(result, {"eligible_level_ids": [], "new_one_time_event_ids": []})

if __name__ == "__main__":
    unittest.main()
