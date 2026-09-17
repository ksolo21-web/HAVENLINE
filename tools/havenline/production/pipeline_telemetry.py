#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
from statistics import median

ROOT=Path(__file__).resolve().parents[3];DOCS=ROOT/'Docs/Production';POL=DOCS/'PIPELINE_TELEMETRY_POLICY.json';LEDGER=DOCS/'PIPELINE_TELEMETRY.json'
def load(p):return json.loads(p.read_text())
def validate(policy=None,ledger=None):
    policy=policy or load(POL);ledger=ledger or load(LEDGER);errors=[]
    if policy.get('schema_version')!=1 or ledger.get('schema_version')!=1:errors.append('schema_version must be 1')
    req=set(policy.get('required_metrics',[]));forbidden=[x.lower() for x in policy.get('forbidden_fields',[])]
    if policy.get('quality_threshold_changes_from_telemetry')!='FORBIDDEN':errors.append('telemetry must not change quality thresholds')
    for i,row in enumerate(ledger.get('records',[])):
        missing=req-set(row)
        if missing:errors.append(f'record {i} missing {sorted(missing)}')
        lower=' '.join(row.keys()).lower()
        if any(x in lower for x in forbidden):errors.append(f'record {i} contains forbidden field')
    return {'passed':not errors,'errors':errors,'record_count':len(ledger.get('records',[]))}
def summarize(records=None):
    records=records if records is not None else load(LEDGER).get('records',[])
    if not records:return {'records':0,'queue_seconds_median':None,'run_seconds_median':None,'reruns':0,'c0_cycles':0,'proof_cache_hits':0}
    return {'records':len(records),'queue_seconds_median':median([r['queue_seconds'] for r in records]),'run_seconds_median':median([r['run_seconds'] for r in records]),'reruns':sum(r['rerun_count'] for r in records),'c0_cycles':sum(r['c0_cycles'] for r in records),'proof_cache_hits':sum(r['proof_cache_hits'] for r in records)}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['validate','summary']);a=ap.parse_args();r=validate() if a.command=='validate' else summarize();print(json.dumps(r,indent=2));raise SystemExit(0 if r.get('passed',True) else 2)
if __name__=='__main__':main()
