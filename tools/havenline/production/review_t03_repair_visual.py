#!/usr/bin/env python3
from __future__ import annotations
import base64, hashlib, io, json, math, os, pathlib, subprocess, time, urllib.request
from PIL import Image, ImageDraw

ROOT=pathlib.Path.cwd()
EVIDENCE=ROOT/os.environ.get("EVIDENCE_ROOT","task03-evidence")
OUT=ROOT/os.environ.get("OUT_DIR","task03-critic")
CANDIDATE=os.environ["EXPECTED_SOURCE"]
CRITIC=os.environ["CRITIC_ID"].upper()
assert CRITIC in {"C1","C2"}
OUT.mkdir(parents=True,exist_ok=True)

def sha(path:pathlib.Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(4*1024*1024),b""): h.update(block)
    return h.hexdigest()

ev=json.loads((EVIDENCE/"evidence.json").read_text())
assert ev["candidate_sha"]==CANDIDATE
assert ev["machine_gate_passed"] is True
assert ev["primitive_audit"]["passed"] is True and ev["primitive_audit"]["finding_count"]==0
assert ev["tests"]["all_passed"] is True and ev["tests"]["suite_count"]==16
assert ev["gallery_stills"]==47 and ev["native_4k_stills"]==11 and ev["total_stills"]==58
for rel,digest in ev["image_hashes"].items():
    p=EVIDENCE/rel
    assert p.is_file() and sha(p)==digest,("candidate image mismatch",rel)

coverage=json.loads((ROOT/"Docs/Production/T05/ReferenceFrames/coverage.json").read_text())
reference_rows={pathlib.Path(x["path"]).name:x for x in coverage["items"]}
reference_names=["B-006.00.png","B-008.00.png","B-010.00.png","B-028.00.png","B-048.00.png"]
references=[]
for name in reference_names:
    p=ROOT/"Docs/Production/T05/ReferenceFrames"/name
    assert p.is_file()
    assert sha(p)==reference_rows[name]["sha256"],("reference hash mismatch",name)
    references.append(p)

GROUPS={
 "perimeter":[
   "gallery/perimeter-topdown.png","gallery/perimeter-oblique.png",
   "gallery/camp-lanes-overhead.png","gallery/camp-lanes-oblique.png",
   "native4k/native-perimeter.png","native4k/native-camp-oblique.png"
 ],
 "north-side-gates":[
   "gallery/north-gate-front.png","gallery/north-gate-rear.png",
   "gallery/west-work-gate.png","gallery/east-work-gate.png",
   "gallery/gameplay-north-gate.png","gallery/gameplay-west-gate.png","gallery/gameplay-east-gate.png",
   "native4k/native-north-gate.png","native4k/native-side-gate-west.png","native4k/native-side-gate-east.png"
 ],
 "river-gates":[
   "gallery/river-gate-west-approach.png","gallery/river-gate-west.png","gallery/river-gate-west-camp-side.png","gallery/gameplay-river-gate-west.png",
   "gallery/river-gate-centre-approach.png","gallery/river-gate-centre.png","gallery/river-gate-centre-camp-side.png","gallery/gameplay-river-gate-centre.png",
   "gallery/river-gate-east-approach.png","gallery/river-gate-east.png","gallery/river-gate-east-camp-side.png","gallery/gameplay-river-gate-east.png",
   "native4k/native-river-gate-west.png","native4k/native-river-gate-centre.png","native4k/native-river-gate-east.png"
 ],
 "lanes":[
   "gallery/central-spine-north.png","gallery/central-spine-centre.png","gallery/central-spine-river.png",
   "gallery/cross-lane-west.png","gallery/cross-lane-centre.png","gallery/cross-lane-east.png",
   "gallery/shelter-branch-west.png","gallery/shelter-branch-east.png",
   "gallery/bank-lane-west.png","gallery/bank-lane-centre.png","gallery/bank-lane-east.png",
   "gallery/reserved-crossings-overhead.png","native4k/native-lane-network.png"
 ],
 "detail-contact":[
   "gallery/fence-panel-detail.png","gallery/gate-post-detail.png","gallery/open-gate-leaves-detail.png",
   "gallery/south-fence-west.png","gallery/south-fence-centre.png","gallery/south-fence-east.png",
   "native4k/native-fence-detail.png","native4k/native-south-fence.png"
 ],
 "conditions":[
   "gallery/boundary-condition-day.png","gallery/boundary-condition-dusk.png","gallery/boundary-condition-night.png",
   "gallery/boundary-condition-dawn.png","gallery/boundary-condition-blizzard-night.png","gallery/boundary-condition-day-return.png"
 ]
}
NOTES={
 "perimeter":"Judge the T03 palisade perimeter, six gate openings and used-lane composition at whole-camp scale.",
 "north-side-gates":"Judge the north-main and west/east work gates: framed open leaves, threshold posts, grounding and readable passage.",
 "river-gates":"Judge all three river-facing future-crossing gates across approach, three-quarter, camp-side, gameplay and native-4K views. No bridge is required.",
 "lanes":"Judge the compacted T03 lane network as wear/compression in the same accepted T02 surface, never a floating path or broad repaint.",
 "detail-contact":"Judge T03 fence snow crowns, palisade finish, framed X-braced gate leaves, posts, joins and ground contact.",
 "conditions":"Judge T03 material/geometry stability through day, dusk, night, dawn and blizzard without demanding later-task content."
}

execution=json.loads((ROOT/"Docs/Production/CRITIC_EXECUTION.json").read_text())
matrix=json.loads((ROOT/"Docs/Production/CRITIC_MATRIX.json").read_text())
runtime=execution["local_independent_runtime"]
cache=pathlib.Path(os.path.expanduser(runtime["cache_path"]))
m=json.loads((cache/"manifest.json").read_text())
assert m["publisher"]==runtime["provider"] and m["base_model"]==runtime["base_model"]
assert m["revision"]==runtime["model_revision"]
assert m.get("runtime_release")=="b10809"
for item in m["files"]:
    assert sha(cache/item["filename"])==item["sha256"]
servers=list((cache/"runtime").rglob("llama-server"))
assert len(servers)==1
server=servers[0]

DIMS={
 "C1":["reference_fidelity","visual_language","cross_view_consistency"],
 "C2":["geometry_contact","clipping_seams","intentional_gap_integrity","cross_view_integrity"]
}[CRITIC]
schema={
 "type":"object",
 "properties":{
   "observations":{"type":"array","items":{"type":"string","maxLength":220},"minItems":2,"maxItems":4},
   "defects":{"type":"array","items":{"type":"string","maxLength":220},"maxItems":4},
   "coverage_complete":{"type":"boolean"},
   "confidence":{"type":"string","enum":["low","medium","high"]},
   "scores":{"type":"object","properties":{k:{"type":"number","minimum":0,"maximum":10} for k in DIMS},"required":DIMS,"additionalProperties":False}
 },
 "required":["observations","defects","coverage_complete","confidence","scores"],
 "additionalProperties":False
}

c1_prompt="""You are Havenline C1 Reference Fidelity Critic in a genuinely separate CI reviewer runtime. Review only Task T03's changed visual domain: palisade fences, framed gate leaves, threshold posts and compacted work lanes. Actual locked user-reference pixels are displayed at the top of every board. Later-task stations/buildings/props may appear in context; do not charge those foreign-owned classes against T03, but never excuse a visible T03 defect because later tasks remain pending.
The global Reference Style Lock is strict: T03 reference_fidelity and visual_language each require EXACTLY 10.0/10.0 unrounded with zero style defects and complete coverage. 9.9 fails. The style target is bright polished stylized 3D, clean sculpted readable forms, blue-white winter masses, warm salmon/brown work-zone timber, crisp white snow frosting, deliberate soft/contact shadows and framed warm timber gate panels consistent with the supplied reference pixels. The reference gates show solid framed timber panels with diagonal bracing; the fence family is a dense pointed palisade with snow caps. T03 lanes should preserve the accepted T02 snow/work-floor language and read as compacted/worn use, not a new dark road material.
Score reference_fidelity, visual_language and cross_view_consistency. Any score below the required pass rule must identify an actionable T03-specific defect. If no actionable T03 defect exists, defects MUST be []. Return JSON only."""
c2_prompt="""You are Havenline C2 Technical / Visual Integrity Critic in a genuinely separate CI reviewer runtime. Review only Task T03 fences, framed open gate leaves, threshold posts and compacted lanes. Judge actual source-bound pixels for grounding, joins, clipping, seams, consistent snow caps, framed-leaf integrity, intentional gate gaps, clear thresholds and cross-view consistency. The six openings are intentional: north-main, west/east work and three river-facing future crossings. No bridge is required in T03. Do not invent defects from objects outside T03 ownership.
Every mandatory C2 dimension must be strictly greater than 9.0 unrounded; exactly 9.0 fails. No average can hide a weak dimension. Any score <=9.0 must cite an actionable visible T03 defect. If no actionable defect exists, defects MUST be []. Return JSON only."""
BASE_PROMPT=c1_prompt if CRITIC=="C1" else c2_prompt

def board(group:str)->pathlib.Path:
    refs=[]
    for p in references:
        im=Image.open(p).convert("RGB")
        im.thumbnail((400,300),Image.Resampling.LANCZOS)
        refs.append((p.name,im))
    candidates=[]
    for rel in GROUPS[group]:
        im=Image.open(EVIDENCE/rel).convert("RGB")
        im.thumbnail((430,260),Image.Resampling.LANCZOS)
        candidates.append((rel,im))
    cols=3
    ref_rows=(len(refs)+cols-1)//cols
    cand_rows=(len(candidates)+cols-1)//cols
    w=1380
    ref_h=ref_rows*330
    cand_y=55+ref_h+35
    h=cand_y+cand_rows*305+20
    canvas=Image.new("RGB",(w,h),(19,29,40))
    draw=ImageDraw.Draw(canvas)
    draw.text((12,10),"LOCKED USER REFERENCE PIXELS — authoritative A/B source frames",fill="white")
    for i,(name,im) in enumerate(refs):
        c=i%cols;r=i//cols;x=c*460+(460-im.width)//2;y=40+r*330+28
        draw.text((c*460+8,40+r*330+5),name,fill="white")
        canvas.paste(im,(x,y))
    draw.text((12,cand_y-28),f"T03 EXACT CANDIDATE {CANDIDATE[:12]} — {group}",fill="white")
    for i,(name,im) in enumerate(candidates):
        c=i%cols;r=i//cols;x=c*460+(460-im.width)//2;y=cand_y+r*305+28
        draw.text((c*460+8,cand_y+r*305+4),name[:72],fill="white")
        canvas.paste(im,(x,y))
    path=OUT/(group+"-board.jpg")
    canvas.save(path,quality=92)
    return path

manifest={
 "schema_version":1,"task_id":"T03","critic_id":CRITIC,"candidate_commit":CANDIDATE,
 "references":[{"path":str(p.relative_to(ROOT)),"sha256":sha(p)} for p in references],
 "groups":[{"id":g,"note":NOTES[g],"items":[{"path":r,"sha256":ev["image_hashes"][r]} for r in GROUPS[g]]} for g in GROUPS]
}
manifest_path=OUT/"input-manifest.json"
manifest_path.write_text(json.dumps(manifest,indent=2)+"\n")

env=dict(os.environ)
env["LD_LIBRARY_PATH"]=str(server.parent)+":"+env.get("LD_LIBRARY_PATH","")
log=(OUT/"runtime.log").open("w")
cmd=[str(server),"-m",str(cache/m["model_file"]),"--mmproj",str(cache/m["projector_file"]),"--host","127.0.0.1","--port","8080","-c","12288","-t","4","-tb","4","-ngl","0","--no-mmproj-offload","--parallel","1","--jinja","--image-min-tokens","768","--image-max-tokens","2048"]
proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
rows=[];fatal=None
try:
    for _ in range(180):
        if proc.poll() is not None: raise RuntimeError("reviewer runtime exited")
        try:
            if json.load(urllib.request.urlopen("http://127.0.0.1:8080/health",timeout=3)).get("status")=="ok": break
        except Exception: pass
        time.sleep(2)
    else: raise RuntimeError("reviewer runtime not ready")
    for group in GROUPS:
        bp=board(group)
        im=Image.open(bp).convert("RGB")
        im.thumbnail((1664,1664),Image.Resampling.LANCZOS)
        buf=io.BytesIO();im.save(buf,format="JPEG",quality=92)
        prompt=BASE_PROMPT+"\nEvidence group: "+group+". "+NOTES[group]+" Review every labelled candidate panel and the displayed reference pixels."
        body={
          "model":"havenline-t03-"+CRITIC.lower(),
          "messages":[{"role":"user","content":[
             {"type":"image_url","image_url":{"url":"data:image/jpeg;base64,"+base64.b64encode(buf.getvalue()).decode()}},
             {"type":"text","text":prompt}
          ]}],
          "max_tokens":800,"temperature":0.2,"top_p":0.9,
          "seed":20260923+(1 if CRITIC=="C1" else 101),
          "repeat_penalty":1.12,
          "chat_template_kwargs":{"enable_thinking":False},
          "response_format":{"type":"json_object","schema":schema},
          "cache_prompt":False
        }
        req_path=OUT/(group+"-request.json")
        req_path.write_text(json.dumps({"prompt":prompt,"board_sha256":sha(bp),"schema":schema},indent=2))
        req=urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",data=json.dumps(body).encode(),headers={"Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(req,timeout=1800) as resp: raw=json.load(resp)
        (OUT/(group+"-raw.json")).write_text(json.dumps(raw,indent=2))
        choice=raw["choices"][0]
        if choice.get("finish_reason")!="stop": raise RuntimeError("incomplete response "+group)
        review=json.loads(choice["message"]["content"])
        scores=review["scores"]
        if set(scores)!=set(DIMS): raise RuntimeError("dimension mismatch "+group)
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in scores.values()): raise RuntimeError("invalid score "+group)
        if CRITIC=="C1":
            passed=(scores["reference_fidelity"]==10.0 and scores["visual_language"]==10.0 and scores["cross_view_consistency"]>9.0)
        else:
            passed=all(v>9.0 for v in scores.values())
        passed=passed and review["defects"]==[] and review["coverage_complete"] is True and review["confidence"] in ("medium","high")
        rows.append({"group":group,"review":review,"passed":passed})
except Exception as exc:
    fatal=type(exc).__name__+": "+str(exc)
finally:
    proc.terminate()
    try: proc.wait(timeout=15)
    except Exception: proc.kill()
    log.close()

dim_scores={d:min((r["review"]["scores"][d] for r in rows if d in r.get("review",{}).get("scores",{})),default=0) for d in DIMS}
defects=[f'{r["group"]}: {d}' for r in rows for d in r.get("review",{}).get("defects",[])]
confidence_order={"low":0,"medium":1,"high":2}
confidence=min((r.get("review",{}).get("confidence","low") for r in rows),key=lambda x:confidence_order.get(x,0),default="low")
raw_output={"task_id":"T03","critic_id":CRITIC,"candidate":CANDIDATE,"groups":rows,"fatal_error":fatal}
raw_path=OUT/"raw-output.json"
raw_path.write_text(json.dumps(raw_output,indent=2)+"\n")
passed=fatal is None and len(rows)==len(GROUPS) and all(r["passed"] for r in rows)
record={
 "task_id":"T03","critic_id":CRITIC,"provider":m["publisher"],"model":m["base_model"],
 "model_revision":m["revision"],"request_or_run_id":os.environ.get("GITHUB_RUN_ID","local")+"/"+os.environ.get("GITHUB_JOB","review"),
 "candidate_hash":CANDIDATE,"input_manifest_hash":sha(manifest_path),
 "raw_output_path":str(raw_path.relative_to(ROOT)),"raw_output_hash":sha(raw_path),
 "scores":dim_scores,"defects":defects,
 "coverage_complete":fatal is None and len(rows)==len(GROUPS) and all(r.get("review",{}).get("coverage_complete") is True for r in rows),
 "confidence":confidence,"independent_runtime":True,"groups":rows,"fatal_error":fatal,"passed":passed,
 "reference_pixels_reviewed":True,"reference_style_lock_exact_10_enforced":CRITIC=="C1"
}
(OUT/"critic-record.json").write_text(json.dumps(record,indent=2)+"\n")
print(json.dumps(record,indent=2))
raise SystemExit(0 if passed else 1)
