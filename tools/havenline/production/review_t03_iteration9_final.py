#!/usr/bin/env python3
from __future__ import annotations
import base64,hashlib,io,json,math,os,pathlib,subprocess,time,urllib.request
from PIL import Image,ImageDraw

ROOT=pathlib.Path.cwd()
EVIDENCE=ROOT/os.environ.get("EVIDENCE_ROOT","task03-evidence")
OUT=ROOT/os.environ.get("OUT_DIR","task03-final")
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
REF_NAMES=["B-008.00.png","B-028.00.png","B-048.00.png"]
REFS=[]
for name in REF_NAMES:
    p=ROOT/"Docs/Production/T05/ReferenceFrames"/name
    assert p.is_file() and digest(p)==rows[name]["sha256"],("reference hash",name)
    REFS.append(p)

GROUPS={
 "fence":[
  "gallery/fence-panel-detail.png","native4k/native-fence-detail.png"
 ],
 "north-gate":[
  "gallery/open-gate-leaves-detail.png","gallery/gate-post-detail.png","gallery/north-gate-front.png",
  "gallery/north-gate-rear.png","native4k/native-north-gate.png"
 ],
 "work-gates":[
  "gallery/west-work-gate.png","gallery/east-work-gate.png","gallery/gameplay-west-gate.png",
  "gallery/gameplay-east-gate.png","native4k/native-side-gate-west.png","native4k/native-side-gate-east.png"
 ],
 "river-gates":[
  "gallery/river-gate-west.png","gallery/river-gate-centre.png","gallery/river-gate-east.png",
  "native4k/native-river-gate-west.png","native4k/native-river-gate-centre.png","native4k/native-river-gate-east.png"
 ],
 "lanes-central":[
  "gallery/central-spine-north.png","gallery/central-spine-centre.png","gallery/central-spine-river.png",
  "gallery/cross-lane-west.png","gallery/cross-lane-centre.png","gallery/cross-lane-east.png"
 ],
 "lanes-bank":[
  "gallery/bank-lane-west.png","gallery/bank-lane-centre.png","gallery/bank-lane-east.png",
  "gallery/reserved-crossings-overhead.png","native4k/native-lane-network.png"
 ],
 "conditions":[
  "gallery/boundary-condition-day.png","gallery/boundary-condition-dusk.png","gallery/boundary-condition-night.png",
  "gallery/boundary-condition-dawn.png","gallery/boundary-condition-blizzard-night.png","gallery/boundary-condition-day-return.png"
 ]
}
NOTES={
 "fence":"Only continuous T03 palisade closeups are included here. River/open-gate gaps are intentionally excluded and reviewed in gate groups. Judge snow crowns, vertical joins, grounding and timber finish.",
 "north-gate":"Judge the north-main gate only. The authored solid dark timber faces, warm frame/X-bracing and snow-capped threshold posts must be visibly present and grounded. Perspective trapezoid shape is expected for an opened leaf.",
 "work-gates":"Judge west/east work gates only. Confirm framed X-braced leaves, threshold posts, hinge contact and readable open passages across gameplay and native-4K views.",
 "river-gates":"Judge the three river-facing future-crossing gates only. Framed open leaves and posts must read at each threshold; no bridge is required. The open corridor itself is intentional.",
 "lanes-central":"Judge the central/cross-camp T03 lane treatment only. It is compressed/worn material in the SAME accepted T02 surface, using darker salmon-brown wear and paired ruts—not a separate road mesh or dark asphalt.",
 "lanes-bank":"Judge bank and future-crossing T03 lane treatment only. In snow it should read as low-contrast cool packed wear/ruts continuous toward gate thresholds; it must remain part of the same T02 terrain surface.",
 "conditions":"Judge T03 fence/gate/lane identity and geometry across day/dusk/night/dawn/blizzard. Lighting is expected to change apparent color; do not demand daytime color values at night."
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

if CRITIC=="C1" and GROUP=="conditions":
    DIMS=["cross_view_consistency"]
    pass_scores={"cross_view_consistency":{"type":"number","exclusiveMinimum":9.0,"maximum":10}}
elif CRITIC=="C1":
    DIMS=["reference_fidelity","visual_language","cross_view_consistency"]
    pass_scores={
      "reference_fidelity":{"type":"number","minimum":10,"maximum":10},
      "visual_language":{"type":"number","minimum":10,"maximum":10},
      "cross_view_consistency":{"type":"number","exclusiveMinimum":9.0,"maximum":10}
    }
else:
    DIMS=["geometry_contact","clipping_seams","intentional_gap_integrity","cross_view_integrity"]
    pass_scores={k:{"type":"number","exclusiveMinimum":9.0,"maximum":10} for k in DIMS}

common={
 "observations":{"type":"array","items":{"type":"string","maxLength":220},"minItems":2,"maxItems":4},
 "coverage_complete":{"type":"boolean"},
 "confidence":{"type":"string","enum":["low","medium","high"]}
}
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
    show_refs=not (CRITIC=="C1" and GROUP=="conditions")
    refs=[]
    if show_refs:
        for p in REFS:
            im=Image.open(p).convert("RGB");im.thumbnail((360,270),Image.Resampling.LANCZOS);refs.append((p.name,im))
    cand=[]
    for rel in GROUPS[GROUP]:
        im=Image.open(EVIDENCE/rel).convert("RGB")
        im.thumbnail((560,330),Image.Resampling.LANCZOS)
        cand.append((rel,im))
    cols=2
    w=1180
    y=10
    canvas_h=80
    if refs:canvas_h+=300*((len(refs)+2)//3)
    canvas_h+=360*((len(cand)+1)//2)+30
    out=Image.new("RGB",(w,canvas_h),(19,29,40));d=ImageDraw.Draw(out)
    if refs:
        d.text((12,y),"AUTHORITATIVE USER REFERENCE PIXELS — visual grammar authority",fill="white");y+=28
        for i,(name,im) in enumerate(refs):
            x=(i%3)*390+(390-im.width)//2
            yy=y+(i//3)*300+25
            d.text(((i%3)*390+8,y+(i//3)*300+4),name,fill="white")
            out.paste(im,(x,yy))
        y+=300*((len(refs)+2)//3)+10
    d.text((12,y),f"T03 EXACT SOURCE {CANDIDATE[:12]} — {GROUP} — ONLY THIS T03 DOMAIN IS SCORED",fill="white");y+=28
    for i,(name,im) in enumerate(cand):
        c=i%2;r=i//2;x=c*590+(590-im.width)//2;yy=y+r*360+26
        d.text((c*590+8,y+r*360+4),name[:80],fill="white");out.paste(im,(x,yy))
    p=OUT/(GROUP+"-board.jpg");out.save(p,quality=94);return p

if CRITIC=="C1" and GROUP=="conditions":
    rubric="""You are the independent Havenline C1 cross-view consistency critic for T03. Review only the supplied T03 perimeter/gate/lane appearance across environmental conditions. Day, dusk, night, dawn and blizzard intentionally change illumination; that is NOT style drift by itself. Judge whether the same authored fence/gate/lane material identities and geometry remain coherent and artifact-free across views. Foreign stations/buildings/lamps/characters are outside T03. cross_view_consistency must be strictly >9.0 with zero actionable T03 defects. If no actionable defect exists, defects MUST be []. Return JSON only."""
elif CRITIC=="C1":
    rubric="""You are the independent Havenline C1 Reference Fidelity Critic. Review exact pixels for ONE T03-owned domain only. The reference pixels are actual locked user-video frames. T03 owns only snow-capped palisade fences, framed timber gate leaves/threshold posts, and compacted work-lane treatment. Trees and T02 ground/snow/water are accepted baselines; stations, pads, machinery, shelters, lamps, characters and later-task props are foreign-owned and MUST NOT be scored.
The Reference Style Lock is strict: reference_fidelity=10.0 exactly and visual_language=10.0 exactly are required; cross_view_consistency must be >9.0. Do not invent a defect simply because the candidate is not a literal copy of the reference scene layout. Judge the locked visual grammar: bright polished stylized 3D, clean sculpted readable forms, pale warm salmon/brown timber, crisp white snow frosting, purposeful solid framed/X-braced timber gates, coherent contact shadows, and compacted/worn routes that remain part of the accepted terrain surface. An opened gate may appear trapezoidal from perspective; do not call its clearly visible solid face/frame/bracing missing. T03 snow lanes should be low-contrast packed wear, not black asphalt. If there is no actionable T03 defect, defects MUST be [] and scores must use the strict passing values. Return JSON only."""
else:
    rubric="""You are the independent Havenline C2 Technical / Visual Integrity Critic. Review exact pixels for ONE T03-owned domain only. T03 owns palisade fences, framed open gate leaves/threshold posts, and compacted work lanes. Ignore foreign stations, pads, machinery, buildings, lamps, characters and props.
Every mandatory dimension must be strictly >9.0 unrounded; exactly 9.0 fails. Do not invent defects outside the named group. Continuous-fence boards intentionally exclude gate openings; gate openings are reviewed separately. For lane groups, the lane is intentionally the same terrain material with visible compaction/ruts, never a separate mesh. For opened gates, perspective foreshortening is expected; evaluate actual grounding, seams, framed-face presence, intentional gaps and continuity. If no actionable T03 defect exists, defects MUST be []. Return JSON only."""
prompt=rubric+"\nGROUP-SPECIFIC SCOPE: "+NOTES[GROUP]+" Review every candidate panel in the board."

bp=board()
im=Image.open(bp).convert("RGB");im.thumbnail((1664,1664),Image.Resampling.LANCZOS)
buf=io.BytesIO();im.save(buf,format="JPEG",quality=94)
request={
 "model":"havenline-t03-iter9-"+CRITIC.lower(),
 "messages":[{"role":"user","content":[
  {"type":"image_url","image_url":{"url":"data:image/jpeg;base64,"+base64.b64encode(buf.getvalue()).decode()}},
  {"type":"text","text":prompt}
 ]}],
 "max_tokens":750,"temperature":0.12,"top_p":0.9,
 "seed":20260923+(0 if CRITIC=="C1" else 100),
 "repeat_penalty":1.12,
 "chat_template_kwargs":{"enable_thinking":False},
 "response_format":{"type":"json_object","schema":schema},
 "cache_prompt":False
}
(OUT/"request-provenance.json").write_text(json.dumps({
 "candidate":CANDIDATE,"critic":CRITIC,"group":GROUP,"board_sha256":digest(bp),
 "reference_files":[{"path":str(p.relative_to(ROOT)),"sha256":digest(p)} for p in REFS] if GROUP!="conditions" else [],
 "candidate_files":[{"path":x,"sha256":ev["image_hashes"][x]} for x in GROUPS[GROUP]],
 "prompt":prompt,"schema":schema
},indent=2)+"\n")

env=dict(os.environ);env["LD_LIBRARY_PATH"]=str(server.parent)+":"+env.get("LD_LIBRARY_PATH","")
log=(OUT/"runtime.log").open("w")
cmd=[str(server),"-m",str(cache/m["model_file"]),"--mmproj",str(cache/m["projector_file"]),"--host","127.0.0.1","--port","8080","-c","12288","-t","4","-tb","4","-ngl","0","--no-mmproj-offload","--parallel","1","--jinja","--image-min-tokens","1024","--image-max-tokens","2560"]
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
if CRITIC=="C1" and GROUP=="conditions":
    score_pass=valid and scores.get("cross_view_consistency",0)>9.0
elif CRITIC=="C1":
    score_pass=valid and scores.get("reference_fidelity")==10.0 and scores.get("visual_language")==10.0 and scores.get("cross_view_consistency",0)>9.0
else:
    score_pass=valid and all(v>9.0 for v in scores.values())
passed=fatal is None and score_pass and defects==[] and review.get("coverage_complete") is True and review.get("confidence") in ("medium","high")
record={"task_id":"T03","critic_id":CRITIC,"candidate_hash":CANDIDATE,"group":GROUP,"provider":m["publisher"],"model":m["base_model"],"model_revision":m["revision"],"request_or_run_id":os.environ.get("GITHUB_RUN_ID","local")+"/"+os.environ.get("GITHUB_JOB","review"),"scores":scores,"defects":defects,"coverage_complete":review.get("coverage_complete",False),"confidence":review.get("confidence","low"),"independent_runtime":True,"reference_pixels_reviewed":GROUP!="conditions","foreign_domain_exclusion_explicit":True,"fatal_error":fatal,"passed":passed,"review":review}
(OUT/"critic-record.json").write_text(json.dumps(record,indent=2)+"\n")
print(json.dumps(record,indent=2))
raise SystemExit(0 if passed else 1)
