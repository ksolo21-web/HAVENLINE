import hashlib,json,sys,tempfile,unittest
from pathlib import Path
PROD=Path(__file__).resolve().parents[1];ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(PROD))
import architecture_v32,authority_consistency,branch_budget,critic_invalidation,critic_package_preflight,execution_checkpoint,forward_prep_contract,parallel_preparation_planner,performance_ledger,rolling_canary,task_graduation_gate,timeout_stage_plan,blocker_family_gate

SHA='a'*40
class V32Tests(unittest.TestCase):
 def test_t11_assignment_graduation_is_valid(self):
  out=task_graduation_gate.evaluate('T11','ASSIGNED');self.assertTrue(out['passed'],out)
  build=task_graduation_gate.evaluate('T11','BUILDING_ISOLATED')
  manifest=ROOT/'Docs/Production/T11/GRADUATION.json'
  self.assertEqual(manifest.exists(),build['passed'],build)
 def test_parallel_queue_and_external_blockers(self):
  t11=parallel_preparation_planner.classify('T11');self.assertIn(t11['classification'],('BUILD_WHEN_UNLOCKED','ACTIVE_RUNTIME','PRESERVE'))
  t35=parallel_preparation_planner.classify('T35');self.assertIn(t35['classification'],parallel_preparation_planner.load('PARALLEL_PREPARATION_POLICY.json')['classifications'])
  if t35['external_blockers']: self.assertEqual('BLOCKED_EXTERNAL',t35['classification'])
 def test_timeout_checkpoint_is_fail_closed(self):
  good={'schema_version':1,'task_id':'T11','integration_sha':SHA,'candidate_sha':None,'branch':'havenline/T11-camp-construction','stage':'PRECHECK','stage_status':'TIMEOUT','completed_gates':[],'reusable_proof':[],'blocker_families':[],'running_workflows':[123],'next_action':'INFRASTRUCTURE_FAILURE retry same SHA','next_command':'rerun failed shard','updated_at':'now'}
  self.assertTrue(execution_checkpoint.validate_record(good)['passed'])
  bad=dict(good);bad['next_action']='fix gameplay'
  self.assertFalse(execution_checkpoint.validate_record(bad)['passed'])
 def test_three_blockers_require_family_reconciliation(self):
  report={'task_id':'T11','failed_candidate':SHA,'blockers':[{'id':'B1','root_cause':'same root','affected_object':'camp view'},{'id':'B2','root_cause':'same root','affected_object':'camp view'},{'id':'B3','root_cause':'another symptom','affected_object':'camp view'}]}
  p=ROOT/'tools/havenline/production/tests/.v32-blockers.json'
  try:
   p.write_text(json.dumps(report));out=blocker_family_gate.evaluate('T11',SHA,str(p));self.assertFalse(out['passed']);self.assertTrue(out['causal_family_reconciliation_required']);self.assertEqual(3,out['blocker_count'])
  finally:
   p.unlink(missing_ok=True)
 def test_critic_package_preflight_rejects_wrong_source(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);f=d/'note.txt';f.write_text('proof');h=hashlib.sha256(f.read_bytes()).hexdigest()
   m={'task_id':'T11','critic_id':'C3','candidate_commit':SHA,'groups':[{'id':'g1','items':[{'path':'note.txt','kind':'text','sha256':h}]}],'response_contract':{'observations_max':2,'observation_chars_max':160,'defects_max':5,'defect_chars_max':160,'completion_tokens_max':600}}
   mp=d/'manifest.json';mp.write_text(json.dumps(m))
   self.assertTrue(critic_package_preflight.validate_manifest(mp,SHA,'C3')['passed'])
   self.assertFalse(critic_package_preflight.validate_manifest(mp,'b'*40,'C3')['passed'])
 def test_critic_specific_invalidation(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);b=d/'b.json';a=d/'a.json'
   b.write_text(json.dumps({'task_id':'T11','candidate_sha':SHA,'critics':{'C2':'x','C3':'y','C4':'z'}}))
   a.write_text(json.dumps({'task_id':'T11','candidate_sha':SHA,'critics':{'C2':'x','C3':'changed','C4':'z'}}))
   out=critic_invalidation.evaluate(b,a);self.assertEqual(['C3'],out['rerun_critics']);self.assertEqual(['C2','C4'],out['preserve_critics'])
   a.write_text(json.dumps({'task_id':'T11','candidate_sha':'b'*40,'critics':{'C2':'x','C3':'changed','C4':'z'}}))
   out=critic_invalidation.evaluate(b,a);self.assertEqual(['C2','C3','C4'],out['rerun_critics'])
 def test_stage_plan_parallelizes_critics_and_checkpoints(self):
  out=timeout_stage_plan.plan('T11');self.assertGreaterEqual(out['critic_parallelism'],4);self.assertTrue(all(x.get('checkpoint_after') for x in out['shards']))
  self.assertFalse(out['timeout_is_product_judgment'])
 def test_rolling_canaries_start_early(self):
  c11={x['canary'] for x in rolling_canary.requirements('T11')['canaries']};self.assertIn('opening_loop_L1_10',c11)
  c12={x['canary'] for x in rolling_canary.requirements('T12')['canaries']};self.assertIn('level_1_100_reachability',c12)
 def test_branch_and_performance_ledgers_validate(self):
  self.assertTrue(branch_budget.validate()['passed']);self.assertTrue(performance_ledger.validate()['passed'])
 def test_authority_and_forward_prep_contracts(self):
  self.assertTrue(authority_consistency.validate()['passed'])
  prep=forward_prep_contract.validate();self.assertTrue(prep['passed']);self.assertGreaterEqual(prep['prep_task_count'],20)
 def test_full_v32_validator(self):
  out=architecture_v32.validate();self.assertTrue(out['passed'],out);self.assertEqual(60,out['task_count'])
if __name__=='__main__':unittest.main()
