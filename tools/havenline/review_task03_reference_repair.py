#!/usr/bin/env python3
from __future__ import annotations
import base64,hashlib,io,json,math,os,pathlib,subprocess,time,urllib.request
from PIL import Image,ImageDraw

ROOT=pathlib.Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/os.environ.get("EVIDENCE_ROOT","t03-repair")
OUT=ROOT/os.environ.get("REVIEW_OUT","t03-reference-repair-review")
SOURCE=os.environ["EXPECTED_SOURCE"]
CRITIC=os.environ["REVIEW_CRITIC"].upper()
REVIEW_GROUP=os.environ.get("REVIEW_GROUP","").strip()
assert CRITIC in {"C1","C2","C6"} and len(SOURCE)==40
OUT.mkdir(parents=True,exist_ok=True)

def digest(path):
    h=hashlib.sha256()
    with pathlib.Path(path).open("rb") as f:
        for block in iter(lambda:f.read(4*1024*1024),b""):h.update(block)
    return h.hexdigest()

evidence=json.loads((EVIDENCE/"evidence.json").read_text())
assert evidence["candidate_sha"]==SOURCE
assert evidence["machine_gate_passed"] is True
assert evidence["primitive_audit"]["passed"] is True and evidence["primitive_audit"]["finding_count"]==0
assert evidence["tests"]["all_passed"] is True and evidence["tests"]["suite_count"]==16
for name,sha in evidence["image_hashes"].items():
    p=EVIDENCE/name
    assert p.is_file() and digest(p)==sha,(name,"evidence hash mismatch")

cache=pathlib.Path(os.path.expanduser("~/.cache/havenline-t01-qwen35"))
runtime=json.loads((ROOT/"Docs/Production/CRITIC_EXECUTION.json").read_text())["local_independent_runtime"]
manifest=json.loads((cache/"manifest.json").read_text())
assert manifest["publisher"]==runtime["provider"]
assert manifest["base_model"]==runtime["base_model"]
assert manifest["revision"]==runtime["model_revision"]
for item in manifest["files"]:
    assert digest(cache/item["filename"])==item["sha256"],item["filename"]
servers=list((cache/"runtime").rglob("llama-server"));assert len(servers)==1
server=servers[0]

REFS=[
    ROOT/"Docs/Production/T05/ReferenceFrames/B-008.00.png",
    ROOT/"Docs/Production/T05/ReferenceFrames/B-028.00.png",
    ROOT/"Docs/Production/T05/ReferenceFrames/B-048.00.png",
]
for p in REFS: assert p.is_file()
ref_hashes={str(p.relative_to(ROOT)):digest(p) for p in REFS}

GROUPS={
 "boundary_portals":[
   "gallery/perimeter-oblique.png","gallery/north-gate-front.png",
   "gallery/west-work-gate.png","gallery/east-work-gate.png",
   "gallery/river-gate-centre.png","gallery/open-gate-leaves-detail.png",
   "native4k/native-perimeter.png","native4k/native-north-gate.png"
 ],
 "routes_contacts":[
   "gallery/fence-panel-detail.png","gallery/gate-post-detail.png",
   "gallery/central-spine-north.png","gallery/central-spine-river.png",
   "gallery/cross-lane-centre.png","gallery/bank-lane-centre.png",
   "gallery/gameplay-river-gate-centre.png","native4k/native-lane-network.png"
 ],
 "iteration11_changed_domains":[
   "gallery/west-work-gate.png","gallery/river-gate-west.png",
   "gallery/river-gate-west-approach.png","gallery/river-gate-west-camp-side.png",
   "gallery/bank-lane-west.png","gallery/bank-lane-centre.png",
   "gallery/bank-lane-east.png","native4k/native-river-gate-west.png"
 ]
}

def make_board(group,paths):
    ref_tiles=[]
    for p in REFS:
        im=Image.open(p).convert("RGB");im.thumbnail((420,520),Image.Resampling.LANCZOS)
        ref_tiles.append((p.name,im))
    cand=[]
    for name in paths:
        im=Image.open(EVIDENCE/name).convert("RGB");im.thumbnail((500,285),Image.Resampling.LANCZOS)
        cand.append((name,im))
    w=1600;ref_h=570;cols=3;rows=(len(cand)+cols-1)//cols;h=ref_h+70+rows*335
    board=Image.new("RGB",(w,h),(18,29,40));d=ImageDraw.Draw(board)
    d.text((15,10),"AUTHORITATIVE REFERENCE B — T03 fence/gate/work-area language",fill="white")
    for i,(name,im) in enumerate(ref_tiles):
        cell=530;x=i*cell+(cell-im.width)//2;y=38
        board.paste(im,(x,y));d.text((i*cell+8,548),name,fill="white")
    y0=ref_h+35;d.text((15,y0-25),"EXACT-SOURCE T03 CANDIDATE — "+group,fill="white")
    for i,(name,im) in enumerate(cand):
        c=i%cols;r=i//cols;cell=530;x=c*cell+(cell-im.width)//2;y=y0+r*335+28
        d.text((c*cell+8,y0+r*335+5),name[:78],fill="white");board.paste(im,(x,y))
    path=OUT/(group+"-board.jpg");board.save(path,quality=94);return path

def response_schema(dimensions):
    return {
      "type":"object","properties":{
        "observations":{"type":"array","items":{"type":"string","maxLength":180},"minItems":2,"maxItems":4},
        "defects":{"type":"array","items":{"type":"string","maxLength":180},"maxItems":4},
        "coverage_complete":{"type":"boolean"},
        "confidence":{"type":"string","enum":["low","medium","high"]},
        "scores":{"type":"object","properties":{d:{"type":"number","minimum":0,"maximum":10} for d in dimensions},"required":dimensions,"additionalProperties":False}
      },
      "required":["observations","defects","coverage_complete","confidence","scores"],"additionalProperties":False
    }

def request(board,prompt,schema,label,max_tokens=750):
    content=[]
    if board:
        im=Image.open(board).convert("RGB");im.thumbnail((1664,1664),Image.Resampling.LANCZOS)
        b=io.BytesIO();im.save(b,format="JPEG",quality=93)
        content.append({"type":"image_url","image_url":{"url":"data:image/jpeg;base64,"+base64.b64encode(b.getvalue()).decode()}})
    content.append({"type":"text","text":prompt})
    body={"model":"havenline-t03-"+CRITIC,"messages":[{"role":"user","content":content}],"max_tokens":max_tokens,"temperature":0.15,"top_p":0.9,"seed":20260922+(1 if CRITIC=="C1" else 2 if CRITIC=="C2" else 6),"repeat_penalty":1.12,"chat_template_kwargs":{"enable_thinking":False},"response_format":{"type":"json_object","schema":schema},"cache_prompt":False}
    (OUT/(label+"-request.json")).write_text(json.dumps(body,indent=2))
    req=urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",data=json.dumps(body).encode(),headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=1500) as resp:raw=json.load(resp)
    (OUT/(label+"-raw.json")).write_text(json.dumps(raw,indent=2))
    choice=raw["choices"][0]
    if choice.get("finish_reason")!="stop": raise RuntimeError("incomplete reviewer response")
    parsed=json.loads(choice["message"]["content"])
    (OUT/(label+"-review.json")).write_text(json.dumps(parsed,indent=2))
    return parsed

env=dict(os.environ);env["LD_LIBRARY_PATH"]=str(server.parent)+":"+env.get("LD_LIBRARY_PATH","")
cmd=[str(server),"-m",str(cache/manifest["model_file"]),"--mmproj",str(cache/manifest["projector_file"]),"--host","127.0.0.1","--port","8080","-c","12288","-t","4","-tb","4","-ngl","0","--no-mmproj-offload","--parallel","1","--jinja","--image-min-tokens","768","--image-max-tokens","2048"]
log=(OUT/"runtime.log").open("w")
proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
try:
    for _ in range(180):
        if proc.poll() is not None: raise RuntimeError("review runtime exited")
        try:
            if json.load(urllib.request.urlopen("http://127.0.0.1:8080/health",timeout=3)).get("status")=="ok":break
        except Exception:pass
        time.sleep(2)
    else: raise RuntimeError("review runtime not ready")

    if CRITIC in {"C1","C2"}:
        dims=["reference_fidelity","visual_language","cross_view_consistency"] if CRITIC=="C1" else ["geometry_contact","clipping_seams","intentional_gap_integrity","cross_view_integrity"]
        role="Reference Fidelity Critic" if CRITIC=="C1" else "Technical / Visual Integrity Critic"
        checks="Match the supplied reference fence/gate/work-area language and judge cross-view consistency." if CRITIC=="C1" else "Judge grounding, seams, clipping, intentional gate gaps, leaf/post contact, route continuity and cross-view integrity."
        base=f"""You are Havenline's independent {role}. Review exact candidate {SOURCE}. Scope is ONLY T03 fences, gates, threshold posts and the narrower packed/worn route strips that connect gates and the work area. T02 terrain, snow, water, river/riverbank/shoreline, and the large orange camp work-floor are user-accepted context and MUST NOT lower T03 scores or be reported as T03 defects. T04+ buildings, stations, characters and later systems visible in context are NOT scored here. The circular blue furnace/workstation visible behind the reference gate is contextual T04+ equipment, not a T03 gate component; do not require it as part of gate fidelity. T03 packed/worn lanes are the narrower visibly depressed/worn route strips, not the entire orange work-floor. The top reference frames are authoritative gameplay references for the T03 art language. {checks}
The repair standard is unusually strict: every mandatory visual dimension must be 10.0 for this repaired visual approval. Do not average. A score below 10.0 requires a concrete actionable T03-owned defect in defects. Every sub-10 defect MUST cite the exact candidate filename printed on the board and a visible T03-owned location in that panel. If there is no actionable T03 defect, defects must be [] exactly. Do not invent defects from T02 context or downstream T04+ content. coverage_complete means you inspected every candidate panel in the evidence group; it must remain true when every panel was inspected even if you found a defect. Return JSON only."""
        if REVIEW_GROUP:
            assert REVIEW_GROUP in GROUPS,("unknown review group",REVIEW_GROUP)
            selected_groups={REVIEW_GROUP:GROUPS[REVIEW_GROUP]}
        else:
            selected_groups=GROUPS
        rows=[]
        for gid,paths in selected_groups.items():
            board=make_board(gid,paths)
            review=request(board,base+"\nEvidence group: "+gid+". Inspect every candidate panel and the reference row.",response_schema(dims),gid)
            scores=review.get("scores",{})
            errors=[]
            if set(scores)!=set(dims):errors.append("dimension mismatch")
            if any(type(v) not in (int,float) or isinstance(v,bool) or not math.isfinite(v) or v!=10.0 for v in scores.values()):errors.append("visual score below exact 10")
            if review.get("defects")!=[]:errors.append("unresolved defects")
            if review.get("coverage_complete") is not True:errors.append("coverage incomplete")
            if review.get("confidence") not in ("medium","high"):errors.append("confidence insufficient")
            rows.append({"group":gid,"review":review,"passed":not errors,"errors":errors})
        score_min={d:min(row["review"]["scores"].get(d,0) for row in rows) for d in dims}
        defects=[f"{row['group']}: {x}" for row in rows for x in row["review"].get("defects",[])]
        passed=len(rows)==len(selected_groups) and all(row["passed"] for row in rows)
        raw={"critic_id":CRITIC,"candidate":SOURCE,"groups":rows,"reference_hashes":ref_hashes}
        raw_path=OUT/"raw-output.json";raw_path.write_text(json.dumps(raw,indent=2)+"\n")
        record={"task_id":"T03","critic_id":CRITIC,"review_group":REVIEW_GROUP or "all","provider":manifest["publisher"],"model":manifest["base_model"],"model_revision":manifest["revision"],"request_or_run_id":os.environ.get("GITHUB_RUN_ID","local")+"/"+os.environ.get("GITHUB_JOB","critic"),"candidate_hash":SOURCE,"input_manifest_hash":hashlib.sha256(json.dumps({"evidence":evidence["image_hashes"],"references":ref_hashes},sort_keys=True).encode()).hexdigest(),"raw_output_path":str(raw_path.relative_to(ROOT)),"raw_output_hash":digest(raw_path),"scores":score_min,"defects":defects,"coverage_complete":all(r["review"].get("coverage_complete") is True for r in rows),"confidence":"high" if all(r["review"].get("confidence")=="high" for r in rows) else "medium","independent_runtime":True,"groups":rows,"passed":passed,"visual_exact_10_required":True}
    else:
        capture=json.loads((EVIDENCE/"gallery/capture.json").read_text())
        native=json.loads((EVIDENCE/"native4k/capture.json").read_text())
        frames=capture["captures"]+native["captures"]
        b=capture["boundary"]
        candidate_manifest=json.loads(subprocess.check_output(["git","show",SOURCE+":HavenlineGodot/assets/t03_boundary_v2/manifest.json"],cwd=ROOT,text=True))
        fence_tri=next(x["triangles"] for x in candidate_manifest["assets"] if x["name"]=="fence_panel")
        gate_tri=next(x["triangles"] for x in candidate_manifest["assets"] if x["name"]=="gate_leaf")
        post_tri=next(x["triangles"] for x in candidate_manifest["assets"] if x["name"]=="gate_post")
        incremental_tri=(fence_tri*int(b["fence_visual_instances"])+gate_tri*int(b["open_gate_leaf_instances"])+post_tri*int(b["gate_post_instances"]))
        metrics={"candidate_commit":SOURCE,"capture_frames":len(frames),"native_4k_frames":evidence["native_4k_stills"],"scene_draw_calls_max":max(int(x["draw_calls"]) for x in frames),"scene_submitted_primitives_max":max(int(x["submitted_primitives"]) for x in frames),"t03_draw_batches":int(b["draw_batches"]),"collision_panels":int(b["collision_panel_instances"]),"fence_visual_instances":int(b["fence_visual_instances"]),"gate_post_instances":int(b["gate_post_instances"]),"open_gate_leaf_instances":int(b["open_gate_leaf_instances"]),"fence_mesh_triangles":fence_tri,"gate_leaf_mesh_triangles":gate_tri,"gate_post_mesh_triangles":post_tri,"t03_incremental_visual_triangles":incremental_tri,"new_textures":0,"new_animations":0,"new_npcs":0,"new_active_physics_bodies":0,"primitive_findings":evidence["primitive_audit"]["finding_count"],"render_scale":1.0,"physical_device_certification":False}
        dims=["frame_time","draw_calls","geometry","texture_memory","shader_cost","physics","animation","population","thermal_risk"]
        prompt=f"""You are Havenline's quantitative C6 Performance Critic for exact candidate {SOURCE}. This is an intermediate subsystem budget review, not T68/T69 physical-device certification. Judge only the incremental T03 fence/gate/lane repair from the exact metrics below. T03 uses {metrics["t03_draw_batches"]} batched visual submissions, adds no textures, animations, NPCs or active physics bodies, and its route/collision topology is unchanged. Whole-scene draw/primitives are context; do not misattribute all of them to T03. Every dimension must be strictly above 9.0 unrounded to pass. If any score is <=9.0, defects must identify a concrete metric-supported T03 issue. Return JSON only.\nMETRICS:\n"""+json.dumps(metrics,sort_keys=True,indent=2)
        review=request(None,prompt,response_schema(dims),"C6",650)
        scores=review.get("scores",{})
        errors=[]
        if set(scores)!=set(dims):errors.append("dimension mismatch")
        if any(type(v) not in (int,float) or isinstance(v,bool) or not math.isfinite(v) or v<=9.0 for v in scores.values()):errors.append("score <=9")
        if review.get("defects")!=[]:errors.append("unresolved defects")
        if review.get("coverage_complete") is not True:errors.append("coverage incomplete")
        if review.get("confidence") not in ("medium","high"):errors.append("confidence insufficient")
        raw={"critic_id":"C6","candidate":SOURCE,"metrics":metrics,"review":review}
        raw_path=OUT/"raw-output.json";raw_path.write_text(json.dumps(raw,indent=2)+"\n")
        record={"task_id":"T03","critic_id":"C6","provider":manifest["publisher"],"model":manifest["base_model"],"model_revision":manifest["revision"],"request_or_run_id":os.environ.get("GITHUB_RUN_ID","local")+"/"+os.environ.get("GITHUB_JOB","C6"),"candidate_hash":SOURCE,"input_manifest_hash":hashlib.sha256(json.dumps(metrics,sort_keys=True).encode()).hexdigest(),"raw_output_path":str(raw_path.relative_to(ROOT)),"raw_output_hash":digest(raw_path),"scores":scores,"defects":review.get("defects",[]),"coverage_complete":review.get("coverage_complete") is True,"confidence":review.get("confidence","low"),"independent_runtime":True,"metrics":metrics,"passed":not errors,"physical_device_certification":False}
    (OUT/"critic-record.json").write_text(json.dumps(record,indent=2)+"\n")
    print(json.dumps(record,indent=2))
    raise SystemExit(0 if record["passed"] else 1)
finally:
    proc.terminate()
    try:proc.wait(timeout=10)
    except Exception:proc.kill()
    log.close()
