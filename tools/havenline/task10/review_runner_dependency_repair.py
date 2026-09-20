#!/usr/bin/env python3
"""Review the exact T10 workflow runner dependency repair; never approves gameplay."""
from __future__ import annotations
import argparse,hashlib,json,math,os,pathlib,re,subprocess,time,urllib.request

B="90f1d56e8781f4998b00b9563f0f9d49458ebf53"
R="69e13b80540b520f252b4ac959ea374cea9bed85"
PATHS=[".github/workflows/havenline-task10-isolated.yml",".github/workflows/havenline-task10-world-transformation.yml"]
INSTALL="python3 -m pip install --disable-pip-version-check --no-input numpy==2.3.5 pillow==12.3.0"
PRODUCT=[
"HavenlineGodot/scripts/world_transform.gd","HavenlineGodot/scripts/world_transform_view.gd",
"HavenlineGodot/data/world_transform_recipes.json","HavenlineGodot/tests/test_task10_world_transform.gd",
"HavenlineGodot/tests/test_task10_integration.gd","HavenlineGodot/tests/capture_task10_world_transform.gd",
"tools/havenline/task10/benchmark_world_transform.gd","Docs/Production/CRITIC_MATRIX.json",
"Docs/Production/CRITIC_EXECUTION.json","Docs/Production/task-gates.json",
]
DIMS=["runner_dependency_correctness","root_cause_closure","gameplay_immutability","acceptance_preservation","source_binding"]
def run(repo,*args,**kw):return subprocess.check_output(list(args),cwd=repo,stderr=subprocess.STDOUT,**kw)
def git(repo,*args,text=False):return subprocess.check_output(["git",*args],cwd=repo,text=text,stderr=subprocess.PIPE)
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,v):p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+"\n")
def preflight(repo,out):
 repo=pathlib.Path(repo);out=pathlib.Path(out);out.mkdir(parents=True,exist_ok=True)
 if git(repo,"rev-parse","HEAD",text=True).strip()!=R:raise ValueError("wrong reviewed source")
 changed=git(repo,"diff","--name-only",B,R,text=True).splitlines()
 if changed!=PATHS:raise ValueError("unexpected changed paths "+repr(changed))
 diff=git(repo,"diff","--unified=20",B,R,"--",*PATHS,text=True)
 texts={p:(repo/p).read_text() for p in PATHS}
 for p,t in texts.items():
  if t.count(INSTALL)!=1:raise ValueError("exact pinned dependency install missing/duplicate: "+p)
  pos=t.index(INSTALL);prod=t.index("python3 -m unittest discover -s tools/havenline/production/tests")
  task=t.index("python3 -m unittest discover -s tools/havenline/task10/tests")
  if not(pos<prod<task):raise ValueError("dependency install does not precede tooling tests: "+p)
 if "python3 -m pip install numpy==2.3.5" in texts[PATHS[1]]:raise ValueError("stale late NumPy install remains")
 hashes={}
 for p in PRODUCT:
  before=git(repo,"show",B+":"+p);after=(repo/p).read_bytes()
  if before!=after:raise ValueError("protected product/acceptance byte changed: "+p)
  hashes[p]=sha(after)
 subprocess.run(["python3","-m","pip","install","--disable-pip-version-check","--no-input","numpy==2.3.5","pillow==12.3.0"],cwd=repo,check=True,stdout=(out/"pip.log").open("w"),stderr=subprocess.STDOUT,timeout=240)
 suites=[]
 for label,cmd in [
  ("production",["python3","-m","unittest","discover","-s","tools/havenline/production/tests","-p","test_*.py","-v"]),
  ("task10",["python3","-m","unittest","discover","-s","tools/havenline/task10/tests","-p","test_*.py","-v"]),
 ]:
  path=out/(label+".log")
  with path.open("w") as h:r=subprocess.run(cmd,cwd=repo,stdout=h,stderr=subprocess.STDOUT,timeout=900)
  text=path.read_text(errors="replace");m=re.search(r"Ran (\d+) tests?",text)
  suites.append({"suite":label,"exit_code":r.returncode,"tests":int(m.group(1)) if m else None,"passed":r.returncode==0,"log_sha256":sha(path.read_bytes())})
 if not all(x["passed"] for x in suites):raise ValueError("tooling suites still red: "+repr(suites))
 c0r=out/"c0r.json"
 subprocess.run(["python3","tools/havenline/production/repair_sufficiency_critic.py","--c0","Docs/Production/T10/C0_ROOT_CAUSE.json","--plan","Docs/Production/T10/REPAIR_PLAN.json","--output",str(c0r.resolve())],cwd=repo,check=True,stdout=(out/"c0r.log").open("w"),stderr=subprocess.STDOUT,timeout=180)
 c0r_obj=json.loads(c0r.read_text())
 if c0r_obj.get("passed") is not True:raise ValueError("C0R red")
 plan=json.loads((repo/"Docs/Production/T10/REPAIR_PLAN.json").read_text());repair_base=plan["repair_base"]
 env=dict(os.environ,INTEGRATION_BRANCH="codex/havenline-sequential-task-01",INTEGRATION_HEAD=B)
 gate=out/"builder-gate.json"
 proc=subprocess.run(["python3","tools/havenline/production/builder_repair_gate.py","--c0","Docs/Production/T10/C0_ROOT_CAUSE.json","--plan","Docs/Production/T10/REPAIR_PLAN.json","--base",repair_base,"--head",R,"--output",str(gate.resolve())],cwd=repo,env=env,stdout=(out/"builder-gate.log").open("w"),stderr=subprocess.STDOUT,timeout=240)
 gate_obj=json.loads(gate.read_text()) if gate.exists() else {}
 if proc.returncode!=0 or gate_obj.get("passed") is not True:raise ValueError("builder gate red: "+repr(gate_obj.get("errors")))
 result={"base":B,"source":R,"changed_paths":changed,"exact_diff":diff,"dependency_install":INSTALL,"tooling_suites":suites,"c0r_passed":True,"builder_gate_passed":True,"product_and_acceptance_bytes_unchanged":True,"protected_hashes":hashes,"thresholds_unchanged":True,"critic_contracts_unchanged":True,"task_approved":False,"t11_unlocked":False}
 write(out/"preflight.json",result);return result
def review(repo,out):
 out=pathlib.Path(out);pre=preflight(repo,out/"preflight")
 root=pathlib.Path.cwd();runtime=json.loads((root/"Docs/Production/CRITIC_EXECUTION.json").read_text())["local_independent_runtime"]
 cache=pathlib.Path(os.path.expanduser(runtime["cache_path"]));manifest=json.loads((cache/"manifest.json").read_text());servers=list((cache/"runtime").rglob("llama-server"))
 if len(servers)!=1:raise ValueError("pinned reviewer runtime missing/ambiguous")
 server=servers[0];env=dict(os.environ);env["LD_LIBRARY_PATH"]=str(server.parent)+":"+env.get("LD_LIBRARY_PATH","");out.mkdir(parents=True,exist_ok=True)
 log=(out/"runtime.log").open("w");proc=subprocess.Popen([str(server),"-m",str(cache/manifest["model_file"]),"--mmproj",str(cache/manifest["projector_file"]),"--host","127.0.0.1","--port","8080","-c","8192","-t","4","-tb","4","-ngl","0","--no-mmproj-offload","--parallel","1","--jinja","--image-min-tokens","768","--image-max-tokens","2048"],stdout=log,stderr=subprocess.STDOUT,env=env)
 try:
  for _ in range(180):
   if proc.poll() is not None:raise RuntimeError("review runtime exited")
   try:
    if json.load(urllib.request.urlopen("http://127.0.0.1:8080/health",timeout=3)).get("status")=="ok":break
   except Exception:time.sleep(2)
  else:raise RuntimeError("review runtime not ready")
  props={d:{"type":"number","minimum":0,"maximum":10} for d in DIMS}
  schema={"type":"object","properties":{"observations":{"type":"array","items":{"type":"string","maxLength":180},"minItems":3,"maxItems":4},"defects":{"type":"array","items":{"type":"string","maxLength":180},"maxItems":5},"coverage_complete":{"type":"boolean"},"confidence":{"type":"string","enum":["low","medium","high"]},"scores":{"type":"object","properties":props,"required":DIMS,"additionalProperties":False}},"required":["observations","defects","coverage_complete","confidence","scores"],"additionalProperties":False}
  prompt="""Independent non-voting T10 tooling repair review. Do not approve gameplay.
The exact frozen candidate failed both final workflows before engine/gameplay because task10 tooling tests imported numpy before workflow installation. Review the exact two-workflow repair below.
Required: dependency install must occur before both tooling suites; it must fix the observed missing numpy/Pillow environment without changing gameplay, tests, thresholds, benchmark code, or critic contracts. Deterministic preflight already reran production and T10 tooling suites and builder/C0R gates.
Final C1/C2/C3/C4/C6/C7, G1-G14, regression and closeout remain mandatory after this repair. Report any genuine defect. Every score must be strictly >9.0 to accept this tooling source.
Return JSON only.
EVIDENCE:
"""+json.dumps(pre,indent=2)
  body={"model":"havenline-specialist-local","messages":[{"role":"user","content":[{"type":"text","text":prompt}]}],"max_tokens":800,"temperature":0.2,"top_p":0.9,"seed":20260921,"chat_template_kwargs":{"enable_thinking":False},"response_format":{"type":"json_object","schema":schema},"cache_prompt":False}
  raw=json.dumps(body).encode();(out/"request.json").write_bytes(raw)
  req=urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions",data=raw,headers={"Content-Type":"application/json"},method="POST")
  with urllib.request.urlopen(req,timeout=1200) as resp:reply=json.load(resp)
  (out/"raw.json").write_text(json.dumps(reply,indent=2));choice=reply["choices"][0]
  if choice.get("finish_reason")!="stop":raise ValueError("incomplete reviewer output")
  row=json.loads(choice["message"]["content"]);errors=[]
  if row.get("coverage_complete") is not True:errors.append("coverage incomplete")
  if row.get("confidence") not in ("medium","high"):errors.append("confidence insufficient")
  if row.get("defects"):errors.append("unresolved defects")
  scores=row.get("scores",{})
  if set(scores)!=set(DIMS):errors.append("dimension mismatch")
  for d,v in scores.items():
   if type(v) not in (int,float) or isinstance(v,bool) or not math.isfinite(v) or v<=9.0:errors.append(d+" not strictly above 9")
  result={"task_id":"T10","review_kind":"RUNNER_DEPENDENCY_REPAIR","base":B,"source":R,"review":row,"passed":not errors,"errors":errors,"lowest_score":min(scores.values()) if scores else 0,"provider":manifest.get("publisher"),"model":manifest.get("base_model"),"model_revision":manifest.get("revision"),"non_voting":True,"task_approved":False,"t11_unlocked":False}
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
