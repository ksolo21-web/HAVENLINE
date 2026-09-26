from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve()
PRODUCTION = HERE.parents[1]
sys.path.insert(0, str(PRODUCTION))

from flake_intelligence import observations_from_files, classify_records
from pipeline_telemetry import records_from_files, summarize
from runtime_dependency_learning import validate_trace

SHA = "a" * 40
ENV = "b" * 64


class FactoryObservationConsumerTests(unittest.TestCase):
    def test_observer_bundle_feeds_flake_and_telemetry_without_repo_ledger_mutation(self):
        bundle = {
            "schema_version": 1,
            "telemetry": {
                "queue_seconds": 5.0,
                "run_seconds": 20.0,
                "gate_durations": {"job::sentinel": 10.0},
                "rerun_count": 1,
                "c0_cycles": 1,
                "proof_cache_hits": 2,
                "artifact_bytes": 4096,
                "terminal_gate": "job: sentinel",
                "terminal_class": "FAILURE",
            },
            "flake_observations": [
                {"source_sha": SHA, "gate_id": "job", "test_id": "sentinel", "environment_fingerprint": ENV, "result": "FAIL"},
                {"source_sha": SHA, "gate_id": "job", "test_id": "sentinel", "environment_fingerprint": ENV, "result": "PASS"},
                {"source_sha": SHA, "gate_id": "job", "test_id": "sentinel", "environment_fingerprint": ENV, "result": "FAIL"},
            ],
        }
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td) / "factory-observation.json"
            path.write_text(json.dumps(bundle))
            flake = observations_from_files([path])
            telemetry = records_from_files([path])
        self.assertTrue(flake["passed"], flake["errors"])
        self.assertTrue(telemetry["passed"], telemetry["errors"])
        classification = classify_records(flake["observations"], SHA, "job", "sentinel", ENV, 3)
        self.assertEqual(classification["classification"], "FLAKY")
        self.assertTrue(classification["mandatory_gate_still_required"])
        summary = summarize(telemetry["records"])
        self.assertEqual(summary["records"], 1)
        self.assertEqual(summary["reruns"], 1)
        self.assertEqual(summary["c0_cycles"], 1)
        self.assertEqual(summary["proof_cache_hits"], 2)

    def test_bad_external_observation_is_rejected_not_partially_learned(self):
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td) / "bad.json"
            path.write_text(json.dumps({"flake_observations": [{"source_sha": SHA, "gate_id": "x", "test_id": "y", "environment_fingerprint": ENV, "result": "MAYBE"}]}))
            loaded = observations_from_files([path])
        self.assertFalse(loaded["passed"])
        self.assertEqual(loaded["observations"], [])

    def test_runtime_trace_contract_is_source_bound_and_additive_only(self):
        trace = {
            "schema_version": 1,
            "source_sha": SHA,
            "task_id": "T10",
            "observer": "fixture-harness",
            "events": [{
                "path": "HavenlineGodot/scripts/world_transaction.gd",
                "affected_task": "T10",
                "suites": ["test_t10_world"],
                "kind": "runtime_call",
            }],
        }
        result = validate_trace(trace)
        self.assertTrue(result["passed"], result["errors"])
        self.assertTrue(result["observation_is_additive_only"])
        self.assertTrue(result["static_coverage_removal_forbidden"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
