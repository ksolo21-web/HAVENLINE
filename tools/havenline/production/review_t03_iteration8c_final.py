#!/usr/bin/env python3
from __future__ import annotations
import base64,hashlib,io,json,math,os,pathlib,subprocess,time,urllib.request
from PIL import Image,ImageDraw

ROOT=pathlib.Path.cwd()
EVIDENCE=ROOT/os.environ.get("EVIDENCE_ROOT","task03-evidence")
OUT=ROOT/os.environ.get("OUT_DIR","task03-final-review")
CANDIDATE=os.environ["EXPECTED_SOURCE"]
CRITIC=os.environ["CRITIC_ID"].upper()
GROUP=os.environ["GROUP_ID"]
assert CRITIC in ("C1","C2")
OUT.mkdir(parents=True,exist_ok=True)

def digest(path:pathlib.Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(4*1024*1024),b""):h.update(b)
    return h.hexdigest()

ev=json.loads((EVIDENCE/"evidence.json").read_text())
assert ev["candidate_sha"]==CANDIDATE
assert ev["machine_gate_passed"] is True
assert ev["tests"]["all_passed"] is True and ev["tests"]["suite_count"]==16
assert ev["primitive_audit"]["passed"] is True and ev["primitive_audit"]["finding_count"]==0
assert ev["gallery_stills"]==47 and ev["native_4k_stills"]==11 and ev["total_stills"]==58
for rel,sha in ev["image_hashes"].items():
    p=EVIDENCE/rel
    assert p.is_file() and digest(p)==sha,("changed evidence",rel)

coverage=json.loads((ROOT/"Docs/Production/T05/ReferenceFrames/coverage.json").read_text())
rows={pathlib.Path(x["path"]).name:x for x in coverage["items"]}
REFS=["B-008.00.png","B-010.00.png","B-028.00.png","B-048.00.png"]
references=[]
for name in REFS:
    p=ROOT/"Docs/Production/T05/ReferenceFrames"/name
    assert p.is_file() and digest(p)==rows[name]["sha256"],("reference hash",name)
    references.append(p)

GROUPS={
 "fence":[
   "gallery/fence-panel-detail.png","gallery/south-fence-west.png","gallery/south-fence-centre.png","gallery/south-fence-east.png",
   "native4k/native-fence-detail.png","native4k/native-south-fence.png"
 ],
 "north-work-gates":[
   "gallery/north-gate-front.png","gallery/north-gate-rear.png","gallery/west-work-gate.png","gallery/east-work-gate.png",
   "gallery/gameplay-north-gate.png","gallery/gameplay-west-gate.png","gallery/gameplay-east-gate.png",
   "native4k/native-north-gate.png","native4k/native-side-gate-west.png","native4k/native-side-gate-east.png"
 ],
 "river-gates":[
   "gallery/river-gate-west-approach.png","gallery/river-gate-west.png","gallery/river-gate-west-camp-side.png",
   "gallery/river-gate-centre-approach.png","gallery/river-gate-centre.png","gallery/river-gate-centre-camp-side.png",
   "gallery/river-gate-east-approach.png","gallery/river-gate-east.png","gallery/river-gate-east-camp-side.png",
   "native4k/native-river-gate-west.png","native4k/native-river-gate-centre.png","native4k/native-river-gate-east.png"
 ],
 "lanes":[
   "gallery/central-spine-north.png","gallery/central-spine-centre.png","gallery/central-spine-river.png",
   "gallery/cross-lane-west.png","gallery/cross-lane-centre.png","gallery/cross-lane-east.png",
   "gallery/bank-lane-west.png","gallery/bank-lane-centre.png","gallery/bank-lane-east.png",
   "gallery/reserved-crossings-overhead.png","native4k/native-lane-network.png"
 ],
 "conditions":[
   "gallery/boundary-condition-day.png","gallery/boundary-condition-dusk.png","gallery/boundary-condition-night.png",
   "gallery/boundary-condition-dawn.png","gallery/boundary-condition-blizzard-night.png","gallery/boundary-condition-day-return.png"
 ]
}
NOTES={
 "fence":"Judge only T03 snow-capped pointed palisade: vertical silhouette, snow crowns, joins, grounding and reference-style timber. The intentionally removed exposed horizontal rail must not be demanded.",
 "north-work-gates":"Judge only north-main plus west/east work T03 gates: framed X-braced leaves, threshold posts, intentional open passage, hinge contact and cross-view readability.",
 "river-gates":"Judge only the three T03 river-facing future-crossing gates: framed leaves/posts, readable opening, dry approach and preserved clear corridor. No bridge is required.",
 "lanes":"Judge only T03 compacted/worn lane treatment inside the already user-accepted T02 ground/snow surface. Ignore dark station/pad rectangles and other foreign-owned props; they are not T03 lanes.",
 "conditions":"Judge only whether T03 fence/gates/lanes remain materially and geometrically consistent across day/dusk/night/dawn/blizzard. Ignore later-task stations, buildings, lamps and props."
}
assert GROUP in GROUPS

execution=json.loads((ROOT/"Docs/Production/CRITIC_EXECUTION.json").read_text())
runtime=execution["local_independent_runtime"]
cache=pathlib.Path(os.path.expanduser(runtime["cache_path"]))
m=json.loads((cache/"manifest.json").read_text())
assert m["publisher"]==runtime["provider"] and m["base_model"]==runtime["base_model"] and m["revision"]==runtime["model_revision"]
assert m.get("runtime_release")=="b10809"
for item in m["files"]:assert digest(cache/item["filename"])==item["sha256"]
servers=list((cache/"runtime").rglob("llama-server"));assert len(servers)==1;server=servers[0]

DIMS={"C1":["reference_fidelity","visual_language","cross_view_consistency"],"C2":["geometry_contact","clipping_seams","intentional_gap_integrity","cross_view_integrity"]}[CRITIC]
common={
 "observations":{"type":"array","items":{"type":"string","maxLength":220},"minItems":2,"maxItems":4},
 "coverage_complete":{"type":"boolean"},
 "confidence":{"type":"string","enum":["low","medium","high"]}
}
if CRITIC=="C1":
    pass_scores={
      "reference_fidelity":{"type":"number","minimum":10,"maximum":10},
      "visual_language":{"type":"number","minimum":10,"maximum":10},
      "cross_view_consistency":{"type":"number","exclusiveMinimum":9.0,"maximum":10}
    }
else:
    pass_scores={k:{"type":"number","exclusiveMinimum":9.0,"maximum":10} for k in DIMS}
all_scores={k:{"type":"number","minimum":0,"maximum":10} for k in DIMS}
pass_branch={"type":"object","properties":{
 **common,
 "defects":{"type":"array","items":{"type":"string","maxLength":220},"maxItems":0},
 "scores":{"type":"object","properties":pass_scores,"required":DIMS,"additionalProperties":False}
},"required":["observations","defects","coverage_complete","confidence","scores"],"additionalProperties":False}
fail_branch={"type":"object","properties":{
 **common,
 "defects":{"type":"array","items":{"type":"string","maxLength":220},"minItems":1,"maxItems":4},
 "scores":{"type":"object","properties":all_scores,"required":DIMS,"additionalProperties":False}
},"required":["observations","defects","coverage_complete","confidence","scores"],"additionalProperties":False}
schema={"oneOf":[pass_branch,fail_branch]}

def board()->pathlib.Path:
    ref_tiles=[]
    for p in references:
        im=Image.open(p).convert("RGB");im.thumbnail((420,300),Image.Resampling.LANCZOS);ref_tiles.append((p.name,im))
    cand=[]
    for rel in GROUPS[GROUP]:
        im=Image.open(EVIDENCE/rel).convert("RGB");im.thumbnail((420,255),Image.Resampling.LANCZOS);cand.append((rel,im))
    cols=3
    rr=(len(ref_tiles)+cols-1)//cols
    cr=(len(cand)+cols-1)//cols
    w=1350;ref_y=38;ref_h=rr*330;cand_y=ref_y+ref_h+45;h=cand_y+cr*300+20
    out=Image.new("RGB",(w,h),(19,29,40));d=ImageDraw.Draw(out)
    d.text((12,10),"AUTHORITATIVE USER REFERENCE PIXELS — style/material/shape language",fill="white")
    for i,(name,im) in enumerate(ref_tiles):
        c=i%cols;r=i//cols;x=c*450+(450-im.width)//2;y=ref_y+r*330+25
        d.text((c*450+8,ref_y+r*330+5),name,fill="white");out.paste(im,(x,y))
    d.text((12,cand_y-25),f"T03 EXACT SOURCE {CANDIDATE[:12]} — {GROUP} — ONLY THE NAMED T03 DOMAIN IS SCORED",fill="white")
    for i,(name,im) in enumerate(cand):
        c=i%cols;r=i//cols;x=c*450+(450-im.width)//2;y=cand_y+r*300+25
        d.text((c*450+8,cand_y+r*300+5),name[:68],fill="white");out.paste(im,(x,y))
    p=OUT/(GROUP+"-board.jpg");out.save(p,quality=93);return p

if CRITIC=="C1":
    rubric="""You are the independent Havenline C1 Reference Fidelity Critic. Review exact candidate pixels for ONE T03-owned domain only. The authoritative user-reference pixels are at the top of the board. T03 owns only palisade fences, framed gate leaves/threshold posts, and compacted work-lane treatment. Trees and T02 ground/snow/water are accepted baselines; stations, dark pads, machinery, shelters, lamps, characters and other later-task props are foreign-owned and MUST NOT be scored as T03 defects.
The Reference Style Lock is strict: reference_fidelity=10.0 exactly and visual_language=10.0 exactly are required; cross_view_consistency must be >9.0. A score below its pass rule requires a concrete visible T03-specific actionable defect. If the T03 domain has no actionable defect, defects MUST be [] and the pass scores must satisfy the strict rule. Judge visual grammar, not literal scene-layout identity: bright polished stylized 3D, clean sculpted readable forms, warm salmon/brown timber, crisp white snow frosting, purposeful framed timber gates, coherent contact shadows and compacted/worn lanes within the accepted T02 surface. Do not demand bridges or later-task props. Return JSON only."""
else:
    rubric="""You are the independent Havenline C2 Technical / Visual Integrity Critic. Review exact candidate pixels for ONE T03-owned domain only. T03 owns only palisade fences, framed open gate leaves/threshold posts, and compacted work-lane treatment. Ignore foreign-owned stations, pads, machinery, shelters, lamps, characters and later-task props.
Every mandatory C2 dimension must be strictly >9.0 unrounded. Exactly 9.0 fails. A score <=9.0 requires a concrete visible T03-specific defect. If no actionable T03 defect exists, defects MUST be []. Judge grounding/contact, clipping/seams, intentional gate gaps, lane continuity and cross-view integrity. Six openings are intentional: north-main, west/east work and three river future crossings. No bridge is required. Return JSON only."""
prompt=rubric+"\nGROUP-SPECIFIC SCOPE: "+NOTES[GROUP]+" Review every candidate panel in this board and nothing outside that named T03 domain."

bp=board();im=Image.open(bp).convert("RGB");im.thumbnail((1664,1664),Image.Resampling.LANCZOS);buf=io.BytesIO();im.save(buf,format="JPEG",quality=92)
request={
 "model":"havenline-t03-final-"+CRITIC.lower(),
 "messages":[{"role":"user","content":[
   {"type":"image_url","image_url":{"url":"data:image/jpeg;base64,"+base64.b64encode(buf.getvalue()).decode()}},
   {"type":"text","text":prompt}
 ]}],
 "max_tokens":750,"temperature":0.15,"top_p":0.9,"seed":20260923+(0 if CRITIC=="C1" else 100),
 "repeat_penalty":1.12,"chat_template_kwargs":{"enable_thinking":False},
 "response_format":{"type":"json_object","schema":schema},"cache_prompt":False
}
(OUT/"request-provenance.json").write_text(json.dumps({"candidate":CANDIDATE,"critic":CRITIC,"group":GROUP,"board_sha256":digest(bp),"reference_files":[{"path":str(p),"sha256":digest(p)} for p in references],"candidate_files":[{"path":x,"sha256":ev["image_hashes"][x]} for x in GROUPS[GROUP]],"prompt":prompt,"schema":schema},indent=2)+"\n")

env=dict(os.environ);env["LD_LIBRARY_PATH"]=str(server.parent)+":"+env.get("LD_LIBRARY_PATH","")
log=(OUT/"runtime.log").open("w")
cmd=[str(server),"-m",str(cache/m["model_file"]),"--mmproj",str(cache/m["projector_file"]),"--host","127.0.0.1","--port","8080","-c","12288","-t","4","-tb","4","-ngl","0","--no-mmproj-offload","--parallel","1","--jinja","--image-min-tokens","768","--image-max-tokens","2048"]
proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
fatal=None;review={}
try:
    for _ in range(180):
        if proc.poll() is not None:raise RuntimeError("reviewer runtime exited")
        try:
            if json.load(urllib.request.urlopen("http://127.0.0.1:8080/health",timeout=3)).get("status")=="ok":break
        except Exception:pass
        time.sleep(2)
    else:raise RuntimeError("reviewer runtime not ready")
    req=urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",data=json.dumps(request).encode(),headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=1800) as resp:raw=json.load(resp)
    (OUT/"raw.json").write_text(json.dumps(raw,indent=2))
    choice=raw["choices"][0]
    if choice.get("finish_reason")!="stop":raise RuntimeError("incomplete response")
    review=json.loads(choice["message"]["content"])
except Exception as exc:
    fatal=type(exc).__name__+": "+str(exc)
finally:
    proc.terminate()
    try:proc.wait(timeout=15)
    except Exception:proc.kill()
    log.close()

scores=review.get("scores",{});defects=review.get("defects",[])
valid=set(scores)==set(DIMS) and all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in scores.values())
if CRITIC=="C1":
    score_pass=valid and scores.get("reference_fidelity")==10.0 and scores.get("visual_language")==10.0 and scores.get("cross_view_consistency",0)>9.0
else:
    score_pass=valid and all(v>9.0 for v in scores.values())
passed=fatal is None and score_pass and defects==[] and review.get("coverage_complete") is True and review.get("confidence") in ("medium","high")
record={"task_id":"T03","critic_id":CRITIC,"candidate_hash":CANDIDATE,"group":GROUP,"provider":m["publisher"],"model":m["base_model"],"model_revision":m["revision"],"request_or_run_id":os.environ.get("GITHUB_RUN_ID","local")+"/"+os.environ.get("GITHUB_JOB","review"),"scores":scores,"defects":defects,"coverage_complete":review.get("coverage_complete",False),"confidence":review.get("confidence","low"),"independent_runtime":True,"reference_pixels_reviewed":True,"foreign_domain_exclusion_explicit":True,"fatal_error":fatal,"passed":passed,"review":review}
(OUT/"critic-record.json").write_text(json.dumps(record,indent=2)+"\n")
print(json.dumps(record,indent=2))
raise SystemExit(0 if passed else 1)
