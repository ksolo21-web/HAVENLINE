import copy,importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('t10close',Path(__file__).parents[1]/'closeout_evidence.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class TerminalTests(unittest.TestCase):
 def rows(self):
  sha='a'*40;run=dict(head_sha=sha,status='completed',conclusion='success');cs=['C1','C2','C3','C4','C6','C7']
  agg=dict(candidate_commit=sha,passed=True,required_critics=cs,quantitative_c6=dict(critic_id='C6',candidate=sha,passed=True),results=[dict(critic_id=c,passed=True,candidate=sha) for c in cs])
  return [sha,run,copy.deepcopy(run),agg,dict(candidate_commit=sha)]
 def test_valid_terminal_inputs(self):self.assertEqual([],m.terminal_errors(*self.rows()))
 def test_failed_or_running_run_rejects(self):
  for key,value in [('status','in_progress'),('conclusion','failure'),('head_sha','b'*40)]:
   r=self.rows();r[1][key]=value;self.assertTrue(m.terminal_errors(*r))
 def test_missing_or_stale_critic_rejects(self):
  r=self.rows();r[3]['results'].pop();self.assertTrue(m.terminal_errors(*r))
  r=self.rows();r[3]['results'][0]['candidate']='b'*40;self.assertTrue(m.terminal_errors(*r))
 def test_missing_provenance_rejects(self):
  r=self.rows();r[4]={};self.assertTrue(m.terminal_errors(*r))

 def test_quantitative_supplement_is_independently_required(self):
  for supplement in ({},dict(critic_id='C6',candidate='b'*40,passed=True),dict(critic_id='C6',candidate='a'*40,passed=False)):
   r=self.rows();r[3]['quantitative_c6']=supplement;self.assertTrue(m.terminal_errors(*r))
