#!/usr/bin/env python3
"""Promote the independently reviewed T10 bookkeeping-only correction.

Never approves T10; final gameplay critics/gates remain mandatory.
"""
from __future__ import annotations
import argparse,hashlib,json,os,pathlib,re,subprocess,tempfile,zipfile

TASK="T10";BRANCH="codex/havenline-sequential-task-01"
R="fc9010daebf6b4d520333279486a1b6bea164e7c";R_TREE="dad82b4136efa814f2a4328ef50f6a225899d61c"
OLD_H="249b61b02db28f694291dda8c1019c2514e991bf"
PLAN="Docs/Production/T10/REPAIR_PLAN.json";C0="Docs/Production/T10/C0_ROOT_CAUSE.json";C0R="Docs/Production/T10/C0R_REPAIR_SUFFICIENCY.json"
RECORD="Docs/Production/ChangeRequests/T10-repeated-python-source-review.json";VERIFIER="tools/havenline/production/verify_python_repair_bindings.py"
INHERITED=["Docs/Production/ChangeRequests/T10-benchmark-liveness-contract.json","Docs/Production/ChangeRequests/T10-c0-decoded-complete-evidence.json","Docs/Production/ChangeRequests/T10-c0r-structured-mechanism-detection.json",RECORD]

def run(*args,cwd=None,input=None,env=None):return subprocess.check_output(["git",*args],cwd=cwd,input=input,env=env,stderr=subprocess.PIPE)
def show(ref,path):return run("show",f"{ref}:{path}")
def sha(b):return hashlib.sha256(b).hexdigest()
def stable(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def mode(ref,path):
 raw=run("ls-tree",ref,"--",path).decode().strip()
 if not raw:raise ValueError("missing "+path)
 return raw.split()[0]
def write(path,obj):p=pathlib.Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2)+"\n")
def tip():
 rows=run("ls-remote","--exit-code","origin","refs/heads/"+BRANCH).decode().splitlines()
 if len(rows)!=1:raise ValueError("ambiguous canonical")
 h,ref=rows[0].split("\t",1)
 if ref!="refs/heads/"+BRANCH or re.fullmatch(r"[0-9a-f]{40}",h) is None:raise ValueError("bad canonical response")
 return h

def review_from_zip(path):
 raw=pathlib.Path(path).read_bytes()
 with zipfile.ZipFile(path) as z:
  names=[n for n in z.namelist() if n.endswith("bookkeeping-critic/result.json")]
  if len(names)!=1:raise ValueError("bookkeeping result missing/duplicate")
  row=json.loads(z.read(names[0]))
 if row.get("source")!=R or row.get("base")!=OLD_H or row.get("passed") is not True or row.get("task_approved") is not False or row.get("t11_unlocked") is not False:
  raise ValueError("review identity/status mismatch")
 review=row.get("review",{})
 if review.get("defects")!=[] or review.get("coverage_complete") is not True or review.get("confidence") not in ("medium","high"):raise ValueError("review unresolved")
 scores=review.get("scores",{})
 if not scores or any(type(v) not in (int,float) or isinstance(v,bool) or v<=9.0 for v in scores.values()):raise ValueError("review score gate failed")
 return row,{"archive_sha256":sha(raw),"result_sha256":stable(row),"lowest_score":min(scores.values())}

def bindings(plan):
 rows=[]
 for group in plan.get("repair_sufficiency",{}).get("repair_groups",[]):
  if not isinstance(group,dict) or not isinstance(group.get("same_family_attempt_count"),int) or group["same_family_attempt_count"]<2:continue
  contract=group.get("implementation_diff_contract",{})
  for path in contract.get("causal_files",[]):
   if isinstance(path,str) and path.endswith(".py"):
    base=contract["comparison_base"]
    rows.append({"group_id":group.get("group_id"),"failure_family_id":group.get("failure_family",{}).get("id"),"comparison_base":base,"path":path,"operation_contract_sha256":stable(group),"before_sha256":sha(show(base,path)),"after_sha256":sha(show(R,path)),"before_mode":mode(base,path),"after_mode":mode(R,path)})
 return rows

def record(review_meta):
 plan=json.loads(show(R,PLAN));rows=bindings(plan);prior_sha=sha(show(OLD_H,RECORD))
 evidence={"bookkeeping_review":review_meta,"prior_source_authority_sha256":prior_sha,"prior_candidate":OLD_H,"scope":"Two-file bookkeeping classification correction only; all gameplay/runtime/test bytes unchanged."}
 return {"schema_version":1,"task_id":TASK,"diagnosis_id":plan["diagnosis_id"],"decision":"ACCEPTED_BOUNDED_SOURCE","non_voting":True,"task_approved":False,"thresholds_unchanged":True,"runtime_model_contracts_unchanged":True,"c0_sha256":sha(show(R,C0)),"canonical_inherited_paths":INHERITED,"independent_review":{"reviewer":"independent-final-bookkeeping-review","review_id":"T10-bookkeeping-"+R[:12],"reviewed_commit":R,"reviewed_tree":R_TREE,"evidence_sha256":stable(evidence),"score":review_meta["lowest_score"],"evidence":evidence},"bindings":rows,"causal_source_set_sha256":stable(rows),"authority_boundary":"Exact metadata-only reviewed source; owner must verify ordered [R,H] and use a non-forced canonical update. No T10 approval or T11 unlock."}

def commit(work,parents,msg):
 tree=run("write-tree",cwd=work).decode().strip();args=["commit-tree",tree]
 for p in parents:args+=["-p",p]
 env=dict(os.environ,GIT_AUTHOR_NAME="T10 Integration Owner",GIT_AUTHOR_EMAIL="t10-owner@example.invalid",GIT_COMMITTER_NAME="T10 Integration Owner",GIT_COMMITTER_EMAIL="t10-owner@example.invalid")
 return run(*args,cwd=work,input=(msg+"\n").encode(),env=env).decode().strip(),tree

def build_authority(rec,tmp):
 work=pathlib.Path(tmp)/"authority";subprocess.run(["git","worktree","add","--detach",str(work),OLD_H],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 write(work/RECORD,rec);subprocess.run(["git","add","--",RECORD],cwd=work,check=True)
 return commit(work,[OLD_H],"T10: install independently reviewed bookkeeping source authority\n\nMetadata-only authority. Gameplay bytes and acceptance thresholds unchanged; final critics remain mandatory.")

def candidate_plan(authority):
 plan=json.loads(show(R,PLAN));plan["reconciled_integration_head"]=authority
 plan["inherited_noncausal_files"]=list(dict.fromkeys(plan.get("inherited_noncausal_files",[])+INHERITED))
 for fix in plan.get("fixes",[]):fix["files"]=[p for p in fix.get("files",[]) if p not in INHERITED]
 return plan

def build_candidate(authority,tmp):
 work=pathlib.Path(tmp)/"candidate";subprocess.run(["git","worktree","add","--detach",str(work),R],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 for path in INHERITED:
  target=work/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(show(authority,path))
 plan=candidate_plan(authority);write(work/PLAN,plan)
 c0r=json.loads(show(R,C0R));c0r["input_bindings"]["plan_sha256"]=sha((work/PLAN).read_bytes());write(work/C0R,c0r)
 subprocess.run(["git","add","--"]+list(dict.fromkeys(INHERITED+[PLAN,C0R])),cwd=work,check=True)
 return (*commit(work,[R,authority],"T10: freeze final bookkeeping-corrected candidate\n\nOrdered [reviewed metadata source, canonical authority]. Gameplay bytes unchanged; final validation remains mandatory."),work)

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--review");ap.add_argument("--out",required=True);ap.add_argument("--preflight",action="store_true");a=ap.parse_args()
 out=pathlib.Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
 if run("rev-parse",R+"^{tree}").decode().strip()!=R_TREE:raise ValueError("R tree mismatch")
 if tip()!=OLD_H:raise ValueError("canonical not exact expected base")
 if a.preflight:
  meta={"archive_sha256":"0"*64,"result_sha256":"1"*64,"lowest_score":9.1};rec=record(meta)
 else:
  if not a.review:raise ValueError("--review required")
  _,meta=review_from_zip(a.review);rec=record(meta)
 with tempfile.TemporaryDirectory(prefix="t10-bookkeeping-promotion-") as tmp:
  h,h_tree=build_authority(rec,tmp);p,p_tree,work=build_candidate(h,tmp)
  parents=run("rev-list","--parents","-n","1",p).decode().strip().split()[1:]
  if parents!=[R,h]:raise ValueError("parent topology mismatch")
  product="HavenlineGodot/scripts/world_transform_view.gd"
  if show(p,product)!=show(OLD_H,product) or sha(show(p,product))!="fc35ebc4bc59dd41e165f6eb8d091ed274c1f02a5fe48e56cf8c9d15b8970b75":raise ValueError("gameplay product changed")
  plan=json.loads(show(p,PLAN));inh=set(plan["inherited_noncausal_files"]);causal={q for f in plan["fixes"] for q in f["files"]}
  if inh & causal:raise ValueError("causal/noncausal overlap in candidate")
  info={"reviewed":R,"authority":h,"authority_tree":h_tree,"candidate":p,"candidate_tree":p_tree,"parents":parents,"product_unchanged":True,"task_approved":False,"t11_unlocked":False}
  write(out/"prepublication.json",info)
  if a.preflight:print(json.dumps(info));return
  if tip()!=OLD_H:raise ValueError("canonical moved before authority")
  subprocess.run(["git","push","--porcelain","origin",f"{h}:refs/heads/{BRANCH}"],check=True,stdout=(out/"authority-push.log").open("w"),stderr=subprocess.STDOUT)
  if tip()!=h:raise ValueError("authority push mismatch")
  subprocess.run(["git","fetch","--no-tags","origin",f"+refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}"],cwd=work,check=True)
  vo=(out/"owner-verifier.json");vl=(out/"owner-verifier.log")
  subprocess.run(["python3","-I",VERIFIER,"--repo",".","--canonical-head",h,"--candidate",p,"--task",TASK,"--output",str(vo),"--promotion-check"],cwd=work,check=True,stdout=vl.open("w"),stderr=subprocess.STDOUT)
  if json.loads(vo.read_text()).get("passed") is not True:raise ValueError("owner verifier red")
  if tip()!=h:raise ValueError("canonical moved after verification")
  subprocess.run(["git","push","--porcelain","origin",f"{p}:refs/heads/{BRANCH}"],check=True,stdout=(out/"candidate-push.log").open("w"),stderr=subprocess.STDOUT)
  if tip()!=p:raise ValueError("candidate push mismatch")
  info.update({"canonical_after":p,"owner_verifier_passed":True,"next_required":"fresh complete T10 gates/critics"})
  write(out/"promotion-result.json",info);print(json.dumps(info))
if __name__=="__main__":main()
