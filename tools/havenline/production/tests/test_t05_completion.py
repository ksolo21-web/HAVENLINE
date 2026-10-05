#!/usr/bin/env python3
import copy
import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/"tools/havenline/production"))

from validate_migration import T05_ACCEPTED_SOURCE,t05_completion_errors


def passing_record():
    return {
        "status":"PASS",
        "accepted_gameplay_source":T05_ACCEPTED_SOURCE,
        "acceptance_rule":{"mandatory_dimension_operator":">","mandatory_dimension_threshold":9.0,"unrounded":True,"score_averaging_used":False},
        "mechanical_evidence":{"all_passed":True,"functional_suites":18,"total_assertions_checks":1119,"source_bound_images":77},
        "visual_review":{"passed":True,"status":"PASS","source":T05_ACCEPTED_SOURCE,"score_averaging_used":False,"valid_unresolved_defects":[],"scores":{"C1":{"reference_fidelity":9.5,"visual_language":9.6,"cross_view_consistency":9.7},"C2":{"geometry_contact":9.5,"clipping_seams":9.6,"intentional_gap_integrity":9.7,"cross_view_integrity":9.8}}},
        "performance_critic":{"critic":"C6","passed":True,"coverage_complete":True,"candidate_source":T05_ACCEPTED_SOURCE,"defects":[],"scores":{"frame_time":9.1,"draw_calls":9.2,"geometry":9.3,"texture_memory":9.4,"shader_cost":9.5,"physics":9.6,"animation":9.7,"population":9.8,"thermal_risk":9.9}},
        "final_gate":{"passed":True,"source":T05_ACCEPTED_SOURCE,"ready_for_final_pixel_signoff":True,"errors":[]},
        "pixel_signoff":{"performed_against_accepted_gameplay_source":True,"unresolved_mandatory_task_defects":[]},
        "gates":{f"G{i}":True for i in range(1,15)},
        "artifacts":{name:{"id":index,"digest":"sha256:"+str(index)*64} for index,name in enumerate(("integrated_precritic","visual_resolution","C6","final_gate"),1)},
    }


def passing_ledger():
    return {"task_id":"T05","candidate_commit":T05_ACCEPTED_SOURCE,"defects":[{"id":"T05-D01","status":"REJECTED_AS_INVALID_FINDING"},{"id":"T05-D02","status":"VERIFIED_CLOSED"}]}


class T05CompletionTests(unittest.TestCase):
    def test_accepts_complete_strict_source_bound_record(self):
        self.assertEqual(t05_completion_errors(passing_record(),passing_ledger()),[])

    def test_rejects_exactly_nine(self):
        record=passing_record();record["visual_review"]["scores"]["C1"]["reference_fidelity"]=9.0
        self.assertTrue(any("strictly above 9.0" in row for row in t05_completion_errors(record,passing_ledger())))

    def test_rejects_open_defect(self):
        ledger=passing_ledger();ledger["defects"][1]["status"]="READY_FOR_VERIFICATION"
        self.assertTrue(any("unresolved" in row for row in t05_completion_errors(passing_record(),ledger)))

    def test_rejects_wrong_source_and_incomplete_regression(self):
        record=copy.deepcopy(passing_record())
        record["accepted_gameplay_source"]="0"*40
        record["mechanical_evidence"]["total_assertions_checks"]=1118
        errors=t05_completion_errors(record,passing_ledger())
        self.assertTrue(any("accepted source" in row for row in errors))
        self.assertTrue(any("regression" in row for row in errors))

    def test_rejects_missing_gate_and_invalid_artifact_digest(self):
        record=passing_record()
        del record["gates"]["G14"]
        record["artifacts"]["final_gate"]["digest"]="not-a-digest"
        errors=t05_completion_errors(record,passing_ledger())
        self.assertTrue(any("G1-G14" in row for row in errors))
        self.assertTrue(any("artifact identity" in row for row in errors))


if __name__=="__main__":
    unittest.main()
