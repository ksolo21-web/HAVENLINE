import sys,unittest
from pathlib import Path
PROD=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROD))
import external_readiness,forward_prep_packet

class FuturePrepPacketTests(unittest.TestCase):
 def test_current_external_readiness_policy_is_valid(self):
  out=external_readiness.evaluate();self.assertTrue(out['passed'],out);self.assertGreaterEqual(int(out['frontier'][1:]),10)
 def test_future_frontier_warns_before_activation(self):
  out=external_readiness.evaluate('T34');self.assertTrue(out['passed'],out)
  self.assertIn('authoritative_backend',out['activation_blockers'])
  self.assertIn('google_play_billing_sandbox',out['activation_blockers'])
  self.assertIn('google_signin_oauth',out['preparation_due'])
  self.assertIn('cloud_backend',out['preparation_due'])
  self.assertIn('physical_phone_4k60',out['preparation_due'])
 def test_task_specific_prep_packets(self):
  cases={
   'T12':['progression','Level 1-100 reachability graph fixture'],
   'T14':['save_versioning','golden-save fixture contract'],
   'T35':['transaction_security','google_play_billing_sandbox'],
   'T62':['progression','validation-only'],
   'T68':['physical_reconnaissance','physical_phone_4k60']
  }
  for task,tokens in cases.items():
   text=forward_prep_packet.render(task)
   self.assertIn('PREPARATION ONLY',text)
   for token in tokens:self.assertIn(token,text,(task,token))
 def test_t11_uses_real_packet_not_future_prep_packet(self):
  with self.assertRaises(ValueError):forward_prep_packet.render('T11')
if __name__=='__main__':unittest.main()
