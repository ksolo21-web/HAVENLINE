#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];DOCS=ROOT/'Docs/Production';LOCK=DOCS/'CI_TOOLCHAIN_LOCK.json'
ACTION_USE_RE=re.compile(r'uses:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_./-]+)?)@([^\s#]+)')
def load():return json.loads(LOCK.read_text())
def validate_workflow_action_pins(text:str,pins:dict[str,str],rel:str='<memory>')->list[str]:
    errors=[]
    for full_action,ref in ACTION_USE_RE.findall(text):
        parts=full_action.split('/')
        base='/'.join(parts[:2])
        expected=pins.get(base)
        if expected is None:errors.append(f'{rel}: unregistered external action {full_action}@{ref}')
        elif ref!=expected:errors.append(f'{rel}: {full_action} must pin base action {base} to {expected}, found {ref}')
    return errors
def validate():
    cfg=load();errors=[];pins=cfg.get('action_pins',{})
    if cfg.get('schema_version')!=1:errors.append('schema_version must be 1')
    if cfg.get('mutable_action_tags_forbidden') is not True:errors.append('mutable action tags must be forbidden')
    runtime=cfg.get('action_runtime',{})
    if runtime.get('required')!='node24':errors.append('critical external actions must target node24')
    verified=runtime.get('verified_official_major_tags',{})
    if set(verified)!=set(pins):errors.append('verified official major-tag registry must cover every action pin exactly')
    critical=cfg.get('critical_workflows',[])
    retired=cfg.get('retired_workflows',{})
    if set(critical)&set(retired):errors.append('workflow cannot be both critical and retired')
    for rel,row in retired.items():
        p=ROOT/rel
        if not p.exists():errors.append('missing retired workflow '+rel)
        if row.get('status')!='RETIRED_APPROVED_TASK':errors.append(f'{rel}: retired workflow status invalid')
        if row.get('forward_execution_allowed') is not False:errors.append(f'{rel}: retired workflow may not remain a forward execution path')
        if row.get('reopen_requires_full_revalidation') is not True:errors.append(f'{rel}: reopening must require full revalidation')
        src=str(row.get('accepted_integrated_source',''))
        if not re.fullmatch(r'[0-9a-f]{40}',src):errors.append(f'{rel}: retired workflow accepted source must be exact SHA')
    for rel in critical:
        p=ROOT/rel
        if not p.exists():errors.append('missing critical workflow '+rel);continue
        text=p.read_text();errors+=validate_workflow_action_pins(text,pins,rel)
        for m in re.findall(r'runs-on:\s*([^\s#]+)',text):
            if m.startswith('${{'):continue
            if m!=cfg['runner']['required_label']:errors.append(f'{rel}: runner {m} != {cfg["runner"]["required_label"]}')
    native=(ROOT/'.github/workflows/havenline-godot-android.yml').read_text();tools=cfg['tools']
    for token in (tools['godot'],tools['godot_editor_sha512'],tools['godot_templates_sha512'],tools['android_build_tools']):
        if token not in native:errors.append('native workflow missing tool lock '+token[:24])
    release=(ROOT/'.github/workflows/havenline-device-release-gate.yml').read_text()
    if f"python-version: '{tools['python']}'" not in release and f'python-version: "{tools["python"]}"' not in release:errors.append('release workflow missing locked Python version')
    if cfg['runner'].get('runtime_provenance_required') is not True:errors.append('runner provenance must be required')
    return {'passed':not errors,'errors':errors,'critical_workflow_count':len(critical),'retired_workflow_count':len(retired),'action_pin_count':len(pins),'action_runtime':runtime.get('required'),'runner_label':cfg['runner']['required_label']}
def provenance():
    cfg=load();return {'schema_version':1,'runner_label_expected':cfg['runner']['required_label'],'ImageOS':os.environ.get('ImageOS'),'ImageVersion':os.environ.get('ImageVersion'),'RUNNER_OS':os.environ.get('RUNNER_OS'),'RUNNER_ARCH':os.environ.get('RUNNER_ARCH'),'provenance_complete':all(os.environ.get(k) for k in cfg['runner']['required_runtime_fields'])}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['validate','provenance']);ap.add_argument('--output');a=ap.parse_args();r=validate() if a.command=='validate' else provenance();text=json.dumps(r,indent=2)+'\n';print(text,end='');
    if a.output:(ROOT/a.output).resolve().write_text(text)
    raise SystemExit(0 if r.get('passed',True) else 2)
if __name__=='__main__':main()
