#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, pathlib
from lib import ROOT

def need(errors:list[str],cond:bool,msg:str):
    if not cond:errors.append(msg)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('domain',choices=['progression','economy','liveops','accessibility']);ap.add_argument('--candidate',required=True);ap.add_argument('--record',required=True);ap.add_argument('--out');a=ap.parse_args()
    p=(ROOT/a.record).resolve();d=json.loads(p.read_text());errors=[]
    need(errors,d.get('candidate_commit')==a.candidate,'candidate mismatch')
    if a.domain=='progression':
        need(errors,d.get('level_cap')==100,'launch level cap must be 100')
        need(errors,d.get('levels_1_to_100_defined') is True,'levels 1-100 not fully defined')
        need(errors,d.get('f2p_completion_realistic') is True,'F2P completion not realistic')
        need(errors,d.get('max_visual_progression_gap_levels',999)<=3,'visual progression gap exceeds 3 levels')
        need(errors,d.get('max_major_milestone_gap_levels',999)<=10,'major milestone gap exceeds ~10 levels')
        need(errors,d.get('impossible_spikes',999)==0,'impossible difficulty spikes present')
        need(errors,d.get('boring_stretches_over_limit',999)==0,'boring progression stretches present')
        need(errors,d.get('meaningful_upgrades_preserved') is True,'upgrades not consistently meaningful')
        need(errors,d.get('challenge_director_spend_inputs',[])==[],'Challenge Director consumes spend/VIP/purchase signals')
        need(errors,d.get('difficulty_is_not_hp_only') is True,'difficulty is HP-only inflation')
    elif a.domain=='economy':
        need(errors,d.get('energy_wall') is False,'energy wall detected')
        need(errors,d.get('mandatory_payment') is False,'mandatory payment detected')
        need(errors,d.get('primary_premium_currency_count')==1,'must have one primary premium currency')
        need(errors,d.get('vip_permanent') is True and d.get('vip_transparent') is True,'VIP not permanent/transparent')
        need(errors,d.get('fake_discounts') is False,'fake discounts detected')
        need(errors,d.get('f2p_level_100_realistic') is True,'F2P Level-100 completion not realistic')
        need(errors,d.get('purchase_value_retained') is True,'advertised purchase value not retained')
        need(errors,d.get('difficulty_spend_inputs',[])==[],'difficulty uses spend signals')
        need(errors,d.get('launch_store_limited') is True,'launch store not intentionally limited')
        need(errors,d.get('technically_free_but_miserable') is False,'F2P path is intentionally miserable')
    elif a.domain=='liveops':
        need(errors,d.get('server_authoritative_time') is True,'time is not server authoritative')
        need(errors,d.get('automatic_scheduling') is True,'automatic scheduling absent')
        need(errors,d.get('automatic_validation') is True,'automatic event validation absent')
        need(errors,d.get('remote_kill_switch') is True,'remote event kill switch absent')
        need(errors,d.get('impossible_requirements',999)==0,'impossible event requirements')
        need(errors,d.get('event_collisions',999)==0,'event schedule collisions')
        need(errors,d.get('duplicate_rewards',999)==0,'duplicate rewards detected')
        need(errors,d.get('invalid_pricing_or_sales',999)==0,'invalid pricing/sales detected')
        need(errors,d.get('f2p_infeasible_events',999)==0,'F2P-infeasible events detected')
        need(errors,d.get('bad_timing_windows',999)==0,'bad event timing windows')
        need(errors,d.get('missing_assets_or_localization',999)==0,'event assets/localization missing')
        if d.get('launch_rehearsal') is True:need(errors,d.get('first_thaw_present') is True,'The First Thaw missing from launch rehearsal')
    else:
        need(errors,float(d.get('minimum_touch_target_dp',0))>=48.0,'touch targets below 48dp')
        need(errors,d.get('ui_scaling_supported') is True,'UI scaling unsupported')
        need(errors,d.get('text_readability_passed') is True,'text readability failed')
        need(errors,d.get('color_only_critical_cues') is False,'critical cues rely on color alone')
        need(errors,d.get('reduced_motion_supported') is True,'reduced motion unsupported')
        need(errors,d.get('subtitles_supported') is True,'subtitles unsupported')
        need(errors,d.get('joystick_layout_adaptive') is True,'joystick layout is not adaptive')
        device_states=set(d.get('device_states_passed',[]));need(errors,{'phone','tablet','folded','unfolded'}.issubset(device_states),'phone/tablet/foldable matrix incomplete')
        controller=d.get('controller_state');need(errors,controller in ('supported','explicitly_out_of_scope_with_rationale'),'controller state unresolved')
        if controller=='explicitly_out_of_scope_with_rationale':need(errors,bool(d.get('controller_rationale')),'controller N/A lacks rationale')
    result={'gate':'domain_safeguard_v1','domain':a.domain,'candidate_commit':a.candidate,'source_record':str(p.relative_to(ROOT)),'passed':not errors,'errors':errors}
    text=json.dumps(result,indent=2)+'\n';print(text,end='')
    if a.out:
        out=(ROOT/a.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(text)
    raise SystemExit(0 if not errors else 1)
if __name__=='__main__':main()
