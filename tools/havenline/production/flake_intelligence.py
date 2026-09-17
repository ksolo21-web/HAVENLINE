#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
REG=ROOT/'Docs/Production/FLAKE_REGISTRY.json'

def load(path:Path=REG): return json.loads(path.read_text())

def validate(data=None):
    data=data or load();errors=[]
    p=data.get('policy',{})
    if data.get('schema_version')!=1:errors.append('schema_version must be 1')
    if p.get('mandatory_gate_can_be_waived') is not False:errors.append('flake policy may never waive mandatory gates')
    if p.get('classification_changes_diagnosis_only') is not True:errors.append('flake classification must change diagnosis only')
    for i,row in enumerate(data.get('observations',[])):
        for key in ('source_sha','gate_id','test_id','environment_fingerprint','result'):
            if not str(row.get(key,'')).strip():errors.append(f'observation {i} missing {key}')
        if row.get('result') not in ('PASS','FAIL'):errors.append(f'observation {i} invalid result')
    return {'passed':not errors,'errors':errors,'observation_count':len(data.get('observations',[]))}

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
    a=ap.parse_args();result=validate() if a.cmd=='validate' else classify(a.source,a.gate,a.test,a.environment)
    print(json.dumps(result,indent=2));raise SystemExit(0 if result.get('passed',True) else 2)
if __name__=='__main__':main()
