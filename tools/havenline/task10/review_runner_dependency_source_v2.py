#!/usr/bin/env python3
"""Independent preparation/review for final T10 runner-dependency source."""
from __future__ import annotations
import argparse,hashlib,json,math,os,pathlib,re,subprocess,time,urllib.request

BASE="90f1d56e8781f4998b00b9563f0f9d49458ebf53"
SOURCE="5484a8c3d47ffb0d895b379aeb267f190f3ff577"
AUTH_PREP="621f22c6682837c9b01a352d7e2feba46e258aa1"
AUTH_PATH="Docs/Production/ChangeRequests/T10-benchmark-liveness-contract.json"
AUTH_SHA="ac4a2f46743940a58fcd675623611b1fe9052ed615fcd7ab2fcba478a5822dec"
ISOLATED=".github/workflows/havenline-task10-isolated.yml"
WORLD=".github/workflows/havenline-task10-world-transformation.yml"
ARCH="tools/havenline/production/validate_architecture_v32_t10.py"
CHANGED=[ISOLATED,WORLD,ARCH]
INSTALL="python3 -m pip install --disable-pip-version-check --no-input numpy==2.3.5 pillow==12.3.0"
LATE="python3 -m pip install numpy==2.3.5"
DIMS=["runner_dependency_correctness","authorization_separation","architecture_binding","regression_safety","gameplay_immutability","source_binding"]
PROTECTED=[
"HavenlineGodot/scripts/world_transform.gd","HavenlineGodot/scripts/world_transform_view.gd",
"HavenlineGodot/data/world_transform_recipes.json","HavenlineGodot/tests/test_task10_world_transform.gd",
"HavenlineGodot/tests/test_task10_integration.gd","HavenlineGodot/tests/capture_task10_world_transform.gd",
"tools/havenline/task10/benchmark_world_transform.gd","Docs/Production/CRITIC_MATRIX.json",
"Docs/Production/CRITIC_EXECUTION.json","Docs/Production/task-gates.json"
]
def git(repo,*args,text=False):return subprocess.check_output(["git",*args],cwd=repo,text=text,stderr=subprocess.PIPE)
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,v):p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+"\n")
def authority_bytes(repo):
 return git(repo,"show",AUTH_PREP+":"+AUTH_PATH)
def preflight(repo,out):
 repo=pathlib.Path(repo);out=pathlib.Path(out);out.mkdir(parents=True,exist_ok=True)
 if git(repo,"rev-parse","HEAD",text=True).strip()!=SOURCE:raise ValueError("wrong reviewed source")
 changed=git(repo,"diff","--name-only",BASE,SOURCE,text=True).splitlines()
 if changed!=CHANGED:raise ValueError("unexpected source delta "+repr(changed))
 iso=(repo/ISOLATED).read_text();world=(repo/WORLD).read_text();arch=(repo/ARCH).read_text()
 for p,t in [(ISOLATED,iso),(WORLD,world)]:
  if t.count(INSTALL)!=1:raise ValueError("pinned dependency install missing/duplicate: "+p)
  if t.index(INSTALL)>t.index("python3 -m unittest discover -s tools/havenline/production/tests"):raise ValueError("install occurs after production suite: "+p)
  if t.index(INSTALL)>t.index("python3 -m unittest discover -s tools/havenline/task10/tests"):raise ValueError("install occurs after task10 suite: "+p)
 if LATE not in world:raise ValueError("existing late NumPy compatibility marker removed")
 auth=authority_bytes(repo)
 if sha(auth)!=AUTH_SHA:raise ValueError("prepared benchmark authority bytes changed")
 auth_obj=json.loads(auth)
 if auth_obj["implementation_sha256"][ISOLATED]!="6bc062d4e8c5438414dd4781ce5bca23e7977739db73690873593c6c70583c05":raise ValueError("prepared isolated authorization mismatch")
 if auth_obj.get("final_runner_dependency_repair",{}).get("world_workflow_sha256")!="7c1518a7995c6888ab403ac678ffc26fb518499300cd87cf50ac9432b3775ea4":raise ValueError("prepared world workflow evidence mismatch")
 if 'BENCHMARK_LIVENESS_REQUEST_SHA256 = "'+AUTH_SHA+'"' not in arch:raise ValueError("architecture pin does not bind prepared authority")
 protected={}
 for p in PROTECTED:
  before=git(repo,"show",BASE+":"+p);after=(repo/p).read_bytes()
  if before!=after:raise ValueError("protected product/acceptance source changed: "+p)
  protected[p]=sha(after)
 # Overlay only the separately prepared noncausal authority metadata for deterministic consumer tests.
 (repo/AUTH_PATH).write_bytes(auth)
 if sha((repo/AUTH_PATH).read_bytes())!=AUTH_SHA:raise ValueError("authority overlay failed")
 subprocess.run(["python3","-m","pip","install","--disable-pip-version-check","--no-input","numpy==2.3.5","pillow==12.3.0"],cwd=repo,check=True,stdout=(out/"pip.log").open("w"),stderr=subprocess.STDOUT,timeout=240)
 suites=[]
 for label,cmd in [
  ("production",["python3","-m","unittest","discover","-s","tools/havenline/production/tests","-p","test_*.py","-v"]),
  ("task10",["python3","-m","unittest","discover","-s","tools/havenline/task10/tests","-p","test_*.py","-v"]),
 ]:
  log=out/(label+".log")
  with log.open("w") as h:r=subprocess.run(cmd,cwd=repo,stdout=h,stderr=subprocess.STDOUT,timeout=1000)
  text=log.read_text(errors="replace");m=re.search(r"Ran (\d+) tests?",text)
  row={"suite":label,"exit_code":r.returncode,"tests":int(m.group(1)) if m else None,"passed":r.returncode==0,"log_sha256":sha(log.read_bytes())};suites.append(row);print(json.dumps(row),flush=True)
 if not all(x["passed"] for x in suites):raise ValueError("deterministic suites red: "+repr(suites))
 c0r=out/"c0r.json"
 subprocess.run(["python3","tools/havenline/production/repair_sufficiency_critic.py","--c0","Docs/Production/T10/C0_ROOT_CAUSE.json","--plan","Docs/Production/T10/REPAIR_PLAN.json","--output",str(c0r.resolve())],cwd=repo,check=True,stdout=(out/"c0r.log").open("w"),stderr=subprocess.STDOUT,timeout=180)
 c0r_obj=json.loads(c0r.read_text())
 if c0r_obj.get("passed") is not True:raise ValueError("C0R red")
 result={"base":BASE,"source":SOURCE,"changed_paths":changed,"prepared_authority":{"source_commit":AUTH_PREP,"path":AUTH_PATH,"sha256":AUTH_SHA,"separate_noncausal_parent_required":True},"workflow_contract":{"install":INSTALL,"late_world_marker_preserved":True},"deterministic_suites":suites,"c0r_passed":True,"protected_product_acceptance_bytes_unchanged":True,"protected_hashes":protected,"final_acceptance_unchanged":"Fresh C1/C2/C3/C4/C6/C7 >9 unrounded; G1-G14/regression; zero mandatory defects; integrated closeout; T11 locked until approval.","task_approved":False,"t11_unlocked":False}
 write(out/"preflight.json",result);return result
def review(repo,out):
 out=pathlib.Path(out);pre=preflight(repo,out/"preflight");root=pathlib.Path.cwd()
 runtime=json.loads((root/"Docs/Production/CRITIC_EXECUTION.json").read_text())["local_independent_runtime"];cache=pathlib.Path(os.path.expanduser(runtime["cache_path"]));manifest=json.loads((cache/"manifest.json").read_text());servers=list((cache/"runtime").rglob("llama-server"))
 if len(servers)!=1:raise ValueError("pinned reviewer runtime unavailable")
 server=servers[0];env=dict(os.environ);env["LD_LIBRARY_PATH"]=str(server.parent)+":"+env.get("LD_LIBRARY_PATH","");out.mkdir(parents=True,exist_ok=True);log=(out/"runtime.log").open("w")
 proc=subprocess.Popen([str(server),"-m",str(cache/manifest["model_file"]),"--mmproj",str(cache/manifest["projector_file"]),"--host","127.0.0.1","--port","8080","-c","12288","-t","4","-tb","4","-ngl","0","--no-mmproj-offload","--parallel","1","--jinja","--image-min-tokens","768","--image-max-tokens","2048"],stdout=log,stderr=subprocess.STDOUT,env=env)
 try:
  for _ in range(180):
   if proc.poll() is not None:raise RuntimeError("review runtime exited")
   try:
    if json.load(urllib.request.urlopen("http://127.0.0.1:8080/health",timeout=3)).get("status")=="ok":break
   except Exception:time.sleep(2)
  else:raise RuntimeError("review runtime not ready")
  props={d:{"type":"number","minimum":0,"maximum":10} for d in DIMS}
  schema={"type":"object","properties":{"observations":{"type":"array","items":{"type":"string","maxLength":180},"minItems":3,"maxItems":5},"defects":{"type":"array","items":{"type":"string","maxLength":180},"maxItems":5},"coverage_complete":{"type":"boolean"},"confidence":{"type":"string","enum":["low","medium","high"]},"scores":{"type":"object","properties":props,"required":DIMS,"additionalProperties":False}},"required":["observations","defects","coverage_complete","confidence","scores"],"additionalProperties":False}
  prompt="""Independent non-voting T10 final runner-source review. Do not approve gameplay.
The prior exact candidate passed C0R but both final workflows failed before engine/gameplay because NumPy-backed T10 verifier tests executed before dependencies were installed. This source changes only two workflow callers plus the architecture digest pin. The benchmark authorization JSON is intentionally NOT in this source; it is separately prepared noncausal authority metadata and will be a distinct canonical authority parent before exact [R,H] promotion.
Deterministic preflight overlays those exact authority bytes only for validation and requires production + task10 tooling suites and C0R green. Gameplay/runtime/tests/critic thresholds remain byte-identical.
Judge whether the source + separate-authority design closes the runner failure without weakening acceptance or conflating metadata with repair source. Final six critics/G1-G14/regression/closeout remain mandatory. Report every genuine defect. Every dimension must be strictly >9.0 and defects empty for source acceptance.
EVIDENCE:
"""+json.dumps(pre,indent=2)
  body={"model":"havenline-specialist-local","messages":[{"role":"user","content":[{"type":"text","text":prompt}]}],"max_tokens":900,"temperature":0.2,"top_p":0.9,"seed":20260922,"chat_template_kwargs":{"enable_thinking":False},"response_format":{"type":"json_object","schema":schema},"cache_prompt":False}
  raw=json.dumps(body).encode();(out/"request.json").write_bytes(raw);req=urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",data=raw,headers={"Content-Type":"application/json"},method="POST")
  with urllib.request.urlopen(req,timeout=1200) as resp:reply=json.load(resp)
  (out/"raw.json").write_text(json.dumps(reply,indent=2));choice=reply["choices"][0]
  if choice.get("finish_reason")!="stop":raise ValueError("incomplete review output")
  row=json.loads(choice["message"]["content"]);errors=[]
  if row.get("coverage_complete") is not True:errors.append("coverage incomplete")
  if row.get("confidence") not in ("medium","high"):errors.append("confidence insufficient")
  if row.get("defects"):errors.append("unresolved defects")
  scores=row.get("scores",{})
  if set(scores)!=set(DIMS):errors.append("dimension mismatch")
  for d,v in scores.items():
   if type(v) not in (int,float) or isinstance(v,bool) or not math.isfinite(v) or v<=9.0:errors.append(d+" not strictly above 9")
  result={"task_id":"T10","review_kind":"FINAL_RUNNER_SOURCE_REVIEW","base":BASE,"source":SOURCE,"prepared_authority_sha256":AUTH_SHA,"review":row,"passed":not errors,"errors":errors,"lowest_score":min(scores.values()) if scores else 0,"provider":manifest.get("publisher"),"model":manifest.get("base_model"),"model_revision":manifest.get("revision"),"runtime_release":manifest.get("runtime_release"),"non_voting":True,"task_approved":False,"t11_unlocked":False}
  write(out/"result.json",result);print(json.dumps(result,indent=2));return 0 if not errors else 1
 finally:
  proc.terminate()
  try:proc.wait(timeout=10)
  except Exception:proc.kill()
  log.close()
def main():
 p=argparse.ArgumentParser();p.add_argument("--mode",choices=["preflight","review"],required=True);p.add_argument("--repo",required=True);p.add_argument("--out",required=True);a=p.parse_args()
 if a.mode=="preflight":print(json.dumps(preflight(a.repo,a.out),indent=2));return 0
 return review(a.repo,a.out)
if __name__=="__main__":raise SystemExit(main())
