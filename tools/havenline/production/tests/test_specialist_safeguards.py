#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,pathlib,subprocess,sys,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools/havenline/production'))
from lib import DOCS,load_json,sha256_file
import critic_harness,specialist_evidence_manifest

CANDIDATE='a'*40

def run(*args):return subprocess.run(list(args),cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)

class SpecialistSafeguards(unittest.TestCase):
    def test_all_critics_operational_and_known(self):
        matrix=load_json(DOCS/'CRITIC_MATRIX.json');execution=load_json(DOCS/'CRITIC_EXECUTION.json');expected={f'C{i}' for i in range(1,12)}
        self.assertEqual(set(matrix['critics']),expected);self.assertEqual(set(execution['critics']),expected)
        self.assertTrue(all(execution['critics'][c]['status']=='OPERATIONAL' for c in expected))
        for cs in matrix['task_applicability'].values():self.assertFalse(set(cs)-expected)

    def _record(self,tmp:pathlib.Path,score=10.0,independent=True):
        dims=load_json(DOCS/'CRITIC_EXECUTION.json')['critics']['C3']['dimensions'];raw=tmp/'raw.json';raw.write_text('{}')
        return {'critic_id':'C3','provider':'test','model':'test-model','request_or_run_id':'test/1','candidate_hash':CANDIDATE,'input_manifest_hash':'f'*64,'raw_output_path':str(raw.relative_to(ROOT)),'raw_output_hash':sha256_file(raw),'scores':{k:score for k in dims},'defects':[],'coverage_complete':True,'confidence':'high','independent_runtime':independent,'passed':score>9.0}

    def test_raw_critic_strictly_above_nine(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            t=pathlib.Path(td);good=self._record(t);p=t/'good.json';p.write_text(json.dumps(good));self.assertTrue(critic_harness.validate_raw(p,'C3',CANDIDATE)['passed'])
            bad=self._record(t,9.0);p2=t/'bad.json';p2.write_text(json.dumps(bad));self.assertFalse(critic_harness.validate_raw(p2,'C3',CANDIDATE)['passed'])

    def test_independent_runtime_cannot_be_faked_by_self_review(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            t=pathlib.Path(td);d=self._record(t,10.0,False);p=t/'self.json';p.write_text(json.dumps(d));r=critic_harness.validate_raw(p,'C3',CANDIDATE);self.assertFalse(r['passed']);self.assertTrue(any('independent' in x for x in r['errors']))

    def test_specialist_manifest_requires_all_categories_and_hashes(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            t=pathlib.Path(td);items=[]
            for category in ('gameplay_state','control_state','loop_evidence'):
                p=t/(category+'.txt');p.write_text(category);items.append({'path':str(p.relative_to(ROOT)),'kind':'text','category':category,'sha256':sha256_file(p),'description':category})
            m={'task_id':'T07','critic_id':'C3','candidate_commit':CANDIDATE,'groups':[{'id':'core-loop','items':items}]}
            self.assertEqual(specialist_evidence_manifest.validate(m),[])
            m['groups'][0]['items'].pop();self.assertTrue(any('missing required categories' in x for x in specialist_evidence_manifest.validate(m)))

    def test_c9_secure_adapter_passes_and_vulnerable_adapter_fails(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            out=pathlib.Path(td)/'secure';adapter=f"{sys.executable} tools/havenline/production/tests/security_mock_adapter.py"
            p=run(sys.executable,'tools/havenline/production/security_exploit_harness.py','--candidate',CANDIDATE,'--adapter',adapter,'--out',str(out.relative_to(ROOT)));self.assertEqual(p.returncode,0,p.stdout)
            record=json.loads((out/'critic-record.json').read_text());self.assertEqual(len(record['scores']),10);self.assertTrue(all(v==10.0 for v in record['scores'].values()))
            out2=pathlib.Path(td)/'vulnerable';adapter2=adapter+' --vulnerable'
            p2=run(sys.executable,'tools/havenline/production/security_exploit_harness.py','--candidate',CANDIDATE,'--adapter',adapter2,'--out',str(out2.relative_to(ROOT)));self.assertNotEqual(p2.returncode,0);r2=json.loads((out2/'critic-record.json').read_text());self.assertEqual(r2['scores']['fake_purchase'],0.0)

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
