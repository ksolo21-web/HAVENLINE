import copy,json,sys,tempfile,unittest
from pathlib import Path
PROD=Path(__file__).resolve().parents[1];ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(PROD))
import v32_forward_prep_harness as h

class ForwardPrepHarnessTests(unittest.TestCase):
 def setUp(self):
  self.can=json.loads((ROOT/'Docs/Production/V32_FORWARD_PREP_CANARIES.json').read_text())
 def test_all_canaries_and_external_status_validate(self):
  out=h.validate_all();self.assertTrue(out['passed'],out);self.assertGreaterEqual(out['domain_count'],12)
 def test_progression_unreachable_and_purchase_required_reject(self):
  r=copy.deepcopy(self.can['progression']);r['nodes'][49]['prerequisites']=['MISSING'];self.assertFalse(h.check('progression',r)['passed'])
  r=copy.deepcopy(self.can['progression']);r['nodes'][10]['purchase_required']=True;self.assertFalse(h.check('progression',r)['passed'])
 def test_difficulty_spend_signal_and_spike_reject(self):
  r=copy.deepcopy(self.can['difficulty']);r['allowed_inputs'].append('purchase_history');self.assertFalse(h.check('difficulty',r)['passed'])
  r=copy.deepcopy(self.can['difficulty']);r['samples'][20]['difficulty']=99;self.assertFalse(h.check('difficulty',r)['passed'])
 def test_save_missing_migration_and_corrupt_recovery_reject(self):
  r=copy.deepcopy(self.can['save_versioning']);r['migrations']=[];self.assertFalse(h.check('save_versioning',r)['passed'])
  r=copy.deepcopy(self.can['save_versioning']);r['corrupt_recovery']='BEST_EFFORT';self.assertFalse(h.check('save_versioning',r)['passed'])
 def test_population_duplicate_identity_and_deadlock_reject(self):
  r=copy.deepcopy(self.can['population']);r['agents'][1]['actor_id']=r['agents'][0]['actor_id'];self.assertFalse(h.check('population',r)['passed'])
  r=copy.deepcopy(self.can['population']);r['deadlocks']=1;self.assertFalse(h.check('population',r)['passed'])
 def test_action_priority_tie_or_wrong_selection_reject(self):
  r=copy.deepcopy(self.can['action_arbitration']);r['contexts'][0]['eligible'][1]['priority']=100;self.assertFalse(h.check('action_arbitration',r)['passed'])
  r=copy.deepcopy(self.can['action_arbitration']);r['contexts'][0]['selected']='move';self.assertFalse(h.check('action_arbitration',r)['passed'])
 def test_motion_missing_species_or_profile_reject(self):
  r=copy.deepcopy(self.can['motion_readiness']);del r['species']['owl'];self.assertFalse(h.check('motion_readiness',r)['passed'])
  r=copy.deepcopy(self.can['motion_readiness']);r['species']['fox']['combat']=[];self.assertFalse(h.check('motion_readiness',r)['passed'])
 def test_transaction_duplicate_debit_and_replay_reject(self):
  r=copy.deepcopy(self.can['transaction_security']);r['attempts'][1]['debit']=25;self.assertFalse(h.check('transaction_security',r)['passed'])
  r=copy.deepcopy(self.can['transaction_security']);r['attempts'][2]['accepted']=True;self.assertFalse(h.check('transaction_security',r)['passed'])
 def test_liveops_duplicate_reward_and_missing_case_reject(self):
  r=copy.deepcopy(self.can['liveops_clock']);r['cases'][0]['duplicate_rewards']=1;self.assertFalse(h.check('liveops_clock',r)['passed'])
  r=copy.deepcopy(self.can['liveops_clock']);r['cases']=r['cases'][:-1];self.assertFalse(h.check('liveops_clock',r)['passed'])
 def test_region_accessibility_and_physical_contracts_fail_closed(self):
  r=copy.deepcopy(self.can['region_template']);r['resources']=[];self.assertFalse(h.check('region_template',r)['passed'])
  r=copy.deepcopy(self.can['accessibility_device']);r['reduced_motion']=False;self.assertFalse(h.check('accessibility_device',r)['passed'])
  r=copy.deepcopy(self.can['physical_reconnaissance']);r['non_certification']=False;self.assertFalse(h.check('physical_reconnaissance',r)['passed'])
 def test_ready_external_without_evidence_rejects(self):
  row={'external':{'billing':{'state':'READY','evidence':None}}};self.assertFalse(h.check('external_capabilities',row)['passed'])
if __name__=='__main__':unittest.main()
