import pathlib, sys, unittest
HERE=pathlib.Path(__file__).resolve();PROD=HERE.parents[1];sys.path.insert(0,str(PROD))
from c0_root_cause_advisor import superseded_report, validate_report
from builder_repair_gate import validate as validate_builder


def packet(conclusion="failure"):
    return {
        "task_id":"T09","failed_run_id":123,"failed_candidate":"a"*40,"integration_head":"b"*40,
        "run_conclusion":conclusion,"current_branch_head":"c"*40,"steps":[],"changed_files":["tools/havenline/task09/motion_capture.py"],
        "protected_files":["HavenlineGodot/assets/characters/Character1.glb"],"unexecuted_checks":["C2","C3"],
    }


def complete_c0():
    return {
        "schema_version":1,"critic_id":"C0","non_voting":True,"validated":True,"report_sha256":"d"*64,
        "diagnosis_id":"C0-T09-123","task_id":"T09","failed_candidate":"a"*40,"failed_run_id":123,"integration_head":"b"*40,
        "diagnosis_status":"DIAGNOSIS_COMPLETE","terminal_class":"TOOLING_DEFECT","complete_known_blocker_set":True,
        "blockers":[{
            "id":"C0-B001","classification":"TOOLING_DEFECT","symptom":"bad pose gate","evidence":["log line"],
            "root_cause":"pixel equality used as pose identity","affected_object":"C5 test harness","causal_fix":"compare skeleton transforms",
            "files_to_change":["tools/havenline/task09/motion_capture.py"],"files_not_to_change":["HavenlineGodot/assets/characters/Character1.glb"],
            "verification":["pose-space preflight passes"]
        }],
        "unexecuted_checks":["C2"],"builder_action":"REPAIR",
        "candidate_freeze":{"required":True,"validation_concurrency_policy":"finish_running_sha","cancelled_run_product_judgment":False},
        "summary":"tooling defect only","confidence":"high"
    }


def plan():
    return {
        "schema_version":1,"task_id":"T09","failed_candidate":"a"*40,"diagnosis_id":"C0-T09-123","c0_report_sha256":"d"*64,
        "full_blocker_set_acknowledged":True,"candidate_freeze_after_build":True,"validation_concurrency_policy":"finish_running_sha",
        "must_not_change":["HavenlineGodot/assets/characters/Character1.glb"],
        "fixes":[{"blocker_id":"C0-B001","files":["tools/havenline/task09/motion_capture.py"],"causal_change":"compare skeleton transforms","verification":["pose-space preflight passes"]}],
        "blast_radius_checks":["T06 regression"],"plan_path":"Docs/Production/T09/REPAIR_PLAN.json"
    }


class C0BuilderTests(unittest.TestCase):
    def test_cancelled_run_is_superseded_not_product_failure(self):
        p=packet("cancelled");r=superseded_report(p)
        self.assertEqual(r["terminal_class"],"SUPERSEDED")
        self.assertEqual(r["builder_action"],"FREEZE_AND_VALIDATE")
        self.assertEqual(r["blockers"][0]["files_to_change"],[])
        self.assertEqual(validate_report(r,p),[])

    def test_complete_tooling_diagnosis_allows_exact_repair_plan(self):
        self.assertEqual(validate_builder(complete_c0(),plan()),[])

    def test_missing_blocker_mapping_is_rejected(self):
        p=plan();p["fixes"]=[]
        self.assertTrue(any("every C0 blocker" in e for e in validate_builder(complete_c0(),p)))

    def test_protected_approved_file_is_rejected(self):
        p=plan();p["fixes"][0]["files"]=["HavenlineGodot/assets/characters/Character1.glb"]
        errors=validate_builder(complete_c0(),p)
        self.assertTrue(any("must_not_change" in e or "exceeds" in e for e in errors))

    def test_post_build_extra_file_is_rejected(self):
        errors=validate_builder(complete_c0(),plan(),["tools/havenline/task09/motion_capture.py","HavenlineGodot/scripts/main.gd"])
        self.assertTrue(any("exceeds authorized surface" in e for e in errors))

    def test_superseded_report_cannot_authorize_builder_repair(self):
        p=packet("cancelled");r=superseded_report(p);r["validated"]=True;r["report_sha256"]="d"*64
        errors=validate_builder(r,plan())
        self.assertTrue(any("superseded" in e for e in errors))

if __name__=="__main__":unittest.main(verbosity=2)
