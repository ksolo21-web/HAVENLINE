#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
TOOL_PATH = ROOT / "tools/havenline/task12/initialize_candidate_evidence.py"
TEMPLATE_PATH = ROOT / "Docs/Production/T12/CANDIDATE_EVIDENCE_TEMPLATE.json"

spec = importlib.util.spec_from_file_location("t12_candidate_initializer", TOOL_PATH)
initializer = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(initializer)


class T12CandidateEvidenceInitializerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template = json.loads(TEMPLATE_PATH.read_text())

    def resolution(self):
        return {
            "schema_version": 1,
            "task_id": "T12",
            "status": "RESOLVED_FOR_ACTIVATION",
            "dependencies": {
                "T10": {
                    "accepted_integrated_source": "1" * 40,
                    "verified_completion_path": "Docs/Production/T10/verified-completion.json",
                    "resolved_public_ids": [{"id": "transform.ready", "kind": "transform_state", "source_path": "x.json", "json_pointer": "/id"}],
                },
                "T11": {
                    "accepted_integrated_source": "2" * 40,
                    "verified_completion_path": "Docs/Production/T11/verified-completion.json",
                    "resolved_public_ids": [{"id": "camp.ready", "kind": "camp_state", "source_path": "y.json", "json_pointer": "/id"}],
                },
            },
            "promotion_allowed": True,
        }

    def initialize(self, template=None, resolution=None):
        return initializer.initialize_packet(
            copy.deepcopy(template if template is not None else self.template),
            copy.deepcopy(resolution if resolution is not None else self.resolution()),
            activation_base="a" * 40,
            candidate_source="b" * 40,
            integration_head="9" * 40,
            levels_sha256="c" * 64,
            milestones_sha256="d" * 64,
            binding_resolution_sha256="e" * 64,
            changed_file_manifest_ref="artifact://authorized-files.json",
        )

    def test_initializer_fills_provenance_only(self):
        packet = self.initialize()
        self.assertEqual(packet["status"], "CANDIDATE_EVIDENCE_PENDING_REVIEW")
        self.assertEqual(packet["exact_source"]["candidate_source"], "b" * 40)
        self.assertEqual(packet["exact_source"]["integration_head"], "9" * 40)
        self.assertEqual(packet["exact_source"]["upstream_sources"]["T10"], "1" * 40)
        self.assertEqual(packet["exact_source"]["upstream_sources"]["T11"], "2" * 40)
        self.assertTrue(all(row["status"] == "PENDING" for row in packet["static_reports"].values()))
        self.assertTrue(all(row["status"] == "PENDING" for row in packet["critic_reviews"].values()))
        self.assertTrue(
            all(
                row["status"] == "PENDING" and row["evidence_ref"] == ""
                for row in packet["gates"].values()
            )
        )
        self.assertEqual(
            packet["exact_source"]["validator_source"],
            initializer.validator_bundle.bundle_digest(ROOT),
        )
        self.assertIsNone(packet["performance_c6"]["score"])

    def test_unresolved_binding_record_fails(self):
        resolution = self.resolution()
        resolution["status"] = "PREPARATION_TEMPLATE_UNRESOLVED"
        with self.assertRaisesRegex(ValueError, "RESOLVED_FOR_ACTIVATION"):
            self.initialize(resolution=resolution)

    def test_binding_without_public_ids_fails(self):
        resolution = self.resolution()
        resolution["dependencies"]["T10"]["resolved_public_ids"] = []
        with self.assertRaisesRegex(ValueError, "resolved_public_ids"):
            self.initialize(resolution=resolution)

    def test_invalid_candidate_sha_fails(self):
        with self.assertRaisesRegex(ValueError, "candidate_source"):
            initializer.initialize_packet(
                copy.deepcopy(self.template),
                self.resolution(),
                activation_base="a" * 40,
                candidate_source="not-a-sha",
                integration_head="9" * 40,
                levels_sha256="c" * 64,
                milestones_sha256="d" * 64,
                binding_resolution_sha256="e" * 64,
                changed_file_manifest_ref="artifact://files.json",
                validator_source="sha256:x",
            )

    def test_invalid_integration_head_fails(self):
        with self.assertRaisesRegex(ValueError, "integration_head"):
            initializer.initialize_packet(
                copy.deepcopy(self.template),
                self.resolution(),
                activation_base="a" * 40,
                candidate_source="b" * 40,
                integration_head="not-a-sha",
                levels_sha256="c" * 64,
                milestones_sha256="d" * 64,
                binding_resolution_sha256="e" * 64,
                changed_file_manifest_ref="artifact://files.json",
                validator_source="sha256:x",
            )

    def test_prepassed_static_report_in_template_fails(self):
        template = copy.deepcopy(self.template)
        template["static_reports"]["level_100_completeness"]["status"] = "PASS"
        with self.assertRaisesRegex(ValueError, "pre-passed static report"):
            self.initialize(template=template)

    def test_prepassed_critic_in_template_fails(self):
        template = copy.deepcopy(self.template)
        template["critic_reviews"]["C2"]["status"] = "PASS"
        with self.assertRaisesRegex(ValueError, "pre-pass or pre-score critics"):
            self.initialize(template=template)

    def test_prepassed_gate_in_template_fails(self):
        template = copy.deepcopy(self.template)
        template["gates"]["G1"]["status"] = "PASS"
        template["gates"]["G1"]["evidence_ref"] = "artifact://fake-g1.json"
        with self.assertRaisesRegex(ValueError, "pre-pass or pre-evidence gate G1"):
            self.initialize(template=template)

    def test_prebuild_c6_flag_remains_false(self):
        packet = self.initialize()
        self.assertFalse(packet["performance_c6"]["prebuild_python_benchmark_used_as_shipping_c6"])


    def test_invalid_validator_source_digest_fails(self):
        with self.assertRaisesRegex(ValueError, "validator_source"):
            initializer.initialize_packet(
                copy.deepcopy(self.template),
                self.resolution(),
                activation_base="a" * 40,
                candidate_source="b" * 40,
                integration_head="9" * 40,
                levels_sha256="c" * 64,
                milestones_sha256="d" * 64,
                binding_resolution_sha256="e" * 64,
                changed_file_manifest_ref="artifact://files.json",
                validator_source="sha256:" + "f" * 64,
            )



if __name__ == "__main__":
    unittest.main()
