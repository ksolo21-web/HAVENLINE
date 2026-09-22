#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
TOOL_PATH = ROOT / "tools/havenline/task12/validate_evidence_index.py"
TEMPLATE_PATH = ROOT / "Docs/Production/T12/EVIDENCE_INDEX_TEMPLATE.json"

spec = importlib.util.spec_from_file_location("t12_evidence_index", TOOL_PATH)
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validator)


class T12EvidenceIndexTests(unittest.TestCase):
    candidate_sha = "a" * 40

    @classmethod
    def setUpClass(cls):
        cls.template = json.loads(TEMPLATE_PATH.read_text())

    def candidate(self):
        return {
            "exact_source": {
                "candidate_source": self.candidate_sha,
                "authorized_changed_file_manifest_ref": "artifact://changed-files.json",
            },
            "static_reports": {"level_100_completeness": {"evidence_ref": "artifact://static-levels.json"}},
            "engine_parity": {
                "output_ref": "artifact://parity-output.json",
                "comparator_output_ref": "artifact://parity-compare.json",
            },
            "regression": {"artifact_ref": "artifact://regression.zip"},
            "functional_sequences": {
                "ordinary_level_progression": {"evidence_refs": ["artifact://ordinary-sequence.json"]}
            },
            "adaptive_readability": {"player_facing_presentation_exists": False},
            "performance_c6": {"evidence_ref": "artifact://c6.json"},
            "gates": {"G1": {"evidence_ref": "artifact://g1.json"}},
            "critic_reviews": {"C2": {"evidence_ref": "artifact://c2-review.json"}},
        }

    def critics(self):
        return {
            "candidate_source": self.candidate_sha,
            "critics": {
                "C2": {
                    "review_evidence_ref": "artifact://c2-review.json",
                    "dimensions": [
                        {"evidence_refs": ["artifact://c2-state-integrity.json"]}
                    ],
                }
            },
        }

    def resolved_index(self, candidate=None, critics=None):
        candidate = candidate if candidate is not None else self.candidate()
        critics = critics if critics is not None else self.critics()
        data = copy.deepcopy(self.template)
        data["status"] = "EVIDENCE_INDEX_COMPLETE"
        data["candidate_source"] = self.candidate_sha
        categories = validator.required_ref_categories(candidate, critics)
        refs = sorted(categories)
        data["entries"] = [
            {
                "artifact_id": f"artifact-{index:03d}",
                "category": next(iter(categories[uri])),
                "uri": uri,
                "sha256": f"{index + 1:064x}",
                "candidate_source": self.candidate_sha,
                "producer": "synthetic-test-producer",
                "content_verified": True,
            }
            for index, uri in enumerate(refs)
        ]
        return data

    def test_template_passes(self):
        result = validator.validate_index(self.template)
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["entry_count"], 0)

    def test_complete_synthetic_index_passes(self):
        candidate = self.candidate()
        critics = self.critics()
        result = validator.validate_index(
            self.resolved_index(candidate, critics),
            require_resolved=True,
            candidate=candidate,
            critics=critics,
        )
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["missing_required_ref_count"], 0)
        self.assertEqual(result["entry_count"], result["required_ref_count"])

    def test_missing_required_reference_fails(self):
        candidate = self.candidate()
        critics = self.critics()
        index = self.resolved_index(candidate, critics)
        index["entries"].pop()
        result = validator.validate_index(index, require_resolved=True, candidate=candidate, critics=critics)
        self.assertFalse(result["passed"])
        self.assertTrue(any("missing from index" in error for error in result["errors"]))

    def test_missing_gate_evidence_reference_fails(self):
        candidate = self.candidate()
        critics = self.critics()
        index = self.resolved_index(candidate, critics)
        index["entries"] = [
            row for row in index["entries"]
            if row["uri"] != "artifact://g1.json"
        ]
        result = validator.validate_index(index, require_resolved=True, candidate=candidate, critics=critics)
        self.assertFalse(result["passed"])
        self.assertTrue(any("artifact://g1.json" in error and "missing from index" in error for error in result["errors"]))

    def test_duplicate_uri_fails(self):
        candidate = self.candidate()
        critics = self.critics()
        index = self.resolved_index(candidate, critics)
        index["entries"][1]["uri"] = index["entries"][0]["uri"]
        result = validator.validate_index(index, require_resolved=True, candidate=candidate, critics=critics)
        self.assertFalse(result["passed"])
        self.assertTrue(any("duplicate uri" in error for error in result["errors"]))

    def test_bad_digest_fails(self):
        candidate = self.candidate()
        critics = self.critics()
        index = self.resolved_index(candidate, critics)
        index["entries"][0]["sha256"] = "not-a-digest"
        result = validator.validate_index(index, require_resolved=True, candidate=candidate, critics=critics)
        self.assertFalse(result["passed"])
        self.assertTrue(any("SHA-256" in error for error in result["errors"]))

    def test_candidate_mismatch_fails(self):
        candidate = self.candidate()
        critics = self.critics()
        index = self.resolved_index(candidate, critics)
        index["entries"][0]["candidate_source"] = "b" * 40
        result = validator.validate_index(index, require_resolved=True, candidate=candidate, critics=critics)
        self.assertFalse(result["passed"])
        self.assertTrue(any("candidate_source mismatch" in error for error in result["errors"]))

    def test_unverified_content_fails(self):
        candidate = self.candidate()
        critics = self.critics()
        index = self.resolved_index(candidate, critics)
        index["entries"][0]["content_verified"] = False
        result = validator.validate_index(index, require_resolved=True, candidate=candidate, critics=critics)
        self.assertFalse(result["passed"])
        self.assertTrue(any("content_verified" in error for error in result["errors"]))


    def test_rejects_schema_version_drift(self):
        candidate = self.candidate()
        critics = self.critics()
        index = self.resolved_index(candidate, critics)
        index["schema_version"] = 2
        result = validator.validate_index(index, require_resolved=True, candidate=candidate, critics=critics)
        self.assertFalse(result["passed"])
        self.assertTrue(any("schema_version" in error for error in result["errors"]))


    def test_wrong_evidence_category_fails(self):
        candidate = self.candidate()
        critics = self.critics()
        index = self.resolved_index(candidate, critics)
        target = next(
            row for row in index["entries"]
            if row["uri"] == "artifact://changed-files.json"
        )
        target["category"] = "static_report"
        result = validator.validate_index(index, require_resolved=True, candidate=candidate, critics=critics)
        self.assertFalse(result["passed"])
        self.assertTrue(any("category mismatch" in error for error in result["errors"]))



if __name__ == "__main__":
    unittest.main()
