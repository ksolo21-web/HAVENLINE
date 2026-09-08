#!/usr/bin/env python3
"""Task-one closure only: validates real records; never supplies critic scores."""
from __future__ import annotations
import argparse,hashlib,json,math
from pathlib import Path
ROLES=('reference-fidelity','visual-integrity')
GROUPS={'variant-1','variant-2','variant-3','forest','clearance','camera-motion'}
KEYS={'silhouette','materials','reference_fidelity','integration','geometric_integrity'}
MODEL='Qwen/Qwen3.5-9B';REVISION='3885219b6810b007914f3a7950a8d1b469d598a5'
PROBE={'A':'human_character','B':'snow_tree','C':'snow_tree','D':'human_character'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def relative(root,name):
 p=Path(name)
 if p.is_absolute() or '..' in p.parts:raise ValueError('Unsafe evidence path')
 r=(root/p).resolve()
 if not r.is_relative_to(root.resolve()):raise ValueError('Escaping evidence path')
 return r

def validate_review(row,raw,source):
 errors=[];r=row.get('review',{});s=r.get('scores',{})
 if row.get('source')!=source or row.get('independent_execution') is not True or row.get('competency_passed') is not True:errors.append('source/execution')
 if set(s)!=KEYS or any(type(x) not in (int,float) or not math.isfinite(x) or not 9<=x<=10 for x in s.values()):errors.append('scores')
 elif row.get('lowest_score')!=min(s.values()):errors.append('reported_minimum')
 if (type(r.get('defect_count')) is not int or r['defect_count']!=0 or not isinstance(r.get('defect_details'),str) or not r['defect_details'].strip()):errors.append('unresolved_defects')
 if r.get('coverage_complete') is not True or r.get('confidence') not in ('high','medium'):errors.append('coverage/confidence')
 try:
  c=raw['choices'][0]
  if c['finish_reason']!='stop' or json.loads(c['message']['content'])!=r:errors.append('raw_mismatch')
 except (KeyError,IndexError,ValueError,TypeError):errors.append('invalid_raw')
 if row.get('passed') is not True:errors.append('reviewer_did_not_pass')
 return errors

def main():
 p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);p.add_argument('--reviews',type=Path,required=True);p.add_argument('--source-tree',type=Path,required=True);p.add_argument('--signoff',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();errors=[];rows=[]
 try:
  pro=load(a.evidence/'provenance.json');source=pro['source']
  if len(source)!=40 or pro['task']!='T01' or pro['revision']!=4:errors.append('source identity')
  required={f'gallery/v{i:02d}-{angle}.png' for i in (1,2,3) for angle in ('front','rear','side','three-quarter')}
  required|={f'gallery/orbit-{i:02d}.png' for i in range(24)}|{f'gallery/integration-{i:02d}.png' for i in range(12)}
  required|={'gallery/gameplay-integration.png','gallery/forest-boundary-gameplay.png'}
  required|={f'clearance/clearance-{name}.png' for name in ('baseline','disabled','enabled')}
  required|={f'clearance/resource-clearance-{i:02d}.png' for i in range(6)}
  required|={'clearance/resource-depleted.png','clearance/resource-restored.png','native4k/native-scene.png','native4k/gameplay.png'}
  if set(pro['captures'])!=required:errors.append('required frame coverage')
  for name,h in pro['captures'].items():
   if sha(relative(a.evidence,name))!=h:errors.append('capture bytes '+name)
  for name,h in pro['assets'].items():
   if sha(relative(a.source_tree,name))!=h:errors.append('asset bytes '+name)
  before=load(a.evidence/'protected-before.json')
  if len(before)!=30:errors.append('original model count')
  for name,h in before.items():
   if sha(relative(a.source_tree,name))!=h:errors.append('original model changed '+name)
  mech=load(a.evidence/'mechanical-review.json');geometry=load(a.evidence/'geometry-audit.json')
  if mech['source']!=source or mech.get('passed') is not True or mech['engine_checks']!=676 or len(mech['mechanical_checks'])!=52 or any(c['passed'] is not True for c in mech['mechanical_checks']):errors.append('mechanical gate')
  if geometry.get('passed') is not True or geometry['geometry_checks']!=9:errors.append('geometry gate')
  if pro['native_dimensions'][0]<3840 or pro['native_dimensions'][1]<2160 or type(pro['render_scale']) not in (int,float) or pro['render_scale']!=1 or pro['renderer']!='mobile':errors.append('native renderer')
  for role in ROLES:
   role_rows=[];shards=[]
   for path in a.reviews.glob('*'+role+'*/shard-review.json'):
    r=load(path);shards.append(r.get('shard'))
    if r['source']!=source or r['role']!=role or r.get('competency_passed') is not True:errors.append('shard '+str(path))
    pr=load(path.parent/'provenance.json');c=load(path.parent/'competency.json');raw=load(path.parent/'competency-raw.json')['choices'][0]
    if pr['model']!=MODEL or pr['model_revision']!=REVISION or pr['source']!=source or pr['independent_model_execution'] is not True:errors.append('model provenance '+str(path))
    if c['passed'] is not True or c['answers']!=PROBE or raw['finish_reason']!='stop' or json.loads(raw['message']['content'])!=PROBE:errors.append('competency '+str(path))
    for row in r['reviews']:
     label=role+'/'+row['group'];role_rows.append(row)
     errors += [label+': '+s for s in validate_review(row,load(path.parent/(row['group']+'-raw.json')),source)]
     if row['role']!=role:errors.append('review role '+label)
     board=path.parent/(row['group']+'.png')
     if sha(board)!=row['inputs'][0]['board_sha256']:errors.append('model board bytes '+label)
     for panel in load(path.parent/(row['group']+'-sources.json')):
      if pro['captures'].get(panel['file'])!=panel['source_sha256']:errors.append('panel origin '+label)
   if len(shards)!=3 or set(shards)!={0,1,2} or len(role_rows)!=6 or {r['group'] for r in role_rows}!=GROUPS:errors.append('independent coverage '+role)
   rows+=role_rows
  sign=load(a.signoff)
  checks={'reference_pixels_verified','all_variant_angles_inspected','camera_sequence_inspected','ground_contact_inspected','cutaway_and_resource_behavior_verified','raw_critic_findings_checked','source_and_asset_hashes_verified','prior_glbs_unchanged','frozen_scope_preserved','no_unresolved_mandatory_task_defect'}
  if sign.get('source')!=source or set(sign.get('checks',{}))!=checks or any(v is not True for v in sign['checks'].values()):errors.append('actual pixel signoff')
 except (OSError,ValueError,KeyError,IndexError,TypeError) as exc:
  errors.append('missing/malformed evidence: '+str(exc));source=locals().get('source',None)
 scores={role:min((r.get('lowest_score',0) for r in rows if r.get('role')==role),default=None) for role in ROLES}
 report={'task':'T01','source':source,'status':'PASS' if not errors else 'BLOCKED','minimum_dimension_score':9,'target':10,'role_scores':scores,'score':min((r.get('lowest_score',0) for r in rows),default=None),'review_groups':len(rows),'errors':errors,'critic_model':MODEL,'critic_model_revision':REVISION,'same_model_family_roles_disclosed':True,'independent_critic_execution_by_this_validator':False,'full_game_approved':False,'physical_phone_tablet_4k60_verified':False,'task2_started':False}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
