"""Synthetic checker fixtures only, never an art verdict or device certificate."""
import unittest,json,importlib.util
from pathlib import Path
sp=importlib.util.spec_from_file_location('gate',Path(__file__).with_name('validate_task01_revision4.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
class Tests(unittest.TestCase):
 def setUp(self):
  self.source='a'*40
  self.review={'observations':['SYNTHETIC CHECK','Not an art verdict'],'defect_count':0,'defect_details':'none','coverage_complete':True,'confidence':'high','scores':{k:9.2 for k in m.KEYS}}
  self.row={'source':self.source,'role':'reference-fidelity','group':'variant-1','independent_execution':True,'competency_passed':True,'passed':True,'lowest_score':9.2,'review':self.review}
 def raw(self):return {'choices':[{'finish_reason':'stop','message':{'content':json.dumps(self.review)}}]}
 def errs(self):return m.validate_review(self.row,self.raw(),self.source)
 def test_valid_synthetic_schema_not_approval(self):self.assertEqual(self.errs(),[])
 def test_exact9(self):
  self.review['scores']={k:9 for k in m.KEYS};self.row['lowest_score']=9;self.assertEqual(self.errs(),[])
 def test_below9(self):self.review['scores']['materials']=8.99;self.assertIn('scores',self.errs())
 def test_nan(self):self.review['scores']['materials']=float('nan');self.assertIn('scores',self.errs())
 def test_infinity(self):self.review['scores']['materials']=float('inf');self.assertIn('scores',self.errs())
 def test_bool_score(self):self.review['scores']['materials']=True;self.assertIn('scores',self.errs())
 def test_missing_dimension(self):self.review['scores'].pop('materials');self.assertIn('scores',self.errs())
 def test_extra_dimension(self):self.review['scores']['fake']=10;self.assertIn('scores',self.errs())
 def test_inflated_minimum(self):self.row['lowest_score']=10;self.assertIn('reported_minimum',self.errs())
 def test_stale_source(self):self.row['source']='b'*40;self.assertIn('source/execution',self.errs())
 def test_nonindependent(self):self.row['independent_execution']=False;self.assertIn('source/execution',self.errs())
 def test_competency_fail(self):self.row['competency_passed']=False;self.assertIn('source/execution',self.errs())
 def test_false_pass(self):self.row['passed']=False;self.assertIn('reviewer_did_not_pass',self.errs())
 def test_defect(self):self.review['defect_count']=1;self.review['defect_details']='broken join';self.assertIn('unresolved_defects',self.errs())
 def test_bool_defect_count(self):self.review['defect_count']=False;self.assertIn('unresolved_defects',self.errs())
 def test_empty_details(self):self.review['defect_details']='';self.assertIn('unresolved_defects',self.errs())
 def test_explicit_no_defect_sentence_not_false_failure(self):self.review['defect_details']='No visible defects in these panels.';self.assertNotIn('unresolved_defects',self.errs())
 def test_incomplete_coverage(self):self.review['coverage_complete']=False;self.assertIn('coverage/confidence',self.errs())
 def test_low_confidence(self):self.review['confidence']='low';self.assertIn('coverage/confidence',self.errs())
 def test_invalid_confidence(self):self.review['confidence']='unreviewed';self.assertIn('coverage/confidence',self.errs())
 def test_truncated(self):
  raw=self.raw();raw['choices'][0]['finish_reason']='length';self.assertIn('raw_mismatch',m.validate_review(self.row,raw,self.source))
 def test_changed_raw_score(self):
  raw=self.raw();self.review['scores']['materials']=9.8;self.assertIn('raw_mismatch',m.validate_review(self.row,raw,self.source))
 def test_empty_raw(self):self.assertIn('invalid_raw',m.validate_review(self.row,{},self.source))
 def test_absolute_path(self):
  with self.assertRaises(ValueError):m.relative(Path('/tmp'),'/etc/passwd')
 def test_parent_path(self):
  with self.assertRaises(ValueError):m.relative(Path('/tmp'),'../etc/passwd')
 def test_over10(self):self.review['scores']['materials']=11;self.assertIn('scores',self.errs())
if __name__=='__main__':unittest.main(verbosity=2)
