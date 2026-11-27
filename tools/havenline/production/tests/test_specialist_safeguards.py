#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,pathlib,subprocess,sys,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools/havenline/production'))
from lib import DOCS,load_json,sha256_file
import critic_harness,specialist_evidence_manifest
from reference_acceptance import acceptance_binding

CANDIDATE='a'*40

def run(*args):return subprocess.run(list(args),cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)

class SpecialistSafeguards(unittest.TestCase):
    def test_all_critics_operational_and_known(self):
        matrix=load_json(DOCS/'CRITIC_MATRIX.json');execution=load_json(DOCS/'CRITIC_EXECUTION.json');expected={f'C{i}' for i in range(1,12)}
        self.assertEqual(set(matrix['critics']),expected);self.assertEqual(set(execution['critics']),expected)
        self.assertTrue(all(execution['critics'][c]['status']=='OPERATIONAL' for c in expected-{'C5'}))
        self.assertEqual(execution['critics']['C5']['status'],'OPERATIONAL_INTERIM_STATIC_SCREENING_ONLY')
        self.assertFalse(execution['critics']['C5']['automated_final_approval'])
        for cs in matrix['task_applicability'].values():self.assertFalse(set(cs)-expected)

    def _record(self,tmp:pathlib.Path,score=10.0,independent=True,cid='C3',reference_dimensions=None):
        spec=load_json(DOCS/'CRITIC_EXECUTION.json')['critics'][cid];dims=spec['dimensions']
        refs=reference_dimensions or [];items=[]
        for category in spec.get('required_categories',[]):
            evidence=tmp/(category+'.txt');evidence.write_text('Explicit test fixture '+category)
            items.append({'path':str(evidence.relative_to(ROOT)),'sha256':sha256_file(evidence),'kind':'text','category':category,'description':category})
        manifest=tmp/'input.json';manifest.write_text(json.dumps({'task_id':'T07','critic_id':cid,'candidate_commit':CANDIDATE,'reference_sensitive_dimensions':refs,'groups':[{'id':'core','items':items}]}))
        review={'scores':{k:score for k in dims},'defects':[],'coverage_complete':True,'confidence':'high'}
        response=tmp/'response.json';response.write_text(json.dumps(review))
        request=tmp/'request.json';request.write_text(json.dumps({'candidate':CANDIDATE,'input_manifest_hash':sha256_file(manifest)}))
        record={'task_id':'T07','critic_id':cid,'provider':'test','model':'test-model','request_or_run_id':'test/1','candidate_hash':CANDIDATE,'input_manifest_path':str(manifest.relative_to(ROOT)),'input_manifest_hash':sha256_file(manifest),**review,'independent_runtime':independent,'passed':True,'status':'PASS','reference_acceptance':acceptance_binding(),'reference_sensitive_dimensions':refs}
        raw=tmp/'raw.json';raw.write_text(json.dumps({**record,'format':'havenline-specialist-report-v2','fatal_error':None,'groups':[{'group':'core','review':review,'response_path':str(response.relative_to(ROOT)),'response_sha256':sha256_file(response),'request_path':str(request.relative_to(ROOT)),'request_sha256':sha256_file(request)}]}))
        return {**record,'raw_output_path':str(raw.relative_to(ROOT)),'raw_output_hash':sha256_file(raw)}

    def test_raw_visual_critic_requires_exact_ten_current_policy(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            t=pathlib.Path(td);good=self._record(t);p=t/'good.json';p.write_text(json.dumps(good));self.assertTrue(critic_harness.validate_raw(p,'C3',CANDIDATE)['passed'])
            bad=self._record(t,9.99);p2=t/'bad.json';p2.write_text(json.dumps(bad));self.assertFalse(critic_harness.validate_raw(p2,'C3',CANDIDATE)['passed'])

    def test_independent_runtime_cannot_be_faked_by_self_review(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            t=pathlib.Path(td);d=self._record(t,10.0,False);p=t/'self.json';p.write_text(json.dumps(d));r=critic_harness.validate_raw(p,'C3',CANDIDATE);self.assertFalse(r['passed']);self.assertTrue(any('independent' in x for x in r['errors']))

    def test_high_scores_do_not_replace_independent_reviewer_or_raw_evidence(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            t=pathlib.Path(td)
            for field in ('provider','model','request_or_run_id','raw_output_hash','raw_output_path','input_manifest_hash'):
                record=self._record(t)
                record.pop(field)
                p=t/'missing.json';p.write_text(json.dumps(record))
                with self.subTest(field=field):
                    self.assertFalse(critic_harness.validate_raw(p,'C3',CANDIDATE)['passed'])

    def test_specialist_manifest_requires_all_categories_and_hashes(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            t=pathlib.Path(td);items=[]
            for category in ('gameplay_state','control_state','loop_evidence'):
                p=t/(category+'.txt');p.write_text(category);items.append({'path':str(p.relative_to(ROOT)),'kind':'text','category':category,'sha256':sha256_file(p),'description':category})
            m={'task_id':'T07','critic_id':'C3','candidate_commit':CANDIDATE,'reference_sensitive_dimensions':[],'groups':[{'id':'core-loop','items':items}]}
            self.assertEqual(specialist_evidence_manifest.validate(m),[])
            m['groups'][0]['items'].pop();self.assertTrue(any('missing required categories' in x for x in specialist_evidence_manifest.validate(m)))

    def test_empty_raw_and_missing_hash_bound_input_cannot_pass(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            t=pathlib.Path(td);record=self._record(t);raw=ROOT/record['raw_output_path'];raw.write_text('{}')
            record['raw_output_hash']=sha256_file(raw);p=t/'record.json';p.write_text(json.dumps(record))
            result=critic_harness.validate_raw(p,'C3',CANDIDATE)
            self.assertFalse(result['passed']);self.assertTrue(any('missing or empty' in x for x in result['errors']))
            record=self._record(t);record['input_manifest_hash']='not-a-hash';p.write_text(json.dumps(record))
            self.assertFalse(critic_harness.validate_raw(p,'C3',CANDIDATE)['passed'])
            record=self._record(t);source=ROOT/record['input_manifest_path'];source.write_text('{}')
            record['input_manifest_hash']=sha256_file(source);p.write_text(json.dumps(record))
            self.assertFalse(critic_harness.validate_raw(p,'C3',CANDIDATE)['passed'])

    def test_duplicate_scores_and_raw_identity_contradictions_fail(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            t=pathlib.Path(td);record=self._record(t);p=t/'record.json'
            key=next(iter(record['scores']));p.write_text(json.dumps(record).replace('"'+key+'": 10.0','"'+key+'": 7, "'+key+'": 10.0'))
            result=critic_harness.validate_raw(p,'C3',CANDIDATE);self.assertFalse(result['passed']);self.assertTrue(any('duplicate JSON key' in x for x in result['errors']))
            for key,value in [('independent_runtime',False),('status','FAIL'),('passed',False),('task_id','T08'),('approval_allowed',False)]:
                record=self._record(t);raw=ROOT/record['raw_output_path'];body=json.loads(raw.read_text());body[key]=value;raw.write_text(json.dumps(body));record['raw_output_hash']=sha256_file(raw);p.write_text(json.dumps(record))
                with self.subTest(field=key):self.assertFalse(critic_harness.validate_raw(p,'C3',CANDIDATE)['passed'])

    def test_frozen_reference_dimension_cannot_be_omitted_or_scored_9_5(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            t=pathlib.Path(td);record=self._record(t,9.5,cid='C7',reference_dimensions=['pacing']);p=t/'record.json'
            record.pop('reference_sensitive_dimensions');p.write_text(json.dumps(record))
            result=critic_harness.validate_raw(p,'C7',CANDIDATE)
            self.assertFalse(result['passed']);self.assertTrue(any('pacing' in x and '9.9' in x for x in result['errors']))
            record=self._record(t,9.9,cid='C7',reference_dimensions=['pacing']);p.write_text(json.dumps(record))
            result=critic_harness.validate_raw(p,'C7',CANDIDATE);self.assertTrue(result['passed'],result['errors'])

    def test_static_c5_report_never_grants_final_motion_approval(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            t=pathlib.Path(td);record=self._record(t,cid='C5');p=t/'record.json';p.write_text(json.dumps(record))
            result=critic_harness.validate_raw(p,'C5',CANDIDATE)
            self.assertFalse(result['passed']);self.assertTrue(any('full-cycle playback' in x for x in result['errors']))

    def test_c6_invalid_measurements_and_missing_cpu_fail(self):
        soft=load_json(DOCS/'PERFORMANCE_BUDGETS.json')['global_soft_budgets']
        good={key:0 for key in ('visible_triangles','draw_calls','materials_visible','texture_gpu_memory_mb','process_memory_mb','physics_active_bodies','animated_rigs_active','npc_companion_active_population','storage_download_mb','cpu_frame_ms')}
        good['candidate_commit']=CANDIDATE
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            p=pathlib.Path(td)/'performance.json';p.write_text(json.dumps(good));self.assertTrue(critic_harness.c6(p,CANDIDATE)['passed'])
            for value in (True,-1,float('nan'),float('inf'),'0'):
                bad=dict(good,draw_calls=value);p.write_text(json.dumps(bad));self.assertFalse(critic_harness.c6(p,CANDIDATE)['passed'])
            bad=dict(good);bad.pop('cpu_frame_ms');p.write_text(json.dumps(bad));self.assertFalse(critic_harness.c6(p,CANDIDATE)['passed'])

    def test_c9_secure_adapter_passes_and_vulnerable_adapter_fails(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            out=pathlib.Path(td)/'secure';adapter=f"{sys.executable} tools/havenline/production/tests/security_mock_adapter.py"
            p=run(sys.executable,'tools/havenline/production/security_exploit_harness.py','--candidate',CANDIDATE,'--adapter',adapter,'--out',str(out.relative_to(ROOT)));self.assertEqual(p.returncode,0,p.stdout)
            record=json.loads((out/'critic-record.json').read_text());self.assertEqual(len(record['scores']),10);self.assertTrue(all(v==10.0 for v in record['scores'].values()))
            self.assertEqual(record['reference_acceptance'],acceptance_binding())
            self.assertTrue(critic_harness.validate_raw(out/'critic-record.json','C9',CANDIDATE)['passed'])
            broken=dict(record);broken.pop('raw_output_hash');(out/'missing-evidence.json').write_text(json.dumps(broken))
            self.assertFalse(critic_harness.validate_raw(out/'missing-evidence.json','C9',CANDIDATE)['passed'])
            out2=pathlib.Path(td)/'vulnerable';adapter2=adapter+' --vulnerable'
            p2=run(sys.executable,'tools/havenline/production/security_exploit_harness.py','--candidate',CANDIDATE,'--adapter',adapter2,'--out',str(out2.relative_to(ROOT)));self.assertNotEqual(p2.returncode,0);r2=json.loads((out2/'critic-record.json').read_text());self.assertEqual(r2['scores']['fake_purchase'],0.0)

    def test_c9_consumer_rejects_internally_consistent_weaker_substitute_attack_matrix(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            root=pathlib.Path(td);out=root/'security';adapter=f"{sys.executable} tools/havenline/production/tests/security_mock_adapter.py"
            process=run(sys.executable,'tools/havenline/production/security_exploit_harness.py','--candidate',CANDIDATE,
                '--adapter',adapter,'--out',str(out.relative_to(ROOT)))
            self.assertEqual(0,process.returncode,process.stdout)
            record_path=out/'critic-record.json'
            self.assertTrue(critic_harness.validate_raw(record_path,'C9',CANDIDATE)['passed'])
            record=json.loads(record_path.read_text());manifest_path=ROOT/record['input_manifest_path'];manifest=json.loads(manifest_path.read_text())
            matrix=load_json(DOCS/'SECURITY_ATTACK_MATRIX.json')
            for attack in matrix['attacks']:attack['required_assertions']=[]
            weaker=root/'weaker-matrix.json';weaker.write_text(json.dumps(matrix))
            manifest['groups'][0]['items'][0].update(path=str(weaker.relative_to(ROOT)),sha256=sha256_file(weaker))
            manifest_path.write_text(json.dumps(manifest));record['input_manifest_hash']=sha256_file(manifest_path)
            raw_path=ROOT/record['raw_output_path'];raw=json.loads(raw_path.read_text());raw['input_manifest_hash']=record['input_manifest_hash']
            # All counterfeit source hashes and the same ten IDs are consistent,
            # but the logs now omit every required attack assertion.
            for row in raw['results']:
                row['result']['assertions']={};log=ROOT/row['log'];log.write_text(json.dumps(row['result'])+'\n');row['log_sha256']=sha256_file(log)
            record['results']=raw['results'];raw_path.write_text(json.dumps(raw));record['raw_output_hash']=sha256_file(raw_path);record_path.write_text(json.dumps(record))
            result=critic_harness.validate_raw(record_path,'C9',CANDIDATE)
            self.assertFalse(result['passed']);self.assertTrue(any('current canonical attack matrix' in error for error in result['errors']))

    def _domain(self,domain,data,expect=True):
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            t=pathlib.Path(td);data={'candidate_commit':CANDIDATE,**data};p=t/'record.json';p.write_text(json.dumps(data));r=run(sys.executable,'tools/havenline/production/domain_safeguard_gate.py',domain,'--candidate',CANDIDATE,'--record',str(p.relative_to(ROOT)));self.assertEqual(r.returncode==0,expect,r.stdout)

    def test_progression_spend_blind_and_level100_gate(self):
        good={'level_cap':100,'levels_1_to_100_defined':True,'f2p_completion_realistic':True,'max_visual_progression_gap_levels':3,'max_major_milestone_gap_levels':10,'impossible_spikes':0,'boring_stretches_over_limit':0,'meaningful_upgrades_preserved':True,'challenge_director_spend_inputs':[],'difficulty_is_not_hp_only':True}
        self._domain('progression',good,True);bad=dict(good,challenge_director_spend_inputs=['vip_level']);self._domain('progression',bad,False)

    def test_economy_fairness_gate_rejects_energy_and_miserable_f2p(self):
        good={'energy_wall':False,'mandatory_payment':False,'primary_premium_currency_count':1,'vip_permanent':True,'vip_transparent':True,'fake_discounts':False,'f2p_level_100_realistic':True,'purchase_value_retained':True,'difficulty_spend_inputs':[],'launch_store_limited':True,'technically_free_but_miserable':False}
        self._domain('economy',good,True);bad=dict(good,energy_wall=True,technically_free_but_miserable=True);self._domain('economy',bad,False)

    def test_liveops_gate_rejects_collisions_and_missing_kill_switch(self):
        good={'server_authoritative_time':True,'automatic_scheduling':True,'automatic_validation':True,'remote_kill_switch':True,'impossible_requirements':0,'event_collisions':0,'duplicate_rewards':0,'invalid_pricing_or_sales':0,'f2p_infeasible_events':0,'bad_timing_windows':0,'missing_assets_or_localization':0,'launch_rehearsal':True,'first_thaw_present':True}
        self._domain('liveops',good,True);bad=dict(good,event_collisions=1,remote_kill_switch=False);self._domain('liveops',bad,False)

    def test_accessibility_gate_requires_device_matrix_and_touch_targets(self):
        good={'minimum_touch_target_dp':48,'ui_scaling_supported':True,'text_readability_passed':True,'color_only_critical_cues':False,'reduced_motion_supported':True,'subtitles_supported':True,'joystick_layout_adaptive':True,'device_states_passed':['phone','tablet','folded','unfolded'],'controller_state':'supported'}
        self._domain('accessibility',good,True);bad=dict(good,minimum_touch_target_dp=40,device_states_passed=['phone']);self._domain('accessibility',bad,False)

if __name__=='__main__':unittest.main()
