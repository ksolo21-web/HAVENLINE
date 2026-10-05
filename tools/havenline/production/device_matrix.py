#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, pathlib, shlex, subprocess
from lib import ROOT, DOCS, load_json, sha256_file

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidate",required=True);ap.add_argument("--task",required=True)
    ap.add_argument("--adapter",required=True,help="Executable command. Matrix id,width,height are appended.")
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    matrix=load_json(DOCS/"DEVICE_LAYOUT_MATRIX.json")
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
