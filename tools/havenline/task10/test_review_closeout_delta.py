import copy, json, pathlib, sys, unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import review_closeout_delta as r
class OwnerDeltaTests(unittest.TestCase):
 def good(self):return {'observations':['First complete observation.','Second complete observation.','Third complete observation.'],'defects':[],'coverage_complete':True,'confidence':'high','scores':{d:9.7 for d in r.DIMENSIONS['authority']}}
 def test_pass(self):self.assertEqual([],r.validate(self.good(),r.DIMENSIONS['authority']))
 def test_nine_fails(self):
  row=self.good();row['scores']['source_binding']=9.0;self.assertTrue(r.validate(row,r.DIMENSIONS['authority']))
 def test_unrounded(self):
  row=self.good();row['scores']['source_binding']=9.00000001;self.assertFalse(r.validate(row,r.DIMENSIONS['authority']))
 def test_nan_fails(self):
  row=self.good();row['scores']['source_binding']=float('nan');self.assertTrue(r.validate(row,r.DIMENSIONS['authority']))
 def test_bool_fails(self):
  row=self.good();row['scores']['source_binding']=True;self.assertTrue(r.validate(row,r.DIMENSIONS['authority']))
 def test_missing_dimension(self):
  row=self.good();del row['scores']['source_binding'];self.assertTrue(r.validate(row,r.DIMENSIONS['authority']))
 def test_missing_coverage(self):
  row=self.good();row['coverage_complete']=False;self.assertTrue(r.validate(row,r.DIMENSIONS['authority']))
 def test_defect_blocks(self):
  row=self.good();row['defects']=['Concrete defect.'];self.assertTrue(r.validate(row,r.DIMENSIONS['authority']))
 def test_unfinished_blocks(self):
  row=self.good();row['observations'][0]='not finished';self.assertTrue(r.validate(row,r.DIMENSIONS['authority']))
 def test_low_confidence(self):
  row=self.good();row['confidence']='low';self.assertTrue(r.validate(row,r.DIMENSIONS['authority']))
 def test_duplicate_raw_key(self):
  with self.assertRaises(ValueError):r.strict_json('{"a":1,"a":2}')
 def test_nonfinite_raw(self):
  with self.assertRaises(ValueError):r.strict_json('{"score":NaN}')
 def test_semantic_delta(self):
  a={'k':[1,2],'x':7};b={'k':[1,3,4],'y':8}
  self.assertEqual([{'path':'/k/1','before':2,'after':3},{'path':'/k/2','added':4},{'path':'/x','removed':7},{'path':'/y','added':8}],r.semantic_delta(a,b))
 def test_semantic_equal_representation(self):self.assertEqual([],r.semantic_delta({'a':9},{'a':9.0}))
 def test_grammar_does_not_force_success(self):
  grammar=r.review_grammar(r.schema(r.DIMENSIONS['authority']));self.assertIn('"false"',grammar);self.assertIn('number ::=',grammar);self.assertIn('defects ::= ',grammar)
if __name__=='__main__':unittest.main()
