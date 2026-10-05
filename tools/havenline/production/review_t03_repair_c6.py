#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,math,os,pathlib,subprocess,time,urllib.request
ROOT=pathlib.Path.cwd()
EVIDENCE=ROOT/os.environ.get("EVIDENCE_ROOT","task03-evidence")
OUT=ROOT/os.environ.get("OUT_DIR","task03-c6")
OUT.mkdir(parents=True,exist_ok=True)
CANDIDATE=os.environ["EXPECTED_SOURCE"]
BASELINE=os.environ["BASELINE_SOURCE"]
BASE_BENCH=pathlib.Path(os.environ["BASELINE_BENCHMARK"])
CAND_BENCH=pathlib.Path(os.environ["CANDIDATE_BENCHMARK"])

def sha(p:pathlib.Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(4*1024*1024),b""):h.update(b)
    return h.hexdigest()

ev=json.loads((EVIDENCE/"evidence.json").read_text())
assert ev["candidate_sha"]==CANDIDATE and ev["machine_gate_passed"] is True
gallery=json.loads((EVIDENCE/"gallery/capture.json").read_text())
native=json.loads((EVIDENCE/"native4k/capture.json").read_text())
assert gallery["boundary"]["draw_batches"]==3
assert gallery["boundary"]["open_gate_leaf_instances"]==12
assert gallery["boundary"]["authored_gate_leaf_asset"]=="t03_boundary_v2/gate_leaf.obj"
base=json.loads(BASE_BENCH.read_text());cand=json.loads(CAND_BENCH.read_text())
for data in (base,cand):
    assert data["renderer"]=="mobile"
    assert data["native_dimensions_and_scale_maintained"] is True
    assert data["fixed_timestep_used"] is False
    assert data["samples"]>0 and data["retained_seconds"]>=10.0

all_frames=gallery["captures"]+native["captures"]
metrics={
 "candidate_commit":CANDIDATE,"comparison_baseline":BASELINE,
 "functional_suites":ev["tests"]["suite_count"],"functional_checks":ev["tests"]["total_checks"],
 "primitive_audit_findings":ev["primitive_audit"]["finding_count"],
 "capture_frames":len(all_frames),"native_4k_frames":ev["native_4k_stills"],
 "scene_draw_calls_max":max(int(x["draw_calls"]) for x in all_frames),
 "scene_submitted_primitives_max":max(int(x["submitted_primitives"]) for x in all_frames),
 "t03_static_draw_batches":gallery["boundary"]["draw_batches"],
 "t03_fence_instances":gallery["boundary"]["fence_visual_instances"],
 "t03_gate_leaf_instances":gallery["boundary"]["open_gate_leaf_instances"],
 "t03_gate_post_instances":gallery["boundary"]["gate_post_instances"],
 "gate_leaf_source_triangles":84,
 "new_textures":0,"new_shaders":0,"new_physics_bodies":0,"new_animations":0,"new_npcs":0,
 "baseline_benchmark":{"average_engine_fps":base["average_engine_fps"],"p50_ms":base["p50_ms"],"p95_ms":base["p95_ms"],"p99_ms":base["p99_ms"],"draw_calls":base["draw_calls"],"primitives":base["primitives"],"software_renderer":base["software_renderer"]},
 "candidate_benchmark":{"average_engine_fps":cand["average_engine_fps"],"p50_ms":cand["p50_ms"],"p95_ms":cand["p95_ms"],"p99_ms":cand["p99_ms"],"draw_calls":cand["draw_calls"],"primitives":cand["primitives"],"software_renderer":cand["software_renderer"]},
 "physical_device_certified":False,
 "note":"Same-runner software/Vulkan comparison is incremental evidence only; T68/T69 retain physical native-4K60/thermal certification."
}
(OUT/"metrics.json").write_text(json.dumps(metrics,indent=2)+"\n")

execution=json.loads((ROOT/"Docs/Production/CRITIC_EXECUTION.json").read_text())
runtime=execution["local_independent_runtime"]
cache=pathlib.Path(os.path.expanduser(runtime["cache_path"]))
m=json.loads((cache/"manifest.json").read_text())
assert m["publisher"]==runtime["provider"] and m["base_model"]==runtime["base_model"] and m["revision"]==runtime["model_revision"]
assert m.get("runtime_release")=="b10809"
for item in m["files"]: assert sha(cache/item["filename"])==item["sha256"]
servers=list((cache/"runtime").rglob("llama-server"));assert len(servers)==1;server=servers[0]

dims=["frame_time","draw_calls","geometry","texture_memory","shader_cost","physics","animation","population","thermal_risk"]
schema={"type":"object","properties":{
 "observations":{"type":"array","items":{"type":"string","maxLength":220},"minItems":2,"maxItems":4},
 "defects":{"type":"array","items":{"type":"string","maxLength":220},"maxItems":4},
 "coverage_complete":{"type":"boolean"},
 "confidence":{"type":"string","enum":["low","medium","high"]},
 "scores":{"type":"object","properties":{k:{"type":"number","minimum":0,"maximum":10} for k in dims},"required":dims,"additionalProperties":False}
},"required":["observations","defects","coverage_complete","confidence","scores"],"additionalProperties":False}
prompt="""You are Havenline C6 Performance Critic. Review ONLY the incremental performance effect of T03 iteration 6 versus its immediately preceding iteration 5 on the same full integrated game. This is an early subsystem budget gate, not T68/T69 physical certification. Absolute software-renderer FPS is not Android certification and must not be treated as one. Compare same-runner baseline versus candidate engine intervals and the exact source-bound scene metrics. Iteration 6 adds one static authored gate-leaf draw batch and an 84-triangle source mesh instanced 12 times, with no new textures, shaders, physics bodies, animations or NPCs. The global soft budgets are 650 draw calls and 2,000,000 visible triangles/primitives, and the candidate's exact capture maxima are supplied below.
Score frame_time, draw_calls, geometry, texture_memory, shader_cost, physics, animation, population and thermal_risk. Every dimension must be strictly greater than 9.0 unrounded with no actionable defect. Exactly 9.0 fails. Do not penalize missing physical-device certification because that belongs to T68/T69. If no actionable incremental T03 defect exists, defects MUST be []. Return JSON only.
METRICS:
"""+json.dumps(metrics,sort_keys=True)

env=dict(os.environ);env["LD_LIBRARY_PATH"]=str(server.parent)+":"+env.get("LD_LIBRARY_PATH","")
log=(OUT/"runtime.log").open("w")
cmd=[str(server),"-m",str(cache/m["model_file"]),"--host","127.0.0.1","--port","8080","-c","8192","-t","4","-tb","4","-ngl","0","--parallel","1","--jinja"]
proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
fatal=None;review={}
try:
    for _ in range(180):
        if proc.poll() is not None: raise RuntimeError("reviewer runtime exited")
        try:
            if json.load(urllib.request.urlopen("http://127.0.0.1:8080/health",timeout=3)).get("status")=="ok": break
        except Exception: pass
        time.sleep(2)
    else: raise RuntimeError("reviewer runtime not ready")
    body={"model":"havenline-t03-c6","messages":[{"role":"user","content":prompt}],"max_tokens":700,"temperature":0.2,"top_p":0.9,"seed":20260923,"repeat_penalty":1.12,"chat_template_kwargs":{"enable_thinking":False},"response_format":{"type":"json_object","schema":schema},"cache_prompt":False}
    (OUT/"request.json").write_text(json.dumps(body,indent=2))
    req=urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",data=json.dumps(body).encode(),headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=1200) as resp:raw=json.load(resp)
    (OUT/"raw.json").write_text(json.dumps(raw,indent=2))
    choice=raw["choices"][0]
    if choice.get("finish_reason")!="stop": raise RuntimeError("incomplete C6 response")
    review=json.loads(choice["message"]["content"])
except Exception as exc:
    fatal=type(exc).__name__+": "+str(exc)
finally:
    proc.terminate()
    try:proc.wait(timeout=15)
    except Exception:proc.kill()
    log.close()

scores=review.get("scores",{})
passed=fatal is None and set(scores)==set(dims) and all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) and v>9.0 for v in scores.values()) and review.get("defects")==[] and review.get("coverage_complete") is True and review.get("confidence") in ("medium","high")
record={"task_id":"T03","critic_id":"C6","provider":m["publisher"],"model":m["base_model"],"model_revision":m["revision"],"request_or_run_id":os.environ.get("GITHUB_RUN_ID","local")+"/"+os.environ.get("GITHUB_JOB","c6"),"candidate_hash":CANDIDATE,"comparison_baseline":BASELINE,"metrics_path":str((OUT/"metrics.json").relative_to(ROOT)),"metrics_hash":sha(OUT/"metrics.json"),"raw_output_path":str((OUT/"raw.json").relative_to(ROOT)) if (OUT/"raw.json").exists() else None,"raw_output_hash":sha(OUT/"raw.json") if (OUT/"raw.json").exists() else None,"scores":scores,"defects":review.get("defects",[]),"coverage_complete":review.get("coverage_complete",False),"confidence":review.get("confidence","low"),"independent_runtime":True,"fatal_error":fatal,"passed":passed,"physical_device_certification":False}
(OUT/"critic-record.json").write_text(json.dumps(record,indent=2)+"\n")
print(json.dumps(record,indent=2))
raise SystemExit(0 if passed else 1)
