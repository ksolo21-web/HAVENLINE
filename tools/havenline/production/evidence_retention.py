#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];DOCS=ROOT/'Docs/Production';POL=DOCS/'EVIDENCE_RETENTION_POLICY.json'
def load(p):return json.loads(p.read_text())
def validate_manifest(data:dict,policy=None,path:Path|None=None):
    policy=policy or load(POL);errors=[]
    for key in ('task_id','accepted_source','retention_class','records','regeneration_contract'):
        if key not in data:errors.append('missing '+key)
    tier=data.get('retention_class');cfg=policy.get('tiers',{}).get(tier)
    if cfg is None:errors.append('unknown retention_class')
    src=str(data.get('accepted_source',''))
    if not re.fullmatch(r'[0-9a-f]{40}',src):errors.append('accepted_source must be exact 40-char SHA')
    task=str(data.get('task_id','')).upper()
    if not re.fullmatch(r'T[0-9]{2}',task):errors.append('task_id must be canonical TNN')
    records=data.get('records',[])
    if not isinstance(records,list):errors.append('records must be list');records=[]
    minimum=int(cfg.get('minimum_days',0)) if cfg else 0
    repo_durable=0
    for i,row in enumerate(records):
        for k in ('kind','sha256','locator','reproducible','retention_days'):
            if k not in row:errors.append(f'record {i} missing {k}')
        if row.get('sha256') and not re.fullmatch(r'[0-9a-f]{64}',str(row.get('sha256'))):errors.append(f'record {i} invalid sha256')
        locator=str(row.get('locator','')).strip()
        if cfg and cfg.get('persistent_locator_required') and not locator:errors.append(f'record {i} persistent locator required')
        days=row.get('retention_days')
        if not isinstance(days,int) or isinstance(days,bool):errors.append(f'record {i} retention_days must be integer')
        elif days<minimum:errors.append(f'record {i} retention_days {days} below {tier} minimum {minimum}')
        if locator.startswith('repo://') and isinstance(days,int) and days>=minimum:repo_durable+=1
    if cfg and cfg.get('durable_manifest_required') and not records:errors.append('durable manifest tier requires records')
    if cfg and cfg.get('repository_manifest_required'):
        if repo_durable<1:errors.append('approval provenance requires durable repo:// record')
        expected=policy.get('approval_manifest_path','').replace('<TASK>',task)
        if path is not None:
            try: rel=path.resolve().relative_to(ROOT).as_posix()
            except ValueError: rel=''
            if rel!=expected:errors.append('approval manifest must use canonical path '+expected)
    regen=data.get('regeneration_contract')
    if not regen or not isinstance(regen,(str,dict)):errors.append('regeneration_contract must be non-empty string or object')
    if policy.get('secret_material_forbidden') is not True:errors.append('secret material must remain forbidden')
    return {'passed':not errors,'errors':errors,'retention_class':tier,'minimum_days':minimum,'record_count':len(records)}
def validate_policy():
    p=load(POL);errors=[]
    if p.get('schema_version')!=1:errors.append('schema_version must be 1')
    if p.get('artifact_expiry_may_not_erase_approval_provenance') is not True:errors.append('approval provenance must survive artifact expiry')
    for name in ('transient_raw','review_evidence','approval_provenance','irreplaceable'):
        if name not in p.get('tiers',{}):errors.append('missing tier '+name)
    return {'passed':not errors,'errors':errors}
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True);sub.add_parser('validate-policy');m=sub.add_parser('validate-manifest');m.add_argument('path');a=ap.parse_args()
    if a.cmd=='validate-policy':r=validate_policy()
    else:
        path=(ROOT/a.path).resolve();r=validate_manifest(load(path),path=path)
    print(json.dumps(r,indent=2));raise SystemExit(0 if r['passed'] else 2)
if __name__=='__main__':main()
