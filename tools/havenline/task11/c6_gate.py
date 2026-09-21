#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math, pathlib, sys

ROOT=pathlib.Path(__file__).resolve().parents[3]
PROD=ROOT/'tools'/'havenline'/'production'
sys.path.insert(0,str(PROD))
from critic_harness import c6
from lib import DOCS, load_json

def score_ratio(value, limit):
    if value is None or not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(float(value)):
        return 0.0
    if limit <= 0:
        return 10.0 if value <= 0 else 0.0
    ratio=max(0.0,float(value)/float(limit))
    if ratio > 1.0:
        return max(0.0,9.0-(ratio-1.0))
    return round(10.0-0.8*ratio,4)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--candidate',required=True);ap.add_argument('--record',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    path=(ROOT/a.record).resolve();perf=json.loads(path.read_text());candidate=a.candidate
    base=c6(path,candidate)
    budgets=load_json(DOCS/'PERFORMANCE_BUDGETS.json')['global_soft_budgets']
    errors=list(base.get('errors',[]))
    cpu=perf.get('cpu_frame_ms')
    if cpu is None:
        errors.append('missing measured cpu_frame_ms for T11 early C6')
    if perf.get('custom_shader_count') is None:
        errors.append('missing custom_shader_count')
    scores={
      'frame_time':score_ratio(cpu,budgets['cpu_frame_ms']),
      'draw_calls':score_ratio(perf.get('draw_calls'),budgets['draw_calls']),
      'geometry':score_ratio(perf.get('visible_triangles'),budgets['visible_triangles']),
      'texture_memory':score_ratio(perf.get('texture_gpu_memory_mb'),budgets['texture_gpu_memory_mb']),
      'shader_cost':10.0 if perf.get('custom_shader_count')==0 else score_ratio(perf.get('custom_shader_count'),32),
      'physics':score_ratio(perf.get('physics_active_bodies'),budgets['physics_active_bodies']),
      'animation':score_ratio(perf.get('animated_rigs_active'),budgets['animated_rigs_active']),
      'population':score_ratio(perf.get('npc_companion_active_population'),budgets['npc_companion_active_population']),
      'thermal_risk':min(
          score_ratio(cpu,budgets['cpu_frame_ms']),
          score_ratio(perf.get('draw_calls'),budgets['draw_calls']),
          score_ratio(perf.get('process_memory_mb'),budgets['process_memory_mb'])
      ),
    }
    if any(v<=9.0 for v in scores.values()):
        errors.append('one or more deterministic C6 dimensions are not strictly above 9.0')
    result={
      'schema_version':1,'task_id':'T11','critic_id':'C6','candidate':candidate,'candidate_commit':candidate,
      'passed':not errors,'errors':errors,'defects':errors.copy(),'coverage_complete':True,
      'scores':scores,'mandatory_dimensions':scores,'measurement':perf,
      'score_rule':'>9.0 unrounded; deterministic utilization scoring with hard budget failure',
      'physical_4k60_certified':False,
      'note':'Early quantitative C6 gate only; T68/T69 remain the physical certification authority.'
    }
    out=(ROOT/a.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['passed'] else 1)

if __name__=='__main__':
    main()
