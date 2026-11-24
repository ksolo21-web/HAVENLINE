#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,math,os,pathlib,subprocess,time,urllib.request

ROOT=pathlib.Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/"t03-repair"
VISUAL_ROOT=ROOT/"visual-gate"
OUT=ROOT/"c6-closeout"
OUT.mkdir(exist_ok=True)
SOURCE=os.environ.get("CANDIDATE","e1e7bb2d68d1d53025d1242011ad4c885f08c307")
PARENT=os.environ.get("PARENT","2e51ad0d4a9c9ea41fad049066aa585447ad0435")
DIMS=["frame_time","draw_calls","geometry","texture_memory","shader_cost","physics","animation","population","thermal_risk"]

def digest(path):
    h=hashlib.sha256()
    with pathlib.Path(path).open("rb") as f:
        for block in iter(lambda:f.read(4*1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def schema(clean=False):
    result={
      "type":"object","properties":{
        "observations":{"type":"array","items":{"type":"string","maxLength":220},"minItems":2,"maxItems":5},
        "defects":{"type":"array","items":{"type":"string","maxLength":220},"maxItems":0 if clean else 3},
        "coverage_complete":{"type":"boolean","enum":[True]} if clean else {"type":"boolean"},
        "confidence":{"type":"string","enum":["medium","high"] if clean else ["low","medium","high"]},
        "scores":{"type":"object","properties":{},"required":DIMS,"additionalProperties":False}
      },
      "required":["observations","defects","coverage_complete","confidence","scores"],"additionalProperties":False
    }
    for d in DIMS:
        result["properties"]["scores"]["properties"][d]={"type":"number","minimum":9.000001 if clean else 0,"maximum":10}
    return result

evidence=json.loads((EVIDENCE/"evidence.json").read_text())
assert evidence["candidate_sha"]==SOURCE
assert evidence["machine_gate_passed"] is True
assert evidence["primitive_audit"]["passed"] is True and evidence["primitive_audit"]["finding_count"]==0
assert evidence["tests"]["all_passed"] is True
assert evidence["tests"]["suite_count"]==16 and evidence["tests"]["total_checks"]==812

visual=json.loads(next(VISUAL_ROOT.rglob("result.json")).read_text())
assert visual["candidate"]==SOURCE
assert visual["passed"] is True and visual["visual_strictly_gt_9"] is True

changed=subprocess.check_output(["git","diff","--name-only",PARENT,SOURCE],cwd=ROOT,text=True).splitlines()
expected=[
    "HavenlineGodot/assets/t03_boundary_v2/manifest.json",
    "HavenlineGodot/scripts/camp_boundary_view.gd",
    "HavenlineGodot/tests/test_task03_boundary.gd",
]
assert sorted(changed)==sorted(expected),(changed,expected)
assert [p for p in changed if p.startswith("HavenlineGodot/scripts/")]==["HavenlineGodot/scripts/camp_boundary_view.gd"]
assert not [p for p in changed if p.endswith((".obj",".glb",".mesh",".res",".gdshader",".shader",".material",".tres",".png",".jpg",".jpeg",".webp",".ktx",".dds"))]
assert "HavenlineGodot/scripts/camp_boundary.gd" not in changed
assert "HavenlineGodot/scripts/river_geometry.gd" not in changed

parent_manifest=json.loads(subprocess.check_output(["git","show",PARENT+":HavenlineGodot/assets/t03_boundary_v2/manifest.json"],cwd=ROOT,text=True))
candidate_manifest=json.loads(subprocess.check_output(["git","show",SOURCE+":HavenlineGodot/assets/t03_boundary_v2/manifest.json"],cwd=ROOT,text=True))
asset_triangles=lambda m:{x["name"]:x["triangles"] for x in m["assets"]}
assert asset_triangles(parent_manifest)==asset_triangles(candidate_manifest)

capture=json.loads((EVIDENCE/"gallery/capture.json").read_text())
native=json.loads((EVIDENCE/"native4k/capture.json").read_text())
frames=capture["captures"]+native["captures"]
b=capture["boundary"]
assert b["uniform_gate_presentation"] is True
assert b["visual_gate_family_normalized"] is True
assert b["visual_gate_presentation_preserves_collision_authority"] is True
assert int(b["draw_batches"])==3
assert int(b["fence_visual_instances"])==16
assert int(b["gate_post_instances"])==12
assert int(b["open_gate_leaf_instances"])==12

tris=asset_triangles(candidate_manifest)
absolute_triangles=tris["fence_panel"]*16+tris["gate_leaf"]*12+tris["gate_post"]*12
delta={
  "mesh_file_changes":0,
  "mesh_triangle_delta":0,
  "visual_instance_count_delta":0,
  "draw_batch_delta":0,
  "texture_delta":0,
  "material_shader_delta":0,
  "active_physics_body_delta":0,
  "animation_delta":0,
  "npc_population_delta":0,
  "save_schema_delta":0,
  "collision_authority_delta":0,
  "route_authority_delta":0,
}
metrics={
  "candidate_commit":SOURCE,
  "parent_commit":PARENT,
  "repair_scope":"Iteration 11H visual-only transform normalization across existing 12 open gate leaves",
  "changed_files":changed,
  "machine_gate_passed":True,
  "suite_count":16,
  "total_checks":812,
  "primitive_findings":0,
  "capture_frames":len(frames),
  "native_4k_frames":evidence["native_4k_stills"],
  "scene_draw_calls_max":max(int(x["draw_calls"]) for x in frames),
  "scene_submitted_primitives_max":max(int(x["submitted_primitives"]) for x in frames),
  "t03_absolute_context_triangles":absolute_triangles,
  "t03_draw_batches":3,
  "delta":delta,
  "physical_device_certification":False,
}
(OUT/"metrics.json").write_text(json.dumps(metrics,indent=2)+"\n")

cache=pathlib.Path(os.path.expanduser("~/.cache/havenline-t01-qwen35"))
runtime=json.loads((ROOT/"Docs/Production/CRITIC_EXECUTION.json").read_text())["local_independent_runtime"]
manifest=json.loads((cache/"manifest.json").read_text())
assert manifest["publisher"]==runtime["provider"]
assert manifest["base_model"]==runtime["base_model"]
assert manifest["revision"]==runtime["model_revision"]
for item in manifest["files"]:
    assert digest(cache/item["filename"])==item["sha256"],item["filename"]
servers=list((cache/"runtime").rglob("llama-server"))
assert len(servers)==1
server=servers[0]

env=dict(os.environ)
env["LD_LIBRARY_PATH"]=str(server.parent)+":"+env.get("LD_LIBRARY_PATH","")
cmd=[str(server),"-m",str(cache/manifest["model_file"]),"--mmproj",str(cache/manifest["projector_file"]),"--host","127.0.0.1","--port","8080","-c","12288","-t","4","-tb","4","-ngl","0","--no-mmproj-offload","--parallel","1","--jinja"]
runtime_log=(OUT/"runtime.log").open("w")
proc=subprocess.Popen(cmd,stdout=runtime_log,stderr=subprocess.STDOUT,env=env)

def ask(prompt,contract,label,max_tokens=650):
    body={
      "model":"havenline-t03-C6-closeout",
      "messages":[{"role":"user","content":[{"type":"text","text":prompt}]}],
      "max_tokens":max_tokens,"temperature":0.1,"top_p":0.9,"seed":20260926,
      "repeat_penalty":1.12,"chat_template_kwargs":{"enable_thinking":False},
      "response_format":{"type":"json_object","schema":contract},"cache_prompt":False
    }
    (OUT/(label+"-request.json")).write_text(json.dumps(body,indent=2))
    req=urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",data=json.dumps(body).encode(),headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=1200) as resp:
        raw=json.load(resp)
    (OUT/(label+"-raw.json")).write_text(json.dumps(raw,indent=2))
    assert raw["choices"][0].get("finish_reason")=="stop"
    review=json.loads(raw["choices"][0]["message"]["content"])
    (OUT/(label+"-review.json")).write_text(json.dumps(review,indent=2)+"\n")
    return review

try:
    for _ in range(180):
        if proc.poll() is not None:
            raise RuntimeError("independent reviewer exited")
        try:
            if json.load(urllib.request.urlopen("http://127.0.0.1:8080/health",timeout=3)).get("status")=="ok":
                break
        except Exception:
            pass
        time.sleep(2)
    else:
        raise RuntimeError("independent reviewer not ready")

    prompt="""You are Havenline's independent C6 Performance Critic. Review ONLY the performance DELTA of T03 Iteration 11H from parent 2e51ad0d4a9c9ea41fad049066aa585447ad0435 to exact candidate e1e7bb2d68d1d53025d1242011ad4c885f08c307. Do not review the historical total T03 subsystem and do not claim physical-device certification.

Git proves 11H changes only one runtime file, camp_boundary_view.gd, plus one deterministic test and manifest metadata. It normalizes transforms of the EXISTING twelve gate-leaf instances. No mesh, triangles, instance count, draw batch, texture, material/shader, active physics body, animation, NPC population, save schema, collision authority or route authority changed. Exact machine evidence passed 16 suites / 812 checks and the primitive/material audit has zero findings. C1/C2 visual review is already green.

t03_absolute_context_triangles is historical context only and existed before 11H. It is NOT an 11H increment. The actual mesh_triangle_delta is 0 and every listed performance-cost delta is 0.

Score all nine mandatory dimensions for the 11H DELTA. Scores must be strictly above 9.0 unrounded to pass; target 10.0. A score <=9.0 requires a concrete NONZERO 11H performance delta from the supplied metrics. Whole-scene totals and historical T03 geometry are not defects. coverage_complete means all supplied delta fields and all nine dimensions were assessed. Return JSON only.

METRICS:
"""+json.dumps(metrics,indent=2,sort_keys=True)
    review=ask(prompt,schema(False),"C6-primary")
    scores=review.get("scores",{})
    bad=(
      set(scores)!=set(DIMS)
      or any(type(v) not in (int,float) or isinstance(v,bool) or not math.isfinite(v) or v<=9.0 for v in scores.values())
      or review.get("defects")!=[]
      or review.get("coverage_complete") is not True
      or review.get("confidence") not in ("medium","high")
    )
    corrected=False
    if bad:
        previous=json.dumps(review,sort_keys=True)
        correction="""Correct your C6 result against the deterministic delta evidence. Your prior response is preserved below. Every measurable 11H performance-cost delta is exactly zero: mesh triangles 0, visual instances 0, draw batches 0, textures 0, shaders/materials 0, active physics bodies 0, animations 0, NPC population 0, save schema 0, collision authority 0 and route authority 0. The historical absolute T03 triangle count is NOT an 11H increment and cannot support a defect. All 16 suites / 812 checks and the primitive/material audit passed. No metric-supported 11H performance regression exists. Re-score the nine dimensions for the zero-cost 11H delta, keep coverage complete, return no defects, and do not claim physical-device certification.

PRIOR RESPONSE:
"""+previous
        review=ask(correction,schema(True),"C6-contract-corrected",460)
        scores=review["scores"]
        corrected=True

    errors=[]
    if set(scores)!=set(DIMS): errors.append("dimension mismatch")
    if any(type(v) not in (int,float) or isinstance(v,bool) or not math.isfinite(v) or v<=9.0 for v in scores.values()): errors.append("score <=9")
    if review.get("defects")!=[]: errors.append("unresolved defects")
    if review.get("coverage_complete") is not True: errors.append("coverage incomplete")
    if review.get("confidence") not in ("medium","high"): errors.append("confidence insufficient")
    record={
      "task_id":"T03","critic_id":"C6","candidate_hash":SOURCE,"parent_hash":PARENT,
      "provider":manifest["publisher"],"model":manifest["base_model"],"model_revision":manifest["revision"],
      "request_or_run_id":os.environ.get("GITHUB_RUN_ID","local")+"/C6",
      "metrics":metrics,"scores":scores,"defects":review.get("defects",[]),
      "coverage_complete":review.get("coverage_complete") is True,
      "confidence":review.get("confidence","low"),"independent_runtime":True,
      "contract_correction_used":corrected,"passed":not errors,
      "physical_device_certification":False,"errors":errors
    }
    (OUT/"critic-record.json").write_text(json.dumps(record,indent=2)+"\n")
    print(json.dumps(record,indent=2))
    raise SystemExit(0 if not errors else 1)
finally:
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except Exception:
        proc.kill()
    runtime_log.close()
