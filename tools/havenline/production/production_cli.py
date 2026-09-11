#!/usr/bin/env python3
"""Havenline controlled-parallel production accelerator. Stdlib-only.

This tool enforces coordination contracts; it does not award independent critic
passes and does not certify physical-device performance.
"""
from __future__ import annotations
import argparse, fnmatch, hashlib, json, os, subprocess, sys, zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
PROD=ROOT/'Docs/Production'
ACTIVE={'ASSIGNED','BUILDING_ISOLATED','BUILT_PENDING_DEPENDENCY','INTEGRATION_READY','INTEGRATING','UNDER_REVIEW','FIX_REQUIRED'}
STRICT_MIN=9.0

def load(name): return json.loads((PROD/name).read_text())
def sha256(p):
 h=hashlib.sha256();
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def match(path,pat): return fnmatch.fnmatch(path,pat) or (pat.endswith('/**') and path.startswith(pat[:-3]))
def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()

def validate_registry():
 reg=load('WORKSTREAM_REGISTRY.json'); own=load('PATH_OWNERSHIP.json'); graph=load('DEPENDENCY_GRAPH.json')
 errors=[]; active=[w for w in reg['workstreams'] if w['status'] in ACTIVE]
 seen=[]
 for w in active:
  for p in w.get('owned_paths',[]):
   for other,op in seen:
    if other!=w['task_id'] and (match(p,op) or match(op,p) or (p.endswith('/**') and op.startswith(p[:-3])) or (op.endswith('/**') and p.startswith(op[:-3]))):
     errors.append(f'ownership collision {w["task_id"]}:{p} vs {other}:{op}')
   seen.append((w['task_id'],p))
  deps=graph['tasks'].get(w['task_id'],{}).get('depends_on',[]) if w['task_id'].startswith('T') else w.get('dependencies',[])
  approved={x['task_id'] for x in reg['workstreams'] if x['status']=='APPROVED'}
  missing=[d for d in deps if d not in approved]
  if w['status'] not in {'BLOCKED','UNDER_REVIEW','FIX_REQUIRED'} and missing: errors.append(f'{w["task_id"]} active before dependencies approved: {missing}')
 if reg['integration_branch']!=own['integration_branch']: errors.append('integration branch mismatch')
 return errors

def task_record(task):
 reg=load('WORKSTREAM_REGISTRY.json')
 for w in reg['workstreams']:
  if w['task_id']==task:return w
 for w in reg.get('planned_wave_1_locked_until_T03_approved',[]):
  if w['task_id']==task:return w
 return None

def validate_candidate(task, changed, integration_owner=False):
 own=load('PATH_OWNERSHIP.json'); reg=load('WORKSTREAM_REGISTRY.json'); errors=[]
 rec=task_record(task)
 if not rec: return [f'unknown task {task}']
 allowed=rec.get('owned_paths', own.get('wave_1_reservations_after_T03_approval',{}).get(task,[]))
 protected=[]
 for xs in own.get('protected_approved',{}).values():protected+=xs
 for w in reg['workstreams']:
  if w['task_id']!=task and w['status'] in ACTIVE: protected+=w.get('owned_paths',[])
 shared=own.get('shared_integration_owner_only',[])
 for p in changed:
  if any(match(p,x) for x in protected): errors.append(f'unauthorized protected/foreign path: {p}');continue
  if any(match(p,x) for x in shared) and not integration_owner: errors.append(f'integration-owner-only path: {p}');continue
  if not any(match(p,x) for x in allowed) and not (integration_owner and p.startswith('Docs/Production/')):
   errors.append(f'outside owned paths: {p}')
 return errors

def impacted(changed):
 rules=load('REGRESSION_SUITES.json'); tasks=set()
 for p in changed:
  for r in rules['impact_rules']:
   if match(p,r['glob']): tasks.update(r['tasks'])
 return sorted(tasks)

def regression_plan(changed):
 r=load('REGRESSION_SUITES.json'); tasks=impacted(changed); suites=list(r['universal_baseline'])
 for t in tasks:suites+=r['approved_task_suites'].get(t,[])
 return {'changed_files':changed,'impacted_tasks':tasks,'required_suites':list(dict.fromkeys(suites))}

def packet(task, output):
 graph=load('DEPENDENCY_GRAPH.json'); matrix=load('CRITIC_MATRIX.json'); own=load('PATH_OWNERSHIP.json'); rec=task_record(task) or {}
 deps=graph['tasks'][task]['depends_on']; paths=rec.get('owned_paths') or own.get('wave_1_reservations_after_T03_approval',{}).get(task,[])
 critics=matrix['task_overrides'].get(task) or []
 text=(PROD/'TASK_PACKET_TEMPLATE.md').read_text()+f"\n\n---\n## Generated values\n- Task: {task}\n- Dependencies: {deps}\n- Owned paths: {paths}\n- Required critics: {critics}\n- Integration branch at generation: {load('WORKSTREAM_REGISTRY.json')['integration_branch']}\n- Base integration commit: {git('rev-parse','HEAD')}\n"
 Path(output).write_text(text); print(output)

def capture_plan(task,motion=False):
 states=['front','rear','left','right','three_quarter','gameplay_scale','detail','overhead_if_relevant','day','night','weather_if_relevant','native_3840x2160_scale1_if_applicable']
 if motion: states+=['realtime_cycle','slow_cycle','turn_left','turn_right','transition','feet_toes_knees','hands','gear','tail_wings_mane_if_applicable','ground_contact','clipping_state']
 return {'task':task,'deterministic_required_states':states,'metadata_required':['candidate_commit','candidate_hash','scene_state','camera','renderer','resolution','render_scale','timestamp_utc','build_id'],'physical_fps_certification':False}

def save_matrix(task):
 return {'task':task,'cases':['fresh_save','existing_save','previous_version_save','interrupted_save','reload','migration','rollback_recovery_if_applicable'],'require_no_loss':True}
def device_matrix(task):
 return {'task':task,'classes':['phone_landscape','tablet_landscape','foldable_inner_landscape','foldable_transition_if_supported'],'checks':['safe_area','touch_targets','text_readability','camera_world_scale','resize','lifecycle','save_continuity'],'manual_device_selector_forbidden':True}

def evidence_package(task,candidate,changed,outzip):
 manifest={'task':task,'candidate_commit':candidate,'created_utc':datetime.now(timezone.utc).isoformat(),'changed_files':changed,'regression_plan':regression_plan(changed),'capture_plan':capture_plan(task),'save_matrix':save_matrix(task),'device_matrix':device_matrix(task),'known_failures':[],'final_dispositions':[]}
 z=Path(outzip);z.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as f:f.writestr('manifest.json',json.dumps(manifest,indent=2))
 print(json.dumps({'path':str(z),'sha256':sha256(z)},indent=2))

def closure(path):
 d=json.loads(Path(path).read_text()); errors=[]
 required=['G1','G2','G3','G4','G5','G6','G7','G8','G12','G13','G14']
 for g in required:
  if d.get('gates',{}).get(g) is not True: errors.append(f'{g} not passed')
 for g in ['G9','G10','G11']:
  v=d.get('gates',{}).get(g,'NOT_APPLICABLE')
  if v not in (True,'NOT_APPLICABLE'): errors.append(f'{g} applicable but not passed')
 if d.get('unresolved_mandatory_defects'):errors.append('unresolved mandatory defects')
 if d.get('hashes_valid') is not True:errors.append('invalid hashes')
 if d.get('evidence_current') is not True:errors.append('stale/missing evidence')
 for c in d.get('critic_reviews',[]):
  if c.get('independent') is not True: errors.append(f'critic {c.get("critic_id")} not independent')
  for k,v in c.get('mandatory_dimensions',{}).items():
   if isinstance(v,bool) or not isinstance(v,(int,float)) or not (v>STRICT_MIN): errors.append(f'{c.get("critic_id")} {k} must be >9.0, got {v}')
  if c.get('unresolved_defects'): errors.append(f'critic {c.get("critic_id")} unresolved defects')
 ok=not errors; print(json.dumps({'passed':ok,'errors':errors},indent=2)); return 0 if ok else 1

def main():
 ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='cmd',required=True)
 sp.add_parser('validate-registry')
 p=sp.add_parser('validate-candidate');p.add_argument('task');p.add_argument('files',nargs='+');p.add_argument('--integration-owner',action='store_true')
 p=sp.add_parser('impact');p.add_argument('files',nargs='+')
 p=sp.add_parser('regression-plan');p.add_argument('files',nargs='+')
 p=sp.add_parser('task-packet');p.add_argument('task');p.add_argument('--output',required=True)
 p=sp.add_parser('capture-plan');p.add_argument('task');p.add_argument('--motion',action='store_true')
 p=sp.add_parser('save-matrix');p.add_argument('task')
 p=sp.add_parser('device-matrix');p.add_argument('task')
 p=sp.add_parser('package');p.add_argument('task');p.add_argument('--candidate',required=True);p.add_argument('--changed',nargs='*',default=[]);p.add_argument('--output',required=True)
 p=sp.add_parser('closure');p.add_argument('manifest')
 a=ap.parse_args()
 if a.cmd=='validate-registry':
  e=validate_registry();print(json.dumps({'passed':not e,'errors':e},indent=2));sys.exit(0 if not e else 1)
 if a.cmd=='validate-candidate':
  e=validate_candidate(a.task,a.files,a.integration_owner);print(json.dumps({'passed':not e,'errors':e},indent=2));sys.exit(0 if not e else 1)
 if a.cmd=='impact':print(json.dumps({'impacted_tasks':impacted(a.files)},indent=2))
 elif a.cmd=='regression-plan':print(json.dumps(regression_plan(a.files),indent=2))
 elif a.cmd=='task-packet':packet(a.task,a.output)
 elif a.cmd=='capture-plan':print(json.dumps(capture_plan(a.task,a.motion),indent=2))
 elif a.cmd=='save-matrix':print(json.dumps(save_matrix(a.task),indent=2))
 elif a.cmd=='device-matrix':print(json.dumps(device_matrix(a.task),indent=2))
 elif a.cmd=='package':evidence_package(a.task,a.candidate,a.changed,a.output)
 elif a.cmd=='closure':sys.exit(closure(a.manifest))
if __name__=='__main__':main()
