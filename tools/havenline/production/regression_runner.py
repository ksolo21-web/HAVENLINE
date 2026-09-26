#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, pathlib, shutil, subprocess, sys, time
from lib import ROOT, DOCS
from change_impact import calculate
from lib import changed_files

def resolve_godot(explicit=None):
    names=[explicit,os.environ.get("GODOT_BIN"),"Godot_v4.7.2-stable_linux.x86_64","godot4","godot"]
    for n in names:
        if not n: continue
        p=shutil.which(n)
        if p:return p
    return None

def suite_script(name):
    if name.endswith(".py"): return None
    if name.startswith("test_"): return f"res://tests/{name}.gd"
    return f"res://tests/{name}.gd"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base",required=True);ap.add_argument("--head",default="HEAD")
    ap.add_argument("--godot");ap.add_argument("--plan-only",action="store_true")
    ap.add_argument("--out",default="Docs/Production/Evidence/Regression/latest.json")
    a=ap.parse_args()
    impact=calculate(changed_files(a.base,a.head))
    result={"base":a.base,"head":a.head,"impact":impact,"executed":False,"results":[]}
    if a.plan_only:
        print(json.dumps(result,indent=2));return
    godot=resolve_godot(a.godot)
    if not godot: raise SystemExit("Godot 4.7.2 executable not found; use --plan-only or --godot")
    outdir=ROOT/"Docs/Production/Evidence/Regression/logs";outdir.mkdir(parents=True,exist_ok=True)
    failures=[]
    for suite in impact["required_suites"]:
        started=time.time()
        if suite.endswith(".py"):
            cmd=[sys.executable,str(ROOT/"tools/havenline"/suite)]
        else:
            cmd=[godot,"--headless","--audio-driver","Dummy","--path",str(ROOT/"HavenlineGodot"),"--script",suite_script(suite)]
        p=subprocess.run(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=240)
        log=outdir/f"{suite.replace('/','_')}.log";log.write_text(p.stdout,encoding="utf-8")
        ok=p.returncode==0 and "SCRIPT ERROR" not in p.stdout and "Parse Error" not in p.stdout
        row={"suite":suite,"passed":ok,"returncode":p.returncode,"seconds":round(time.time()-started,3),"log":str(log.relative_to(ROOT))}
        result["results"].append(row)
        if not ok: failures.append(suite)
    result["executed"]=True;result["passed"]=not failures;result["failures"]=failures
    path=ROOT/a.out;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    if failures: raise SystemExit(1)

if __name__=="__main__": main()
