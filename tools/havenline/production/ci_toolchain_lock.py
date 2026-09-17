#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];DOCS=ROOT/'Docs/Production';LOCK=DOCS/'CI_TOOLCHAIN_LOCK.json'
def load():return json.loads(LOCK.read_text())
def validate():
    cfg=load();errors=[];pins=cfg.get('action_pins',{})
    if cfg.get('schema_version')!=1:errors.append('schema_version must be 1')
    if cfg.get('mutable_action_tags_forbidden') is not True:errors.append('mutable action tags must be forbidden')
    for rel in cfg.get('critical_workflows',[]):
        p=ROOT/rel
        if not p.exists():errors.append('missing critical workflow '+rel);continue
        text=p.read_text()
        for action,ref in re.findall(r'uses:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@([^\s#]+)',text):
            expected=pins.get(action)
            if expected is None:errors.append(f'{rel}: unregistered external action {action}@{ref}')
            elif ref!=expected:errors.append(f'{rel}: {action} must pin {expected}, found {ref}')
        for m in re.findall(r'runs-on:\s*([^\s#]+)',text):
            if m.startswith('${{'):continue
            if m!=cfg['runner']['required_label']:errors.append(f'{rel}: runner {m} != {cfg["runner"]["required_label"]}')
    native=(ROOT/'.github/workflows/havenline-godot-android.yml').read_text()
    tools=cfg['tools']
    for token in (tools['godot'],tools['godot_editor_sha512'],tools['godot_templates_sha512'],tools['android_build_tools']):
        if token not in native:errors.append('native workflow missing tool lock '+token[:24])
    release=(ROOT/'.github/workflows/havenline-device-release-gate.yml').read_text()
    if f"python-version: '{tools['python']}'" not in release and f'python-version: "{tools["python"]}"' not in release:errors.append('release workflow missing locked Python version')
    if cfg['runner'].get('runtime_provenance_required') is not True:errors.append('runner provenance must be required')
    return {'passed':not errors,'errors':errors,'critical_workflow_count':len(cfg.get('critical_workflows',[])),'action_pin_count':len(pins),'runner_label':cfg['runner']['required_label']}
def provenance():
    cfg=load();return {'schema_version':1,'runner_label_expected':cfg['runner']['required_label'],'ImageOS':os.environ.get('ImageOS'),'ImageVersion':os.environ.get('ImageVersion'),'RUNNER_OS':os.environ.get('RUNNER_OS'),'RUNNER_ARCH':os.environ.get('RUNNER_ARCH'),'provenance_complete':all(os.environ.get(k) for k in cfg['runner']['required_runtime_fields'])}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['validate','provenance']);ap.add_argument('--output');a=ap.parse_args();r=validate() if a.command=='validate' else provenance();text=json.dumps(r,indent=2)+'\n';print(text,end='');
    if a.output:(ROOT/a.output).resolve().write_text(text)
    raise SystemExit(0 if r.get('passed',True) else 2)
if __name__=='__main__':main()
