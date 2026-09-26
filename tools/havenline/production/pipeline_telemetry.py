#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
from statistics import median

ROOT=Path(__file__).resolve().parents[3];DOCS=ROOT/'Docs/Production';POL=DOCS/'PIPELINE_TELEMETRY_POLICY.json';LEDGER=DOCS/'PIPELINE_TELEMETRY.json'
def load(p):return json.loads(Path(p).read_text())
def validate(policy=None,ledger=None):
    policy=policy or load(POL);ledger=ledger or load(LEDGER);errors=[]
    if policy.get('schema_version')!=1 or ledger.get('schema_version')!=1:errors.append('schema_version must be 1')
    req=set(policy.get('required_metrics',[]));forbidden=[x.lower() for x in policy.get('forbidden_fields',[])]
    if policy.get('quality_threshold_changes_from_telemetry')!='FORBIDDEN':errors.append('telemetry must not change quality thresholds')
    for i,row in enumerate(ledger.get('records',[])):
        if not isinstance(row,dict):errors.append(f'record {i} must be object');continue
        missing=req-set(row)
        if missing:errors.append(f'record {i} missing {sorted(missing)}')
        lower=' '.join(row.keys()).lower()
        if any(x in lower for x in forbidden):errors.append(f'record {i} contains forbidden field')
    return {'passed':not errors,'errors':errors,'record_count':len(ledger.get('records',[]))}
def records_from_files(paths:list[str|Path]):
    rows=[];errors=[];sources=[]
    for raw in paths:
        path=Path(raw);sources.append(str(path))
        try:data=load(path)
        except Exception as exc:errors.append(f'{path}: invalid JSON: {exc}');continue
        if isinstance(data,dict) and isinstance(data.get('telemetry'),dict):candidate=[data['telemetry']]
        elif isinstance(data,dict) and isinstance(data.get('records'),list):candidate=data['records']
        elif isinstance(data,dict):candidate=[data]
        else:errors.append(f'{path}: unsupported telemetry document');continue
        check=validate(ledger={'schema_version':1,'records':candidate})
        errors.extend(f'{path}: {e}' for e in check['errors'])
        if check['passed']:rows.extend(candidate)
    return {'passed':not errors,'errors':errors,'records':rows,'source_files':sources}
def summarize(records=None):
    records=records if records is not None else load(LEDGER).get('records',[])
    if not records:return {'records':0,'queue_seconds_median':None,'run_seconds_median':None,'reruns':0,'c0_cycles':0,'proof_cache_hits':0}
    return {'records':len(records),'queue_seconds_median':median([r['queue_seconds'] for r in records]),'run_seconds_median':median([r['run_seconds'] for r in records]),'reruns':sum(r['rerun_count'] for r in records),'c0_cycles':sum(r['c0_cycles'] for r in records),'proof_cache_hits':sum(r['proof_cache_hits'] for r in records),'artifact_bytes':sum(r['artifact_bytes'] for r in records)}
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='command',required=True);sub.add_parser('validate');sub.add_parser('summary');v=sub.add_parser('validate-files');v.add_argument('files',nargs='+');s=sub.add_parser('summary-files');s.add_argument('files',nargs='+');a=ap.parse_args()
    if a.command=='validate':r=validate()
    elif a.command=='summary':r=summarize()
    else:
        loaded=records_from_files(a.files)
        if a.command=='validate-files':r=loaded
        elif not loaded['passed']:r=loaded
        else:r=summarize(loaded['records']);r['source_files']=loaded['source_files'];r['passed']=True
    print(json.dumps(r,indent=2));raise SystemExit(0 if r.get('passed',True) else 2)
if __name__=='__main__':main()
