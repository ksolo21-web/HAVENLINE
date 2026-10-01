#!/usr/bin/env python3
"""Ingest original separate-runtime C1/C2 records without assigning scores."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/havenline/production'))
from critic_harness import validate_raw

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--critic',choices=['C1','C2'],required=True);ap.add_argument('--candidate',required=True);ap.add_argument('--manifest',required=True);ap.add_argument('--record',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
 record=Path(a.record).resolve();manifest=Path(a.manifest).resolve();data=json.loads(record.read_text());m=json.loads(manifest.read_text())
 assert m['candidate_commit']==a.candidate and m['critic_id']==a.critic
 assert data['input_manifest_hash']==hashlib.sha256(manifest.read_bytes()).hexdigest()
 assert data['independent_runtime'] is True and data.get('request_or_run_id'),'separate actual reviewer provenance required'
 result=validate_raw(record,a.critic,a.candidate)
 Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'critic_id':a.critic,'passed':result['passed'],'errors':result['errors']}));raise SystemExit(0 if result['passed'] else 1)
if __name__=='__main__':main()
