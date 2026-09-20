import copy
import unittest
from tools.havenline.task10 import admit_screen_pixel_full as m

class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.actual={'commit':'a'*40,'tree':'b'*40,'ref':'refs/heads/'+m.BRANCH,'event':'push','workflow_path':m.WORKFLOW,'files_sha256':{'view':'c'*64}}
        self.auth={'task_id':'T10','authorization_kind':m.KIND,'disposition':'AUTHORIZED_FOR_ONE_DIAGNOSTIC_EXECUTION','diagnostic_execution_authorized':True,'max_runs':1,'domain_cases':684,'task_approved':False,'profiles':m.PROFILES,'probe':copy.deepcopy(self.actual)}
        self.auth['prerequisite_canary']={'run_id':35483383557,'source':'31f08a6830dcb55855f5c7ef2a54ddb773e99b97','passed':True,'artifact_zip_sha256':'d'*64,'independent_result_review_sha256':'e'*64}
        self.canary={'id':35483383557,'head_sha':'31f08a6830dcb55855f5c7ef2a54ddb773e99b97','status':'completed','conclusion':'success','run_attempt':1}
        self.run={'id':123,'run_attempt':1,'path':m.WORKFLOW,'head_sha':'a'*40,'head_branch':m.BRANCH,'event':'push'}
        self.history={'total_count':1,'workflow_runs':[self.run]}
    def call(self):return m.validate(self.auth,self.actual,self.history,123,'1',self.canary)
    def test_runner_domain_matches_admission(self):
        import sys
        from pathlib import Path
        sys.path.insert(0,str(Path(__file__).parents[1]))
        import run_screen_pixel_canary as runner
        self.assertEqual(list(runner.FULL_PROFILES),m.PROFILES)
        self.assertEqual(sum(len(runner.verifier.profile_cases(p)) for p in runner.FULL_PROFILES),684)
        self.assertIn('foldable_inner__1.35',runner.FULL_PROFILES)
    def test_canary_must_be_exact_accepted_complete_run(self):
        for key,value in [('head_sha','wrong'),('conclusion','failure'),('status','in_progress'),('id',0),('run_attempt',2)]:
            canary=dict(self.canary);canary[key]=value
            with self.assertRaises(ValueError):m.validate(self.auth,self.actual,self.history,123,'1',canary)
        self.auth['prerequisite_canary']['independent_result_review_sha256']=''
        with self.assertRaises(ValueError):self.call()
    def test_exact_admission(self):self.assertTrue(self.call()['admitted'])
    def test_source_file_tree_ref_mutations(self):
        for key in ['commit','tree','ref','event','workflow_path','files_sha256']:
            with self.subTest(key=key):
                actual=copy.deepcopy(self.actual);actual[key]='mutated'
                with self.assertRaises(ValueError):m.validate(self.auth,actual,self.history,123,'1',self.canary)
    def test_authorization_flags_and_domain(self):
        for key,value in [('max_runs',True),('domain_cases',True),('domain_cases',650),('task_approved',True),('diagnostic_execution_authorized',1),('profiles',[])]:
            auth=copy.deepcopy(self.auth);auth[key]=value
            with self.assertRaises(ValueError):m.validate(auth,self.actual,self.history,123,'1',self.canary)
    def test_rerun_prior_and_missing_run(self):
        with self.assertRaises(ValueError):m.validate(self.auth,self.actual,self.history,123,'2',self.canary)
        self.history={'total_count':2,'workflow_runs':[self.run,{**self.run,'id':122}]}
        with self.assertRaises(ValueError):self.call()
        self.history={'total_count':0,'workflow_runs':[]}
        with self.assertRaises(ValueError):self.call()
    def test_incomplete_history(self):
        for count,runs in [(True,[self.run]),(101,[self.run]),(2,[self.run]),(1,None)]:
            self.history={'total_count':count,'workflow_runs':runs}
            with self.assertRaises(ValueError):self.call()
if __name__=='__main__':unittest.main()
