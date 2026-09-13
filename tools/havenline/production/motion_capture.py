#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, pathlib, shutil, subprocess
from lib import ROOT, sha256_file

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidate",required=True);ap.add_argument("--task",required=True)
    ap.add_argument("--scene",required=True);ap.add_argument("--subject-path",default=".")
    ap.add_argument("--animation-player-path",required=True);ap.add_argument("--animations",required=True)
    ap.add_argument("--out",required=True);ap.add_argument("--godot")
    a=ap.parse_args()
    godot=a.godot or os.environ.get("GODOT_BIN") or shutil.which("Godot_v4.7.2-stable_linux.x86_64") or shutil.which("godot4") or shutil.which("godot")
    if not godot:raise SystemExit("Godot executable not found")
    out=(ROOT/a.out).resolve();out.mkdir(parents=True,exist_ok=True)
    cmd=[godot,"--path",str(ROOT/"HavenlineGodot"),"--rendering-method","mobile","--audio-driver","Dummy","--resolution","1280x720",
         "--script","res://tests/production_motion_capture.gd","--",
         f"--out={out}",f"--candidate={a.candidate}",f"--task={a.task}",f"--scene={a.scene}",
         f"--subject-path={a.subject_path}",f"--animation-player-path={a.animation_player_path}",f"--animations={a.animations}"]
    p=subprocess.run(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=1800)
    (out/"motion-harness.log").write_text(p.stdout)
    if p.returncode:raise SystemExit(p.returncode)
    meta=json.loads((out/"motion.json").read_text())
    if meta["candidate_commit"]!=a.candidate:raise SystemExit("candidate mismatch")
    required={"real-time-cycle","slow-review-cycle","turn-0","turn-30","turn-90","turn-180","transition-start","transition-end"}
    present={r["evidence_type"] for r in meta["captures"]}
    missing=required-present
    if missing:raise SystemExit("motion evidence types missing: "+",".join(sorted(missing)))
    frames=sorted(out.rglob("*.png"))
    hashes={str(f.relative_to(out)):sha256_file(f) for f in frames}
    (out/"motion-hashes.json").write_text(json.dumps({"candidate":a.candidate,"frames":hashes},indent=2)+"\n")
    print(json.dumps({"passed":True,"frames":len(frames),"out":str(out.relative_to(ROOT))},indent=2))
if __name__=="__main__":main()
