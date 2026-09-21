#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
VALIDATOR_PATH = ROOT / "tools/havenline/task12/validate_candidate_evidence.py"
TEMPLATE_PATH = ROOT / "Docs/Production/T12/CANDIDATE_EVIDENCE_TEMPLATE.json"

spec = importlib.util.spec_from_file_location("t12_candidate_evidence", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validator)


class T12CandidateEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template = json.loads(TEMPLATE_PATH.read_text())

    def resolved_packet(self):
        data = copy.deepcopy(self.template)
        candidate = "a" * 40
        source = data["exact_source"]
        source["activation_base"] = "b" * 40
        source["candidate_source"] = candidate
        source["integration_head"] = "c" * 40
        source["authorized_changed_file_manifest_ref"] = "artifact://authorized-files.json"
        source["shipping_data_hashes"] = {
            "progression_levels_v1_json_sha256": "c" * 64,
            "progression_milestones_v1_json_sha256": "d" * 64,
            "binding_resolution_json_sha256": "e" * 64,
        }
        source["upstream_sources"]["T10"] = "f" * 40
        source["upstream_sources"]["T11"] = "1" * 40
        source["validator_source"] = "sha256:" + "2" * 64

        for row in data["static_reports"].values():
            row["status"] = "PASS"
            row["evidence_ref"] = "artifact://static-report.json"

        data["engine_parity"].update({
            "status": "PASS",
            "candidate_source": candidate,
            "output_ref": "artifact://engine-parity-output.json",
            "comparator_output_ref": "artifact://engine-parity-compare.json",
        })
        data["regression"].update({
            "status": "PASS",
            "candidate_source": candidate,
            "run_id": 123,
            "artifact_ref": "artifact://t01-t11-regression.zip",
            "failed_suites": [],
        })
        for name, row in data["functional_sequences"].items():
            row["status"] = "PASS"
            row["evidence_refs"] = [f"artifact://sequence-{name}.json"]

        data["adaptive_readability"]["player_facing_presentation_exists"] = False

        data["performance_c6"].update({
            "status": "PASS",
            "candidate_source": candidate,
            "run_id": 456,
            "evidence_ref": "artifact://c6.json",
            "shipping_measurements_present": True,
            "prebuild_python_benchmark_used_as_shipping_c6": False,
            "score": 9.61,
        })
        for critic, row in data["critic_reviews"].items():
            row.update({
                "status": "PASS",
                "candidate_source": candidate,
                "independent": critic != "C6",
                "reviewer_runtime_id": f"review-runtime-{critic.lower()}",
                "evidence_ref": f"artifact://{critic.lower()}-review.json",
                "minimum_mandatory_dimension_score": 9.5,
            })
        for gate in data["gates"]:
            data["gates"][gate] = True
        data["defects"]["unresolved_mandatory"] = []
        return data

    def test_preparation_template_passes(self):
        result = validator.validate_packet(self.template, require_resolved=False)
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["static_report_count"], 10)
        self.assertEqual(result["critic_count"], 5)
        self.assertEqual(result["gate_count"], 14)

    def test_synthetic_resolved_packet_passes(self):
        result = validator.validate_packet(self.resolved_packet(), require_resolved=True)
        self.assertTrue(result["passed"], result["errors"])

    def test_exactly_nine_critic_score_fails(self):
        data = self.resolved_packet()
        data["critic_reviews"]["C3"]["minimum_mandatory_dimension_score"] = 9.0
        result = validator.validate_packet(data, require_resolved=True)
        self.assertFalse(result["passed"])
        self.assertTrue(any("C3" in error and ">9.0" in error for error in result["errors"]))

    def test_independent_critic_without_provenance_fails(self):
        data = self.resolved_packet()
        data["critic_reviews"]["C2"]["reviewer_runtime_id"] = ""
        data["critic_reviews"]["C2"]["evidence_ref"] = ""
        result = validator.validate_packet(data, require_resolved=True)
        self.assertFalse(result["passed"])
        self.assertTrue(any("C2" in error and "provenance" in error for error in result["errors"]))

    def test_c2_independence_false_fails(self):
        data = self.resolved_packet()
        data["critic_reviews"]["C2"]["independent"] = False
        result = validator.validate_packet(data, require_resolved=True)
        self.assertFalse(result["passed"])
        self.assertTrue(any("C2" in error and "independent" in error for error in result["errors"]))

    def test_c6_does_not_fake_independent_requirement(self):
        data = self.resolved_packet()
        data["critic_reviews"]["C6"]["independence_required"] = True
        result = validator.validate_packet(data, require_resolved=True)
        self.assertFalse(result["passed"])
        self.assertTrue(any("C6" in error and "quantitative" in error for error in result["errors"]))

    def test_any_failed_gate_fails(self):
        data = self.resolved_packet()
        data["gates"]["G9"] = False
        result = validator.validate_packet(data, require_resolved=True)
        self.assertFalse(result["passed"])
        self.assertTrue(any("G1-G14" in error for error in result["errors"]))

    def test_unresolved_mandatory_defect_fails(self):
        data = self.resolved_packet()
        data["defects"]["unresolved_mandatory"] = [{"id": "T12-D001"}]
        result = validator.validate_packet(data, require_resolved=True)
        self.assertFalse(result["passed"])
        self.assertTrue(any("zero unresolved" in error for error in result["errors"]))

    def test_prebuild_benchmark_cannot_be_used_as_shipping_c6(self):
        data = self.resolved_packet()
        data["performance_c6"]["prebuild_python_benchmark_used_as_shipping_c6"] = True
        result = validator.validate_packet(data, require_resolved=True)
        self.assertFalse(result["passed"])
        self.assertTrue(any("prebuild Python" in error for error in result["errors"]))

    def test_player_facing_requires_adaptive_refs(self):
        data = self.resolved_packet()
        data["adaptive_readability"]["player_facing_presentation_exists"] = True
        result = validator.validate_packet(data, require_resolved=True)
        self.assertFalse(result["passed"])
        self.assertTrue(any("player-facing evidence" in error for error in result["errors"]))

    def test_wrong_candidate_on_regression_fails(self):
        data = self.resolved_packet()
        data["regression"]["candidate_source"] = "3" * 40
        result = validator.validate_packet(data, require_resolved=True)
        self.assertFalse(result["passed"])
        self.assertTrue(any("regression" in error and "exact candidate" in error for error in result["errors"]))


    def test_rejects_schema_version_drift(self):
        data = self.resolved_packet()
        data["schema_version"] = 2
        result = validator.validate_packet(data, require_resolved=True)
        self.assertFalse(result["passed"])
        self.assertTrue(any("schema_version" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
