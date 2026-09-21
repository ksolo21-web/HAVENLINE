#!/usr/bin/env python3
from __future__ import annotations
import argparse,datetime,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];DOCS=ROOT/'Docs'/'Production';SCHEMA=DOCS/'EXECUTION_CHECKPOINT_SCHEMA.json'
SHA_RE=re.compile(r'^[0-9a-f]{40}$')
def load(p): return json.loads(Path(p).read_text())
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
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
    if row.get('stage_status')=='TIMEOUT':
        note=' '.join(str(row.get(k,'')) for k in ('notes','next_action'))
        if 'INFRASTRUCTURE_FAILURE' not in note: errors.append('TIMEOUT must preserve INFRASTRUCTURE_FAILURE classification')
    return {'passed':not errors,'errors':errors}
def make_record(a):
    return {'schema_version':1,'task_id':a.task.upper(),'integration_sha':a.integration,'candidate_sha':a.candidate,'branch':a.branch,'stage':a.stage,'stage_status':a.status,'completed_gates':[],'reusable_proof':[],'blocker_families':[],'running_workflows':[],'environment_fingerprint':a.environment or None,'next_action':a.next_action,'next_command':a.next_command,'updated_at':now(),'notes':a.notes or ''}
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True)
    n=sub.add_parser('new');n.add_argument('task');n.add_argument('--integration',required=True);n.add_argument('--candidate');n.add_argument('--branch',required=True);n.add_argument('--stage',default='PRECHECK');n.add_argument('--status',default='NOT_STARTED');n.add_argument('--environment');n.add_argument('--next-action',required=True);n.add_argument('--next-command',required=True);n.add_argument('--notes');n.add_argument('--output',required=True)
    v=sub.add_parser('validate');v.add_argument('path');r=sub.add_parser('resume');r.add_argument('path');a=ap.parse_args()
    if a.cmd=='new':
        row=make_record(a);result=validate_record(row)
        if not result['passed']: print(json.dumps(result,indent=2));raise SystemExit(2)
        Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(json.dumps(row,indent=2)+'\n');print(json.dumps(row,indent=2));return
    row=load(a.path);result=validate_record(row)
    if a.cmd=='validate': print(json.dumps(result,indent=2));raise SystemExit(0 if result['passed'] else 2)
    out={'passed':result['passed'],'task_id':row.get('task_id'),'stage':row.get('stage'),'stage_status':row.get('stage_status'),'next_action':row.get('next_action'),'next_command':row.get('next_command'),'candidate_sha':row.get('candidate_sha'),'integration_sha':row.get('integration_sha'),'running_workflows':row.get('running_workflows',[])}
    print(json.dumps(out,indent=2));raise SystemExit(0 if result['passed'] else 2)
if __name__=='__main__':main()
