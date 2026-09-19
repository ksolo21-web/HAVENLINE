#!/usr/bin/env python3
from __future__ import annotations
import json,pathlib
from lib import ROOT,DOCS,load_json

def main():
    matrix=load_json(DOCS/'CRITIC_MATRIX.json');execution=load_json(DOCS/'CRITIC_EXECUTION.json');c0=load_json(DOCS/'C0_EXECUTION.json');errors=[]
    expected={f'C{i}' for i in range(1,12)}
    if set(matrix['critics'])!=expected:errors.append('CRITIC_MATRIX must define exactly approval critics C1-C11')
    if set(execution['critics'])!=expected:errors.append('CRITIC_EXECUTION must define exactly approval critics C1-C11')
    for cid in sorted(expected,key=lambda x:int(x[1:])):
        row=execution['critics'].get(cid,{})
        if row.get('status')!='OPERATIONAL':errors.append(cid+' not OPERATIONAL')
        if not row.get('runner'):errors.append(cid+' runner missing')
        if not row.get('dimensions'):errors.append(cid+' dimensions missing')
        if matrix['critics'][cid].get('independent_model_required') and cid not in ('C1','C2'):
            if row.get('runner')!='tools/havenline/production/specialist_critic_runner.py':errors.append(cid+' not wired to independent specialist runner')
            if not row.get('required_categories'):errors.append(cid+' evidence categories missing')
    if c0.get('critic_id')!='C0' or c0.get('status')!='OPERATIONAL' or c0.get('non_voting') is not True or c0.get('approval_critic') is not False:
        errors.append('C0 must be OPERATIONAL and explicitly non-voting')
    if c0.get('runner')!='tools/havenline/production/c0_root_cause_advisor.py':errors.append('C0 runner mismatch')
    if c0.get('workflow')!='.github/workflows/havenline-c0-root-cause.yml':errors.append('C0 workflow mismatch')
    if c0.get('candidate_freeze_policy')!='finish_running_sha':errors.append('C0 candidate freeze policy mismatch')
    if c0.get('may_score_gameplay') is not False or c0.get('may_approve_task') is not False or c0.get('may_lower_C1_C11_thresholds') is not False:
        errors.append('C0 authority must remain diagnostic-only')
    required_files=[
      'tools/havenline/production/c0_root_cause_advisor.py','tools/havenline/production/builder_repair_gate.py',
      'Docs/Production/C0_ROOT_CAUSE_STANDARD.md','Docs/Production/BUILDER_REPAIR_STANDARD.md','Docs/Production/C0_REPORT_SCHEMA.json','Docs/Production/C0_EXECUTION.json',
      '.github/workflows/havenline-c0-root-cause.yml',
      'tools/havenline/production/specialist_critic_runner.py','tools/havenline/production/specialist_evidence_manifest.py',
      'tools/havenline/production/security_exploit_harness.py','tools/havenline/production/domain_safeguard_gate.py',
      'tools/havenline/production/critic_harness.py','tools/havenline/production/closure_validator.py',
      'tools/havenline/production/motion_capture.py','tools/havenline/production/device_matrix.py',
      '.github/workflows/havenline-specialist-critic.yml','.github/workflows/havenline-specialist-model-cache.yml',
      'Docs/Production/SECURITY_ATTACK_MATRIX.json']
    for rel in required_files:
        if not (ROOT/rel).is_file():errors.append('missing '+rel)
    attacks=load_json(DOCS/'SECURITY_ATTACK_MATRIX.json')['attacks']
    if len(attacks)!=10 or len({a['id'] for a in attacks})!=10:errors.append('C9 must have 10 unique attacks')
    for tid,critics in matrix.get('task_applicability',{}).items():
        unknown=set(critics)-expected
        if unknown:errors.append(tid+' references unknown approval critics '+','.join(sorted(unknown)))
        if 'C0' in critics:errors.append(tid+' must not include non-voting C0 in approval applicability')
    specialist={cid for cid in expected if matrix['critics'][cid].get('independent_model_required') and cid not in ('C1','C2')}
    if specialist!={'C3','C4','C5','C7','C8','C10','C11'}:errors.append('unexpected independent specialist set')
    result={'schema_version':1,'passed':not errors,'diagnostic_critic':{'C0':c0.get('status')},'approval_critics':{cid:execution['critics'][cid]['status'] for cid in sorted(expected,key=lambda x:int(x[1:]))},'independent_specialist_critics':sorted(specialist),'deterministic_approval_critics':['C6','C9'],'errors':errors}
    print(json.dumps(result,indent=2));raise SystemExit(0 if not errors else 1)
if __name__=='__main__':main()
