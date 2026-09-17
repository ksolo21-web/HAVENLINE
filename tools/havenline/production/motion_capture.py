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
    ap.add_argument("--script",default="res://tests/production_motion_capture.gd")
    a=ap.parse_args()
    godot=a.godot or os.environ.get("GODOT_BIN") or shutil.which("Godot_v4.7.2-stable_linux.x86_64") or shutil.which("godot4") or shutil.which("godot")
    if not godot:raise SystemExit("Godot executable not found")
    out=(ROOT/a.out).resolve();out.mkdir(parents=True,exist_ok=True)
    cmd=[godot,"--path",str(ROOT/"HavenlineGodot"),"--rendering-method","mobile","--audio-driver","Dummy","--resolution","1280x720",
         "--script",a.script,"--",
         f"--out={out}",f"--candidate={a.candidate}",f"--task={a.task}",f"--scene={a.scene}",
         f"--subject-path={a.subject_path}",f"--animation-player-path={a.animation_player_path}",f"--animations={a.animations}"]
    p=subprocess.run(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=1800)
    (out/"motion-harness.log").write_text(p.stdout)
    if p.returncode:raise SystemExit(p.returncode)
    meta=json.loads((out/"motion.json").read_text())
    if meta["candidate_commit"]!=a.candidate:raise SystemExit("candidate mismatch")
    required={"real-time-cycle","slow-review-cycle","transition-start","transition-end"}
    if meta.get("harness")=="production_motion_v2":
        required|={"turn-neg-135","turn-neg-090","turn-neg-045","turn-000","turn-030","turn-045","turn-090","turn-135","turn-180","close-upper-front","close-upper-opposite","close-waist-rear","close-lower-front","close-lower-rear"}
    else:
        required|={"turn-0","turn-30","turn-90","turn-180"}
    present={r["evidence_type"] for r in meta["captures"]}
    missing=required-present
    if missing:raise SystemExit("motion evidence types missing: "+",".join(sorted(missing)))
    frames=sorted(out.rglob("*.png"))
    hashes={str(f.relative_to(out)):sha256_file(f) for f in frames}
    if meta.get("harness")=="production_motion_v2":
        if meta.get("initialization_settle_frames",0)<2:raise SystemExit("motion initialization pre-roll metadata missing")
        for animation in a.animations.split(","):
            starts=[out/animation/"real-time-cycle/0000.png",out/animation/"slow-review-cycle/0000.png",out/animation/"transitions/start.png"]
            start_hashes={sha256_file(path) for path in starts}
            if len(start_hashes)!=1:raise SystemExit(f"{animation} t=0 evidence is inconsistent after initialization")
    (out/"motion-hashes.json").write_text(json.dumps({"candidate":a.candidate,"frames":hashes},indent=2)+"\n")
    print(json.dumps({"passed":True,"frames":len(frames),"out":str(out.relative_to(ROOT))},indent=2))
if __name__=="__main__":main()
