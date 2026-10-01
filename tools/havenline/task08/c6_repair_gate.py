#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math,pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[3]
PROD=ROOT/'tools'/'havenline'/'production'
sys.path.insert(0,str(PROD))
from critic_harness import c6
from lib import DOCS,load_json

def score_ratio(value,limit):
    if value is None or not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(float(value)): return 0.0
    if limit<=0: return 10.0 if value<=0 else 0.0
    ratio=max(0.0,float(value)/float(limit))
    if ratio>1.0: return max(0.0,9.0-(ratio-1.0))
    return round(10.0-0.8*ratio,4)

def exact_custom_shader_count(candidate:str)->int:
    out=subprocess.check_output(['git','ls-tree','-r','--name-only',candidate,'--','HavenlineGodot/assets/transfer_feedback_v2'],cwd=ROOT,text=True)
    rows=[x for x in out.splitlines() if x.endswith('.gdshader')]
    if rows!=['HavenlineGodot/assets/transfer_feedback_v2/transfer_feedback_v2.gdshader']:
        raise ValueError('unexpected T08 authored transfer shader set: '+repr(rows))
    return len(rows)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--candidate',required=True);ap.add_argument('--record',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    path=(ROOT/a.record).resolve();perf=json.loads(path.read_text());candidate=a.candidate
    base=c6(path,candidate);budgets=load_json(DOCS/'PERFORMANCE_BUDGETS.json')['global_soft_budgets'];errors=list(base.get('errors',[]))
    frame_p95=float(perf.get('active_transfer_stats',{}).get('frame_usec',{}).get('p95',0))/1000.0
    if frame_p95<=0: errors.append('missing active-transfer p95 frame timing')
    if perf.get('sample_window',{}).get('baseline_samples')!=perf.get('sample_window',{}).get('active_samples'): errors.append('T08 C6 requires equal adjacent baseline/active sample windows')
    if perf.get('sample_window',{}).get('baseline_samples',0)<12: errors.append('T08 C6 requires at least 12 adjacent post-warmup samples per window')
    try: custom_shaders=exact_custom_shader_count(candidate)
    except Exception as exc: custom_shaders=None;errors.append(str(exc))
    scores={
      'frame_time':score_ratio(frame_p95,budgets['cpu_frame_ms']),
      'draw_calls':score_ratio(perf.get('draw_calls'),budgets['draw_calls']),
      'geometry':score_ratio(perf.get('visible_triangles'),budgets['visible_triangles']),
      'texture_memory':score_ratio(perf.get('texture_gpu_memory_mb'),budgets['texture_gpu_memory_mb']),
      'shader_cost':score_ratio(custom_shaders,32),
      'physics':score_ratio(perf.get('physics_active_bodies'),budgets['physics_active_bodies']),
      'animation':score_ratio(perf.get('animated_rigs_active'),budgets['animated_rigs_active']),
      'population':score_ratio(perf.get('npc_companion_active_population'),budgets['npc_companion_active_population']),
      'thermal_risk':min(score_ratio(frame_p95,budgets['cpu_frame_ms']),score_ratio(perf.get('draw_calls'),budgets['draw_calls']),score_ratio(perf.get('process_memory_mb'),budgets['process_memory_mb']))
    }
    if any(v<=9.0 for v in scores.values()): errors.append('one or more deterministic C6 dimensions are not strictly above 9.0')
    result={'schema_version':1,'task_id':'T08','critic_id':'C6','candidate':candidate,'candidate_commit':candidate,'passed':not errors,'errors':errors,'defects':errors.copy(),'coverage_complete':True,'scores':scores,'mandatory_dimensions':scores,'measurement':perf,'score_rule':'>9.0 unrounded; deterministic utilization scoring with hard budget failure','physical_4k60_certified':False,'note':'T08 repair quantitative C6 gate only; T68/T69 remain physical certification authority.'}
    out=(ROOT/a.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));raise SystemExit(0 if result['passed'] else 1)

if __name__=='__main__': main()
