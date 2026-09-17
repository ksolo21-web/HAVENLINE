#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math, os, shutil, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"tools"/"havenline"/"production"))
from lib import sha256_file

REQUIRED={"real-time-cycle","slow-review-cycle","turn-neg-135","turn-neg-090","turn-neg-045","turn-000","turn-030","turn-045","turn-090","turn-135","turn-180","transition-start","transition-end","close-upper-front","close-upper-opposite","close-waist-rear","close-lower-front","close-lower-rear"}
# Initialization identity is checked in final skeleton-transform space. These
# tolerances are deliberately much tighter than visible C5 quality judgments.
START_MAX_TRANSLATION_M=0.005
START_MAX_ROTATION_DEG=1.0
# First-step continuity only rejects a gross initialization jump. C5 still owns
# the actual motion-quality verdict from the preserved rendered evidence.
FIRST_STEP_MAX_TRANSLATION_M=0.40
FIRST_STEP_MAX_ROTATION_DEG=55.0


def _capture(meta:dict,animation:str,evidence_type:str,file_suffix:str)->dict:
    rows=[row for row in meta.get("captures",[]) if row.get("animation")==animation and row.get("evidence_type")==evidence_type and str(row.get("file","")).endswith(file_suffix)]
    if len(rows)!=1:
        raise SystemExit(f"expected exactly one {animation} {evidence_type} {file_suffix} capture, found {len(rows)}")
    if not rows[0].get("pose_signature"):
        raise SystemExit(f"pose signature missing: {animation} {evidence_type} {file_suffix}")
    return rows[0]


def _pose_map(row:dict)->dict[tuple[str,int],tuple[list[float],list[float],str]]:
    result={}
    for bone in row.get("pose_signature",[]):
        key=(str(bone.get("skeleton","")),int(bone.get("bone_index",-1)))
        origin=[float(v) for v in bone.get("origin",[])]
        rotation=[float(v) for v in bone.get("rotation",[])]
        if key in result or len(origin)!=3 or len(rotation)!=4 or key[1]<0:
            raise SystemExit(f"invalid pose signature row: {bone}")
        result[key]=(origin,rotation,str(bone.get("bone","")))
    if not result:
        raise SystemExit("empty pose signature")
    return result


def _distance(a:list[float],b:list[float])->float:
    return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))


def _rotation_delta_deg(a:list[float],b:list[float])->float:
    # q and -q represent the same orientation, hence abs(dot).
    dot=abs(sum(x*y for x,y in zip(a,b)))
    dot=max(-1.0,min(1.0,dot))
    return math.degrees(2.0*math.acos(dot))


def pose_delta(left:dict,right:dict)->dict:
    a=_pose_map(left);b=_pose_map(right)
    if set(a)!=set(b):
        missing_left=sorted(set(b)-set(a));missing_right=sorted(set(a)-set(b))
        raise SystemExit(f"pose bone sets differ; left_missing={missing_left} right_missing={missing_right}")
    translations=[];rotations=[];worst_translation=None;worst_rotation=None
    for key in sorted(a):
        ao,aq,name=a[key];bo,bq,_=b[key]
        translation=_distance(ao,bo);rotation=_rotation_delta_deg(aq,bq)
        translations.append(translation);rotations.append(rotation)
        if worst_translation is None or translation>worst_translation[0]:worst_translation=(translation,name,key)
        if worst_rotation is None or rotation>worst_rotation[0]:worst_rotation=(rotation,name,key)
    return {
        "bone_count":len(a),
        "max_translation_m":max(translations),
        "rms_translation_m":math.sqrt(sum(v*v for v in translations)/len(translations)),
        "max_rotation_deg":max(rotations),
        "rms_rotation_deg":math.sqrt(sum(v*v for v in rotations)/len(rotations)),
        "worst_translation_bone":worst_translation[1],
        "worst_rotation_bone":worst_rotation[1],
    }


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
    if meta.get("initialization_pose_schema")!="skeleton_global_pose_v1":
        raise SystemExit("final skeleton pose schema missing")
    present={row["evidence_type"] for row in meta["captures"]}
    missing=REQUIRED-present
    if missing:raise SystemExit("motion evidence types missing: "+",".join(sorted(missing)))
    frames=sorted(out.rglob("*.png"))
    # Frame hashes bind evidence bytes to this run. They are provenance only and
    # are intentionally NOT used as an animation-pose equivalence gate.
    hashes={str(path.relative_to(out)):sha256_file(path) for path in frames}
    initialization_validation={
        "method":"final_skeleton_pose_transform_v1",
        "start_limits":{"max_translation_m":START_MAX_TRANSLATION_M,"max_rotation_deg":START_MAX_ROTATION_DEG},
        "first_step_limits":{"max_translation_m":FIRST_STEP_MAX_TRANSLATION_M,"max_rotation_deg":FIRST_STEP_MAX_ROTATION_DEG},
        "animations":{},"passed":True,
    }
    failed=[]
    for animation in a.animations.split(","):
        real0=_capture(meta,animation,"real-time-cycle","/0000.png")
        slow0=_capture(meta,animation,"slow-review-cycle","/0000.png")
        transition0=_capture(meta,animation,"transition-start","/start.png")
        real1=_capture(meta,animation,"real-time-cycle","/0001.png")
        start_pairs={
            "real_vs_slow":pose_delta(real0,slow0),
            "real_vs_transition":pose_delta(real0,transition0),
            "slow_vs_transition":pose_delta(slow0,transition0),
        }
        first_step=pose_delta(real0,real1)
        start_translation=max(row["max_translation_m"] for row in start_pairs.values())
        start_rotation=max(row["max_rotation_deg"] for row in start_pairs.values())
        row={"start_pairs":start_pairs,"start_max_translation_m":start_translation,"start_max_rotation_deg":start_rotation,"first_step":first_step}
        initialization_validation["animations"][animation]=row
        if start_translation>START_MAX_TRANSLATION_M or start_rotation>START_MAX_ROTATION_DEG or first_step["max_translation_m"]>FIRST_STEP_MAX_TRANSLATION_M or first_step["max_rotation_deg"]>FIRST_STEP_MAX_ROTATION_DEG:
            initialization_validation["passed"]=False
            failed.append(
                f"{animation} start_translation={start_translation:.6f}m start_rotation={start_rotation:.3f}deg "
                f"first_step_translation={first_step['max_translation_m']:.6f}m first_step_rotation={first_step['max_rotation_deg']:.3f}deg"
            )
    (out/"motion-hashes.json").write_text(json.dumps({"candidate":a.candidate,"frames":hashes,"initialization_validation":initialization_validation},indent=2)+"\n")
    if failed:raise SystemExit("C5 final skeleton pose initialization/continuity is inconsistent after warm-up: "+"; ".join(failed))
    print(json.dumps({"passed":True,"frames":len(frames),"initialization_method":initialization_validation["method"],"out":str(out.relative_to(ROOT))},indent=2))

if __name__=="__main__":main()