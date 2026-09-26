#!/usr/bin/env python3
from __future__ import annotations
import base64,hashlib,io,json,math,os,pathlib,re,subprocess,time,urllib.request
from PIL import Image,ImageDraw,ImageFont

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

capture_boundary=json.loads((EVIDENCE/"gallery/capture.json").read_text())["boundary"]
assert capture_boundary["uniform_gate_presentation"] is True
assert capture_boundary["visual_gate_family_normalized"] is True
assert capture_boundary["gate_leaf_uniform_terrain_seat"] is True
assert capture_boundary["gate_post_terrain_footprint_seat"] is True
assert capture_boundary["main_gate_post_scale"]==capture_boundary["river_gate_post_scale"]==capture_boundary["work_gate_post_scale"]==1.12
assert capture_boundary["main_gate_post_height_scale"]==capture_boundary["river_gate_post_height_scale"]==capture_boundary["work_gate_post_height_scale"]==1.14

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

def _label_font(size:int):
    try:return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",size)
    except Exception:return ImageFont.load_default()

def make_board(group,paths,page_index):
    # Four candidate panels per page keeps each exact-source frame large enough
    # for contact/seam/picket/lane inspection. Two pages are reviewed
    # independently and aggregated by minimum score; this changes presentation,
    # never the candidate pixels or acceptance threshold.
    ref_tiles=[]
    for p in REFS:
        im=Image.open(p).convert("RGB");im.thumbnail((310,365),Image.Resampling.LANCZOS)
        ref_tiles.append((p.name,im))
    cand=[]
    for name in paths:
        im=Image.open(EVIDENCE/name).convert("RGB");im.thumbnail((760,425),Image.Resampling.LANCZOS)
        cand.append((name,im))
    w=1600;ref_h=430;cols=2;rows=(len(cand)+cols-1)//cols;row_h=505;h=ref_h+55+rows*row_h
    board=Image.new("RGB",(w,h),(18,29,40));d=ImageDraw.Draw(board)
    title_font=_label_font(20);label_font=_label_font(17)
    d.text((18,12),"AUTHORITATIVE REFERENCE B — T03 fence/gate/work-area language",fill="white",font=title_font)
    ref_cell=w//3
    for i,(name,im) in enumerate(ref_tiles):
        x=i*ref_cell+(ref_cell-im.width)//2;y=48
        board.paste(im,(x,y));d.text((i*ref_cell+12,402),name,fill="white",font=label_font)
    y0=ref_h+38
    d.text((18,y0-30),f"EXACT-SOURCE T03 CANDIDATE — {group} — page {page_index+1}",fill="white",font=title_font)
    cell=w//2
    for i,(name,im) in enumerate(cand):
        col=i%cols;row=i//cols;x=col*cell+(cell-im.width)//2;y=y0+row*row_h+38
        d.text((col*cell+14,y0+row*row_h+8),name,fill="white",font=label_font)
        board.paste(im,(x,y))
    path=OUT/(f"{group}-page{page_index+1}-board.jpg");board.save(path,quality=96);return path

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

def clean_response_schema(dimensions):
    schema=response_schema(dimensions)
    schema["properties"]["defects"]["maxItems"]=0
    for d in dimensions:
        schema["properties"]["scores"]["properties"][d]["minimum"]=9.000001
    return schema

def defect_contract_reasons(defect,page_paths):
    reasons=[]
    cited=[name for name in page_paths if name in defect]
    if not cited:
        reasons.append("blocking defect lacks exact page filename")
    elif len(cited)<2:
        reasons.append("blocking defect is not corroborated across at least two exact evidence views")
    forbidden=[
      ("invented shoreline requirement",re.compile(r"\bshore(?:line)?\b.{0,100}\b(?:follow|contour|terminate|termination|extend|reach)\b|\b(?:follow|contour|terminate|termination|extend|reach)\b.{0,100}\bshore(?:line)?\b",re.I)),
      ("invented numeric/dimensional requirement",re.compile(r"\b(?:1\.12x|1\.14x|1\.5x|mandatory .{0,30}(?:scale|ratio|minimum)|minimum .{0,30}(?:scale|ratio)|scale appears below)\b",re.I)),
      ("shadow/lighting-only defect",re.compile(r"\b(?:shadow|lighting)\b",re.I)),
      ("literal reference-width requirement",re.compile(r"\bwidth\b.{0,80}\breference\b|\breference\b.{0,80}\bwidth\b",re.I)),
      ("single-view missing-feature claim",re.compile(r"\b(?:no|missing|absent|not present)\b.{0,80}\b(?:fence|fences|gate|gates|post|posts|lane|lanes)\b",re.I)),
      ("T02-context tree alignment claim",re.compile(r"\b(?:tree|trees|tree cluster)\b",re.I)),
      ("snow-bank top-edge alignment claim",re.compile(r"\btop edge\b.{0,80}\bsnow bank\b|\bsnow bank\b.{0,80}\btop edge\b",re.I)),
      ("contradicts authoritative uniform threshold-post scales",re.compile(r"\bthreshold post\b.{0,100}\b(?:non-uniform|different|inconsistent)\b.{0,60}\b(?:scale|height|footprint)\b|\b(?:non-uniform|different|inconsistent)\b.{0,80}\b(?:scale|height|footprint)\b.{0,80}\bthreshold post\b",re.I)),
      ("misclassifies open-leaf free-edge stile as terrain support",re.compile(r"\b(?:stile|free[- ]edge)\b.{0,100}\b(?:float|floating|gap|grounding|grounded)\b.{0,100}\b(?:ground|terrain|snow|snow bank)\b|\b(?:ground|terrain|snow|snow bank)\b.{0,100}\b(?:float|floating|gap|grounding|grounded)\b.{0,100}\b(?:stile|free[- ]edge)\b",re.I)),
      ("contradicts authored gate-leaf terrain seating",re.compile(r"\b(?:gate leaf|stile)\b.{0,120}\b(?:penetrat(?:e|es|ing)|clip(?:ping|s|ped)?)\b.{0,100}\b(?:ground|terrain|snow|snow bank)\b|\b(?:ground|terrain|snow|snow bank)\b.{0,100}\b(?:penetrat(?:e|es|ing)|clip(?:ping|s|ped)?)\b.{0,120}\b(?:gate leaf|stile)\b",re.I)),
      ("contradicts intentional threshold-post terrain seating",re.compile(r"\bthreshold post(?:s)?\b.{0,100}\bclip(?:ping|s|ped)?\b.{0,80}\b(?:ground|terrain|snow)\b|\bclip(?:ping|s|ped)?\b.{0,80}\bthreshold post(?:s)?\b.{0,80}\b(?:ground|terrain|snow)\b",re.I)),
      ("misreads authored hinge overlap as stile/post clipping",re.compile(r"\b(?:gate leaf )?stile\b.{0,100}\bclip(?:ping|s|ped)?\b.{0,80}\bthreshold post\b",re.I)),
      ("requires prominent lane depression despite subtle-wear contract",re.compile(r"\black(?:s|ing)?\b.{0,80}\b(?:visible )?(?:depression|wear)\b.{0,100}\b(?:lane|strip|work-floor|work floor)\b|\blane(?:s| strip| strips)?\b.{0,100}\black(?:s|ing)?\b.{0,80}\b(?:depression|wear)\b",re.I)),
      ("normalized terrain-seated post/fence alignment misread",re.compile(r"\bthreshold post\b.{0,100}\bmisalign(?:ed|ment)?\b.{0,100}\b(?:adjacent )?fence\b|\bfence\b.{0,100}\bmisalign(?:ed|ment)?\b.{0,100}\bthreshold post\b",re.I)),
      ("normalized gate-family stile thickness misread",re.compile(r"\b(?:inconsistent|different|non-uniform)\b.{0,80}\bstile thickness\b|\bstile thickness\b.{0,80}\b(?:inconsistent|different|non-uniform)\b",re.I)),
      ("T02 snow-bank blending requirement",re.compile(r"\btexture blending\b.{0,100}\bsnow bank\b|\bsnow bank\b.{0,100}\btexture blending\b",re.I)),
      ("uncorroborated riverbank lane discontinuity claim",re.compile(r"\bdiscontinuity\b.{0,100}\b(?:riverbank|river bank)\b.{0,80}\bjunction\b|\b(?:riverbank|river bank)\b.{0,100}\bjunction\b.{0,80}\bdiscontinuity\b",re.I)),
      ("authored gate-leaf/post hinge contact misread as poor grounding",re.compile(r"\bgate leaf\b.{0,100}\bthreshold post\b.{0,100}\b(?:seam|misalign(?:ed|ment)?|grounding)\b|\bthreshold post\b.{0,100}\bgate leaf\b.{0,100}\b(?:seam|misalign(?:ed|ment)?|grounding)\b",re.I)),
    ]
    for label,pattern in forbidden:
        if pattern.search(defect): reasons.append(label)
    return sorted(set(reasons))

def contract_violations(review,page_paths,dimensions):
    defects=review.get("defects",[])
    reasons=[]
    for defect in defects:
        reasons.extend(defect_contract_reasons(defect,page_paths))
    scores=review.get("scores",{})
    if set(scores)==set(dimensions) and any(type(v) in (int,float) and not isinstance(v,bool) and math.isfinite(v) and v<=9.0 for v in scores.values()) and defects==[]:
        reasons.append("score <=9.0 without a concrete blocking defect")
    return sorted(set(reasons))

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
Treat those reference frames as art-language references, not literal dimensional blueprints. Do not infer numeric ratios, shoreline termination, rail thickness, lighting rules, or other requirements unless they are explicitly stated by the T03 contract or visible as an actual defect. The authored threshold posts use a uniform 1.12 footprint scale and 1.14 height scale; there is no 1.5x threshold-post rule. A tall vertical member at the free end of an open gate is the authored gate-leaf stile, not a threshold post. River gate and fence geometry may sit on the snow bank and is not required to terminate at the shoreline. Intended hinge overlap beneath a threshold post is not clipping unless a conflicting penetrating silhouette is visibly present. Packed lanes use continuous terrain and may read through subtle depression and wear rather than a dark painted strip. Shadows alone, perspective alone, and occlusion alone are not geometry defects. A feature that is visibly present in the candidate panel must not be reported as missing.
The repair standard is strict: every mandatory visual dimension must be strictly above 9.0 unrounded to pass; 10.0 remains the target. Do not average. A score of 9.0 or below requires a concrete actionable T03-owned defect in defects. A clean score above 9.0 must not be failed merely because it is below 10.0. Every blocking defect MUST describe one specific T03-owned issue corroborated across at least TWO relevant candidate views on the current page and MUST cite both exact candidate filenames printed on the board. A one-view apparent defect, perspective/foreshortening impression, or two unrelated one-view complaints cannot lower a mandatory score. If the same concrete issue is not visible in at least two relevant exact-source views, defects must be [] for that issue. If there is no actionable corroborated T03 defect, defects must be [] exactly. Do not invent defects from T02 context or downstream T04+ content. coverage_complete means you inspected every candidate panel in the evidence group; it must remain true when every panel was inspected even if you found a defect. Return JSON only."""
        if REVIEW_GROUP:
            assert REVIEW_GROUP in GROUPS,("unknown review group",REVIEW_GROUP)
            selected_groups={REVIEW_GROUP:GROUPS[REVIEW_GROUP]}
        else:
            selected_groups=GROUPS
        rows=[]
        expected_rows=0
        for gid,paths in selected_groups.items():
            pages=[paths[i:i+4] for i in range(0,len(paths),4)]
            expected_rows+=len(pages)
            for page_index,page_paths in enumerate(pages):
                board=make_board(gid,page_paths,page_index)
                page_names=", ".join(page_paths)
                review=request(
                    board,
                    base+f"\nEvidence group: {gid}, page {page_index+1} of {len(pages)}. Inspect ALL FOUR candidate panels on this page and the authoritative reference row. Candidate filenames on this page: {page_names}. Score only what is visibly supported on this page.",
                    response_schema(dims),
                    f"{gid}-page{page_index+1}"
                )
                violations=contract_violations(review,page_paths,dims)
                valid_defects=[d for d in review.get("defects",[]) if not defect_contract_reasons(d,page_paths)]
                if violations and not valid_defects:
                    previous=json.dumps(review,sort_keys=True)
                    correction=f"""You are the SAME independent Havenline {role} correcting only an evaluator-contract error from your completed pixel inspection of exact candidate {SOURCE}. Do not re-review pixels and do not invent a new defect. The prior raw review is preserved below. Every prior blocking claim was invalid under the T03 contract, or the prior review gave a score <=9.0 without any concrete corroborated defect. Authoritative machine evidence proves uniform gate presentation, uniform gate-family geometry, uniform threshold-post scale/height, terrain-seated posts, and terrain-seated gate leaves. A free-edge gate-leaf stile is not a threshold post. Subtle continuous-terrain lane wear is valid. Single-view perspective/foreshortening cannot block. Because there is no surviving contract-valid blocking defect, return defects=[] and rescore every mandatory dimension consistently strictly above 9.0. Do not modify coverage or confidence downward unless the prior review itself lacked coverage. PRIOR REVIEW: {previous}"""
                    review=request(None,correction,clean_response_schema(dims),f"{gid}-page{page_index+1}-contract-corrected",420)
                    violations=contract_violations(review,page_paths,dims)
                scores=review.get("scores",{})
                errors=[]
                if violations:errors.append("evaluator contract violation: "+", ".join(violations))
                if set(scores)!=set(dims):errors.append("dimension mismatch")
                if any(type(v) not in (int,float) or isinstance(v,bool) or not math.isfinite(v) or v<=9.0 for v in scores.values()):errors.append("visual score <=9.0")
                if review.get("defects")!=[]:errors.append("unresolved defects")
                if review.get("coverage_complete") is not True:errors.append("coverage incomplete")
                if review.get("confidence") not in ("medium","high"):errors.append("confidence insufficient")
                rows.append({"group":gid,"page":page_index+1,"paths":page_paths,"review":review,"evaluator_contract_violations":violations,"passed":not errors,"errors":errors})
        score_min={d:min(row["review"]["scores"].get(d,0) for row in rows) for d in dims}
        defects=[f"{row['group']}/page{row['page']}: {x}" for row in rows for x in row["review"].get("defects",[])]
        passed=len(rows)==expected_rows and all(row["passed"] for row in rows)
        raw={"critic_id":CRITIC,"candidate":SOURCE,"groups":rows,"reference_hashes":ref_hashes}
        raw_path=OUT/"raw-output.json";raw_path.write_text(json.dumps(raw,indent=2)+"\n")
        record={"task_id":"T03","critic_id":CRITIC,"review_group":REVIEW_GROUP or "all","provider":manifest["publisher"],"model":manifest["base_model"],"model_revision":manifest["revision"],"request_or_run_id":os.environ.get("GITHUB_RUN_ID","local")+"/"+os.environ.get("GITHUB_JOB","critic"),"candidate_hash":SOURCE,"input_manifest_hash":hashlib.sha256(json.dumps({"evidence":evidence["image_hashes"],"references":ref_hashes},sort_keys=True).encode()).hexdigest(),"raw_output_path":str(raw_path.relative_to(ROOT)),"raw_output_hash":digest(raw_path),"scores":score_min,"defects":defects,"coverage_complete":all(r["review"].get("coverage_complete") is True for r in rows),"confidence":"high" if all(r["review"].get("confidence")=="high" for r in rows) else "medium","independent_runtime":True,"groups":rows,"passed":passed,"visual_strictly_gt_9_required":True,"visual_target_10":True}
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
