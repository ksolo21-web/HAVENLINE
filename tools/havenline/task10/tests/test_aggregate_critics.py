import copy,importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('t10aggregate',Path(__file__).parents[1]/'aggregate_critics.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class OriginalOutputTests(unittest.TestCase):
 def rows(self,cid='C1'):
  sha='a'*40
  raw=dict(scores={'fixture_dimension':9.5},defects=[],coverage_complete=True,confidence='high')
  record=dict(raw,critic_id=cid,candidate_hash=sha,independent_runtime=True)
  manifest=dict(candidate_commit=sha,critic_id=cid,groups=[{'id':'fixture'}])
  if cid=='C3':raw=dict(candidate=sha,critic_id=cid,fatal_error=None,groups=[dict(group='fixture',passed=True,review=raw)])
  return [record,raw,manifest,cid,sha]
 def test_unchanged_visual_and_specialist_outputs(self):
  for cid in ['C1','C3']:m.verify_original(*self.rows(cid))
 def test_score_or_disposition_rewrite_rejects(self):
  for key,value in [('scores',{'fixture_dimension':10}),('defects',['actual defect']),('coverage_complete',False),('confidence','low'),('independent_runtime',False),('candidate_hash','b'*40)]:
   data=self.rows();data[0][key]=value
   with self.subTest(key=key),self.assertRaises(AssertionError):m.verify_original(*data)
 def test_missing_or_failed_raw_group_rejects(self):
  for change in ['missing','failed','fatal']:
   data=self.rows('C3')
   if change=='missing':data[1]['groups']=[]
   elif change=='failed':data[1]['groups'][0]['passed']=False
   else:data[1]['fatal_error']='truncated'
   with self.subTest(change=change),self.assertRaises(AssertionError):m.verify_original(*data)
