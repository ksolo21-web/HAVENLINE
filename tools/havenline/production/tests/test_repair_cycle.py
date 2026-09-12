import copy
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
from validate_repair_cycle import validate_ledger


def fixture():
    return {
        "schema_version": 1,
        "task_id": "T03",
        "task_status": "FIX_REQUIRED",
        "rejected_candidates": [{"commit": "old", "status": "REJECTED"}],
        "repair_range": {"classifications": ["PRODUCTION_FIX", "TEST_FIX"]},
        "same_object_before_after": {
            "same_camera_required": True,
            "capture_source_file": "capture.gd",
            "required_gameplay_evidence_ids": ["river-gate/west/gameplay-scale"],
        },
        "defects": [{
            "defect_id": "D1",
            "critic_source": "critic",
            "visible_symptom": "fence floats",
            "triage": "VALID_PRODUCTION_DEFECT",
            "affected_production_object": "fence",
            "probable_root_cause": "shallow terrain seating",
            "production_files_likely_implicated": ["runtime.gd"],
            "production_change": "seat the fence deeper",
            "expected_visible_result": "continuous snow contact",
            "required_proof": ["river-gate/west/gameplay-scale"],
            "status": "READY_FOR_VERIFICATION",
            "counters": {"evidence_only_attempt_count": 2},
        }],
    }


class RepairCycleTests(unittest.TestCase):
    def test_causal_production_repair_passes(self):
        capture = {"captures": [{
            "evidence_id": "river-gate/west/gameplay-scale",
            "evidence_kind": "gameplay-scale",
            "gameplay_camera_position_and_scale_preserved": True,
        }]}
        self.assertEqual(validate_ledger(fixture(), {"runtime.gd"}, capture, True), [])

    def test_camera_only_repair_is_blocked(self):
        data = fixture()
        data["repair_range"]["classifications"] = ["EVIDENCE_FIX"]
        errors = validate_ledger(data, {"capture.gd"}, None, False)
        self.assertTrue(any("no implicated production file changed" in e for e in errors))
        self.assertTrue(any("lacks PRODUCTION_FIX" in e for e in errors))
        self.assertTrue(any("camera source changed" in e for e in errors))

    def test_rejected_candidate_cannot_be_relabelled(self):
        data = fixture()
        data["rejected_candidates"][0]["status"] = "READY_FOR_VERIFICATION"
        self.assertTrue(any("explicitly REJECTED" in e for e in validate_ledger(data, {"runtime.gd"})))

    def test_closeup_cannot_replace_gameplay_proof(self):
        capture = {"captures": [{
            "evidence_id": "river-gate/west/gameplay-scale",
            "evidence_kind": "threshold-three-quarter",
            "gameplay_camera_position_and_scale_preserved": False,
        }]}
        errors = validate_ledger(fixture(), {"runtime.gd"}, capture, True)
        self.assertTrue(any("non-gameplay proof" in e for e in errors))
        self.assertTrue(any("shipping gameplay scale" in e for e in errors))


if __name__ == "__main__":
    unittest.main()

