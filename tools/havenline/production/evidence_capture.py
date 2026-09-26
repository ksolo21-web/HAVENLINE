#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, pathlib, shutil, subprocess, time
from lib import ROOT, sha256_file

REQUIRED=["front","rear","left","right","three-quarter","gameplay-scale","detail","overhead","condition-day","condition-night","condition-blizzard"]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidate",required=True);ap.add_argument("--task",required=True)
    ap.add_argument("--focus",default="0,0");ap.add_argument("--godot")
    ap.add_argument("--out",required=True);ap.add_argument("--native-4k",action="store_true")
    a=ap.parse_args()
    godot=a.godot or os.environ.get("GODOT_BIN") or shutil.which("Godot_v4.7.2-stable_linux.x86_64") or shutil.which("godot4") or shutil.which("godot")
    if not godot: raise SystemExit("Godot executable not found")
    out=(ROOT/a.out).resolve();out.mkdir(parents=True,exist_ok=True)
    resolution="3840x2160" if a.native_4k else "1280x720"
    cmd=[godot,"--path",str(ROOT/"HavenlineGodot"),"--rendering-method","mobile","--audio-driver","Dummy","--resolution",resolution,
         "--script","res://tests/production_capture_harness.gd","--",
         f"--out={out}",f"--focus={a.focus}",f"--candidate={a.candidate}",f"--task={a.task}",f"--build-id={int(time.time())}"]
    if a.native_4k:cmd.append("--native-4k")
    proc=subprocess.run(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=900)
    (out/"harness.log").write_text(proc.stdout)
    if proc.returncode:raise SystemExit(proc.returncode)
    meta=json.loads((out/"capture.json").read_text())
    names={r["name"] for r in meta["captures"]}
    missing=[x for x in REQUIRED if x not in names]
    if missing:raise SystemExit("missing required views: "+",".join(missing))
    if meta["candidate_commit"]!=a.candidate:raise SystemExit("candidate mismatch")
    manifest={p.name:sha256_file(p) for p in sorted(out.glob("*.png"))}
    (out/"capture-hashes.json").write_text(json.dumps({"candidate":a.candidate,"resolution":resolution,"files":manifest},indent=2)+"\n")
    print(json.dumps({"passed":True,"candidate":a.candidate,"task":a.task,"resolution":resolution,"images":len(manifest),"out":str(out.relative_to(ROOT))},indent=2))

if __name__=="__main__":main()
