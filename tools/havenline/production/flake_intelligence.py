#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
REG=ROOT/'Docs/Production/FLAKE_REGISTRY.json'

def load(path:Path=REG): return json.loads(path.read_text())

def validate_observations(rows:list[dict]):
    errors=[]
    for i,row in enumerate(rows):
        if not isinstance(row,dict):errors.append(f'observation {i} must be object');continue
        for key in ('source_sha','gate_id','test_id','environment_fingerprint','result'):
            if not str(row.get(key,'')).strip():errors.append(f'observation {i} missing {key}')
        if row.get('result') not in ('PASS','FAIL'):errors.append(f'observation {i} invalid result')
    return errors

def validate(data=None):
    data=data or load();errors=[];p=data.get('policy',{})
    if data.get('schema_version')!=1:errors.append('schema_version must be 1')
    if p.get('mandatory_gate_can_be_waived') is not False:errors.append('flake policy may never waive mandatory gates')
    if p.get('classification_changes_diagnosis_only') is not True:errors.append('flake classification must change diagnosis only')
    errors.extend(validate_observations(data.get('observations',[])))
    return {'passed':not errors,'errors':errors,'observation_count':len(data.get('observations',[]))}

def observations_from_files(paths:list[str|Path]):
    rows=[];errors=[];sources=[]
    for raw in paths:
        path=Path(raw);sources.append(str(path))
        try:data=json.loads(path.read_text())
        except Exception as exc:errors.append(f'{path}: invalid JSON: {exc}');continue
        if isinstance(data,dict) and isinstance(data.get('flake_observations'),list):candidate=data['flake_observations']
        elif isinstance(data,dict) and isinstance(data.get('observations'),list):candidate=data['observations']
        else:errors.append(f'{path}: no flake observation list');continue
        row_errors=validate_observations(candidate)
        errors.extend(f'{path}: {e}' for e in row_errors)
        if not row_errors:rows.extend(candidate)
    return {'passed':not errors,'errors':errors,'observations':rows,'source_files':sources}

def classify_records(records:list[dict],source_sha:str,gate_id:str,test_id:str,environment_fingerprint:str,minimum:int=3):
    same=[r for r in records if r.get('source_sha')==source_sha and r.get('gate_id')==gate_id and r.get('test_id')==test_id and r.get('environment_fingerprint')==environment_fingerprint]
    results=[r.get('result') for r in same if r.get('result') in ('PASS','FAIL')]
    if len(results)<minimum:classification='INSUFFICIENT_HISTORY'
    elif 'PASS' in results and 'FAIL' in results:classification='FLAKY'
    elif results and all(x=='PASS' for x in results):classification='STABLE_PASS'
    else:classification='STABLE_FAIL'
    return {'classification':classification,'observations':len(results),'passes':results.count('PASS'),'failures':results.count('FAIL'),'mandatory_gate_still_required':True,'repair_authorized':False}

def classify(source_sha,gate_id,test_id,environment_fingerprint,data=None):
    data=data or load();return classify_records(data.get('observations',[]),source_sha,gate_id,test_id,environment_fingerprint,int(data.get('policy',{}).get('minimum_observations',3)))

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True);sub.add_parser('validate')
    c=sub.add_parser('classify');c.add_argument('--source',required=True);c.add_argument('--gate',required=True);c.add_argument('--test',required=True);c.add_argument('--environment',required=True)
    f=sub.add_parser('classify-files');f.add_argument('--source',required=True);f.add_argument('--gate',required=True);f.add_argument('--test',required=True);f.add_argument('--environment',required=True);f.add_argument('files',nargs='+')
    v=sub.add_parser('validate-files');v.add_argument('files',nargs='+')
    a=ap.parse_args()
    if a.cmd=='validate':result=validate()
    elif a.cmd=='classify':result=classify(a.source,a.gate,a.test,a.environment)
    else:
        loaded=observations_from_files(a.files)
        if a.cmd=='validate-files':result=loaded
        elif not loaded['passed']:result=loaded
        else:
            minimum=int(load().get('policy',{}).get('minimum_observations',3));result=classify_records(loaded['observations'],a.source,a.gate,a.test,a.environment,minimum);result['source_files']=loaded['source_files']
    print(json.dumps(result,indent=2));raise SystemExit(0 if result.get('passed',True) else 2)
if __name__=='__main__':main()
