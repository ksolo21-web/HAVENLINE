import sys,unittest
from pathlib import Path
PROD=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROD))
import opening_loop_canary
class OpeningLoopTests(unittest.TestCase):
 def test_current_authoritative_chain_and_future_gap(self):
  out=opening_loop_canary.validate();self.assertTrue(out['passed'],out)
  for segment in ('move','auto_interact','gather','visible_carry','deliver','transform'):self.assertIn(segment,out['implemented_segments'])
  if 'build_upgrade' in out['pending_segments']: self.assertEqual('build_upgrade',out['next_missing_segment']['segment'])
  self.assertTrue(out['this_is_readiness_not_formal_acceptance'])
if __name__=='__main__':unittest.main()
