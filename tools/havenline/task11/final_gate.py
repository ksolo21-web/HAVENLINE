#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math
from pathlib import Path

def load(path): return json.loads(Path(path).read_text())

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--candidate',required=True)
    ap.add_argument('--c2',required=True);ap.add_argument('--c3',required=True);ap.add_argument('--c4',required=True);ap.add_argument('--c6',required=True)
    ap.add_argument('--tests',required=True);ap.add_argument('--out',required=True)
    a=ap.parse_args();errors=[];critics={}
    for cid,path in [('C2',a.c2),('C3',a.c3),('C4',a.c4)]:
        row=load(path);critics[cid]=row
        if row.get('critic_id')!=cid:errors.append(cid+' id mismatch')
        if row.get('candidate_hash')!=a.candidate:errors.append(cid+' candidate mismatch')
        if row.get('passed') is not True:errors.append(cid+' did not pass')
        if row.get('defects')!=[]:errors.append(cid+' unresolved defects')
        if row.get('coverage_complete') is not True:errors.append(cid+' incomplete coverage')
        if row.get('independent_runtime') is not True:errors.append(cid+' independent runtime not proven')
        scores=row.get('scores',{})
        if not scores or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<=9.0 for v in scores.values()):
            errors.append(cid+' strict score failure')
    c6=load(a.c6);critics['C6']=c6
    if c6.get('critic_id')!='C6' or c6.get('candidate')!=a.candidate:errors.append('C6 identity mismatch')
    if c6.get('passed') is not True or c6.get('defects')!=[]:errors.append('C6 did not pass cleanly')
    c6scores=c6.get('mandatory_dimensions',{})
    if not c6scores or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<=9.0 for v in c6scores.values()):
        errors.append('C6 strict score failure')
    tests=load(a.tests)
    if tests.get('source')!=a.candidate or tests.get('all_passed') is not True or tests.get('suite_count')!=6 or tests.get('total_checks',0)<581:
        errors.append('functional/integration evidence incomplete')
    minima={cid:min((row.get('scores') or row.get('mandatory_dimensions') or {}).values()) for cid,row in critics.items()}
    out={
      'schema_version':1,'task_id':'T11','candidate':a.candidate,'passed':not errors,'errors':errors,
      'critic_minima':minima,'strict_rule':'>9.0 unrounded; zero unresolved defects; no averaging waiver',
      'functional_checks':tests.get('total_checks'),'functional_suites':tests.get('suite_count'),
      'ready_for_integration':not errors,'task_approved':False,'post_integration_regression_required':True,
      'physical_4k60_certified':False
    }
    path=Path(a.out);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2));raise SystemExit(0 if out['passed'] else 1)

if __name__=='__main__':
    main()
