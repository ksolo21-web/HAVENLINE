#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, pathlib, shlex, subprocess
from lib import ROOT, DOCS, load_json, sha256_file

def validate_layout_definition(matrix):
    """Reject omitted/duplicated or mislabeled fixtures before an adapter can pass."""
    errors=[]
    expected=['phone_16_9','phone_20_9','tablet_16_10','tablet_4_3','foldable_outer','foldable_inner']
    states=matrix.get('states',[])
    if [s.get('id') for s in states]!=expected:
        errors.append('layout matrix must contain all six distinct named states')
    if matrix.get('landscape_required') is not True:
        errors.append('landscape is a required product contract')
    ratios={'phone_16_9':16/9,'phone_20_9':20/9,'tablet_16_10':16/10,'tablet_4_3':4/3}
    for state in states:
        size=state.get('logical_size',[])
        if len(size)!=2 or any(type(n) is not int or n<=0 for n in size):
            errors.append(f"{state.get('id')}: two positive integer dimensions required")
            continue
        width,height=size
        if width<=height: errors.append(f"{state.get('id')}: landscape dimensions required")
        target=ratios.get(state.get('id'))
        # Native 2732x2048 is a slightly rounded 4:3 panel, not an invalid fixture.
        if target is not None and abs(width/height-target)/target>0.002:
            errors.append(f"{state.get('id')}: dimensions do not match the named aspect ratio")
    checks={'safe_area','primary_joystick_reach','text_readability','touch_target_size',
            'camera_world_scale','HUD_no_clipping','menu_scrollability','resize_transition',
            'lifecycle_resume','save_continuity'}
    if not checks.issubset(set(matrix.get('checks',[]))):
        errors.append('layout matrix is missing a required functional check')
    return errors

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidate",required=True);ap.add_argument("--task",required=True)
    ap.add_argument("--adapter",required=True,help="Executable command. Matrix id,width,height are appended.")
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    matrix=load_json(DOCS/"DEVICE_LAYOUT_MATRIX.json")
    definition_errors=validate_layout_definition(matrix)
    if definition_errors:
        raise SystemExit('Invalid layout definition: '+'; '.join(definition_errors))
    out=(ROOT/a.out).resolve();out.mkdir(parents=True,exist_ok=True)
    rows=[];fail=[]
    for state in matrix["states"]:
        w,h=state["logical_size"];sid=state["id"]
        cmd=shlex.split(a.adapter)+[sid,str(w),str(h)]
        env=dict(os.environ,HAVENLINE_CANDIDATE=a.candidate,HAVENLINE_TASK=a.task,HAVENLINE_DEVICE_STATE=sid)
        p=subprocess.run(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=env,timeout=300)
        log=out/f"{sid}.log";log.write_text(p.stdout)
        passed=p.returncode==0
        rows.append({"state":state,"passed":passed,"returncode":p.returncode,"log":str(log.relative_to(ROOT)),"log_sha256":sha256_file(log)})
        if not passed:fail.append(sid)
    result={"harness":"device_layout_matrix_v1","candidate_commit":a.candidate,"task_id":a.task,"checks":matrix["checks"],"states":rows,"passed":not fail,"failures":fail,"physical_4k60_certified":False}
    (out/"device-matrix.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    if fail:raise SystemExit(1)
if __name__=="__main__":main()
