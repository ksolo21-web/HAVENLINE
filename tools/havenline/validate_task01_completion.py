#!/usr/bin/env python3
"""Read-only closure check. Not an independent critic and never creates scores."""
from __future__ import annotations
import argparse,hashlib,json,math
from pathlib import Path

KEYS={'silhouette','materials','reference_fidelity','integration','geometric_integrity'}
GROUPS={'variant-1','variant-2','variant-3','forest','clearance','camera-motion'}
ROLES={'reference-fidelity','visual-integrity'}
SOURCE='8632c5b2c2a70ec1eb88db08bef8ca18b707e1a6'
PROBE={'A':'human_character','B':'snow_tree','C':'snow_tree','D':'human_character'}
MODEL_REVISION='3885219b6810b007914f3a7950a8d1b469d598a5'

def sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def check_reviews(root:Path,source:str)->tuple[list[dict],list[str]]:
    errors=[];rows=[]
    for role in sorted(ROLES):
        found=[];shards=[]
        for path in root.glob('*'+role+'*/shard-review.json'):
            data=json.loads(path.read_text());shards.append(data.get('shard'))
            if data.get('competency_passed') is not True: errors.append('Missing blind competency pass '+str(path))
            try:
                probe=json.loads((path.parent/'competency.json').read_text())
                raw=json.loads((path.parent/'competency-raw.json').read_text())['choices'][0]
                if probe.get('passed') is not True or probe.get('answers')!=PROBE or raw.get('finish_reason')!='stop' or json.loads(raw['message']['content'])!=PROBE:
                    errors.append('Blind competency raw answer not passing '+str(path))
                provenance=json.loads((path.parent/'provenance.json').read_text())
                if provenance.get('source')!=source or provenance.get('model')!='Qwen/Qwen3.5-9B' or provenance.get('model_revision')!=MODEL_REVISION or provenance.get('competency_passed') is not True or provenance.get('independent_model_execution') is not True:
                    errors.append('Invalid pinned critic provenance '+str(path))
            except (OSError,ValueError,KeyError,IndexError) as exc: errors.append('Missing/malformed competency or critic provenance '+str(path)+': '+str(exc))
            if data.get('source')!=source or data.get('role')!=role:
                errors.append('Wrong source or role: '+str(path))
            for row in data.get('reviews',[]):
                found.append(row)
                prefix=role+'/'+str(row.get('group'))
                if row.get('source')!=source or row.get('role')!=role:errors.append('Wrong review source/role '+prefix)
                if row.get('independent_execution') is not True:errors.append('No independent execution '+prefix)
                if row.get('competency_passed') is not True:errors.append('No blind competency for review '+prefix)
                if row.get('passed') is not True:errors.append('Reviewer did not pass '+prefix)
                if row.get('group')=='clearance':
                    wanted={'baseline_tree_blocks_central_player':False,'disabled_tree_blocks_central_player':True,'enabled_tree_blocks_central_player':False,'depleted_resource_tree_visible':False}
                    if row.get('factual_image_recognition_passed') is not True or row.get('review',{}).get('evidence_facts')!=wanted:errors.append('Unverified/incorrect factual clearance recognition '+prefix)
                review=row.get('review',{});scores=review.get('scores',{})
                if set(scores)!=KEYS or any(type(v) not in (float,int) or not math.isfinite(v) or not 9<=v<=10 for v in scores.values()):errors.append('Below9 or invalid dimensions '+prefix)
                elif row.get('lowest_score')!=min(scores.values()):errors.append('Reported minimum differs from actual raw scores '+prefix)
                if review.get('defects')!=[] or review.get('coverage_complete') is not True or review.get('confidence') not in ('medium','high'):errors.append('Defects, missing coverage or confidence '+prefix)
                raw=path.parent/(row.get('group','')+'-raw.json')
                if not raw.is_file():errors.append('Missing raw response '+prefix);continue
                actual=json.loads(raw.read_text())
                try:
                    choice=actual['choices'][0]
                    if choice['finish_reason']!='stop' or json.loads(choice['message']['content'])!=review:errors.append('Raw review does not match scored review '+prefix)
                except Exception:errors.append('Malformed raw review '+prefix)
        if len(shards)!=3 or set(shards)!={0,1,2}:errors.append('Missing/duplicate critic shard '+role)
        if len(found)!=6 or {r.get('group') for r in found}!=GROUPS:errors.append('Incomplete or duplicate group coverage '+role)
        rows+=found
    return rows,errors

def main():
    p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);p.add_argument('--reviews',type=Path,required=True);p.add_argument('--source-tree',type=Path,required=True);p.add_argument('--signoff',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();errors=[];pro=json.loads((a.evidence/'provenance.json').read_text())
    if pro.get('source')!=SOURCE:errors.append('Evidence source mismatch')
    for name,h in pro['captures'].items():
        f=a.evidence/name
        if not f.is_file() or sha(f)!=h:errors.append('Changed/missing capture '+name)
    for name,h in pro['assets'].items():
        f=a.source_tree/name
        if not f.is_file() or sha(f)!=h:errors.append('Changed/missing tree asset '+name)
    mechanical=json.loads((a.evidence/'mechanical-review.json').read_text())
    if mechanical.get('source')!=SOURCE or not mechanical.get('passed') or any(c['passed'] is not True for c in mechanical['mechanical_checks']):errors.append('Mechanical gate not passing')
    rows,issues=check_reviews(a.reviews,SOURCE);errors+=issues
    sign=json.loads(a.signoff.read_text())
    required={'reference_pixels_verified','all_variant_angles_inspected','camera_sequence_inspected','ground_contact_inspected','cutaway_and_resource_behavior_verified','raw_critic_findings_checked','source_and_asset_hashes_verified','prior_glbs_unchanged','frozen_scope_preserved','no_unresolved_mandatory_task_defect'}
    if sign.get('source')!=SOURCE or set(sign.get('checks',{}))!=required or any(v is not True for v in sign['checks'].values()):errors.append('Incomplete actual-evidence signoff')
    report={'task':'T01','source':SOURCE,'status':'PASS' if not errors else 'BLOCKED','minimum_dimension_score':9,'target':10,'score':min((r.get('lowest_score',0) for r in rows),default=None),'critic_roles':{role:min((r.get('lowest_score',0) for r in rows if r.get('role')==role),default=None) for role in sorted(ROLES)},'review_count':len(rows),'capture_count':len(pro['captures']),'engine_checks':mechanical['engine_checks'],'mechanical_check_count':len(mechanical['mechanical_checks']),'errors':errors,'independent_critic_execution_by_this_validator':False,'full_game_approved':False,'physical_phone_tablet_native4k60_verified':False,'task2_started':False,'signoff_sha256':sha(a.signoff),'blind_critic_competency_required':True,'critic_model':'Qwen/Qwen3.5-9B','critic_model_revision':MODEL_REVISION,'same_model_family_roles_disclosed':True}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return 0 if not errors else 1

if __name__=='__main__':raise SystemExit(main())
