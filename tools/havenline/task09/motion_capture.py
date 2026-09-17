#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math, os, shutil, struct, subprocess, sys, zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"tools"/"havenline"/"production"))
from lib import sha256_file

REQUIRED={"real-time-cycle","slow-review-cycle","turn-neg-135","turn-neg-090","turn-neg-045","turn-000","turn-030","turn-045","turn-090","turn-135","turn-180","transition-start","transition-end","close-upper-front","close-upper-opposite","close-waist-rear","close-lower-front","close-lower-rear"}
START_EQUIVALENCE_MAX_RMSE=0.012
FIRST_STEP_MAX_RMSE=0.045

def _paeth(a:int,b:int,c:int)->int:
    p=a+b-c;pa=abs(p-a);pb=abs(p-b);pc=abs(p-c)
    return a if pa<=pb and pa<=pc else b if pb<=pc else c

def png_pixels(path:Path)->bytes:
    raw=path.read_bytes()
    if raw[:8]!=b"\x89PNG\r\n\x1a\n":raise SystemExit(f"invalid PNG signature: {path}")
    pos=8;idat=[];width=height=channels=None
    while pos<len(raw):
        length=struct.unpack(">I",raw[pos:pos+4])[0];kind=raw[pos+4:pos+8];data=raw[pos+8:pos+8+length];pos+=12+length
        if kind==b"IHDR":
            width,height,depth,color,compression,filter_method,interlace=struct.unpack(">IIBBBBB",data)
            channels={2:3,6:4}.get(color)
            if depth!=8 or channels is None or compression or filter_method or interlace:
                raise SystemExit(f"unsupported PNG encoding: {path}")
        elif kind==b"IDAT":idat.append(data)
        elif kind==b"IEND":break
    if width is None or height is None or channels is None:raise SystemExit(f"PNG header missing: {path}")
    decoded=zlib.decompress(b"".join(idat));stride=width*channels;offset=0;prior=bytearray(stride);pixels=bytearray()
    for _ in range(height):
        mode=decoded[offset];offset+=1;scan=bytearray(decoded[offset:offset+stride]);offset+=stride
        for i,value in enumerate(scan):
            left=scan[i-channels] if i>=channels else 0;up=prior[i];upper_left=prior[i-channels] if i>=channels else 0
            if mode==1:scan[i]=(value+left)&255
            elif mode==2:scan[i]=(value+up)&255
            elif mode==3:scan[i]=(value+((left+up)//2))&255
            elif mode==4:scan[i]=(value+_paeth(left,up,upper_left))&255
            elif mode!=0:raise SystemExit(f"unsupported PNG filter: {mode}")
        pixels.extend(scan);prior=scan
    return bytes(pixels)

def normalized_rmse(a:Path,b:Path)->float:
    left=png_pixels(a);right=png_pixels(b)
    if len(left)!=len(right):raise SystemExit(f"PNG dimensions differ: {a} {b}")
    return math.sqrt(sum((x-y)**2 for x,y in zip(left,right))/(len(left)*255.0*255.0))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidate",required=True);ap.add_argument("--task",required=True)
    ap.add_argument("--scene",required=True);ap.add_argument("--subject-path",default=".")
    ap.add_argument("--animation-player-path",required=True);ap.add_argument("--animations",required=True)
    ap.add_argument("--out",required=True);ap.add_argument("--godot")
    a=ap.parse_args()
    if a.task!="T09":raise SystemExit("T09 motion capture requires --task T09")
    godot=a.godot or os.environ.get("GODOT_BIN") or shutil.which("Godot_v4.7.2-stable_linux.x86_64") or shutil.which("godot4") or shutil.which("godot")
    if not godot:raise SystemExit("Godot executable not found")
    out=(ROOT/a.out).resolve();out.mkdir(parents=True,exist_ok=True)
    cmd=[godot,"--path",str(ROOT/"HavenlineGodot"),"--rendering-method","mobile","--audio-driver","Dummy","--resolution","1280x720",
         "--script","res://assets/harvesting_v1/t09_motion_capture.gd","--",
         f"--out={out}",f"--candidate={a.candidate}",f"--task={a.task}",f"--scene={a.scene}",
         f"--subject-path={a.subject_path}",f"--animation-player-path={a.animation_player_path}",f"--animations={a.animations}"]
    p=subprocess.run(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=1800)
    (out/"motion-harness.log").write_text(p.stdout)
    if p.returncode:raise SystemExit(p.returncode)
    meta=json.loads((out/"motion.json").read_text())
    if meta.get("candidate_commit")!=a.candidate:raise SystemExit("candidate mismatch")
    if meta.get("harness")!="production_motion_v2" or meta.get("initialization_settle_frames",0)<2 or meta.get("first_use_warmup_frames",0)<8:
        raise SystemExit("motion initialization pre-roll metadata missing")
    present={row["evidence_type"] for row in meta["captures"]}
    missing=REQUIRED-present
    if missing:raise SystemExit("motion evidence types missing: "+",".join(sorted(missing)))
    frames=sorted(out.rglob("*.png"))
    hashes={str(path.relative_to(out)):sha256_file(path) for path in frames}
    initialization_validation={"start_equivalence_max_rmse":START_EQUIVALENCE_MAX_RMSE,"first_step_max_rmse":FIRST_STEP_MAX_RMSE,"animations":{},"passed":True}
    failed=[]
    for animation in a.animations.split(","):
        starts=[out/animation/"real-time-cycle/0000.png",out/animation/"slow-review-cycle/0000.png",out/animation/"transitions/start.png"]
        start_rmse=max(normalized_rmse(starts[0],starts[1]),normalized_rmse(starts[0],starts[2]),normalized_rmse(starts[1],starts[2]))
        first_step_rmse=normalized_rmse(starts[0],out/animation/"real-time-cycle/0001.png")
        initialization_validation["animations"][animation]={"start_max_normalized_rmse":start_rmse,"first_step_normalized_rmse":first_step_rmse}
        if start_rmse>START_EQUIVALENCE_MAX_RMSE or first_step_rmse>FIRST_STEP_MAX_RMSE:
            initialization_validation["passed"]=False
            failed.append(f"{animation} start={start_rmse:.6f} first_step={first_step_rmse:.6f}")
    (out/"motion-hashes.json").write_text(json.dumps({"candidate":a.candidate,"frames":hashes,"initialization_validation":initialization_validation},indent=2)+"\n")
    if failed:raise SystemExit("t=0 pose or first-step continuity is inconsistent after initialization: "+"; ".join(failed))
    print(json.dumps({"passed":True,"frames":len(frames),"out":str(out.relative_to(ROOT))},indent=2))

if __name__=="__main__":main()
