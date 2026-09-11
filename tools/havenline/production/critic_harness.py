#!/usr/bin/env python3
"""Prepare/validate Havenline specialist critic records.
Does not call paid services and cannot turn self-review into independent review.
"""
import argparse, hashlib, json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];PROD=ROOT/'Docs/Production'
M=json.loads((PROD/'CRITIC_MATRIX.json').read_text())

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def applicable(task):
 v=M['task_overrides'].get(task,[])
 if v:return v
 n=int(task[1:]) if task.startswith('T') and task[1:].isdigit() else -1
 for k,val in M['task_overrides'].items():
  if '-' in k and k.startswith('T'):
   a,b=k.split('-');lo=int(a[1:]);hi=int(b[1:]) if b.startswith('T') else int(b)
   if lo<=n<=hi:return val
 return []
def prepare(task,candidate,inputs,out):
 record={'task':task,'candidate_commit':candidate,'required_critics':applicable(task),'inputs':[{'path':x,'sha256':sha(x)} for x in inputs],'forward_rule':'every mandatory dimension >9.0 unrounded','target':10.0,'independent_required':True,'provider':None,'model':None,'run_id':None,'raw_output_path':None,'self_review_is_not_independent':True}
 Path(out).write_text(json.dumps(record,indent=2));print(out)
def validate(packet,result):
 p=json.loads(Path(packet).read_text());r=json.loads(Path(result).read_text());errors=[]
 if r.get('task')!=p['task'] or r.get('candidate_commit')!=p['candidate_commit']:errors.append('task/candidate mismatch')
 if r.get('independent') is not True:errors.append('review not independent')
 for key in ['provider','model','run_id','raw_output_path']:
  if not r.get(key):errors.append('missing '+key)
 if r.get('critic_id') not in p['required_critics']:errors.append('critic not required/registered for task')
 dims=r.get('mandatory_dimensions',{})
 if not dims:errors.append('missing mandatory dimensions')
 for k,v in dims.items():
  if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not v>9.0:errors.append(f'{k} must be >9.0 unrounded; got {v}')
 if r.get('coverage_complete') is not True:errors.append('coverage incomplete')
 if r.get('unresolved_mandatory_defects'):errors.append('unresolved mandatory defects')
 raw=Path(r.get('raw_output_path',''))
 if not raw.exists():errors.append('raw output missing')
 elif r.get('raw_output_sha256') and sha(raw)!=r['raw_output_sha256']:errors.append('raw output hash mismatch')
 print(json.dumps({'passed':not errors,'errors':errors},indent=2));return 0 if not errors else 1

a=argparse.ArgumentParser();s=a.add_subparsers(dest='cmd',required=True)
p=s.add_parser('prepare');p.add_argument('task');p.add_argument('--candidate',required=True);p.add_argument('--inputs',nargs='+',required=True);p.add_argument('--output',required=True)
p=s.add_parser('validate');p.add_argument('packet');p.add_argument('result')
x=a.parse_args()
if x.cmd=='prepare':prepare(x.task,x.candidate,x.inputs,x.output)
else:raise SystemExit(validate(x.packet,x.result))
