import copy,importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('t10aggregate',Path(__file__).parents[1]/'aggregate_critics.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class OriginalOutputTests(unittest.TestCase):
 def rows(self,cid='C1'):
  sha='a'*40
  raw=dict(scores={'fixture_dimension':9.5},defects=[],coverage_complete=True,confidence='high')
  record=dict(raw,task_id='T10',critic_id=cid,candidate_hash=sha,input_manifest_hash='c'*64,provider='synthetic-provider',model='synthetic-model',request_or_run_id='synthetic-request',independent_runtime=True)
  manifest=dict(candidate_commit=sha,critic_id=cid,groups=[{'id':'fixture'}])
  if cid in ('C1','C2'):raw.update({k:record[k] for k in ('task_id','candidate_hash','critic_id','input_manifest_hash','provider','model','request_or_run_id','independent_runtime')})
  if cid=='C3':raw=dict(candidate=sha,critic_id=cid,fatal_error=None,groups=[dict(group='fixture',passed=True,review=raw)])
  return [record,raw,manifest,cid,sha]
 def test_unchanged_visual_and_specialist_outputs(self):
  for cid in ['C1','C2','C3']:m.verify_original(*self.rows(cid))
 def test_visual_raw_identity_rejects_substitution_missing_and_null(self):
  for cid in ('C1','C2'):
   for key,wrong in [('task_id','T11'),('candidate_hash','b'*40),('critic_id','C2' if cid=='C1' else 'C1'),('input_manifest_hash','d'*64),('provider','wrong'),('model','wrong'),('request_or_run_id','wrong'),('independent_runtime',False)]:
    for mode in ('substitute','missing','null'):
     data=self.rows(cid)
     if mode=='missing':del data[1][key]
     else:data[1][key]=wrong if mode=='substitute' else None
     with self.subTest(cid=cid,key=key,mode=mode),self.assertRaises(AssertionError):m.verify_original(*data)
 def test_visual_matching_absent_manifest_hashes_do_not_pass(self):
  for cid in ('C1','C2'):
   for value in (None,''):
    data=self.rows(cid);data[0]['input_manifest_hash']=value;data[1]['input_manifest_hash']=value
    with self.subTest(cid=cid,value=value),self.assertRaises(AssertionError):m.verify_original(*data)
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
 def test_c6_raw_identity_cannot_be_substituted(self):
  data=self.rows('C6');data[1].update(candidate_hash=data[-1],critic_id='C6');m.verify_original(*data)
  for key,value in [('candidate_hash','b'*40),('critic_id','C1')]:
   forged=copy.deepcopy(data);forged[1][key]=value
   with self.subTest(key=key),self.assertRaises(AssertionError):m.verify_original(*forged)

 def test_quantitative_bytes_must_match_reviewed_manifest(self):
  import tempfile,json,hashlib
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/'performance.json';path.write_text(json.dumps({'candidate_commit':'a'*40,'draw_calls':9}))
   item=dict(path='critic-input/performance.json',kind='json',category='quantitative_budgets',sha256=hashlib.sha256(path.read_bytes()).hexdigest())
   manifest=dict(candidate_commit='a'*40,critic_id='C6',groups=[dict(items=[item])])
   m.verify_performance_binding(path,manifest,'a'*40)
   path.write_text(json.dumps({'candidate_commit':'a'*40,'draw_calls':0}))
   with self.assertRaises(AssertionError):m.verify_performance_binding(path,manifest,'a'*40)
