#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];DOCS=ROOT/'Docs'/'Production'
def norm(s): return re.sub(r'[^a-z0-9]+',' ',str(s).lower()).strip()
def reports(task):
    out=[]
    for p in (DOCS/task).glob('C0*.json'):
        try:
            row=json.loads(p.read_text())
            if row.get('task_id')==task: out.append((p,row))
        except Exception: pass
    return out
def evaluate(task,candidate,report_path=None):
    policy=json.loads((DOCS/'PARALLEL_PREPARATION_POLICY.json').read_text())['blocker_policy'];src=[(Path(report_path),json.loads(Path(report_path).read_text()))] if report_path else reports(task);rows=[]
    for p,r in src:
        if r.get('failed_candidate')!=candidate: continue
        for b in r.get('blockers',[]): rows.append({'id':b.get('id'),'root':norm(b.get('root_cause')),'object':norm(b.get('affected_object')),'source':str(p.relative_to(ROOT))})
    rows=list({x['id']:x for x in rows if x.get('id')}.values());families={}
    for b in rows: families.setdefault(b['object'] or b['root'] or b['id'],[]).append(b['id'])
    trigger=len(rows)>=policy['causal_family_trigger_count'];marker=DOCS/task/f'BLOCKER_FAMILIES-{candidate[:7]}.json';passed=not trigger or marker.exists()
    return {'passed':passed,'task_id':task,'candidate':candidate,'blocker_count':len(rows),'trigger_count':policy['causal_family_trigger_count'],'causal_family_reconciliation_required':trigger,'family_marker':str(marker.relative_to(ROOT)),'family_marker_present':marker.exists(),'families':families,'errors':([] if passed else ['three-blocker causal-family reconciliation required before another candidate'])}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('task');ap.add_argument('candidate');ap.add_argument('--report');a=ap.parse_args();out=evaluate(a.task.upper(),a.candidate,a.report);print(json.dumps(out,indent=2));raise SystemExit(0 if out['passed'] else 2)
if __name__=='__main__':main()
