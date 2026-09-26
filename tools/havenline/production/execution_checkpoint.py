#!/usr/bin/env python3
from __future__ import annotations
import argparse,datetime,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];DOCS=ROOT/'Docs'/'Production';SCHEMA=DOCS/'EXECUTION_CHECKPOINT_SCHEMA.json'
SHA_RE=re.compile(r'^[0-9a-f]{40}$')
def load(p): return json.loads(Path(p).read_text())
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def uniq(seq):
    out=[]
    for x in seq:
        if x not in out: out.append(x)
    return out
def validate_record(row):
    cfg=load(SCHEMA);errors=[]
    for k in cfg['required_fields']:
        if k not in row: errors.append('missing '+k)
    if row.get('schema_version')!=1: errors.append('schema_version must be 1')
    if not re.fullmatch(r'T(?:1[1-9]|[2-6][0-9]|70)',str(row.get('task_id',''))): errors.append('task_id must be T11-T70')
    if row.get('stage') not in cfg['stages']: errors.append('invalid stage')
    if row.get('stage_status') not in cfg['stage_statuses']: errors.append('invalid stage_status')
    if not SHA_RE.fullmatch(str(row.get('integration_sha',''))): errors.append('integration_sha must be exact 40-char SHA')
    cand=row.get('candidate_sha')
    if cand is not None and not SHA_RE.fullmatch(str(cand)): errors.append('candidate_sha must be null or exact SHA')
    if row.get('stage') not in ('PRECHECK','BUILD') and not cand: errors.append('candidate_sha required after BUILD begins')
    for k in ('completed_gates','reusable_proof','blocker_families','running_workflows'):
        if k in row and not isinstance(row[k],list): errors.append(k+' must be a list')
    if not str(row.get('branch','')).strip(): errors.append('branch required')
    if not str(row.get('next_action','')).strip(): errors.append('next_action required')
    if not str(row.get('next_command','')).strip(): errors.append('next_command required')
    prev=row.get('previous_checkpoint_sha256')
    if prev is not None and not re.fullmatch(r'[0-9a-f]{64}',str(prev)): errors.append('previous_checkpoint_sha256 must be SHA-256')
    if row.get('stage_status')=='TIMEOUT':
        note=' '.join(str(row.get(k,'')) for k in ('notes','next_action'))
        if 'INFRASTRUCTURE_FAILURE' not in note: errors.append('TIMEOUT must preserve INFRASTRUCTURE_FAILURE classification')
    return {'passed':not errors,'errors':errors}
def make_record(a):
    return {'schema_version':1,'task_id':a.task.upper(),'integration_sha':a.integration,'candidate_sha':a.candidate,'branch':a.branch,'stage':a.stage,'stage_status':a.status,'completed_gates':[],'reusable_proof':[],'blocker_families':[],'running_workflows':[],'environment_fingerprint':a.environment or None,'next_action':a.next_action,'next_command':a.next_command,'updated_at':now(),'notes':a.notes or ''}
def advance_record(path,a):
    p=Path(path);old_bytes=p.read_bytes();row=json.loads(old_bytes);before=validate_record(row)
    if not before['passed']: return row,{'passed':False,'errors':['existing checkpoint invalid']+before['errors']}
    if a.candidate:
        if row.get('candidate_sha') not in (None,a.candidate):
            return row,{'passed':False,'errors':['candidate SHA change requires a new checkpoint']}
        row['candidate_sha']=a.candidate
    if a.integration and a.integration!=row.get('integration_sha'):
        return row,{'passed':False,'errors':['integration SHA change requires a new checkpoint/reconciliation']}
    row['previous_checkpoint_sha256']=hashlib.sha256(old_bytes).hexdigest()
    row['stage']=a.stage or row['stage'];row['stage_status']=a.status or row['stage_status']
    row['completed_gates']=uniq(row.get('completed_gates',[])+(a.add_gate or []))
    row['reusable_proof']=uniq(row.get('reusable_proof',[])+(a.proof or []))
    row['blocker_families']=uniq(row.get('blocker_families',[])+(a.blocker_family or []))
    if a.clear_running_workflows: row['running_workflows']=[]
    row['running_workflows']=uniq(row.get('running_workflows',[])+(a.workflow_id or []))
    if a.environment is not None: row['environment_fingerprint']=a.environment
    if a.next_action is not None: row['next_action']=a.next_action
    if a.next_command is not None: row['next_command']=a.next_command
    if a.notes is not None: row['notes']=a.notes
    row['updated_at']=now();result=validate_record(row)
    if result['passed']:
        tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(row,indent=2)+'\n');tmp.replace(p)
    return row,result
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True)
    n=sub.add_parser('new');n.add_argument('task');n.add_argument('--integration',required=True);n.add_argument('--candidate');n.add_argument('--branch',required=True);n.add_argument('--stage',default='PRECHECK');n.add_argument('--status',default='NOT_STARTED');n.add_argument('--environment');n.add_argument('--next-action',required=True);n.add_argument('--next-command',required=True);n.add_argument('--notes');n.add_argument('--output',required=True)
    v=sub.add_parser('validate');v.add_argument('path');r=sub.add_parser('resume');r.add_argument('path')
    x=sub.add_parser('advance');x.add_argument('path');x.add_argument('--integration');x.add_argument('--candidate');x.add_argument('--stage');x.add_argument('--status');x.add_argument('--add-gate',action='append');x.add_argument('--proof',action='append');x.add_argument('--blocker-family',action='append');x.add_argument('--workflow-id',action='append',type=int);x.add_argument('--clear-running-workflows',action='store_true');x.add_argument('--environment');x.add_argument('--next-action');x.add_argument('--next-command');x.add_argument('--notes')
    a=ap.parse_args()
    if a.cmd=='new':
        row=make_record(a);result=validate_record(row)
        if not result['passed']: print(json.dumps(result,indent=2));raise SystemExit(2)
        Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(json.dumps(row,indent=2)+'\n');print(json.dumps(row,indent=2));return
    if a.cmd=='advance':
        row,result=advance_record(a.path,a);print(json.dumps({'record':row,'validation':result},indent=2));raise SystemExit(0 if result['passed'] else 2)
    row=load(a.path);result=validate_record(row)
    if a.cmd=='validate': print(json.dumps(result,indent=2));raise SystemExit(0 if result['passed'] else 2)
    out={'passed':result['passed'],'task_id':row.get('task_id'),'stage':row.get('stage'),'stage_status':row.get('stage_status'),'next_action':row.get('next_action'),'next_command':row.get('next_command'),'candidate_sha':row.get('candidate_sha'),'integration_sha':row.get('integration_sha'),'running_workflows':row.get('running_workflows',[]),'previous_checkpoint_sha256':row.get('previous_checkpoint_sha256')}
    print(json.dumps(out,indent=2));raise SystemExit(0 if result['passed'] else 2)
if __name__=='__main__':main()
