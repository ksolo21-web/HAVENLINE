from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve()
PRODUCTION = HERE.parents[1]
sys.path.insert(0, str(PRODUCTION))

from factory_observer import observe, write_bundle


SHA = "a" * 40


def run_doc(conclusion="failure"):
    return {
        "id": 12345,
        "name": "Havenline Task 10 candidate",
        "display_title": "T10 world transformation",
        "head_branch": "havenline/T10-world-transformation",
        "head_sha": SHA,
        "created_at": "2026-09-17T10:00:00Z",
        "run_started_at": "2026-09-17T10:00:05Z",
        "updated_at": "2026-09-17T10:01:00Z",
        "run_attempt": 2,
        "conclusion": conclusion,
        "status": "completed",
    }


def jobs_doc(step_result="failure"):
    return {
        "jobs": [{
            "name": "validate-candidate",
            "conclusion": "failure" if step_result == "failure" else "success",
            "started_at": "2026-09-17T10:00:06Z",
            "completed_at": "2026-09-17T10:00:46Z",
            "steps": [
                {"name": "Set up job", "conclusion": "success", "started_at": "2026-09-17T10:00:06Z", "completed_at": "2026-09-17T10:00:08Z"},
                {"name": "Task sentinel", "conclusion": step_result, "started_at": "2026-09-17T10:00:10Z", "completed_at": "2026-09-17T10:00:40Z"},
                {"name": "Complete job", "conclusion": "success", "started_at": "2026-09-17T10:00:41Z", "completed_at": "2026-09-17T10:00:46Z"},
            ],
        }]
    }


def provenance():
    return {"ImageOS": "ubuntu24", "ImageVersion": "20260907.300.1", "RUNNER_OS": "Linux", "RUNNER_ARCH": "X64"}


class FactoryObserverTests(unittest.TestCase):
    def test_exact_environment_emits_telemetry_flakes_and_task_state(self):
        result = observe(run_doc(), jobs_doc(), {"artifacts": [{"size_in_bytes": 4096}]}, provenance=provenance())
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["task_id"], "T10")
        self.assertTrue(result["environment_exact"])
        self.assertRegex(result["environment_fingerprint"], r"^[0-9a-f]{64}$")
        self.assertEqual(result["telemetry"]["queue_seconds"], 5.0)
        self.assertEqual(result["telemetry"]["rerun_count"], 1)
        self.assertEqual(result["telemetry"]["artifact_bytes"], 4096)
        self.assertEqual(result["telemetry"]["terminal_class"], "FAILURE")
        self.assertIn("Task sentinel", result["telemetry"]["terminal_gate"])
        self.assertTrue(any(row["test_id"] == "Task sentinel" and row["result"] == "FAIL" for row in result["flake_observations"]))
        self.assertIsNotNone(result["task_state"])
        self.assertTrue(result["task_state"]["snapshot_is_derived_not_authority"])

    def test_missing_environment_suppresses_flake_claims_not_telemetry(self):
        result = observe(run_doc(), jobs_doc(), provenance={})
        self.assertTrue(result["passed"])
        self.assertFalse(result["environment_exact"])
        self.assertTrue(result["flake_observations_suppressed"])
        self.assertEqual(result["flake_observations"], [])
        self.assertEqual(result["telemetry"]["terminal_class"], "FAILURE")

    def test_runtime_dependency_trace_must_match_exact_source(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            good = root / "a" / "runtime-dependency-trace.json"
            good.parent.mkdir()
            good.write_text(json.dumps({"source_sha": SHA, "events": [{"path": "HavenlineGodot/scripts/foo.gd"}]}))
            bad = root / "b" / "runtime-dependency-trace.json"
            bad.parent.mkdir()
            bad.write_text(json.dumps({"source_sha": "b" * 40, "events": [{"path": "wrong"}]}))
            result = observe(run_doc(), jobs_doc(), provenance=provenance(), artifact_root=root)
            self.assertEqual(len(result["runtime_dependency_traces"]), 1)
            self.assertEqual(result["runtime_dependency_traces"][0]["trace"]["source_sha"], SHA)

    def test_ambiguous_artifact_provenance_fails_closed_for_flake_fingerprint(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            for idx, version in enumerate(("1", "2")):
                p = root / str(idx) / "runtime-provenance.json"
                p.parent.mkdir()
                row = provenance(); row["ImageVersion"] = version
                p.write_text(json.dumps(row))
            result = observe(run_doc(), jobs_doc(), artifact_root=root)
            self.assertFalse(result["environment_exact"])
            self.assertEqual(result["flake_observations"], [])
            self.assertTrue(result["environment_provenance"]["ambiguous"])

    def test_bundle_writer_produces_machine_records(self):
        with tempfile.TemporaryDirectory() as td:
            result = observe(run_doc("success"), jobs_doc("success"), provenance=provenance())
            write_bundle(result, td)
            root = pathlib.Path(td)
            for name in ("factory-observation.json", "pipeline-telemetry-record.json", "flake-observations.json", "task-state.json"):
                self.assertTrue((root / name).is_file(), name)
            saved = json.loads((root / "factory-observation.json").read_text())
            self.assertTrue(saved["bundle_is_observation_not_authority"])
            self.assertTrue(saved["quality_thresholds_unchanged"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
