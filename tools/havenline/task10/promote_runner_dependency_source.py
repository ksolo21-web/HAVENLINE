#!/usr/bin/env python3
"""Fail-closed promotion of independently reviewed T10 final runner source."""
from __future__ import annotations
import argparse,hashlib,json,os,pathlib,re,subprocess,tempfile,zipfile

TASK="T10";BRANCH="codex/havenline-sequential-task-01"
C="90f1d56e8781f4998b00b9563f0f9d49458ebf53"
R="5484a8c3d47ffb0d895b379aeb267f190f3ff577";R_TREE="27eb21aaa4ef19375e7562d223d19f6b9af169a2"
AUTH_PREP="621f22c6682837c9b01a352d7e2feba46e258aa1"
AUTH_PATH="Docs/Production/ChangeRequests/T10-benchmark-liveness-contract.json"
AUTH_SHA="ac4a2f46743940a58fcd675623611b1fe9052ed615fcd7ab2fcba478a5822dec"
RECORD="Docs/Production/ChangeRequests/T10-repeated-python-source-review.json"
PLAN="Docs/Production/T10/REPAIR_PLAN.json";C0="Docs/Production/T10/C0_ROOT_CAUSE.json";C0R="Docs/Production/T10/C0R_REPAIR_SUFFICIENCY.json"
VERIFIER="tools/havenline/production/verify_python_repair_bindings.py"
INHERITED=[AUTH_PATH,"Docs/Production/ChangeRequests/T10-c0-decoded-complete-evidence.json","Docs/Production/ChangeRequests/T10-c0r-structured-mechanism-detection.json",RECORD]

def run(*args,cwd=None,input=None,env=None):return subprocess.check_output(["git",*args],cwd=cwd,input=input,env=env,stderr=subprocess.PIPE)
def sha(b):return hashlib.sha256(b).hexdigest()
def stable(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def show(ref,path):return run("show",f"{ref}:{path}")
def mode(ref,path):
 raw=run("ls-tree",ref,"--",path).decode().strip()
 if not raw:raise ValueError("missing "+path)
 return raw.split()[0]
def write(path,obj):p=pathlib.Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2)+"\n")
def remote():
 rows=run("ls-remote","--exit-code","origin","refs/heads/"+BRANCH).decode().splitlines()
 if len(rows)!=1:raise ValueError("canonical remote ambiguous")
 s,r=rows[0].split("\t",1)
 if r!="refs/heads/"+BRANCH or re.fullmatch("[0-9a-f]{40}",s) is None:raise ValueError("canonical response invalid")
 return s
def review_zip(path):
 with zipfile.ZipFile(path) as z:
  hits=[]
  for n in z.namelist():
   if not n.endswith("result.json"):continue
   try:v=json.loads(z.read(n))
   except Exception:continue
   if v.get("review_kind")=="FINAL_RUNNER_SOURCE_REVIEW":hits.append(v)
 if len(hits)!=1:raise ValueError("exact runner review result missing/duplicate")
 r=hits[0]
 if r.get("source")!=R or r.get("base")!=C or r.get("prepared_authority_sha256")!=AUTH_SHA or r.get("passed") is not True or r.get("errors")!=[] or r.get("non_voting") is not True or r.get("task_approved") is not False:raise ValueError("runner review identity/disposition invalid")
 rev=r.get("review",{})
 if rev.get("coverage_complete") is not True or rev.get("defects")!=[]:raise ValueError("runner review unresolved")
 scores=rev.get("scores",{})
 if not scores or any(type(v) not in (int,float) or isinstance(v,bool) or v<=9.0 for v in scores.values()):raise ValueError("runner review score not strictly >9")
 return r
def bindings(plan):
 rows=[]
 for g in plan.get("repair_sufficiency",{}).get("repair_groups",[]):
  if not isinstance(g.get("same_family_attempt_count"),int) or g["same_family_attempt_count"]<2:continue
  contract=g.get("implementation_diff_contract",{})
  for p in contract.get("causal_files",[]):
   if isinstance(p,str) and p.endswith(".py"):
    b=contract["comparison_base"]
    rows.append({"group_id":g.get("group_id"),"failure_family_id":g.get("failure_family",{}).get("id"),"comparison_base":b,"path":p,"operation_contract_sha256":stable(g),"before_sha256":sha(show(b,p)),"after_sha256":sha(show(R,p)),"before_mode":mode(b,p),"after_mode":mode(R,p)})
 return rows
def source_record(review,review_archive):
 plan=json.loads(show(R,PLAN));rows=bindings(plan);evidence={"review_archive_sha256":sha(pathlib.Path(review_archive).read_bytes()),"review_result_sha256":stable(review),"lowest_score":min(review["review"]["scores"].values()),"reviewed_commit":R,"reviewed_tree":R_TREE,"prepared_benchmark_authority_sha256":AUTH_SHA}
 return {"schema_version":1,"task_id":TASK,"diagnosis_id":plan["diagnosis_id"],"decision":"ACCEPTED_BOUNDED_SOURCE","non_voting":True,"task_approved":False,"thresholds_unchanged":True,"runtime_model_contracts_unchanged":True,"c0_sha256":sha(show(R,C0)),"canonical_inherited_paths":INHERITED,"independent_review":{"reviewer":"independent-final-runner-source-review","review_id":"T10-runner-"+R[:12],"reviewed_commit":R,"reviewed_tree":R_TREE,"evidence_sha256":stable(evidence),"score":evidence["lowest_score"],"evidence":evidence},"bindings":rows,"causal_source_set_sha256":stable(rows),"authority_boundary":"Benchmark authorization and repeated-Python source review remain a separate metadata-only authority parent. Owner must verify exact ordered [R,H] and publish non-forced. No T10 approval or T11 unlock."}
def copy(ref,path,dest):
 t=pathlib.Path(dest)/path;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(show(ref,path))
def commit_tree(wt,parents,msg):
 tree=run("write-tree",cwd=wt).decode().strip();env=dict(os.environ,GIT_AUTHOR_NAME="T10 Integration Owner",GIT_AUTHOR_EMAIL="t10-owner@example.invalid",GIT_COMMITTER_NAME="T10 Integration Owner",GIT_COMMITTER_EMAIL="t10-owner@example.invalid");args=["commit-tree",tree]
 for p in parents:args+=["-p",p]
 return run(*args,cwd=wt,input=(msg+"\n").encode(),env=env).decode().strip(),tree
def authority(record,tmp):
 wt=pathlib.Path(tmp)/"authority";subprocess.run(["git","worktree","add","--detach",str(wt),C],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 auth=show(AUTH_PREP,AUTH_PATH)
 if sha(auth)!=AUTH_SHA:raise ValueError("prepared benchmark authority changed")
 (wt/AUTH_PATH).write_bytes(auth);write(wt/RECORD,record)
 subprocess.run(["git","add","--",AUTH_PATH,RECORD],cwd=wt,check=True)
 return (*commit_tree(wt,[C],"T10: install reviewed runner-source authority\n\nMetadata-only benchmark/source authority for exact runner repair "+R+". Final six critics and closeout remain mandatory."),wt)
def candidate(h,tmp):
 wt=pathlib.Path(tmp)/"candidate";subprocess.run(["git","worktree","add","--detach",str(wt),R],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 for p in INHERITED:copy(h,p,wt)
 plan=json.loads(show(R,PLAN));plan["reconciled_integration_head"]=h;plan["inherited_noncausal_files"]=list(dict.fromkeys(plan.get("inherited_noncausal_files",[])+INHERITED));write(wt/PLAN,plan)
 c0r=json.loads(show(R,C0R));c0r["input_bindings"]["plan_sha256"]=sha((wt/PLAN).read_bytes());write(wt/C0R,c0r)
 subprocess.run(["git","add","--"]+INHERITED+[PLAN,C0R],cwd=wt,check=True)
 p,tree=commit_tree(wt,[R,h],"T10: freeze final runner-corrected candidate\n\nOrdered parents [reviewed runner source R, metadata authority H]. No approval claim.")
 return p,tree,wt
def verify_candidate(h,p,wt,out):
 parents=run("rev-list","--parents","-n","1",p).decode().strip().split()[1:]
 if parents!=[R,h]:raise ValueError("candidate parent order invalid")
 for path in INHERITED:
  if show(p,path)!=show(h,path):raise ValueError("inherited authority mismatch "+path)
 plan=json.loads(show(p,PLAN));c0r=json.loads(show(p,C0R))
 if plan.get("reconciled_integration_head")!=h or c0r["input_bindings"]["plan_sha256"]!=sha(show(p,PLAN)):raise ValueError("candidate reconciliation binding invalid")
 # Deterministic C0R must remain byte-semantically equal aside from expected input plan binding.
 rec=pathlib.Path(out)/"recomputed-c0r.json"
 with (pathlib.Path(out)/"c0r.log").open("w") as log:subprocess.run(["python3","tools/havenline/production/repair_sufficiency_critic.py","--c0",C0,"--plan",PLAN,"--output",str(rec.resolve())],cwd=wt,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
 if json.loads(rec.read_text())!=json.loads((wt/C0R).read_text()):raise ValueError("candidate C0R differs from deterministic recomputation")
 vo=(pathlib.Path(out)/"owner-verifier.json").resolve()
 with (pathlib.Path(out)/"owner-verifier.log").open("w") as log:subprocess.run(["python3","-I",VERIFIER,"--repo",".","--canonical-head",h,"--candidate",p,"--task",TASK,"--output",str(vo),"--promotion-check"],cwd=wt,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=240)
 if json.loads(vo.read_text()).get("passed") is not True:raise ValueError("owner source verifier red")
 # Full Python suites on exact final candidate with required runner dependencies.
 subprocess.run(["python3","-m","pip","install","--disable-pip-version-check","--no-input","numpy==2.3.5","pillow==12.3.0"],cwd=wt,check=True,stdout=(pathlib.Path(out)/"pip.log").open("w"),stderr=subprocess.STDOUT,timeout=240)
 for label,cmd in [("production",["python3","-m","unittest","discover","-s","tools/havenline/production/tests","-p","test_*.py","-v"]),("task10",["python3","-m","unittest","discover","-s","tools/havenline/task10/tests","-p","test_*.py","-v"])]:
  with (pathlib.Path(out)/(label+".log")).open("w") as log:r=subprocess.run(cmd,cwd=wt,stdout=log,stderr=subprocess.STDOUT,timeout=1000)
  if r.returncode!=0:raise ValueError(label+" final candidate suite red")
 env=dict(os.environ,INTEGRATION_BRANCH=BRANCH,INTEGRATION_HEAD=h)
 gate=(pathlib.Path(out)/"builder-gate.json").resolve()
 with (pathlib.Path(out)/"builder-gate.log").open("w") as log:r=subprocess.run(["python3","tools/havenline/production/builder_repair_gate.py","--c0",C0,"--plan",PLAN,"--base",json.loads((wt/PLAN).read_text())["repair_base"],"--head",p,"--output",str(gate)],cwd=wt,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=300)
 if r.returncode!=0 or json.loads(gate.read_text()).get("passed") is not True:raise ValueError("final builder gate red")
 return parents
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--review",required=True);ap.add_argument("--out",required=True);ap.add_argument("--preflight",action="store_true");a=ap.parse_args();out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
 if run("rev-parse",R+"^{tree}").decode().strip()!=R_TREE:raise ValueError("reviewed source tree changed")
 rv=review_zip(a.review);record=source_record(rv,a.review)
 if remote()!=C:raise ValueError("canonical moved before runner promotion")
 with tempfile.TemporaryDirectory(prefix="t10-runner-promotion-") as tmp:
  h,htree,_=authority(record,tmp);p,ptree,wt=candidate(h,tmp);parents=verify_candidate(h,p,wt,out)
  write(out/"prepublication.json",{"canonical_before":C,"reviewed_source":R,"authority":h,"authority_tree":htree,"candidate":p,"candidate_tree":ptree,"parents":parents,"review_lowest_score":min(rv["review"]["scores"].values()),"task_approved":False,"t11_unlocked":False})
  if a.preflight:
   print(json.dumps({"passed":True,"authority":h,"candidate":p,"canonical_mutated":False,"task_approved":False}));return
  if remote()!=C:raise ValueError("canonical moved before authority push")
  subprocess.run(["git","push","--porcelain","origin",f"{h}:refs/heads/{BRANCH}"],check=True,stdout=(out/"authority-push.log").open("w"),stderr=subprocess.STDOUT)
  if remote()!=h:raise ValueError("authority push mismatch")
  # Re-run source verifier/builder gate against the now-live authority.
  run("fetch","--no-tags","origin",f"+refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}")
  verify_candidate(h,p,wt,out/"post-authority")
  if remote()!=h:raise ValueError("canonical moved after authority verification")
  subprocess.run(["git","push","--porcelain","origin",f"{p}:refs/heads/{BRANCH}"],check=True,stdout=(out/"candidate-push.log").open("w"),stderr=subprocess.STDOUT)
  if remote()!=p:raise ValueError("candidate push mismatch")
  write(out/"promotion-result.json",{"task":"T10","canonical_before":C,"authority":h,"candidate":p,"canonical_after":p,"parents":[R,h],"owner_verifier_passed":True,"builder_gate_passed":True,"python_suites_passed":True,"task_approved":False,"t11_unlocked":False,"next_required":"fresh final pipelines and all six critics"})
  print(json.dumps({"candidate":p,"canonical_after":p,"task_approved":False}))
if __name__=="__main__":main()
