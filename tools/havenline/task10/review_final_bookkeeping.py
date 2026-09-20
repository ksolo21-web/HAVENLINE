#!/usr/bin/env python3
"""Review the final T10 bookkeeping-only repair. Never approves gameplay."""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, subprocess, time, urllib.request

R="fc9010daebf6b4d520333279486a1b6bea164e7c"
B="249b61b02db28f694291dda8c1019c2514e991bf"
PLAN="Docs/Production/T10/REPAIR_PLAN.json"
C0R="Docs/Production/T10/C0R_REPAIR_SUFFICIENCY.json"
PRODUCT=[
 "HavenlineGodot/scripts/world_transform.gd",
 "HavenlineGodot/scripts/world_transform_view.gd",
 "HavenlineGodot/data/world_transform_recipes.json",
 "HavenlineGodot/tests/test_task10_world_transform.gd",
 "HavenlineGodot/tests/test_task10_integration.gd",
 "HavenlineGodot/tests/capture_task10_world_transform.gd",
]
DIMS=["bookkeeping_correctness","causal_scope_integrity","threshold_preservation","gameplay_immutability","source_binding"]

def git(repo,*args,text=False):
 return subprocess.check_output(["git",*args],cwd=repo,text=text,stderr=subprocess.PIPE)
def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def write(path,obj):
 p=pathlib.Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2)+"\n")

def preflight(repo,out):
 repo=pathlib.Path(repo);out=pathlib.Path(out);out.mkdir(parents=True,exist_ok=True)
 if git(repo,"rev-parse","HEAD",text=True).strip()!=R:raise ValueError("review worktree not exact source")
 changed=git(repo,"diff","--name-only",B,R,text=True).splitlines()
 expected=[C0R,PLAN]
 if changed!=expected:raise ValueError("unexpected changed paths: "+repr(changed))
 hashes={}
 for p in PRODUCT:
  before=git(repo,"show",B+":"+p);after=(repo/p).read_bytes()
  if before!=after:raise ValueError("gameplay/test source changed: "+p)
  hashes[p]=sha(after)
 plan=json.loads((repo/PLAN).read_text())
 inherited=set(plan["inherited_noncausal_files"])
 causal={(f["blocker_id"],p) for f in plan["fixes"] for p in f["files"]}
 overlap=[{"blocker_id":bid,"path":p} for bid,p in sorted(causal) if p in inherited]
 if overlap:raise ValueError("causal/noncausal overlap remains: "+repr(overlap))
 b40=next(f for f in plan["fixes"] if f["blocker_id"]=="C0-T10-B040")
 if "Docs/Production/PATH_OWNERSHIP.json" not in b40["files"] or "Docs/Production/PATH_OWNERSHIP.json" in inherited:
  raise ValueError("PATH_OWNERSHIP classification incorrect")
 recomputed=out/"recomputed-c0r.json"
 with (out/"c0r.log").open("w") as log:
  subprocess.run(["python3","tools/havenline/production/repair_sufficiency_critic.py","--c0","Docs/Production/T10/C0_ROOT_CAUSE.json","--plan",PLAN,"--output",str(recomputed.resolve())],cwd=repo,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
 actual=json.loads((repo/C0R).read_text());expected_obj=json.loads(recomputed.read_text())
 if actual!=expected_obj:raise ValueError("committed C0R differs from deterministic recomputation")
 if actual.get("passed") is not True or actual.get("outcome")!="REPAIR_PLAN_ACCEPTED" or actual.get("thresholds_unchanged") is not True or actual.get("rejections") or actual.get("evidence_gaps"):
  raise ValueError("recomputed C0R is not strict green")
 patch=git(repo,"diff","--unified=50",B,R,"--",PLAN,C0R,text=True)
 (out/"exact-diff.patch").write_text(patch)
 result={"source":R,"base":B,"changed_paths":changed,"product_runtime_and_tests_byte_identical":True,"product_hashes":hashes,"causal_inherited_overlap":[],"path_ownership_remains_causal_B040":True,"path_ownership_removed_from_noncausal_inheritance":True,"c0r_object_exact_match":True,"c0r_passed":True,"thresholds_unchanged":True,"task_approved":False,"t11_unlocked":False}
 write(out/"preflight.json",result);return result

def review(repo,out):
 repo=pathlib.Path(repo);out=pathlib.Path(out);out.mkdir(parents=True,exist_ok=True)
 pre=preflight(repo,out/"preflight")
 plan=json.loads((repo/PLAN).read_text());c0r=json.loads((repo/C0R).read_text())
 base_plan=json.loads(git(repo,"show",B+":"+PLAN,text=True));base_c0r=json.loads(git(repo,"show",B+":"+C0R,text=True))
 import copy
 before=copy.deepcopy(base_plan);after=copy.deepcopy(plan)
 before_inherited=before.pop("inherited_noncausal_files");after_inherited=after.pop("inherited_noncausal_files")
 repair_note=after.pop("final_closeout_bookkeeping_repair",None)
 if after!=before:raise ValueError("plan changed outside inheritance classification/note")
 removed=sorted(set(before_inherited)-set(after_inherited));added=sorted(set(after_inherited)-set(before_inherited))
 if removed!=["Docs/Production/PATH_OWNERSHIP.json"] or added:raise ValueError("unexpected inheritance delta")
 before_report=copy.deepcopy(base_c0r);after_report=copy.deepcopy(c0r)
 old_plan_hash=before_report["input_bindings"]["plan_sha256"];new_plan_hash=after_report["input_bindings"]["plan_sha256"]
 after_report["input_bindings"]["plan_sha256"]=old_plan_hash
 if after_report!=before_report:raise ValueError("C0R changed outside exact plan hash binding")
 evidence={
  "preflight":pre,
  "semantic_json_delta":{
   "repair_plan":{"removed_from_inherited_noncausal_files":removed,"added_to_inherited_noncausal_files":added,"all_other_existing_plan_fields_equal":True,"added_audit_note":repair_note},
   "c0r":{"only_changed_field":"input_bindings.plan_sha256","before":old_plan_hash,"after":new_plan_hash,"all_other_fields_equal":True}
  },
  "B040_fix":next(x for x in plan["fixes"] if x["blocker_id"]=="C0-T10-B040"),
  "c0r_result":{"outcome":c0r["outcome"],"passed":c0r["passed"],"thresholds_unchanged":c0r["thresholds_unchanged"],"rejections":c0r.get("rejections"),"evidence_gaps":c0r.get("evidence_gaps")},
  "final_acceptance_still_required":"Fresh C1/C2/C3/C4/C6/C7 each >9 unrounded, G1-G14, regression, zero mandatory defects, integrated closeout; T11 stays locked."
 }
 root=pathlib.Path.cwd();runtime=json.loads((root/"Docs/Production/CRITIC_EXECUTION.json").read_text())["local_independent_runtime"]
 cache=pathlib.Path(os.path.expanduser(runtime["cache_path"]));manifest=json.loads((cache/"manifest.json").read_text())
 servers=list((cache/"runtime").rglob("llama-server"))
 if len(servers)!=1:raise ValueError("pinned reviewer runtime missing/ambiguous")
 server=servers[0];env=dict(os.environ);env["LD_LIBRARY_PATH"]=str(server.parent)+":"+env.get("LD_LIBRARY_PATH","")
 log=(out/"runtime.log").open("w")
 proc=subprocess.Popen([str(server),"-m",str(cache/manifest["model_file"]),"--mmproj",str(cache/manifest["projector_file"]),"--host","127.0.0.1","--port","8080","-c","12288","-t","4","-tb","4","-ngl","0","--no-mmproj-offload","--parallel","1","--jinja","--image-min-tokens","768","--image-max-tokens","2048"],stdout=log,stderr=subprocess.STDOUT,env=env)
 try:
  for _ in range(180):
   if proc.poll() is not None:raise RuntimeError("review runtime exited")
   try:
    if json.load(urllib.request.urlopen("http://127.0.0.1:8080/health",timeout=3)).get("status")=="ok":break
   except Exception:time.sleep(2)
  else:raise RuntimeError("review runtime not ready")
  props={d:{"type":"number","minimum":0,"maximum":10} for d in DIMS}
  schema={"type":"object","properties":{"observations":{"type":"array","items":{"type":"string","maxLength":180},"minItems":3,"maxItems":4},"defects":{"type":"array","items":{"type":"string","maxLength":180},"maxItems":5},"coverage_complete":{"type":"boolean"},"confidence":{"type":"string","enum":["low","medium","high"]},"scores":{"type":"object","properties":props,"required":DIMS,"additionalProperties":False}},"required":["observations","defects","coverage_complete","confidence","scores"],"additionalProperties":False}
  prompt="""You are an independent non-voting T10 bookkeeping repair critic. This is not gameplay approval.
The final acceptance bar is unchanged: fresh C1/C2/C3/C4/C6/C7 strictly >9.0 unrounded, G1-G14 and regression pass, zero mandatory defects, then integrated closeout; T11 stays locked.
Review only this exact two-file metadata delta. Decide whether PATH_OWNERSHIP.json is correctly causal under B040 while removed from inherited_noncausal_files, whether deterministic C0R remains strict, thresholds are preserved, and gameplay/runtime/tests are byte-identical.
Do not force a pass. Report any real source-bound bookkeeping defect. Return JSON only.
EVIDENCE:
"""+json.dumps(evidence,indent=2)
  body={"model":"havenline-specialist-local","messages":[{"role":"user","content":[{"type":"text","text":prompt}]}],"max_tokens":900,"temperature":0.2,"top_p":0.9,"seed":20260920,"chat_template_kwargs":{"enable_thinking":False},"response_format":{"type":"json_object","schema":schema},"cache_prompt":False}
  raw=json.dumps(body).encode();(out/"request.json").write_bytes(raw)
  req=urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",data=raw,headers={"Content-Type":"application/json"},method="POST")
  with urllib.request.urlopen(req,timeout=1200) as resp:reply=json.load(resp)
  (out/"raw.json").write_text(json.dumps(reply,indent=2))
  choice=reply["choices"][0]
  if choice.get("finish_reason")!="stop":raise ValueError("review response incomplete")
  row=json.loads(choice["message"]["content"]);errors=[]
  if row.get("coverage_complete") is not True:errors.append("coverage incomplete")
  if row.get("confidence") not in ("medium","high"):errors.append("confidence insufficient")
  if row.get("defects"):errors.append("unresolved defects")
  scores=row.get("scores",{})
  if set(scores)!=set(DIMS):errors.append("dimension mismatch")
  for d,v in scores.items():
   if type(v) not in (int,float) or isinstance(v,bool) or v<=9.0:errors.append(d+" not strictly above 9")
  result={"task_id":"T10","review_kind":"FINAL_BOOKKEEPING_SOURCE_REVIEW","source":R,"base":B,"review":row,"provider":manifest.get("publisher"),"model":manifest.get("base_model"),"model_revision":manifest.get("revision"),"runtime_release":manifest.get("runtime_release"),"passed":not errors,"errors":errors,"lowest_score":min(scores.values()) if scores else 0,"non_voting":True,"task_approved":False,"t11_unlocked":False}
  write(out/"result.json",result);print(json.dumps(result,indent=2));return 0 if not errors else 1
 finally:
  proc.terminate()
  try:proc.wait(timeout=10)
  except Exception:proc.kill()
  log.close()

def main():
 p=argparse.ArgumentParser();p.add_argument("--mode",choices=["preflight","review"],required=True);p.add_argument("--repo",required=True);p.add_argument("--out",required=True);a=p.parse_args()
 result=preflight(a.repo,a.out) if a.mode=="preflight" else None
 if a.mode=="preflight":print(json.dumps(result,indent=2));return 0
 return review(a.repo,a.out)
if __name__=="__main__":raise SystemExit(main())
