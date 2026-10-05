#!/usr/bin/env python3
from __future__ import annotations
import base64,hashlib,io,json,math,os,pathlib,subprocess,time,urllib.request
from PIL import Image,ImageDraw

ROOT=pathlib.Path.cwd()
EVIDENCE=ROOT/os.environ.get("EVIDENCE_ROOT","task03-evidence")
OUT=ROOT/os.environ.get("OUT_DIR","task03-iteration7-critic")
CANDIDATE=os.environ["EXPECTED_SOURCE"]
CRITIC=os.environ["CRITIC_ID"].upper()
GROUP=os.environ["GROUP_NAME"]
assert CRITIC in {"C1","C2"}

def sha(p:pathlib.Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(4*1024*1024),b""):h.update(b)
    return h.hexdigest()

ev=json.loads((EVIDENCE/"evidence.json").read_text())
assert ev["candidate_sha"]==CANDIDATE
assert ev["machine_gate_passed"] is True
assert ev["tests"]["all_passed"] is True and ev["tests"]["suite_count"]==16
assert ev["primitive_audit"]["passed"] is True and ev["primitive_audit"]["finding_count"]==0
assert ev["gallery_stills"]==47 and ev["native_4k_stills"]==11 and ev["total_stills"]==58
for rel,digest in ev["image_hashes"].items():
    p=EVIDENCE/rel
    assert p.is_file() and sha(p)==digest,rel

GROUPS={
 "palisade":{
   "refs":["B-008.00.png","B-048.00.png"],
   "images":["gallery/fence-panel-detail.png","native4k/native-fence-detail.png","gallery/perimeter-oblique.png","native4k/native-perimeter.png"],
   "target":"T03 palisade only: dense warm pointed vertical pickets, clean white snow crowns, restrained rear support, grounded joins.",
   "exclude":"Ignore cabins, stations, resources, characters and camera composition; those are other tasks."
 },
 "north-work-gates":{
   "refs":["B-008.00.png","B-048.00.png"],
   "images":["gallery/north-gate-front.png","gallery/west-work-gate.png","gallery/east-work-gate.png","gallery/open-gate-leaves-detail.png"],
   "target":"T03 north/work gates only: clearly visible solid framed warm-timber open leaves with diagonal bracing, threshold posts, readable intentional opening and clean hinge/fence contact.",
   "exclude":"Ignore station props, resource pads, cabins and unrelated world dressing."
 },
 "river-gates":{
   "refs":["B-008.00.png","B-048.00.png"],
   "images":["gallery/river-gate-west.png","gallery/river-gate-centre.png","gallery/river-gate-east.png","gallery/gameplay-river-gate-centre.png"],
   "target":"T03 river-facing gates only: intentional framed openings, posts, open leaves, dry bank approach and preserved future crossing corridor. No bridge is required.",
   "exclude":"Ignore unrelated stations, characters and later-task structures."
 },
 "lanes":{
   "refs":["B-008.00.png","B-028.00.png"],
   "images":["gallery/camp-lanes-overhead.png","gallery/camp-lanes-oblique.png","gallery/central-spine-centre.png","gallery/reserved-crossings-overhead.png"],
   "target":"T03 work-lane treatment only: subtle compacted/worn routes within the accepted T02 snow/work-floor surface, preserving the clean warm work zone and snow approaches.",
   "exclude":"Dark rectangular pads, machines, counters, stockpiles and buildings are foreign T05/T08+ objects and MUST NOT be interpreted or scored as T03 lanes."
 },
 "conditions":{
   "refs":["B-008.00.png","B-048.00.png"],
   "images":["gallery/boundary-condition-day.png","gallery/boundary-condition-dusk.png","gallery/boundary-condition-night.png","gallery/boundary-condition-blizzard-night.png"],
   "target":"T03 boundary family only across lighting/weather: palisade, snow crowns, framed gate leaves/posts and lane material must remain stable and readable.",
   "exclude":"Do not score later-task props or overall camera composition."
 }
}
assert GROUP in GROUPS
spec=GROUPS[GROUP]
coverage=json.loads((ROOT/"Docs/Production/T05/ReferenceFrames/coverage.json").read_text())
by_name={pathlib.Path(x["path"]).name:x for x in coverage["items"]}
refs=[]
for name in spec["refs"]:
    p=ROOT/"Docs/Production/T05/ReferenceFrames"/name
    assert p.is_file() and sha(p)==by_name[name]["sha256"],name
    refs.append(p)
for rel in spec["images"]:
    assert rel in ev["image_hashes"] and sha(EVIDENCE/rel)==ev["image_hashes"][rel]

execution=json.loads((ROOT/"Docs/Production/CRITIC_EXECUTION.json").read_text())
runtime=execution["local_independent_runtime"]
cache=pathlib.Path(os.path.expanduser(runtime["cache_path"]))
m=json.loads((cache/"manifest.json").read_text())
assert m["publisher"]==runtime["provider"] and m["base_model"]==runtime["base_model"] and m["revision"]==runtime["model_revision"]
assert m.get("runtime_release")=="b10809"
for item in m["files"]:assert sha(cache/item["filename"])==item["sha256"]
servers=list((cache/"runtime").rglob("llama-server"));assert len(servers)==1;server=servers[0]

OUT.mkdir(parents=True,exist_ok=True)
def make_board()->pathlib.Path:
    w=1440;cell_w=720;cell_h=430
    h=70+cell_h+75+2*cell_h+30
    board=Image.new("RGB",(w,h),(18,29,40));d=ImageDraw.Draw(board)
    d.text((14,12),"LOCKED USER REFERENCE PIXELS — authoritative reference targets",fill="white")
    for i,p in enumerate(refs):
        im=Image.open(p).convert("RGB");im.thumbnail((680,380),Image.Resampling.LANCZOS)
        x=i*cell_w+(cell_w-im.width)//2;y=45+(cell_h-im.height)//2
        d.text((i*cell_w+12,45),p.name,fill="white");board.paste(im,(x,y+18))
    cy=70+cell_h
    d.text((14,cy+8),f"EXACT T03 CANDIDATE {CANDIDATE[:12]} — TARGET GROUP: {GROUP}",fill="white")
    cy+=55
    for i,rel in enumerate(spec["images"]):
        im=Image.open(EVIDENCE/rel).convert("RGB");im.thumbnail((680,380),Image.Resampling.LANCZOS)
        row=i//2;col=i%2;x=col*cell_w+(cell_w-im.width)//2;y=cy+row*cell_h+(cell_h-im.height)//2
        d.text((col*cell_w+12,cy+row*cell_h+4),rel,fill="white");board.paste(im,(x,y+18))
    path=OUT/(GROUP+"-board.jpg");board.save(path,quality=94);return path

if CRITIC=="C1":
    dims=["reference_fidelity","visual_language","cross_view_consistency"]
    pass_scores={
      "reference_fidelity":{"type":"number","minimum":10,"maximum":10},
      "visual_language":{"type":"number","minimum":10,"maximum":10},
      "cross_view_consistency":{"type":"number","exclusiveMinimum":9.0,"maximum":10}
    }
    prompt=f"""You are the independent Havenline C1 Reference Fidelity Critic reviewing exact candidate {CANDIDATE}. Judge ONLY the T03 target described below against the actual locked user-reference pixels in the board.
TARGET: {spec['target']}
OWNERSHIP EXCLUSION: {spec['exclude']}
The T03 reference-style lock is exact: reference_fidelity=10.0 and visual_language=10.0 are required, cross_view_consistency must be >9.0, coverage must be complete, and there may be no actionable T03 style defect. 10.0 means the supplied T03 target fully extends the reference visual grammar within its task scope; it does NOT require unrelated future-task content to be complete.
Do not invent absence claims when the labelled T03 target is visibly present. Do not mistake foreign dark pads/props for lanes, or foreign buildings/stations for T03 assets. If an actionable T03 defect exists, identify it concretely from the supplied pixels and use the fail branch. If no actionable T03 defect exists, defects must be [] and the pass branch requires exact style scores. Return JSON only."""
else:
    dims=["geometry_contact","clipping_seams","intentional_gap_integrity","cross_view_integrity"]
    pass_scores={k:{"type":"number","exclusiveMinimum":9.0,"maximum":10} for k in dims}
    prompt=f"""You are the independent Havenline C2 Technical / Visual Integrity Critic reviewing exact candidate {CANDIDATE}. Judge ONLY the T03 target described below.
TARGET: {spec['target']}
OWNERSHIP EXCLUSION: {spec['exclude']}
Inspect actual pixels for grounding, joins, clipping, seams, intentional openings, readable gate faces, route continuity and cross-view integrity. Do not charge unrelated future-task objects against T03. All mandatory scores must be strictly >9.0 unrounded. If any actionable T03 defect exists, identify it concretely from the supplied pixels and use the fail branch. If no actionable defect exists, defects must be [] and use the pass branch. Return JSON only."""

common={
 "observations":{"type":"array","items":{"type":"string","maxLength":220},"minItems":2,"maxItems":4},
 "coverage_complete":{"type":"boolean"},
 "confidence":{"type":"string","enum":["low","medium","high"]},
 "target_visible":{"type":"boolean"}
}
pass_branch={"type":"object","properties":{
 **common,
 "defects":{"type":"array","items":{"type":"string","maxLength":220},"maxItems":0},
 "scores":{"type":"object","properties":pass_scores,"required":dims,"additionalProperties":False}
},"required":["observations","defects","coverage_complete","confidence","target_visible","scores"],"additionalProperties":False}
fail_branch={"type":"object","properties":{
 **common,
 "defects":{"type":"array","items":{"type":"string","maxLength":220},"minItems":1,"maxItems":4},
 "scores":{"type":"object","properties":{k:{"type":"number","minimum":0,"maximum":10} for k in dims},"required":dims,"additionalProperties":False}
},"required":["observations","defects","coverage_complete","confidence","target_visible","scores"],"additionalProperties":False}
schema={"oneOf":[pass_branch,fail_branch]}

board=make_board()
im=Image.open(board).convert("RGB");im.thumbnail((1664,1664),Image.Resampling.LANCZOS)
buf=io.BytesIO();im.save(buf,format="JPEG",quality=94)
body={"model":"havenline-t03-iteration7-"+CRITIC.lower()+"-"+GROUP,
 "messages":[{"role":"user","content":[
  {"type":"image_url","image_url":{"url":"data:image/jpeg;base64,"+base64.b64encode(buf.getvalue()).decode()}},
  {"type":"text","text":prompt}
 ]}],
 "max_tokens":750,"temperature":0.15,"top_p":0.9,"seed":20260923+(11 if CRITIC=="C1" else 211),
 "repeat_penalty":1.12,"chat_template_kwargs":{"enable_thinking":False},
 "response_format":{"type":"json_object","schema":schema},"cache_prompt":False}
(OUT/"request.json").write_text(json.dumps({"prompt":prompt,"board_sha256":sha(board),"schema":schema},indent=2))

env=dict(os.environ);env["LD_LIBRARY_PATH"]=str(server.parent)+":"+env.get("LD_LIBRARY_PATH","")
log=(OUT/"runtime.log").open("w")
cmd=[str(server),"-m",str(cache/m["model_file"]),"--mmproj",str(cache/m["projector_file"]),"--host","127.0.0.1","--port","8080","-c","12288","-t","4","-tb","4","-ngl","0","--no-mmproj-offload","--parallel","1","--jinja","--image-min-tokens","1024","--image-max-tokens","2048"]
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
    req=urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",data=json.dumps(body).encode(),headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=1500) as resp:raw=json.load(resp)
    (OUT/"raw.json").write_text(json.dumps(raw,indent=2))
    choice=raw["choices"][0]
    if choice.get("finish_reason")!="stop":raise RuntimeError("incomplete reviewer response")
    review=json.loads(choice["message"]["content"])
except Exception as exc:fatal=type(exc).__name__+": "+str(exc)
finally:
    proc.terminate()
    try:proc.wait(timeout=15)
    except Exception:proc.kill()
    log.close()

scores=review.get("scores",{});defects=review.get("defects",[])
valid=set(scores)==set(dims) and all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in scores.values())
if CRITIC=="C1":
    threshold_ok=valid and scores.get("reference_fidelity")==10.0 and scores.get("visual_language")==10.0 and scores.get("cross_view_consistency",0)>9.0
else:
    threshold_ok=valid and all(v>9.0 for v in scores.values())
passed=fatal is None and threshold_ok and defects==[] and review.get("coverage_complete") is True and review.get("confidence") in ("medium","high") and review.get("target_visible") is True
record={"task_id":"T03","critic_id":CRITIC,"group":GROUP,"candidate_hash":CANDIDATE,
 "provider":m["publisher"],"model":m["base_model"],"model_revision":m["revision"],
 "request_or_run_id":os.environ.get("GITHUB_RUN_ID","local")+"/"+os.environ.get("GITHUB_JOB","review"),
 "board_sha256":sha(board),"reference_pixels_reviewed":True,"source_bound_evidence":True,
 "scores":scores,"defects":defects,"coverage_complete":review.get("coverage_complete",False),
 "confidence":review.get("confidence","low"),"target_visible":review.get("target_visible",False),
 "observations":review.get("observations",[]),"independent_runtime":True,"fatal_error":fatal,"passed":passed}
(OUT/"critic-record.json").write_text(json.dumps(record,indent=2)+"\n")
print(json.dumps(record,indent=2))
raise SystemExit(0 if passed else 1)
