import hashlib,json,re,subprocess,sys,tempfile,unittest
from pathlib import Path

PROD=Path(__file__).resolve().parents[1]
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(PROD))

import architecture_v32
import authority_consistency
import blocker_family_gate
import branch_budget
import critic_invalidation
import critic_package_preflight
import control_plane_lineage
import execution_checkpoint
import forward_prep_contract
import forward_task_control
import gate_result_recorder
import failure_learning
import parallel_preparation_planner
import performance_ledger
import rolling_canary
import task_graduation_gate
import timeout_stage_plan
import v32_assignment_claim

SHA='a'*40

class V32Tests(unittest.TestCase):
 def test_t11_assignment_graduation_is_valid(self):
  head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
  stale='fbb81ae34b9053f17fc937fb7e67895e3ef0584b'
  stale_lineage=control_plane_lineage.assess(stale,head)
  self.assertFalse(stale_lineage['passed'],stale_lineage)
  self.assertTrue(stale_lineage['control_plane_sync_required'],stale_lineage)
  self.assertTrue(stale_lineage['governance_only_drift'],stale_lineage)
  self.assertFalse(stale_lineage['runtime_reset_required'],stale_lineage)
  stale_gate=task_graduation_gate.evaluate('T11','ASSIGNED',stale,head)
  self.assertFalse(stale_gate['passed'],stale_gate)
  self.assertFalse(stale_gate['checks']['control_plane_lineage'],stale_gate)
  out=task_graduation_gate.evaluate('T11','ASSIGNED',head,head)
  self.assertTrue(out['passed'],out)
  self.assertTrue(out['checks']['control_plane_lineage'],out)
  build=task_graduation_gate.evaluate('T11','BUILDING_ISOLATED',head,head)
  manifest=ROOT/'Docs/Production/T11/GRADUATION.json'
  self.assertEqual(manifest.exists(),build['passed'],build)

 def test_parallel_queue_and_external_blockers(self):
  t11=parallel_preparation_planner.classify('T11')
  self.assertIn(t11['classification'],('BUILD_WHEN_UNLOCKED','ACTIVE_RUNTIME','PRESERVE'))
  t35=parallel_preparation_planner.classify('T35')
  classes=parallel_preparation_planner.load('PARALLEL_PREPARATION_POLICY.json')['classifications']
  self.assertIn(t35['classification'],classes)
  if t35['external_blockers']:
   self.assertEqual('BLOCKED_EXTERNAL',t35['classification'])

 def test_timeout_checkpoint_is_fail_closed(self):
  good={
   'schema_version':1,'task_id':'T11','integration_sha':SHA,'candidate_sha':None,
   'branch':'havenline/T11-camp-construction','stage':'PRECHECK','stage_status':'TIMEOUT',
   'completed_gates':[],'reusable_proof':[],'blocker_families':[],'running_workflows':[123],
   'next_action':'INFRASTRUCTURE_FAILURE retry same SHA','next_command':'rerun failed shard','updated_at':'now'
  }
  self.assertTrue(execution_checkpoint.validate_record(good)['passed'])
  bad=dict(good);bad['next_action']='fix gameplay'
  self.assertFalse(execution_checkpoint.validate_record(bad)['passed'])

 def test_checkpoint_advance_hashes_prior_state_and_refuses_source_switch(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'checkpoint.json'
   row={
    'schema_version':1,'task_id':'T11','integration_sha':SHA,'candidate_sha':None,
    'branch':'havenline/T11-camp-construction','stage':'PRECHECK','stage_status':'PASS',
    'completed_gates':[],'reusable_proof':[],'blocker_families':[],'running_workflows':[],
    'next_action':'build','next_command':'build command','updated_at':'now'
   }
   p.write_text(json.dumps(row))
   class A: pass
   a=A();a.integration=None;a.candidate='b'*40;a.stage='BUILD';a.status='RUNNING'
   a.add_gate=['scope_dependency'];a.proof=['packet'];a.blocker_family=[];a.workflow_id=[77]
   a.clear_running_workflows=False;a.environment='env';a.next_action='run sentinel'
   a.next_command='sentinel command';a.notes='bounded build'
   updated,result=execution_checkpoint.advance_record(p,a)
   self.assertTrue(result['passed'],result)
   self.assertRegex(updated['previous_checkpoint_sha256'],r'^[0-9a-f]{64}$')
   self.assertEqual(['scope_dependency'],updated['completed_gates'])
   self.assertEqual([77],updated['running_workflows'])
   a.candidate='c'*40
   _,result=execution_checkpoint.advance_record(p,a)
   self.assertFalse(result['passed'])
   self.assertIn('candidate SHA change requires a new checkpoint',result['errors'])

 def test_three_blockers_require_family_reconciliation(self):
  report={
   'task_id':'T11','failed_candidate':SHA,
   'blockers':[
    {'id':'B1','root_cause':'same root','affected_object':'camp view'},
    {'id':'B2','root_cause':'same root','affected_object':'camp view'},
    {'id':'B3','root_cause':'another symptom','affected_object':'camp view'}
   ]
  }
  p=ROOT/'tools/havenline/production/tests/.v32-blockers.json'
  try:
   p.write_text(json.dumps(report))
   out=blocker_family_gate.evaluate('T11',SHA,str(p))
   self.assertFalse(out['passed'])
   self.assertTrue(out['causal_family_reconciliation_required'])
   self.assertEqual(3,out['blocker_count'])
  finally:
   p.unlink(missing_ok=True)

 def test_critic_package_preflight_rejects_wrong_source_and_missing_evidence(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);note=d/'note.txt';note.write_text('proof')
   h=hashlib.sha256(note.read_bytes()).hexdigest()
   manifest={
    'task_id':'T11','critic_id':'C3','candidate_commit':SHA,
    'groups':[{'id':'g1','items':[{'path':'note.txt','kind':'text','sha256':h}]}],
    'response_contract':{
     'observations_max':2,'observation_chars_max':160,'defects_max':5,
     'defect_chars_max':160,'completion_tokens_max':600
    }
   }
   mp=d/'manifest.json';mp.write_text(json.dumps(manifest))
   self.assertTrue(critic_package_preflight.validate_manifest(mp,SHA,'C3')['passed'])
   pkg=d/'pkg';pkg.mkdir();nested=pkg/'manifest.json';nested.write_text(json.dumps(manifest))
   self.assertFalse(critic_package_preflight.validate_manifest(nested,SHA,'C3')['passed'])
   self.assertTrue(critic_package_preflight.validate_manifest(nested,SHA,'C3',d)['passed'])
   self.assertFalse(critic_package_preflight.validate_manifest(mp,'b'*40,'C3')['passed'])
   note.unlink()
   self.assertFalse(critic_package_preflight.validate_manifest(mp,SHA,'C3')['passed'])
   manifest['groups'][0]['items'][0]['external_uri']='artifact://source-bound-note'
   mp.write_text(json.dumps(manifest))
   self.assertTrue(critic_package_preflight.validate_manifest(mp,SHA,'C3')['passed'])

 def test_critic_specific_invalidation_uses_exact_input_fingerprints(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);before=d/'before.json';after=d/'after.json'
   fx='1'*64;fy='2'*64;fz='3'*64;changed='4'*64
   before.write_text(json.dumps({
    'task_id':'T11','candidate_sha':SHA,
    'critics':{
     'C2':{'input_fingerprint':fx,'disposition':'PASS'},
     'C3':{'input_fingerprint':fy,'disposition':'PASS'},
     'C4':{'input_fingerprint':fz,'disposition':'PASS'}
    }
   }))
   after.write_text(json.dumps({
    'task_id':'T11','candidate_sha':SHA,
    'critics':{
     'C2':{'input_fingerprint':fx,'disposition':'PASS'},
     'C3':{'input_fingerprint':changed,'disposition':'PASS'},
     'C4':{'input_fingerprint':fz,'disposition':'PASS'}
    }
   }))
   out=critic_invalidation.evaluate(before,after)
   self.assertTrue(out['passed'],out)
   self.assertEqual(['C3'],out['rerun_critics'])
   self.assertEqual(['C2','C4'],out['preserve_critics'])
   changed_source=json.loads(after.read_text());changed_source['candidate_sha']='b'*40
   after.write_text(json.dumps(changed_source))
   out=critic_invalidation.evaluate(before,after)
   self.assertEqual(['C2','C3','C4'],out['rerun_critics'])
   self.assertEqual([],out['preserve_critics'])
   invalid={
    'task_id':'T11','candidate_sha':SHA,
    'critics':{'C2':{'input_fingerprint':'not-a-hash','disposition':'PASS'}}
   }
   after.write_text(json.dumps(invalid))
   self.assertFalse(critic_invalidation.evaluate(before,after)['passed'])

 def test_stage_plan_parallelizes_critics_and_checkpoints(self):
  out=timeout_stage_plan.plan('T11')
  self.assertGreaterEqual(out['critic_parallelism'],4)
  self.assertTrue(all(x.get('checkpoint_after') for x in out['shards']))
  self.assertFalse(out['timeout_is_product_judgment'])

 def test_rolling_canaries_start_early(self):
  c11={x['canary'] for x in rolling_canary.requirements('T11')['canaries']}
  self.assertIn('opening_loop_L1_10',c11)
  c12={x['canary'] for x in rolling_canary.requirements('T12')['canaries']}
  self.assertIn('level_1_100_reachability',c12)

 def test_branch_and_performance_ledgers_validate(self):
  self.assertTrue(branch_budget.validate()['passed'])
  self.assertTrue(performance_ledger.validate()['passed'])
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'branches.json'
   p.write_text(json.dumps(['havenline/T11-camp-construction']))
   self.assertTrue(branch_budget.validate(inventory=str(p))['passed'])
   p.write_text(json.dumps(['havenline/T11-camp-construction','havenline/T11-repair-a','havenline/T11-repair-b']))
   self.assertFalse(branch_budget.validate(inventory=str(p))['passed'])
   p.write_text(json.dumps(['havenline/T11-camp-construction','havenline/T11-prototype']))
   self.assertFalse(branch_budget.validate(inventory=str(p))['passed'])
   p.write_text(json.dumps(['havenline/T11-camp-construction','havenline/T12-unregistered']))
   self.assertFalse(branch_budget.validate(inventory=str(p))['passed'])

 def test_authority_and_forward_prep_contracts(self):
  self.assertTrue(authority_consistency.validate()['passed'])
  prep=forward_prep_contract.validate()
  self.assertTrue(prep['passed'])
  self.assertGreaterEqual(prep['prep_task_count'],20)

 def test_v32_workflow_actions_are_exact_sha_pinned(self):
  pattern=re.compile(r'uses:\s*(actions/[^@\s]+)@([^\s]+)')
  for rel in ('.github/workflows/havenline-v32-task-preflight.yml','.github/workflows/havenline-v32-specialist-fanout.yml'):
   body=(ROOT/rel).read_text()
   for _,ref in pattern.findall(body):
    self.assertRegex(ref,r'^[0-9a-f]{40}$',rel)

 def test_shared_forward_task_control_is_fail_closed_and_partitions_critics(self):
  head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
  stale=forward_task_control.plan('T11','ASSIGNED',builder='fbb81ae34b9053f17fc937fb7e67895e3ef0584b',integration=head)
  self.assertFalse(stale['passed'],stale)
  out=forward_task_control.plan('T11','ASSIGNED',builder=head,integration=head)
  self.assertTrue(out['passed'],out)
  self.assertEqual(['C3','C4'],out['critic_plan']['specialist_fanout'])
  self.assertEqual(['C2'],out['critic_plan']['reference_specific'])
  self.assertEqual(['C6'],out['critic_plan']['deterministic'])
  blocked=forward_task_control.plan('T11','BUILDING_ISOLATED',builder=head,integration=head)
  self.assertFalse(blocked['passed'])
  self.assertTrue(any('explicit exact candidate SHA' in x for x in blocked['errors']))
  self.assertTrue(forward_task_control.validate_all()['passed'])

 def test_assignment_claim_binds_actual_remote_branch_tips(self):
  head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
  stale=v32_assignment_claim.validate_assignment('T11','havenline/T11-camp-construction','fbb81ae34b9053f17fc937fb7e67895e3ef0584b',head,verify_remote=False)
  self.assertFalse(stale['passed'],stale)
  synced=v32_assignment_claim.validate_assignment('T11','havenline/T11-camp-construction',head,head,verify_remote=False)
  self.assertTrue(synced['passed'],synced)
  body=(ROOT/'tools/havenline/production/v32_assignment_claim.py').read_text()
  for token in ('remote_branch_head','actual_builder','actual_integration','assignment_integration_commit','assignment_branch_head','assignment_lineage_state','legacy_claim'):
   self.assertIn(token,body)

 def test_shared_workflow_avoids_expression_flow_maps(self):
  body=(ROOT/'.github/workflows/havenline-v32-task-preflight.yml').read_text()
  for line in body.splitlines():
   if '${{' in line:
    self.assertFalse('{' in line.split(':',1)[-1].lstrip()[:1],line)
  self.assertNotIn('env: {TASK: ${{',body)
  self.assertNotIn('with: {ref: ${{',body)

 def test_shared_workflow_contains_preflight_review_failure_modes(self):
  body=(ROOT/'.github/workflows/havenline-v32-task-preflight.yml').read_text()
  for token in ('mode:','preflight','review','failure','builder_sha','lineage_head','control_plane_lineage.py','forward_task_control.py','critic_package_preflight.py','havenline-v32-specialist-fanout.yml','havenline-c0-root-cause.yml','cancel-in-progress: false'):
   self.assertIn(token,body)

 def test_gate_result_proposals_require_owner_promotion(self):
  import subprocess
  head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
  evidence=ROOT/'tools/havenline/production/tests/.gate-result-evidence.json'
  try:
   evidence.write_text(json.dumps({'passed':True,'task_id':'T11'}))
   proposal=gate_result_recorder.proposal('T11','scope_dependency',head,str(evidence.relative_to(ROOT)))
   self.assertTrue(gate_result_recorder.validate_proposal(proposal)['passed'])
   self.assertFalse(proposal['approval_authority_granted'])
   with tempfile.TemporaryDirectory() as td:
    pp=Path(td)/'proposal.json';pp.write_text(json.dumps(proposal))
    index=Path(td)/'index.json';index.write_text((ROOT/'Docs/Production/GATE_RESULT_INDEX.json').read_text())
    self.assertFalse(gate_result_recorder.apply_proposal(pp,index,'WRONG')['passed'])
    result=gate_result_recorder.apply_proposal(pp,index,gate_result_recorder.OWNER_DISPOSITION)
    self.assertTrue(result['passed'],result)
    self.assertFalse(result['record']['approval_authority_granted'])
  finally:
   evidence.unlink(missing_ok=True)

 def test_failure_learning_stages_unverified_and_requires_verified_owner_promotion(self):
  doc=failure_learning.propose('Docs/Production/T10/C0_ROOT_CAUSE.json')
  self.assertTrue(doc['passed'],doc)
  self.assertGreater(doc['proposal_count'],0)
  proposal=doc['proposals'][0]
  self.assertEqual('UNVERIFIED_C0_LESSON',proposal['state'])
  self.assertFalse(proposal['approval_authority_granted'])
  with tempfile.TemporaryDirectory() as td:
   pd=Path(td)/'proposals.json';pd.write_text(json.dumps(doc))
   verification=Path(td)/'verification.json'
   verification.write_text(json.dumps({
    'owner_disposition':failure_learning.OWNER_DISPOSITION,
    'proposal_id':proposal['proposal_id'],'candidate_after_repair':'b'*40,
    'causal_repair_verified':True,'full_regression_passed':True,'thresholds_unchanged':True,
    'scope':'cross_task_reusable','gate':'unit-test-gate',
    'signature_terms':['verified','failure','family'],'prevention_rule':'Keep the verified causal invariant.',
    'proof':['Synthetic owner-bound promotion fixture passed.'],
    'source':'Docs/Production/T10/C0_ROOT_CAUSE.json#'+proposal['blocker_id']
   }))
   index=Path(td)/'failure.json';index.write_text((ROOT/'Docs/Production/FAILURE_INTELLIGENCE.json').read_text())
   result=failure_learning.promote(pd,proposal['proposal_id'],verification,index)
   self.assertTrue(result['passed'],result)
   self.assertFalse(result['record']['approval_authority_granted'])

 def test_specialist_capacity_is_one_batch_with_parallel_within_batch(self):
  policy=json.loads((ROOT/'Docs/Production/PRODUCTION_SCHEDULER_POLICY.json').read_text())
  self.assertEqual(1,policy['wip']['independent_critic_runtime_slots'])
  body=(ROOT/'.github/workflows/havenline-v32-specialist-fanout.yml').read_text()
  self.assertIn('havenline-v32-independent-specialist-batch',body)
  self.assertIn('fail-fast: false',body)
  self.assertIn('cancel-in-progress: false',body)

 def test_shared_control_stages_learning_after_existing_c0_without_mutating_c0_workflow(self):
  body=(ROOT/'.github/workflows/havenline-v32-task-preflight.yml').read_text()
  self.assertIn('failure-learning-after-c0',body)
  self.assertIn('failure_learning.py propose',body)
  base=(ROOT/'.github/workflows/havenline-c0-root-cause.yml').read_text()
  self.assertNotIn('failure_learning.py propose',base)

 def test_full_v32_validator(self):
  out=architecture_v32.validate()
  self.assertTrue(out['passed'],out)
  self.assertEqual(60,out['task_count'])

if __name__=='__main__':
 unittest.main()
