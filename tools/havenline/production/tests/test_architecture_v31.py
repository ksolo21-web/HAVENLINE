from __future__ import annotations
import copy,pathlib,sys,unittest
from unittest.mock import patch
HERE=pathlib.Path(__file__).resolve();PROD=HERE.parents[1];sys.path.insert(0,str(PROD))
from architecture_v31 import validate as validate_v31,task_readiness as v31_readiness,ACTIVE_RUNTIME_STATES
from flake_intelligence import classify_records
from pipeline_telemetry import summarize,validate as validate_telemetry
from ci_toolchain_lock import validate as validate_toolchain,validate_workflow_action_pins,load as load_toolchain
from evidence_retention import validate_manifest,validate_policy as validate_retention
from lib import DOCS,load_json
from runtime_dependency_learning import learned_impact,validate as validate_runtime
from task_state_snapshot import snapshot,validate as validate_snapshot
from mutation_canary import run_canaries
from proof_invalidation import invalidate_contract,validate_policy as validate_invalidation
from gate_fingerprint import validate_policy as validate_fingerprint
from closure_validator import validate_raw_critic_record,validate_critic_aggregate,validate_defect_ledger,valid_reviewer_confidence

class ArchitectureV31Tests(unittest.TestCase):
    def test_flake_history_never_waives_mandatory_gate(self):
        rows=[{'source_sha':'a'*40,'gate_id':'C5','test_id':'pose','environment_fingerprint':'env','result':x} for x in ('PASS','FAIL','PASS')]
        r=classify_records(rows,'a'*40,'C5','pose','env',3);self.assertEqual(r['classification'],'FLAKY');self.assertTrue(r['mandatory_gate_still_required']);self.assertFalse(r['repair_authorized'])
    def test_pipeline_telemetry_is_valid_and_does_not_drive_thresholds(self):
        self.assertTrue(validate_telemetry()['passed']);self.assertEqual(summarize()['records'],0)
    def test_irreplaceable_evidence_requires_persistent_locator(self):
        self.assertTrue(validate_retention()['passed']);bad={'task_id':'T68','accepted_source':'a'*40,'retention_class':'irreplaceable','records':[{'kind':'physical','sha256':'b'*64,'locator':'','reproducible':False}],'regeneration_contract':'not exact'};self.assertFalse(validate_manifest(bad)['passed'])
    def test_retention_duration_and_repo_provenance_are_enforced(self):
        good={'task_id':'T09','accepted_source':'a'*40,'retention_class':'approval_provenance','records':[{'kind':'critic-records','sha256':'b'*64,'locator':'repo://Docs/Production/T09/CriticRaw','reproducible':True,'retention_days':3650}],'regeneration_contract':{'exact_source':'a'*40,'workflow':'t09','source_run_id':1,'source_artifact_id':2,'complete_evidence_index_sha256':'c'*64}}
        self.assertTrue(validate_manifest(good)['passed'])
        short={'task_id':'T09','accepted_source':'a'*40,'retention_class':'review_evidence','records':[{'kind':'artifact','sha256':'b'*64,'locator':'github-actions://artifact/1','reproducible':True,'retention_days':89}],'regeneration_contract':'rerun'}
        self.assertFalse(validate_manifest(short)['passed'])
    def test_t09_approval_manifest_hashes_and_required_set_are_fail_closed(self):
        path=DOCS/'Evidence/T09/APPROVAL_EVIDENCE_MANIFEST.json';manifest=load_json(path)
        self.assertTrue(validate_manifest(manifest,path=path)['passed'])
        cases=[]
        wrong_hash=copy.deepcopy(manifest);wrong_hash['records'][0]['sha256']='0'*64;cases.append(wrong_hash)
        empty_hash=copy.deepcopy(manifest);empty_hash['records'][0]['sha256']='';cases.append(empty_hash)
        duplicate=copy.deepcopy(manifest);duplicate['records'].append(copy.deepcopy(duplicate['records'][0]));cases.append(duplicate)
        missing=copy.deepcopy(manifest);missing['records'].pop();cases.append(missing)
        escape=copy.deepcopy(manifest);escape['records'][0]['locator']='repo://../../etc/passwd';cases.append(escape)
        wrong_source=copy.deepcopy(manifest);wrong_source['regeneration_contract']['exact_source']='f'*40;cases.append(wrong_source)
        wrong_index=copy.deepcopy(manifest);wrong_index['regeneration_contract']['complete_evidence_index_sha256']='f'*64;cases.append(wrong_index)
        for case in cases:self.assertFalse(validate_manifest(case,path=path)['passed'])
    def test_v31_readiness_requires_lifecycle_and_ownership(self):
        state=snapshot('T10');state.update({'lifecycle_status':'ASSIGNED','task_branch':'havenline/T10-world-transformation','owned_paths':['HavenlineGodot/scripts/world_transform.gd']})
        with patch('architecture_v31.snapshot',return_value=state):
            r=v31_readiness('T10')
        self.assertEqual(r['v3']['feasibility']['activation_state'],'READY_NOW')
        self.assertEqual(r['task_state']['lifecycle_status'],'ASSIGNED')
        self.assertTrue(r['task_state']['task_branch'])
        self.assertTrue(r['task_state']['owned_paths'])
        self.assertNotIn('lifecycle_status_LOCKED',r['task_state']['blockers'])
        self.assertNotIn('ownership_not_assigned',r['task_state']['blockers'])
        self.assertTrue(r['runtime_activation_allowed'])
        self.assertNotIn('BLOCKED',ACTIVE_RUNTIME_STATES)
    def test_v31_completed_state_is_not_runtime_activation(self):
        state=snapshot('T10');state.update({'lifecycle_status':'APPROVED','task_branch':None,'owned_paths':[]})
        with patch('architecture_v31.snapshot',return_value=state):
            r=v31_readiness('T10')
        self.assertIn('lifecycle_not_activated',r['activation_blockers'])
        self.assertIn('ownership_not_assigned',r['activation_blockers'])
        self.assertFalse(r['runtime_activation_allowed'])

    def test_v31_readiness_rejects_locked_unowned_state(self):
        state=snapshot('T10');state.update({'lifecycle_status':'LOCKED','task_branch':None,'owned_paths':[]})
        with patch('architecture_v31.snapshot',return_value=state):
            r=v31_readiness('T10')
        self.assertIn('lifecycle_not_activated',r['activation_blockers'])
        self.assertIn('ownership_not_assigned',r['activation_blockers'])
        self.assertFalse(r['runtime_activation_allowed'])
    def test_t09_raw_critic_semantics_are_fail_closed(self):
        raw=load_json(DOCS/'T09/CriticRaw/C2.json')
        args=('C2','T09',raw['candidate_commit'],raw['workflow_run_id'],raw['artifact_id'],raw['artifact_sha256'],raw['complete_evidence_index_sha256'],raw['scores'],raw['review_export_commit'])
        self.assertEqual(validate_raw_critic_record(raw,*args),[])
        mutations=[]
        for key,value in (('confidence',0),('score_reuse',True),('minimum_dimension_score',9.99),('artifact_sha256','0'*64),('review_export_commit','bad'),('review_export_commit','f'*40),('acceptance_rule','>=9')):
            bad=copy.deepcopy(raw);bad[key]=value;mutations.append(bad)
        infinite=copy.deepcopy(raw);infinite['scores']['geometry_contact']=float('inf');mutations.append(infinite)
        too_high=copy.deepcopy(raw);too_high['scores']['geometry_contact']=10.0001;mutations.append(too_high)
        empty=copy.deepcopy(raw);empty['scores']={};mutations.append(empty)
        for bad in mutations:self.assertTrue(validate_raw_critic_record(bad,*args))
    def test_original_confidence_schemas_without_conversion(self):
        for value in (0.01,0.96,1,"high","medium"):
            with self.subTest(value=value):self.assertTrue(valid_reviewer_confidence(value))
        for value in (None,True,False,0,-1,1.01,float('nan'),float('inf'),"low","0.96","HIGH","high "," medium",[],{}):
            with self.subTest(value=value):self.assertFalse(valid_reviewer_confidence(value))
    def test_categorical_confidence_does_not_waive_other_raw_gates(self):
        raw=load_json(DOCS/'T09/CriticRaw/C2.json')
        args=('C2','T09',raw['candidate_commit'],raw['workflow_run_id'],raw['artifact_id'],raw['artifact_sha256'],raw['complete_evidence_index_sha256'],raw['scores'],raw['review_export_commit'])
        for confidence in ('high','medium'):
            copied=copy.deepcopy(raw);copied['confidence']=confidence
            self.assertEqual([],validate_raw_critic_record(copied,*args))
            self.assertEqual(confidence,copied['confidence'])
            for key,value in (('score_reuse',True),('coverage_complete',False),('defects',['defect']),('provider',''),('candidate_commit','f'*40)):
                bad=copy.deepcopy(copied);bad[key]=value
                self.assertTrue(validate_raw_critic_record(bad,*args))
            bad=copy.deepcopy(copied);bad['scores'][next(iter(bad['scores']))]=9.0
            self.assertTrue(validate_raw_critic_record(bad,*args))

    def test_t09_aggregate_and_defect_ledger_are_fail_closed(self):
        completion=load_json(DOCS/'T09/verified-completion.json');aggregate=load_json(DOCS/'T09/independent-critic-review.json');ledger=load_json(DOCS/'T09/defect-ledger.json')
        required=['C2','C3','C4','C5','C6'];retained=completion['retained_review_evidence']
        args=(required,completion['candidate_commit'],completion['workflow_run_id'],completion['artifact_id'],completion['artifact_sha256'],completion['evidence']['provenance_hash'],retained,completion['critics'])
        self.assertEqual(validate_critic_aggregate(aggregate,*args),[])
        for mutate in ('status','coverage','minimum','retained'):
            bad=copy.deepcopy(aggregate)
            if mutate=='status':bad['critics']['C2']['status']='FAIL'
            elif mutate=='coverage':bad['critics']['C3']['coverage_complete']=False
            elif mutate=='minimum':bad['critics']['C4']['minimum_dimension_score']=9.99
            else:bad['retained_review_evidence']['artifact_id']=0
            self.assertTrue(validate_critic_aggregate(bad,*args))
        self.assertEqual(validate_defect_ledger(ledger,completion['candidate_commit'],aggregate,required),[])
        for mutate in ('status','unresolved','candidate','minima'):
            bad=copy.deepcopy(ledger)
            if mutate=='status':bad['defects'][0]['status']='OPEN'
            elif mutate=='unresolved':bad['unresolved_mandatory_count']=1
            elif mutate=='candidate':bad['candidate_commit']='f'*40
            else:bad['critic_scores']['C2']=9.99
            self.assertTrue(validate_defect_ledger(bad,completion['candidate_commit'],aggregate,required))
    def test_runtime_dependency_learning_is_additive_only(self):
        data={'schema_version':1,'policy':{'minimum_observations_for_enforcement':3,'minimum_distinct_sources':2,'learned_edges_are_additive_only':True,'static_mandatory_coverage_may_be_removed_automatically':False},'edges':[{'path_pattern':'HavenlineGodot/scripts/foo.gd','affected_task':'T10','suites':['test_t10'],'observation_count':4,'distinct_sources':2}]};r=learned_impact(['HavenlineGodot/scripts/foo.gd'],data);self.assertEqual(r['coverage_mode'],'ADDITIVE_ONLY');self.assertIn('test_t10',r['required_suites']);self.assertTrue(validate_runtime()['passed'])
    def test_task_snapshot_remains_derived(self):
        r=snapshot('T10');self.assertTrue(validate_snapshot(r)['passed']);self.assertTrue(r['snapshot_is_derived_not_authority'])
    def test_t09_snapshot_includes_produced_contract(self):
        r=snapshot('T09');self.assertTrue(validate_snapshot(r)['passed']);self.assertIn('harvest_resource_identity',r['contracts']['produces'])
    def test_mutation_canaries_all_reject_bad_inputs(self):
        r=run_canaries();self.assertTrue(r['passed'],r['errors']);self.assertTrue(all(x['rejected'] for x in r['results']))
    def test_transitive_invalidation_blocks_reuse_without_auto_revocation(self):
        self.assertTrue(validate_invalidation()['passed']);r=invalidate_contract('persistence_schema');self.assertTrue(r['proof_reuse_blocked']);self.assertFalse(r['automatic_approval_revocation']);self.assertIn('T14',r['invalidated_tasks']);self.assertIn('T15',r['invalidated_tasks']);self.assertIn('T70',r['invalidated_tasks']);self.assertIn('save_matrix',r['invalidated_gates'])
    def test_contract_override_ids_match_registry(self):
        r=validate_invalidation();self.assertTrue(r['passed'],r['errors']);self.assertGreaterEqual(r['contract_override_count'],10)
    def test_ci_action_and_toolchain_lock_is_valid(self):
        r=validate_toolchain();self.assertTrue(r['passed'],r['errors']);self.assertEqual(r['critical_workflow_count'],9);self.assertEqual(r['action_runtime'],'node24');self.assertEqual(r['retired_workflow_count'],0)
        cfg=load_toolchain();self.assertIn('.github/workflows/havenline-task09-harvesting.yml',cfg['critical_workflows']);self.assertNotIn('.github/workflows/havenline-task09-harvesting.yml',cfg['retired_workflows'])
    def test_ci_lock_rejects_mutable_subpath_action(self):
        pins=load_toolchain()['action_pins']
        bad=validate_workflow_action_pins('- uses: actions/cache/restore@v4\n',pins,'fixture.yml')
        self.assertTrue(bad)
        self.assertIn('actions/cache/restore',bad[0])
        exact=pins['actions/cache']
        good=validate_workflow_action_pins(f'- uses: actions/cache/restore@{exact}\n- uses: actions/cache/save@{exact}\n',pins,'fixture.yml')
        self.assertEqual(good,[])
    def test_environment_sensitive_gate_policy_remains_safe(self):
        r=validate_fingerprint();self.assertTrue(r['passed'],r['errors'])
    def test_complete_v31_validation_passes(self):
        r=validate_v31();self.assertTrue(r['passed'],r['errors']);self.assertEqual(r['task_count'],62);self.assertEqual(r['snapshot_count'],62)
class HistoricalT09ClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import subprocess
        from closure_validator import ROOT,T09_CLOSURE_CHECKPOINT
        cls.objects={name:subprocess.check_output(['git','show',T09_CLOSURE_CHECKPOINT+':Docs/Production/'+name],cwd=ROOT) for name in ['T09/verified-completion.json','DEPENDENCY_GRAPH.json','PATH_OWNERSHIP.json','task-gates.json']}
    def check(self,objects=None,completion=None):
        from closure_validator import t09_historical_lifecycle_errors
        rows=objects if objects is not None else self.objects
        with patch('closure_validator.subprocess.check_output',side_effect=lambda args,**kwargs:rows[args[-1].split(':Docs/Production/')[1]]):
            return t09_historical_lifecycle_errors(self.objects['T09/verified-completion.json'] if completion is None else completion)
    def test_valid_historical_closeout_after_activation(self):
        self.assertEqual([],self.check())
    def test_changed_completion_rejects(self):
        self.assertTrue(self.check(completion=self.objects['T09/verified-completion.json']+b' '))
    def test_missing_or_malformed_objects_reject(self):
        for name in self.objects:
            with self.subTest(name=name):
                rows=dict(self.objects);del rows[name];self.assertTrue(self.check(rows))
                rows=dict(self.objects);rows[name]=b'{';self.assertTrue(self.check(rows))
    def test_missing_git_history_rejects(self):
        import subprocess
        from closure_validator import t09_historical_lifecycle_errors
        with patch('closure_validator.subprocess.check_output',side_effect=subprocess.CalledProcessError(128,['git'])):
            self.assertTrue(t09_historical_lifecycle_errors(self.objects['T09/verified-completion.json']))
    def test_historical_temporal_violations_reject(self):
        import json
        for name,change in [('DEPENDENCY_GRAPH.json',lambda x:x['tasks']['T09'].update(status='UNDER_REVIEW')),('DEPENDENCY_GRAPH.json',lambda x:x['tasks']['T10'].update(status='ASSIGNED')),('PATH_OWNERSHIP.json',lambda x:x['active_owners'].append({'task_id':'T10'})),('task-gates.json',lambda x:x.update(active_task='T10'))]:
            with self.subTest(name=name):
                rows=dict(self.objects);data=json.loads(rows[name]);change(data);rows[name]=json.dumps(data).encode();self.assertTrue(self.check(rows))

if __name__=='__main__':unittest.main(verbosity=2)
