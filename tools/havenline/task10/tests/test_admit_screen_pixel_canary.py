import copy
import unittest
from tools.havenline.task10 import admit_screen_pixel_canary as m

class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.actual={'commit':'a'*40,'tree':'b'*40,'ref':'refs/heads/'+m.BRANCH,'event':'push','workflow_path':m.WORKFLOW,'files_sha256':{'view':'c'*64}}
        self.auth={'task_id':'T10','authorization_kind':m.KIND,'disposition':'AUTHORIZED_FOR_ONE_DIAGNOSTIC_EXECUTION','diagnostic_execution_authorized':True,'max_runs':1,'domain_cases':180,'task_approved':False,'profiles':m.PROFILES,'probe':copy.deepcopy(self.actual)}
        self.run={'id':123,'run_attempt':1,'path':m.WORKFLOW,'head_sha':'a'*40,'head_branch':m.BRANCH,'event':'push'}
        self.history={'total_count':1,'workflow_runs':[self.run]}
    def call(self):return m.validate(self.auth,self.actual,self.history,123,'1')
    def test_runner_domain_matches_admission(self):
        import sys
        from pathlib import Path
        sys.path.insert(0,str(Path(__file__).parents[1]))
        import run_screen_pixel_canary as runner
        self.assertEqual(list(runner.PROFILES),m.PROFILES)
        self.assertEqual(sum(len(runner.verifier.profile_cases(p)) for p in runner.PROFILES),180)
        self.assertIn('foldable_inner__1.35',runner.PROFILES)
    def test_exact_admission(self):self.assertTrue(self.call()['admitted'])
    def test_source_file_tree_ref_mutations(self):
        for key in ['commit','tree','ref','event','workflow_path','files_sha256']:
            with self.subTest(key=key):
                actual=copy.deepcopy(self.actual);actual[key]='mutated'
                with self.assertRaises(ValueError):m.validate(self.auth,actual,self.history,123,'1')
    def test_authorization_flags_and_domain(self):
        for key,value in [('max_runs',True),('domain_cases',True),('domain_cases',650),('task_approved',True),('diagnostic_execution_authorized',1),('profiles',[])]:
            auth=copy.deepcopy(self.auth);auth[key]=value
            with self.assertRaises(ValueError):m.validate(auth,self.actual,self.history,123,'1')
    def test_rerun_prior_and_missing_run(self):
        with self.assertRaises(ValueError):m.validate(self.auth,self.actual,self.history,123,'2')
        self.history={'total_count':2,'workflow_runs':[self.run,{**self.run,'id':122}]}
        with self.assertRaises(ValueError):self.call()
        self.history={'total_count':0,'workflow_runs':[]}
        with self.assertRaises(ValueError):self.call()
    def test_incomplete_history(self):
        for count,runs in [(True,[self.run]),(101,[self.run]),(2,[self.run]),(1,None)]:
            self.history={'total_count':count,'workflow_runs':runs}
            with self.assertRaises(ValueError):self.call()
if __name__=='__main__':unittest.main()
