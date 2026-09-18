#!/usr/bin/env python3
"""Transport-normalize original critic records; never create or adjust scores."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/havenline/production'))
from critic_harness import validate_raw,c6

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def verify_performance_binding(path,manifest,candidate):
 assert manifest.get('candidate_commit')==candidate and manifest.get('critic_id')=='C6', 'C6 manifest identity mismatch'
 rows=[item for group in manifest.get('groups',[]) for item in group.get('items',[]) if item.get('path')=='critic-input/performance.json']
 assert len(rows)==1 and rows[0].get('kind')=='json' and rows[0].get('category')=='quantitative_budgets', 'C6 performance manifest item missing or duplicated'
 assert sha(path)==rows[0].get('sha256'), 'quantitative C6 differs from reviewed performance bytes'

def verify_original(original, payload, manifest, cid, candidate):
 assert manifest['candidate_commit']==candidate and manifest['critic_id']==cid, 'manifest identity mismatch'
 assert original['candidate_hash']==candidate and original['critic_id']==cid, 'record identity mismatch'
 assert original['independent_runtime'] is True, 'independent runtime required'
 if cid in ('C3','C4','C7'):
  assert payload['candidate']==candidate and payload['critic_id']==cid, 'raw identity mismatch'
  assert payload.get('fatal_error') is None, 'raw fatal error'
  groups=payload['groups']
  assert len(groups)==len(manifest['groups']) and {g['group'] for g in groups}=={g['id'] for g in manifest['groups']}, 'raw group coverage mismatch'
  assert all(g.get('passed') is True for g in groups), 'raw group failed'
  expected={d:min(g['review']['scores'][d] for g in groups) for d in original['scores']}
  defects=[f"{g['group']}: {d}" for g in groups for d in g['review']['defects']]
  coverage=all(g['review']['coverage_complete'] is True for g in groups)
  confidence=min((g['review']['confidence'] for g in groups),key=lambda x:{'low':0,'medium':1,'high':2}[x])
 else:
  if cid in ('C1','C2'):
   assert original.get('task_id')=='T10', 'visual task identity mismatch'
   for key in ('task_id','candidate_hash','critic_id','input_manifest_hash','provider','model','request_or_run_id','independent_runtime'):
    assert original.get(key) and payload.get(key)==original[key], 'raw visual identity mismatch: '+key
   assert payload.get('independent_runtime') is True, 'raw visual independence required'
  if cid=='C6':assert payload.get('candidate_hash')==candidate and payload.get('critic_id')==cid, 'raw C6 identity mismatch'
  expected=payload['scores'];defects=payload['defects'];coverage=payload['coverage_complete'];confidence=payload['confidence']
 assert original['scores']==expected, 'scores differ from original independent output'
 assert original['defects']==defects and original['coverage_complete']==coverage and original['confidence']==confidence, 'disposition differs from original independent output'

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',required=True);ap.add_argument('--records-root',required=True);ap.add_argument('--inputs-root',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
 records=Path(a.records_root).resolve();inputs=Path(a.inputs_root).resolve();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
 results=[]
 for cid in ['C1','C2','C3','C4','C6','C7']:
  source=records/cid/'critic-record.json'
  try:
   original=json.loads(source.read_text());raw=records/cid/Path(original['raw_output_path']).name
   assert sha(raw)==original['raw_output_hash'],'raw output hash mismatch'
   payload=json.loads(raw.read_text())
   manifest=inputs/(cid+'-manifest.json')
   assert sha(manifest)==original['input_manifest_hash'],'input manifest hash mismatch'
   verify_original(original,payload,json.loads(manifest.read_text()),cid,a.candidate)
   normalized=dict(original,raw_output_path=str(raw),transport_original_record_sha256=sha(source),transport_original_raw_path=original['raw_output_path'])
   target=out/(cid+'-transport-record.json');target.write_text(json.dumps(normalized,indent=2)+'\n')
   result=validate_raw(target,cid,a.candidate)
  except Exception as exc: result={'critic_id':cid,'passed':False,'errors':[str(exc)]}
  results.append(result)
 try:
  verify_performance_binding(inputs/'performance.json',json.loads((inputs/'C6-manifest.json').read_text()),a.candidate)
  supplement=c6(inputs/'performance.json',a.candidate)
 except Exception as exc: supplement={'critic_id':'C6','passed':False,'errors':[str(exc)]}
 report={'task_id':'T10','candidate_commit':a.candidate,'required_critics':['C1','C2','C3','C4','C6','C7'],'results':results,'quantitative_c6':supplement,'passed':all(x.get('passed') is True for x in results) and supplement.get('passed') is True,'threshold_operator':'>','threshold':9.0,'unrounded':True,'task_approved':False}
 (out/'critic-aggregate.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'failures':[x for x in results if not x.get('passed')]}));raise SystemExit(0 if report['passed'] else 1)
if __name__=='__main__':main()
