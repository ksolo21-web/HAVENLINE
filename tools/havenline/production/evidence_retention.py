#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];DOCS=ROOT/'Docs/Production';POL=DOCS/'EVIDENCE_RETENTION_POLICY.json'
def load(p):return json.loads(p.read_text())
def validate_manifest(data:dict,policy=None):
    policy=policy or load(POL);errors=[]
    for key in ('task_id','accepted_source','retention_class','records','regeneration_contract'):
        if key not in data:errors.append('missing '+key)
    tier=data.get('retention_class');cfg=policy.get('tiers',{}).get(tier)
    if cfg is None:errors.append('unknown retention_class')
    src=str(data.get('accepted_source',''))
    if not re.fullmatch(r'[0-9a-f]{40}',src):errors.append('accepted_source must be exact 40-char SHA')
    records=data.get('records',[])
    if not isinstance(records,list):errors.append('records must be list');records=[]
    for i,row in enumerate(records):
        for k in ('kind','sha256','locator','reproducible'):
            if k not in row:errors.append(f'record {i} missing {k}')
        if row.get('sha256') and not re.fullmatch(r'[0-9a-f]{64}',str(row.get('sha256'))):errors.append(f'record {i} invalid sha256')
        if cfg and cfg.get('persistent_locator_required') and not str(row.get('locator','')).strip():errors.append(f'record {i} persistent locator required')
    if cfg and cfg.get('durable_manifest_required') and not records:errors.append('durable manifest tier requires records')
    if policy.get('secret_material_forbidden') is not True:errors.append('secret material must remain forbidden')
    return {'passed':not errors,'errors':errors,'retention_class':tier,'record_count':len(records)}
def validate_policy():
    p=load(POL);errors=[]
    if p.get('schema_version')!=1:errors.append('schema_version must be 1')
    if p.get('artifact_expiry_may_not_erase_approval_provenance') is not True:errors.append('approval provenance must survive artifact expiry')
    for name in ('transient_raw','review_evidence','approval_provenance','irreplaceable'):
        if name not in p.get('tiers',{}):errors.append('missing tier '+name)
    return {'passed':not errors,'errors':errors}
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True);sub.add_parser('validate-policy');m=sub.add_parser('validate-manifest');m.add_argument('path');a=ap.parse_args()
    r=validate_policy() if a.cmd=='validate-policy' else validate_manifest(load((ROOT/a.path).resolve()))
    print(json.dumps(r,indent=2));raise SystemExit(0 if r['passed'] else 2)
if __name__=='__main__':main()
