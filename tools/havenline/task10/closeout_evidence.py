#!/usr/bin/env python3
"""Observe terminal GitHub metadata and enforce existing factory closeout gate."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/havenline/production'))
from factory_observer import observe,write_bundle
from factory_closeout_gate import validate

def load(path):return json.loads(Path(path).read_text())
def terminal_errors(candidate,run,regression,aggregate,provenance):
 errors=[]
 for name,row in [('capture/review',run),('regression',regression)]:
  if row.get('head_sha')!=candidate or row.get('status')!='completed' or row.get('conclusion')!='success':errors.append(name+' requires exact-source successful terminal run')
 if aggregate.get('candidate_commit')!=candidate or aggregate.get('passed') is not True or set(aggregate.get('required_critics',[]))!={'C1','C2','C3','C4','C6','C7'}:errors.append('complete exact-source critic aggregate required')
 rows=aggregate.get('results',[])
 if {x.get('critic_id') for x in rows}!={'C1','C2','C3','C4','C6','C7'} or len(rows)!=6 or any(x.get('passed') is not True or x.get('candidate')!=candidate for x in rows):errors.append('six validated exact-source critic results required')
 supplement=aggregate.get('quantitative_c6',{})
 if supplement.get('critic_id')!='C6' or supplement.get('candidate')!=candidate or supplement.get('passed') is not True:errors.append('separate exact-source quantitative C6 required')
 if provenance.get('candidate_commit')!=candidate:errors.append('runner provenance source mismatch')
 return errors

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',required=True);ap.add_argument('--run',required=True);ap.add_argument('--regression-run',required=True);ap.add_argument('--jobs',required=True);ap.add_argument('--artifacts',required=True);ap.add_argument('--provenance',required=True);ap.add_argument('--critic-aggregate',required=True);ap.add_argument('--artifact-root',required=True);ap.add_argument('--c0-cycles',required=True,type=int);ap.add_argument('--out',required=True);a=ap.parse_args()
 run=load(a.run);regression=load(a.regression_run);jobs=load(a.jobs);artifacts=load(a.artifacts);provenance=load(a.provenance);aggregate=load(a.critic_aggregate)
 errors=terminal_errors(a.candidate,run,regression,aggregate,provenance)
 if errors:raise SystemExit('\n'.join(errors))
 bundle=observe(run,jobs,artifacts,task='T10',provenance=provenance,artifact_root=a.artifact_root,c0_cycles=a.c0_cycles)
 write_bundle(bundle,a.out);result=validate('T10',a.candidate,bundle)
 Path(a.out,'factory-closeout-gate.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));raise SystemExit(0 if result['passed'] else 1)
if __name__=='__main__':main()
