#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
TOOL_PATH = ROOT / "tools/havenline/task12/final_candidate_gate.py"
CANDIDATE_TEMPLATE = json.loads((ROOT / "Docs/Production/T12/CANDIDATE_EVIDENCE_TEMPLATE.json").read_text())
CRITIC_TEMPLATE = json.loads((ROOT / "Docs/Production/T12/CRITIC_REVIEW_RECORD_TEMPLATE.json").read_text())
EVIDENCE_INDEX_TEMPLATE = json.loads((ROOT / "Docs/Production/T12/EVIDENCE_INDEX_TEMPLATE.json").read_text())
VECTORS = json.loads((ROOT / "Docs/Production/T12/ENGINE_TEST_VECTORS.json").read_text())
PARITY_SCHEMA = json.loads((ROOT / "Docs/Production/T12/ENGINE_PARITY_OUTPUT_SCHEMA.json").read_text())

spec = importlib.util.spec_from_file_location("t12_final_candidate_gate", TOOL_PATH)
gate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gate)


class T12FinalCandidateGateTests(unittest.TestCase):
    candidate_sha = "a" * 40
    base_sha = "b" * 40
    t10_sha = "c" * 40
    t11_sha = "d" * 40
    levels_digest = "1" * 64
    milestones_digest = "2" * 64
    binding_digest = "3" * 64

    def critic_records(self):
        data = copy.deepcopy(CRITIC_TEMPLATE)
        data["status"] = "CRITIC_REVIEWS_COMPLETE"
        data["candidate_source"] = self.candidate_sha
        for critic, row in data["critics"].items():
            row["independent"] = critic != "C6"
            row["reviewer_runtime_id"] = f"review-runtime-{critic.lower()}"
            row["review_evidence_ref"] = f"artifact://{critic.lower()}-review.json"
            for index, dimension in enumerate(row["dimensions"]):
                dimension["score"] = 9.40 + index * 0.01
                dimension["evidence_refs"] = [f"artifact://{critic.lower()}-{dimension['id']}.json"]
                dimension["unresolved_defects"] = []
        return data

    def critic_minima(self, records):
        return {
            critic: min(float(item["score"]) for item in row["dimensions"])
            for critic, row in records["critics"].items()
        }

    def candidate_packet(self, records):
        data = copy.deepcopy(CANDIDATE_TEMPLATE)
        source = data["exact_source"]
        source["activation_base"] = self.base_sha
        source["candidate_source"] = self.candidate_sha
        source["authorized_changed_file_manifest_ref"] = "artifact://authorized-files.json"
        source["shipping_data_hashes"] = {
            "progression_levels_v1_json_sha256": self.levels_digest,
            "progression_milestones_v1_json_sha256": self.milestones_digest,
            "binding_resolution_json_sha256": self.binding_digest,
        }
        source["upstream_sources"]["T10"] = self.t10_sha
        source["upstream_sources"]["T11"] = self.t11_sha
        source["validator_source"] = "sha256:" + "4" * 64

        for row in data["static_reports"].values():
            row["status"] = "PASS"
            row["evidence_ref"] = "artifact://static-report.json"

        data["engine_parity"].update({
            "status": "PASS",
            "candidate_source": self.candidate_sha,
            "output_ref": "artifact://parity-output.json",
            "comparator_output_ref": "artifact://parity-compare.json",
        })
        data["regression"].update({
            "status": "PASS",
            "candidate_source": self.candidate_sha,
            "run_id": 123,
            "artifact_ref": "artifact://regression.zip",
            "failed_suites": [],
        })
        for name, row in data["functional_sequences"].items():
            row["status"] = "PASS"
            row["evidence_refs"] = [f"artifact://sequence-{name}.json"]
        data["adaptive_readability"]["player_facing_presentation_exists"] = False
        data["performance_c6"].update({
            "status": "PASS",
            "candidate_source": self.candidate_sha,
            "run_id": 456,
            "evidence_ref": "artifact://c6.json",
            "shipping_measurements_present": True,
            "prebuild_python_benchmark_used_as_shipping_c6": False,
            "score": 9.61,
        })

        minima = self.critic_minima(records)
        for critic, row in data["critic_reviews"].items():
            record = records["critics"][critic]
            row.update({
                "status": "PASS",
                "candidate_source": self.candidate_sha,
                "independent": record["independent"],
                "reviewer_runtime_id": record["reviewer_runtime_id"],
                "evidence_ref": record["review_evidence_ref"],
                "minimum_mandatory_dimension_score": minima[critic],
            })
        for key in data["gates"]:
            data["gates"][key] = True
        data["defects"]["unresolved_mandatory"] = []
        return data

    def parity_output(self):
        rows = []
        for case in VECTORS["vectors"]:
            rows.append({
                "vector_id": case["id"],
                "eligible_level_ids": list(case["expected"]["eligible_level_ids"]),
                "new_one_time_event_ids": list(case["expected"]["new_one_time_event_ids"]),
                "state_hash_before": f"state-{case['id']}",
                "state_hash_after": f"state-{case['id']}",
                "repeat_output_hashes": [f"output-{case['id']}", f"output-{case['id']}"],
            })
        return {"task_id": "T12", "candidate_source": self.candidate_sha, "vector_results": rows}

    def binding(self):
        return {
            "schema_version": 1,
            "task_id": "T12",
            "status": "RESOLVED_FOR_ACTIVATION",
            "dependencies": {
                "T10": {"accepted_integrated_source": self.t10_sha, "resolved_public_ids": [{"id": "transform.ready"}]},
                "T11": {"accepted_integrated_source": self.t11_sha, "resolved_public_ids": [{"id": "camp.ready"}]},
            },
            "promotion_allowed": True,
        }

    def evidence_index(self, candidate, records):
        data = copy.deepcopy(EVIDENCE_INDEX_TEMPLATE)
        data["status"] = "EVIDENCE_INDEX_COMPLETE"
        data["candidate_source"] = self.candidate_sha
        refs = sorted(gate.evidence_index_validator.required_refs(candidate, records))
        data["entries"] = [
            {
                "artifact_id": f"evidence-{index:03d}",
                "category": "static_report",
                "uri": uri,
                "sha256": f"{index + 1:064x}",
                "candidate_source": self.candidate_sha,
                "producer": "synthetic-final-gate-test",
                "content_verified": True,
            }
            for index, uri in enumerate(refs)
        ]
        return data

    def validate(
        self,
        candidate=None,
        records=None,
        parity=None,
        evidence_index=None,
        binding=None,
        levels_digest=None,
        progression_validation_result=None,
        binding_verification_result=None,
        checked_out_head=None,
    ):
        records = records if records is not None else self.critic_records()
        candidate = candidate if candidate is not None else self.candidate_packet(records)
        evidence_index = evidence_index if evidence_index is not None else self.evidence_index(candidate, records)
        return gate.validate_consistency(
            candidate,
            records,
            parity if parity is not None else self.parity_output(),
            evidence_index,
            binding if binding is not None else self.binding(),
            progression_validation_result=(
                progression_validation_result
                if progression_validation_result is not None
                else {"passed": True, "errors": []}
            ),
            binding_verification_result=(
                binding_verification_result
                if binding_verification_result is not None
                else {"passed": True, "errors": []}
            ),
            checked_out_head=checked_out_head if checked_out_head is not None else self.candidate_sha,
            levels_sha256=levels_digest if levels_digest is not None else self.levels_digest,
            milestones_sha256=self.milestones_digest,
            binding_resolution_sha256=self.binding_digest,
            vectors=VECTORS,
            parity_schema=PARITY_SCHEMA,
        )

    def test_consistent_synthetic_bundle_passes(self):
        result = self.validate()
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["candidate_source"], self.candidate_sha)
        self.assertTrue(result["evidence_index_passed"])
        self.assertEqual(result["evidence_index_entry_count"], result["evidence_index_required_ref_count"])
        self.assertFalse(result["score_averaging_used"])
        self.assertGreater(result["global_minimum_mandatory_dimension_score"], 9.0)

    def test_critic_candidate_mismatch_fails(self):
        records = self.critic_records()
        candidate = self.candidate_packet(records)
        evidence = self.evidence_index(candidate, records)
        records["candidate_source"] = "e" * 40
        result = self.validate(candidate=candidate, records=records, evidence_index=evidence)
        self.assertFalse(result["passed"])
        self.assertTrue(any("critic records candidate_source" in error for error in result["errors"]))

    def test_shipping_hash_mismatch_fails(self):
        result = self.validate(levels_digest="9" * 64)
        self.assertFalse(result["passed"])
        self.assertTrue(any("progression_levels_v1_json_sha256" in error for error in result["errors"]))

    def test_binding_upstream_mismatch_fails(self):
        binding = self.binding()
        binding["dependencies"]["T10"]["accepted_integrated_source"] = "f" * 40
        result = self.validate(binding=binding)
        self.assertFalse(result["passed"])
        self.assertTrue(any("upstream T10" in error for error in result["errors"]))

    def test_candidate_minimum_must_match_dimension_record(self):
        records = self.critic_records()
        candidate = self.candidate_packet(records)
        evidence = self.evidence_index(candidate, records)
        candidate["critic_reviews"]["C3"]["minimum_mandatory_dimension_score"] = 9.99
        result = self.validate(candidate=candidate, records=records, evidence_index=evidence)
        self.assertFalse(result["passed"])
        self.assertTrue(any("C3 candidate packet minimum" in error for error in result["errors"]))

    def test_reviewer_runtime_mismatch_fails(self):
        records = self.critic_records()
        candidate = self.candidate_packet(records)
        evidence = self.evidence_index(candidate, records)
        candidate["critic_reviews"]["C2"]["reviewer_runtime_id"] = "different-runtime"
        result = self.validate(candidate=candidate, records=records, evidence_index=evidence)
        self.assertFalse(result["passed"])
        self.assertTrue(any("C2 reviewer_runtime_id mismatch" in error for error in result["errors"]))

    def test_parity_candidate_mismatch_fails(self):
        parity = self.parity_output()
        parity["candidate_source"] = "e" * 40
        result = self.validate(parity=parity)
        self.assertFalse(result["passed"])
        self.assertTrue(any("engine parity candidate_source" in error for error in result["errors"]))

    def test_missing_evidence_reference_fails(self):
        records = self.critic_records()
        candidate = self.candidate_packet(records)
        evidence = self.evidence_index(candidate, records)
        evidence["entries"].pop()
        result = self.validate(candidate=candidate, records=records, evidence_index=evidence)
        self.assertFalse(result["passed"])
        self.assertTrue(any("complete evidence digest index failed" in error for error in result["errors"]))

    def test_invalid_actual_shipping_progression_fails(self):
        result = self.validate(
            progression_validation_result={"passed": False, "errors": ["missing level 42"]}
        )
        self.assertFalse(result["passed"])
        self.assertTrue(any("actual split shipping progression data failed" in error for error in result["errors"]))

    def test_unverified_binding_resolution_fails(self):
        result = self.validate(
            binding_verification_result={"passed": False, "errors": ["source drift"]}
        )
        self.assertFalse(result["passed"])
        self.assertTrue(any("exact accepted-source verification" in error for error in result["errors"]))

    def test_wrong_checkout_head_fails(self):
        result = self.validate(checked_out_head="f" * 40)
        self.assertFalse(result["passed"])
        self.assertTrue(any("exact candidate checkout" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
