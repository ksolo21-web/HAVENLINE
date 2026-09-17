#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];DOCS=ROOT/'Docs/Production';POL=DOCS/'EVIDENCE_RETENTION_POLICY.json'

def load(p):return json.loads(p.read_text())
def sha256_file(p:Path):return hashlib.sha256(p.read_bytes()).hexdigest()

def _repo_path(locator:str):
    prefix='repo://'
    if not locator.startswith(prefix):return None
    rel=locator[len(prefix):]
    repository='ksolo21-web/HAVENLINE/'
    if rel.startswith(repository):rel=rel[len(repository):]
    if not rel or rel.startswith('/'):return None
    candidate=(ROOT/rel).resolve()
    try:candidate.relative_to(ROOT.resolve())
    except ValueError:return None
    return candidate

def _approval_required_paths(task:str):
    critic_matrix=load(DOCS/'CRITIC_MATRIX.json')
    required={
      f'Docs/Production/{task}/verified-completion.json',
      f'Docs/Production/{task}/independent-critic-review.json',
      f'Docs/Production/{task}/defect-ledger.json',
      f'Docs/Production/{task}/task-state.json',
      f'Docs/Production/Evidence/{task}/REVIEW_EVIDENCE_MANIFEST.json',
    }
    required.update(f'Docs/Production/{task}/CriticRaw/{cid}.json' for cid in critic_matrix.get('task_applicability',{}).get(task,[]))
    return required

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
    repo_durable=0;repo_rel_paths=[];seen_locators=set()
    for i,row in enumerate(records):
        for k in ('kind','sha256','locator','reproducible','retention_days'):
            if k not in row:errors.append(f'record {i} missing {k}')
        digest=str(row.get('sha256',''))
        if policy.get('hashes_required') is True and not re.fullmatch(r'[0-9a-f]{64}',digest):
            errors.append(f'record {i} invalid sha256')
        locator=str(row.get('locator','')).strip()
        if not locator and cfg and cfg.get('persistent_locator_required'):errors.append(f'record {i} persistent locator required')
        if locator in seen_locators:errors.append(f'record {i} duplicate locator')
        seen_locators.add(locator)
        days=row.get('retention_days')
        if not isinstance(days,int) or isinstance(days,bool):errors.append(f'record {i} retention_days must be integer')
        elif days<minimum:errors.append(f'record {i} retention_days {days} below {tier} minimum {minimum}')
        if locator.startswith('repo://'):
            fp=_repo_path(locator)
            if fp is None:
                errors.append(f'record {i} repo locator escapes repository')
            else:
                try:repo_rel_paths.append(fp.relative_to(ROOT.resolve()).as_posix())
                except ValueError:errors.append(f'record {i} repo locator escapes repository')
                if path is not None:
                    if not fp.is_file():errors.append(f'record {i} repo locator missing file')
                    elif re.fullmatch(r'[0-9a-f]{64}',digest) and sha256_file(fp)!=digest:errors.append(f'record {i} repository hash mismatch')
            if isinstance(days,int) and days>=minimum:repo_durable+=1
    if cfg and cfg.get('durable_manifest_required') and not records:errors.append('durable manifest tier requires records')
    if cfg and cfg.get('repository_manifest_required'):
        if repo_durable<1:errors.append('approval provenance requires durable repo:// record')
        expected=policy.get('approval_manifest_path','').replace('<TASK>',task)
        if path is not None:
            try:rel=path.resolve().relative_to(ROOT.resolve()).as_posix()
            except ValueError:rel=''
            if rel!=expected:errors.append('approval manifest must use canonical path '+expected)
            expected_records=_approval_required_paths(task)
            if set(repo_rel_paths)!=expected_records:
                errors.append('approval provenance record set mismatch')
            if any(not str(row.get('locator','')).startswith('repo://') for row in records):
                errors.append('approval provenance records must all be repository durable')
            if any(row.get('reproducible') is not True for row in records):
                errors.append('approval provenance records must be reproducible')
    regen=data.get('regeneration_contract')
    if not regen or not isinstance(regen,(str,dict)):errors.append('regeneration_contract must be non-empty string or object')
    if isinstance(regen,dict) and tier in {'review_evidence','approval_provenance'}:
        if regen.get('exact_source')!=src:errors.append('regeneration exact_source mismatch')
        workflow=regen.get('workflow')
        if not workflow or not isinstance(workflow,str):errors.append('regeneration workflow missing')
        elif path is not None:
            wf=(ROOT/workflow).resolve()
            try:wf.relative_to(ROOT.resolve())
            except ValueError:errors.append('regeneration workflow escapes repository')
            else:
                if not wf.is_file():errors.append('regeneration workflow missing from repository')
        if tier=='approval_provenance':
            if not isinstance(regen.get('source_run_id'),int) or not isinstance(regen.get('source_artifact_id'),int):
                errors.append('approval regeneration run/artifact identity missing')
            index_path=DOCS/'Evidence'/task/'complete-evidence-index.json'
            if not re.fullmatch(r'[0-9a-f]{64}',str(regen.get('complete_evidence_index_sha256',''))):
                errors.append('approval regeneration evidence index hash missing')
            elif path is not None and (not index_path.is_file() or sha256_file(index_path)!=regen.get('complete_evidence_index_sha256')):
                errors.append('approval regeneration evidence index hash mismatch')
    if policy.get('secret_material_forbidden') is not True:errors.append('secret material must remain forbidden')
    return {'passed':not errors,'errors':errors,'retention_class':tier,'minimum_days':minimum,'record_count':len(records)}
def validate_policy():
    p=load(POL);errors=[]
    if p.get('schema_version')!=1:errors.append('schema_version must be 1')
    if p.get('artifact_expiry_may_not_erase_approval_provenance') is not True:errors.append('approval provenance must survive artifact expiry')
    if p.get('hashes_required') is not True:errors.append('evidence hashes must be required')
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
