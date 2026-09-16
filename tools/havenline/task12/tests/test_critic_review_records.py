#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
VALIDATOR_PATH = ROOT / "tools/havenline/task12/validate_critic_review_records.py"
TEMPLATE_PATH = ROOT / "Docs/Production/T12/CRITIC_REVIEW_RECORD_TEMPLATE.json"

spec = importlib.util.spec_from_file_location("t12_critic_records", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validator)


class T12CriticReviewRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template = json.loads(TEMPLATE_PATH.read_text())

    def resolved(self):
        data = copy.deepcopy(self.template)
        data["status"] = "CRITIC_REVIEWS_COMPLETE"
        data["candidate_source"] = "a" * 40
        for critic, row in data["critics"].items():
            row["independent"] = critic != "C6"
            row["reviewer_runtime_id"] = f"review-runtime-{critic.lower()}"
            row["review_evidence_ref"] = f"artifact://{critic.lower()}-review.json"
            for index, dimension in enumerate(row["dimensions"]):
                dimension["score"] = 9.40 + (index * 0.01)
                dimension["evidence_refs"] = [f"artifact://{critic.lower()}-{dimension['id']}.json"]
                dimension["unresolved_defects"] = []
        return data

    def test_template_passes_with_29_dimensions(self):
        result = validator.validate_record(self.template, require_resolved=False)
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["critic_count"], 5)
        self.assertEqual(result["mandatory_dimension_count"], 29)
        self.assertFalse(result["score_averaging_used"])

    def test_synthetic_resolved_record_passes(self):
        result = validator.validate_record(self.resolved(), require_resolved=True)
        self.assertTrue(result["passed"], result["errors"])
        self.assertGreater(result["global_minimum_mandatory_dimension_score"], 9.0)

    def test_exactly_nine_dimension_fails(self):
        data = self.resolved()
        data["critics"]["C7"]["dimensions"][0]["score"] = 9.0
        result = validator.validate_record(data, require_resolved=True)
        self.assertFalse(result["passed"])
        self.assertTrue(any("C7.meaningful_every_level" in error and ">9.0" in error for error in result["errors"]))

    def test_dimension_cannot_be_omitted(self):
        data = self.resolved()
        data["critics"]["C4"]["dimensions"].pop()
        result = validator.validate_record(data, require_resolved=True)
        self.assertFalse(result["passed"])
        self.assertTrue(any("C4 dimension IDs" in error for error in result["errors"]))

    def test_dimension_evidence_is_required(self):
        data = self.resolved()
        data["critics"]["C2"]["dimensions"][0]["evidence_refs"] = []
        result = validator.validate_record(data, require_resolved=True)
        self.assertFalse(result["passed"])
        self.assertTrue(any("C2.state_integrity" in error and "evidence" in error for error in result["errors"]))

    def test_unresolved_dimension_defect_fails(self):
        data = self.resolved()
        data["critics"]["C3"]["dimensions"][0]["unresolved_defects"] = [{"id": "T12-C3-D001"}]
        result = validator.validate_record(data, require_resolved=True)
        self.assertFalse(result["passed"])
        self.assertTrue(any("C3.core_loop_reinforcement" in error and "unresolved" in error for error in result["errors"]))

    def test_independent_critic_false_fails(self):
        data = self.resolved()
        data["critics"]["C2"]["independent"] = False
        result = validator.validate_record(data, require_resolved=True)
        self.assertFalse(result["passed"])
        self.assertTrue(any("C2" in error and "independent" in error for error in result["errors"]))

    def test_independent_critic_needs_runtime_provenance(self):
        data = self.resolved()
        data["critics"]["C4"]["reviewer_runtime_id"] = ""
        result = validator.validate_record(data, require_resolved=True)
        self.assertFalse(result["passed"])
        self.assertTrue(any("C4" in error and "reviewer_runtime_id" in error for error in result["errors"]))

    def test_c6_remains_quantitative_not_fake_independent(self):
        data = self.resolved()
        data["critics"]["C6"]["independence_required"] = True
        result = validator.validate_record(data, require_resolved=True)
        self.assertFalse(result["passed"])
        self.assertTrue(any("C6 independence_required" in error for error in result["errors"]))

    def test_non_numeric_score_fails(self):
        data = self.resolved()
        data["critics"]["C6"]["dimensions"][1]["score"] = "9.8"
        result = validator.validate_record(data, require_resolved=True)
        self.assertFalse(result["passed"])
        self.assertTrue(any("C6.current_next_query_cost" in error and "numeric" in error for error in result["errors"]))

    def test_candidate_source_must_be_exact_sha(self):
        data = self.resolved()
        data["candidate_source"] = "candidate-branch"
        result = validator.validate_record(data, require_resolved=True)
        self.assertFalse(result["passed"])
        self.assertTrue(any("40-hex" in error for error in result["errors"]))

    def test_template_cannot_be_pre_scored(self):
        data = copy.deepcopy(self.template)
        data["critics"]["C2"]["dimensions"][0]["score"] = 9.9
        result = validator.validate_record(data, require_resolved=False)
        self.assertFalse(result["passed"])
        self.assertTrue(any("template C2.state_integrity score" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
