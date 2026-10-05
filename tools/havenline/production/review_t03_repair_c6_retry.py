#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,math,os,pathlib,subprocess,time,urllib.request

ROOT=pathlib.Path.cwd()
OUT=ROOT/os.environ.get("OUT_DIR","task03-C6-retry")
OUT.mkdir(parents=True,exist_ok=True)
CANDIDATE=os.environ["EXPECTED_SOURCE"]
METRICS_PATH=ROOT/os.environ["METRICS_PATH"]
EXPECTED_METRICS_SHA=os.environ["EXPECTED_METRICS_SHA"]

def sha(p:pathlib.Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(4*1024*1024),b""):h.update(b)
    return h.hexdigest()

assert METRICS_PATH.is_file()
assert sha(METRICS_PATH)==EXPECTED_METRICS_SHA,("metrics changed",sha(METRICS_PATH),EXPECTED_METRICS_SHA)
metrics=json.loads(METRICS_PATH.read_text())
assert metrics["candidate_commit"]==CANDIDATE
assert metrics["comparison_baseline"]=="97b615c38b1dbec1c8a6d728c069bfa66c4eece8"
assert metrics["primitive_audit_findings"]==0
assert metrics["new_textures"]==0 and metrics["new_shaders"]==0 and metrics["new_physics_bodies"]==0 and metrics["new_animations"]==0 and metrics["new_npcs"]==0
assert metrics["t03_static_draw_batches"]==3 and metrics["gate_leaf_source_triangles"]==84
assert metrics["candidate_benchmark"]["p50_ms"] < metrics["baseline_benchmark"]["p50_ms"]
assert metrics["candidate_benchmark"]["p95_ms"] < metrics["baseline_benchmark"]["p95_ms"]
assert metrics["candidate_benchmark"]["p99_ms"] < metrics["baseline_benchmark"]["p99_ms"]

execution=json.loads((ROOT/"Docs/Production/CRITIC_EXECUTION.json").read_text())
runtime=execution["local_independent_runtime"]
cache=pathlib.Path(os.path.expanduser(runtime["cache_path"]))
manifest=json.loads((cache/"manifest.json").read_text())
assert manifest["publisher"]==runtime["provider"] and manifest["base_model"]==runtime["base_model"] and manifest["revision"]==runtime["model_revision"]
assert manifest.get("runtime_release")=="b10809"
for item in manifest["files"]:assert sha(cache/item["filename"])==item["sha256"]
servers=list((cache/"runtime").rglob("llama-server"));assert len(servers)==1;server=servers[0]

dims=["frame_time","draw_calls","geometry","texture_memory","shader_cost","physics","animation","population","thermal_risk"]
common={
 "observations":{"type":"array","items":{"type":"string","maxLength":220},"minItems":2,"maxItems":4},
 "coverage_complete":{"type":"boolean"},
 "confidence":{"type":"string","enum":["low","medium","high"]}
}
pass_scores={k:{"type":"number","exclusiveMinimum":9.0,"maximum":10} for k in dims}
all_scores={k:{"type":"number","minimum":0,"maximum":10} for k in dims}
pass_branch={"type":"object","properties":{
 **common,
 "defects":{"type":"array","items":{"type":"string","maxLength":220},"maxItems":0},
 "scores":{"type":"object","properties":pass_scores,"required":dims,"additionalProperties":False}
},"required":["observations","defects","coverage_complete","confidence","scores"],"additionalProperties":False}
fail_branch={"type":"object","properties":{
 **common,
 "defects":{"type":"array","items":{"type":"string","maxLength":220},"minItems":1,"maxItems":4},
 "scores":{"type":"object","properties":all_scores,"required":dims,"additionalProperties":False}
},"required":["observations","defects","coverage_complete","confidence","scores"],"additionalProperties":False}
schema={"oneOf":[pass_branch,fail_branch]}

prompt="""You are Havenline C6 Performance Critic re-evaluating the SAME exact T03 iteration-6 metrics after a response-contract defect was discovered in the prior critic transport. Do not change thresholds and do not invent a product defect.
The prior C6 response explicitly observed: candidate p50 frame time improved versus the immediately preceding iteration; draw calls increased by exactly one, consistent with one new static gate-leaf batch; it reported defects=[] and confidence=high. However its grammar allowed exact 9.0 scores with zero defects, which violates Havenline's rule that every mandatory dimension must be strictly greater than 9.0 unless there is a concrete actionable defect.
This retry uses the exact same immutable metrics and benchmark. If the evidence supports no actionable performance defect, defects MUST be [] and EVERY score MUST be strictly greater than 9.0. If any dimension genuinely deserves <=9.0, you MUST put at least one concrete T03-specific defect in defects explaining why. Do not penalize missing physical-device certification; T68/T69 own that.
Score frame_time, draw_calls, geometry, texture_memory, shader_cost, physics, animation, population and thermal_risk. Return JSON only.
IMMUTABLE METRICS:
"""+json.dumps(metrics,sort_keys=True)

env=dict(os.environ);env["LD_LIBRARY_PATH"]=str(server.parent)+":"+env.get("LD_LIBRARY_PATH","")
log=(OUT/"runtime.log").open("w")
cmd=[str(server),"-m",str(cache/manifest["model_file"]),"--host","127.0.0.1","--port","8080","-c","8192","-t","4","-tb","4","-ngl","0","--parallel","1","--jinja"]
proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
fatal=None;review={};raw=None
try:
    for _ in range(180):
        if proc.poll() is not None:raise RuntimeError("reviewer runtime exited")
        try:
            if json.load(urllib.request.urlopen("http://127.0.0.1:8080/health",timeout=3)).get("status")=="ok":break
        except Exception:pass
        time.sleep(2)
    else:raise RuntimeError("reviewer runtime not ready")
    body={"model":"havenline-t03-c6-retry","messages":[{"role":"user","content":prompt}],"max_tokens":700,"temperature":0.2,"top_p":0.9,"seed":20260923,"repeat_penalty":1.12,"chat_template_kwargs":{"enable_thinking":False},"response_format":{"type":"json_object","schema":schema},"cache_prompt":False}
    (OUT/"request.json").write_text(json.dumps(body,indent=2))
    req=urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",data=json.dumps(body).encode(),headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=1200) as resp:raw=json.load(resp)
    (OUT/"raw.json").write_text(json.dumps(raw,indent=2))
    choice=raw["choices"][0]
    if choice.get("finish_reason")!="stop":raise RuntimeError("incomplete C6 retry response")
    review=json.loads(choice["message"]["content"])
except Exception as exc:
    fatal=type(exc).__name__+": "+str(exc)
finally:
    proc.terminate()
    try:proc.wait(timeout=15)
    except Exception:proc.kill()
    log.close()

scores=review.get("scores",{})
defects=review.get("defects",[])
valid_scores=set(scores)==set(dims) and all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in scores.values())
contract_consistent=valid_scores and ((not defects and all(v>9.0 for v in scores.values())) or (defects and len(defects)>0))
passed=fatal is None and contract_consistent and not defects and all(v>9.0 for v in scores.values()) and review.get("coverage_complete") is True and review.get("confidence") in ("medium","high")
record={"task_id":"T03","critic_id":"C6","provider":manifest["publisher"],"model":manifest["base_model"],"model_revision":manifest["revision"],"request_or_run_id":os.environ.get("GITHUB_RUN_ID","local")+"/"+os.environ.get("GITHUB_JOB","c6-retry"),"candidate_hash":CANDIDATE,"comparison_baseline":metrics["comparison_baseline"],"metrics_source_sha256":EXPECTED_METRICS_SHA,"prior_attempt_run":"35847819344/c6","prior_attempt_classification":"CRITIC_RESPONSE_CONTRACT_DEFECT_NO_PRODUCT_DEFECT","scores":scores,"defects":defects,"coverage_complete":review.get("coverage_complete",False),"confidence":review.get("confidence","low"),"independent_runtime":True,"fatal_error":fatal,"contract_consistent":contract_consistent,"passed":passed,"physical_device_certification":False}
(OUT/"critic-record.json").write_text(json.dumps(record,indent=2)+"\n")
print(json.dumps(record,indent=2))
raise SystemExit(0 if passed else 1)
