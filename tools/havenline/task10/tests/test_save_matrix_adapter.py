import os,subprocess,sys,unittest
from pathlib import Path
SCRIPT=Path(__file__).parents[1]/'save_matrix_adapter.py'
class SaveAdapterTests(unittest.TestCase):
 def test_unknown_case_rejects_before_engine(self):
  p=subprocess.run([sys.executable,str(SCRIPT),'made_up_case'],capture_output=True,text=True)
  self.assertNotEqual(0,p.returncode);self.assertIn('Unknown canonical save case',p.stderr)
 def test_wrong_candidate_rejects_before_engine(self):
  p=subprocess.run([sys.executable,str(SCRIPT),'fresh_save'],env=dict(os.environ,HAVENLINE_CANDIDATE='0'*40),capture_output=True,text=True)
  self.assertNotEqual(0,p.returncode);self.assertIn('Exact source binding required',p.stderr)
