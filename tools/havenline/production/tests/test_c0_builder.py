import json, pathlib, sys, tempfile, unittest
HERE=pathlib.Path(__file__).resolve();PROD=HERE.parents[1];sys.path.insert(0,str(PROD))
from c0_root_cause_advisor import C0_MAX_REQUEST_BYTES, build_model_request, c0_response_schema, model_projection, retain_http_error, superseded_report, validate_report
from builder_repair_gate import validate as validate_builder
from collect_artifact_diagnostics import collect as collect_artifact_diagnostics


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
        "c0_report_path":"Docs/Production/T09/C0_ROOT_CAUSE.json",
        "schema_version":1,"task_id":"T09","failed_candidate":"a"*40,"diagnosis_id":"C0-T09-123","c0_report_sha256":"d"*64,
        "repair_base":"e"*40,"full_blocker_set_acknowledged":True,"candidate_freeze_after_build":True,"validation_concurrency_policy":"finish_running_sha",
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
        p=plan();errors=validate_builder(complete_c0(),p,["tools/havenline/task09/motion_capture.py","HavenlineGodot/scripts/main.gd"],p["repair_base"])
        self.assertTrue(any("exceeds authorized surface" in e for e in errors))

    def test_post_build_wrong_base_is_rejected(self):
        p=plan();errors=validate_builder(complete_c0(),p,["tools/havenline/task09/motion_capture.py"],"f"*40)
        self.assertTrue(any("repair_base" in e for e in errors))

    def test_superseded_report_cannot_authorize_builder_repair(self):
        p=packet("cancelled");r=superseded_report(p);r["validated"]=True;r["report_sha256"]="d"*64
        errors=validate_builder(r,plan())
        self.assertTrue(any("superseded" in e for e in errors))

    def test_t10_strict_grounding_rejects_invented_quote_and_path(self):
        p=packet();p.update(task_id="T10",strict_evidence_grounding=True,
            failed_logs='{"required_critics":["C1","C2","C3","C4","C6","C7"]}',
            repository_paths=[".github/workflows/havenline-task10-world-transformation.yml"],
            artifact_diagnostics={"records":[{"path":"tests/integration.log","retained_lines":[{"line":41,"text":"assertion failed: exact lifecycle cost changed"}]}]})
        r=complete_c0();r.update(task_id="T10",diagnosis_id="C0-T10-123")
        row=r["blockers"][0];row["evidence"]=['failure_logs | "required_critics": []'];row["files_to_change"]=[".github/workflows/task10_workflow.yml"]
        errors=validate_report(r,p)
        self.assertTrue(any("exact retained source excerpt" in e for e in errors),errors)
        self.assertTrue(any("exact repository path" in e for e in errors),errors)
        row["evidence"]=["artifact_diagnostics:tests/integration.log#L41 | assertion failed: exact lifecycle cost changed"]
        row["files_to_change"]=[".github/workflows/havenline-task10-world-transformation.yml"]
        self.assertEqual([],validate_report(r,p))

    def test_artifact_diagnostics_retain_hashed_failure_lines(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=pathlib.Path(temporary);path=root/"run"/"tests"/"integration.log";path.parent.mkdir(parents=True)
            path.write_text("ordinary output\nASSERT FAILED: expected 8 wood, got 4\n")
            result=collect_artifact_diagnostics(root)
            self.assertTrue(result["passed"])
            self.assertEqual(1,result["record_count"])
            row=result["records"][0]
            self.assertEqual("run/tests/integration.log",row["path"])
            self.assertEqual("ASSERT FAILED: expected 8 wood, got 4",row["retained_lines"][0]["text"])
            self.assertEqual(64,len(row["sha256"]))

class CausalBookkeepingTests(unittest.TestCase):
    def test_documents_cannot_satisfy_causal_change(self):
        p=plan();c=complete_c0();docs=[p['c0_report_path'],p['plan_path']]
        for changed in [docs,docs[:1],docs[1:]]:
            errors=validate_builder(c,p,changed,p['repair_base'])
            self.assertTrue(any('causal files did not change' in e for e in errors))
        causal=p['fixes'][0]['files']
        self.assertEqual(validate_builder(c,p,causal+docs,p['repair_base']),[])
    def test_bookkeeping_in_fix_is_rejected(self):
        import copy
        p=plan();c=complete_c0()
        for document in [p['c0_report_path'],p['plan_path']]:
            bad=copy.deepcopy(p);bad['fixes'][0]['files'].append(document)
            c['blockers'][0]['files_to_change'].append(document)
            self.assertTrue(any('bookkeeping' in e for e in validate_builder(c,bad)))
        p['fixes'][0]['files']=[]
        self.assertTrue(any('non-bookkeeping causal' in e for e in validate_builder(c,p)))
    def test_canonical_paths_required(self):
        for key in ['c0_report_path','plan_path']:
            for value in [None,'Docs/Production/T10/REPAIR_PLAN.json','../escape']:
                p=plan();p[key]=value
                self.assertTrue(any('canonical' in e for e in validate_builder(complete_c0(),p)))
            p=plan();del p[key]
            self.assertTrue(any('canonical' in e for e in validate_builder(complete_c0(),p)))
    def test_each_blocker_needs_its_own_causal_touch(self):
        import copy
        c=complete_c0();p=plan()
        b=copy.deepcopy(c['blockers'][0]);b['id']='C0-B002';b['files_to_change']=['second.py'];c['blockers'].append(b)
        fix=copy.deepcopy(p['fixes'][0]);fix['blocker_id']='C0-B002';fix['files']=['second.py'];p['fixes'].append(fix)
        actual=p['fixes'][0]['files']+[p['c0_report_path'],p['plan_path']]
        self.assertTrue(any('C0-B002 causal files did not change' in e for e in validate_builder(c,p,actual,p['repair_base'])))
        self.assertEqual(validate_builder(c,p,actual+['second.py'],p['repair_base']),[])
    def test_exact_locked_delta(self):
        import validate_architecture_release_lock as v31
        from validate_architecture_v32_t10 import BUILDER,builder_delta_errors
        accepted=v31._git('show',f'{v31.ACCEPTED_SOURCE}:{BUILDER}').stdout.decode()
        current=(v31.ROOT/BUILDER).read_text()
        self.assertEqual(builder_delta_errors(accepted,current),[])
        self.assertTrue(builder_delta_errors(accepted,current+'\n# drift\n'))
        self.assertTrue(builder_delta_errors(accepted,accepted))

class C0BoundedModelPacketTests(unittest.TestCase):
    def packet(self):
        import hashlib,json
        steps=[]
        for index in range(70):
            conclusion='failure' if index in (4,18,32,46,60) else (None if index>=61 else 'success')
            steps.append({'job':f'job-{index//7}','name':f'step-{index}','status':'completed' if conclusion else 'queued','conclusion':conclusion})
        jobs=[];records=[]
        for index in range(5):
            raw=f'critic C{index+1} failed\nscore: 8.{index}\ndefect: actionable-{index}\n';encoded=raw.encode()
            jobs.append({'job_id':100+index,'name':f'C{index+1}','conclusion':'failure','log_bytes':len(encoded),'log_sha256':hashlib.sha256(encoded).hexdigest(),'raw_log':raw})
            records.append({'path':f'artifacts/C{index+1}/critic-record.json','sha256':str(index)*64,'bytes':1000,'critic_id':f'C{index+1}','task_id':'T10','candidate_hash':'a'*40,'passed':False,'scores':{'dimension':8.5},'defects':[f'actionable-{index}'],'coverage_complete':True,'confidence':'high','fatal_error':None,'groups':[{'group':'g','passed':False,'errors':['unresolved defects'],'lowest_score':8.5,'review':{'defects':[f'actionable-{index}']}}]})
        envelope={'schema_version':1,'run_id':123,'repository':'owner/repo','run_status':'completed','run_conclusion':'failure','diagnostic_marker':None,'jobs':jobs}
        log=json.dumps(envelope,ensure_ascii=False)
        return {'task_id':'T10','failed_run_id':123,'failed_candidate':'a'*40,'integration_head':'b'*40,'integration_branch':'integration','task_branch':'task','current_branch_head':'a'*40,'run_conclusion':'failure','run_status':'completed','workflow_name':'T10','event':'workflow_dispatch','steps':steps,'unexecuted_checks':[f'job-9: step-{i}' for i in range(61,70)],'changed_files':[f'tools/havenline/task10/file-{i}.py' for i in range(74)],'protected_files':['approved/runtime'],'failed_logs':log,'failed_logs_bytes':len(log.encode()),'failed_logs_sha256':hashlib.sha256(log.encode()).hexdigest(),'structured_failure_records':records,'task_scope':'mandatory scope\n'*500,'defect_ledger':'defect ledger\n'*500,'historical_failure_intelligence':{'matches':[],'historical_match_is_advisory_only':True}}

    def test_exact_large_shape_fits_and_preserves_every_failure_boundary(self):
        import hashlib,json
        packet=self.packet();packet_sha=hashlib.sha256(json.dumps(packet,sort_keys=True).encode()).hexdigest()
        body,request_bytes,budget,projection=build_model_request(packet,packet_sha,'diagnose complete blocker set',c0_response_schema())
        self.assertLessEqual(len(request_bytes),C0_MAX_REQUEST_BYTES);self.assertTrue(budget['within_budget'])
        self.assertEqual(request_bytes,json.dumps(body,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
        self.assertEqual(5,len(projection['execution']['failed_terminal_steps']))
        self.assertEqual(packet['unexecuted_checks'],projection['execution']['unexecuted_checks'])
        self.assertEqual(5,len(projection['failure_logs']['jobs']))
        self.assertEqual(5,len(projection['structured_failure_records']))
        self.assertFalse(projection['projection_contract']['arbitrary_character_slice_used'])

    def test_log_digest_substitution_and_unbounded_core_fail_closed(self):
        packet=self.packet();packet['failed_logs_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'digest mismatch'):model_projection(packet,'f'*64)
        packet=self.packet();packet['unexecuted_checks']=['x'*5000]*20
        with self.assertRaisesRegex(RuntimeError,'C0_REQUEST_BUDGET_EXCEEDED'):build_model_request(packet,'f'*64,'prompt',c0_response_schema())

    def test_http_400_status_body_and_safe_headers_are_retained(self):
        import io,json,tempfile,urllib.error
        from email.message import Message
        headers=Message();headers['Content-Type']='application/json';headers['Authorization']='secret'
        error=urllib.error.HTTPError('http://127.0.0.1',400,'Bad Request',headers,io.BytesIO(b'{"error":"context exceeded"}'))
        with tempfile.TemporaryDirectory() as directory:
            out=pathlib.Path(directory);retain_http_error(error,out)
            retained=json.loads((out/'http-error.json').read_text())
            self.assertEqual(400,retained['status']);self.assertIn('context exceeded',retained['body'])
            self.assertEqual({'content-type':'application/json'},retained['headers'])

if __name__=="__main__":unittest.main(verbosity=2)
