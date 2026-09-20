import json,os,pathlib,sys,tempfile,unittest,zipfile
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent));import resolve_closeout_admission as s
PREP=os.environ['T10_PREP_ARCHIVE']
class PacketRepair(unittest.TestCase):
 def test_changed_statements_are_current_only(self):
  a='check("test", false)\n';b='check("test", true)\n'
  rows=s.assertions(a,b);self.assertEqual('check("test", true)',rows[0]['current_statement']);self.assertNotIn('false',str(rows))
 def test_unchanged_assertions_not_repaired(self):self.assertEqual([],s.assertions('check("a",true)','check("a",true)'))
 def test_complete_named_function(self):
  x=s.function('func a():\n\tpass\nfunc b():\n\tpass\n','a');self.assertEqual('func a():\n\tpass\n',x['complete_body'])
 def test_ambiguous_function_rejects(self):
  with self.assertRaises(ValueError):s.function('func a():\n\tpass\nfunc a():\n\tpass\n','a')
 def test_current_eight_assertions_match_engine_rows(self):
  _,d=s.packet('assertions',PREP);rows=[x for p in d['evidence']['current_assertions'] for x in p['all_changed_current_assertions']]
  self.assertEqual(8,len(rows));self.assertTrue(all('PASS' in x['executed_result'] for x in rows))
 def test_current_assertions_do_not_contain_removed_policy(self):
  text,_=s.packet('assertions',PREP);self.assertNotIn('constrained_screen_lanes_v1',text);self.assertNotIn('BLOCKED — deliver missing resources',text)
 def test_existing_invalid_scale_implementation_included(self):
  text,_=s.packet('assertions',PREP);self.assertIn('pixels_per_label_unit <= 0.0',text);self.assertIn('return Vector2.ZERO',text)
 def test_history_not_current_verdict(self):
  _,d=s.packet('authority',PREP);history=d['evidence']['historical_metadata'];self.assertEqual(s.r.BASE,history['recorded_previous_source']);self.assertEqual(s.r.SOURCE,history['current_source_engine_results']['source']);self.assertTrue(history['all_exact_canonical_bytes_verified']);self.assertEqual(24,history['inherited_paths_count'])
 def test_binding_graph_matches_current_source(self):
  _,d=s.packet('authority',PREP);self.assertEqual(4,len(d['evidence']['executed_current_bindings']));self.assertTrue(all(x['equality_test'] for x in d['evidence']['executed_current_bindings']))
 def test_complete_metadata_not_promoted(self):
  text,d=s.packet('authority',PREP);self.assertIn('pending and blocked',text);self.assertFalse(d['task_approved'])
 def test_rejected_reviews_do_not_become_passes(self):
  row={'observations':['A.','B.','C.'],'defects':['An actual defect.'],'coverage_complete':True,'confidence':'high','scores':{d:9.0 for d in s.r.DIMENSIONS['authority']}}
  self.assertTrue(s.r.validate(row,s.r.DIMENSIONS['authority']))
 def test_evidence_review_cannot_be_rerun(self):
  with self.assertRaises(ValueError):s.packet('evidence',PREP)
if __name__=='__main__':unittest.main()
