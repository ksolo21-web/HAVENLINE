#!/usr/bin/env python3
"""Fail-closed T10 source-authority and exact [R,H] promotion.

This script never approves T10. It only installs independently reviewed source
authority and promotes the exact reviewed repair candidate for fresh final gates.
"""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, re, shutil, subprocess, tempfile, zipfile

TASK="T10"
BRANCH="codex/havenline-sequential-task-01"
R="06232b7c0e4cf8662f9b94d51bc93aa125fe2f20"
R_TREE="50d50cf0cbf45eb2d8f38590b91821d97cc83e1e"
EXPECTED_OLD_H="0b61aa5bd6a9e9cb3662412f9d0a7003d2bd5f00"
RECORD="Docs/Production/ChangeRequests/T10-repeated-python-source-review.json"
PLAN="Docs/Production/T10/REPAIR_PLAN.json"
C0="Docs/Production/T10/C0_ROOT_CAUSE.json"
C0R="Docs/Production/T10/C0R_REPAIR_SUFFICIENCY.json"
VERIFIER="tools/havenline/production/verify_python_repair_bindings.py"
INHERITED=[
 "Docs/Production/ChangeRequests/T10-benchmark-liveness-contract.json",
 "Docs/Production/ChangeRequests/T10-c0-decoded-complete-evidence.json",
 "Docs/Production/ChangeRequests/T10-c0r-structured-mechanism-detection.json",
 RECORD,
]

def run(*args,cwd=None,input=None,env=None):
 return subprocess.check_output(["git",*args],cwd=cwd,input=input,env=env,stderr=subprocess.PIPE)

def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def stable(v)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def show(ref,path)->bytes:return run("show",f"{ref}:{path}")
def mode(ref,path)->str:
 raw=run("ls-tree",ref,"--",path).decode().strip()
 if not raw:raise ValueError("missing source "+path)
 return raw.split()[0]
def write_json(path,obj):
 pathlib.Path(path).parent.mkdir(parents=True,exist_ok=True)
 pathlib.Path(path).write_text(json.dumps(obj,indent=2)+"\n")
def remote_tip()->str:
 raw=run("ls-remote","--exit-code","origin","refs/heads/"+BRANCH).decode().splitlines()
 if len(raw)!=1:raise ValueError("canonical remote response ambiguous")
 sha_value,ref=raw[0].split("\t",1)
 if ref!="refs/heads/"+BRANCH or re.fullmatch(r"[0-9a-f]{40}",sha_value) is None:raise ValueError("canonical remote response invalid")
 return sha_value

def zip_json(path,suffix,predicate=None):
 with zipfile.ZipFile(path) as z:
  names=[n for n in z.namelist() if n.endswith(suffix)]
  hits=[]
  for n in names:
   try:v=json.loads(z.read(n))
   except Exception:continue
   if predicate is None or predicate(v):hits.append((n,v))
  if len(hits)!=1:raise ValueError(f"expected one {suffix}, got {[x[0] for x in hits]}")
  return hits[0]

def validate_reviews(admission_zip,caller_zip):
 _,admission=zip_json(admission_zip,"owner-delta-reviews.json")
 if admission.get("source")!="2842845c4e4a9866d3bf7bb62a1beeabf58199c2" or admission.get("passed") is not True or admission.get("task_approved") is not False:
  raise ValueError("closeout admission not green")
 if set(admission.get("required_groups",[]))!={"assertions","authority","evidence"} or admission.get("errors")!=[]:
  raise ValueError("closeout admission coverage incomplete")
 _,caller=zip_json(caller_zip,"result.json",lambda v:v.get("group")=="callers")
 if caller.get("source")!=R or caller.get("tree")!=R_TREE or caller.get("passed") is not True or caller.get("task_approved") is not False or caller.get("non_voting") is not True:
  raise ValueError("integrated caller review not green for exact R")
 if caller.get("errors")!=[] or caller.get("review",{}).get("defects")!=[] or caller.get("review",{}).get("coverage_complete") is not True:
  raise ValueError("caller review unresolved")
 all_scores=[v for row in admission["groups"].values() for v in row["review"]["scores"].values()]
 all_scores += list(caller["review"]["scores"].values())
 if not all(type(v) in (int,float) and not isinstance(v,bool) and v>9.0 for v in all_scores):
  raise ValueError("source review score not strictly above 9")
 evidence={
  "admission_archive_sha256":sha(pathlib.Path(admission_zip).read_bytes()),
  "admission_result_sha256":stable(admission),
  "admission_lowest_score":min(v for row in admission["groups"].values() for v in row["review"]["scores"].values()),
  "caller_archive_sha256":sha(pathlib.Path(caller_zip).read_bytes()),
  "caller_result_sha256":stable(caller),
  "caller_lowest_score":min(caller["review"]["scores"].values()),
  "reviewed_commit":R,
  "reviewed_tree":R_TREE,
 }
 return evidence,min(all_scores)

def expected_python_bindings(plan):
 rows=[]
 for group in plan.get("repair_sufficiency",{}).get("repair_groups",[]):
  if not isinstance(group,dict) or not isinstance(group.get("same_family_attempt_count"),int) or group["same_family_attempt_count"]<2:continue
  contract=group.get("implementation_diff_contract",{})
  for path in contract.get("causal_files",[]):
   if isinstance(path,str) and path.endswith(".py"):
    base=contract["comparison_base"]
    rows.append({
     "group_id":group.get("group_id"),
     "failure_family_id":group.get("failure_family",{}).get("id"),
     "comparison_base":base,
     "path":path,
     "operation_contract_sha256":stable(group),
     "before_sha256":sha(show(base,path)),
     "after_sha256":sha(show(R,path)),
     "before_mode":mode(base,path),
     "after_mode":mode(R,path),
    })
 return rows

def build_record(evidence,lowest):
 c0_raw=show(R,C0);plan=json.loads(show(R,PLAN))
 rows=expected_python_bindings(plan)
 return {
  "schema_version":1,"task_id":TASK,"diagnosis_id":plan["diagnosis_id"],
  "decision":"ACCEPTED_BOUNDED_SOURCE","non_voting":True,"task_approved":False,
  "thresholds_unchanged":True,"runtime_model_contracts_unchanged":True,
  "c0_sha256":sha(c0_raw),
  "canonical_inherited_paths":INHERITED,
  "independent_review":{
   "reviewer":"independent-closeout-admission-and-integrated-caller-review",
   "review_id":"T10-final-source-authority-"+R[:12],
   "reviewed_commit":R,"reviewed_tree":R_TREE,
   "evidence_sha256":stable(evidence),
   "score":lowest,
   "evidence":evidence,
  },
  "bindings":rows,
  "causal_source_set_sha256":stable(rows),
  "authority_boundary":"Owner verifies exact ordered [R,H] promotion using the unchanged canonical verifier with --promotion-check and a non-forced update. This source record is non-voting and cannot approve T10 or unlock T11."
 }

def copy_ref(ref,path,dest_root):
 data=show(ref,path);target=pathlib.Path(dest_root)/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)

def commit_tree(worktree,parents,message):
 tree=run("write-tree",cwd=worktree).decode().strip()
 env=dict(os.environ,GIT_AUTHOR_NAME="T10 Integration Owner",GIT_AUTHOR_EMAIL="t10-owner@example.invalid",GIT_COMMITTER_NAME="T10 Integration Owner",GIT_COMMITTER_EMAIL="t10-owner@example.invalid")
 args=["commit-tree",tree]
 for p in parents:args += ["-p",p]
 commit=run(*args,cwd=worktree,input=(message+"\n").encode(),env=env).decode().strip()
 return commit,tree

def build_authority(old_h,record,tmp):
 authority=pathlib.Path(tmp)/"authority"
 subprocess.run(["git","worktree","add","--detach",str(authority),old_h],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 for p in INHERITED[:-1]:copy_ref(R,p,authority)
 write_json(authority/RECORD,record)
 subprocess.run(["git","add","--"]+INHERITED,cwd=authority,check=True)
 return commit_tree(authority,[old_h],"T10: install independently reviewed final source authority\n\nMetadata-only authority for exact reviewed source "+R+". No gameplay approval; final C1/C2/C3/C4/C6/C7, G1-G14, regression and integrated closeout remain mandatory.")

def reconciled_plan(authority):
 plan=json.loads(show(R,PLAN))
 plan["reconciled_integration_head"]=authority
 plan["inherited_noncausal_files"]=list(dict.fromkeys(plan.get("inherited_noncausal_files",[])+INHERITED))
 for fix in plan.get("fixes",[]):
  fix["files"]=[p for p in fix.get("files",[]) if p not in INHERITED]
 return plan

def build_candidate(authority,tmp):
 candidate=pathlib.Path(tmp)/"candidate"
 subprocess.run(["git","worktree","add","--detach",str(candidate),R],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 for p in INHERITED:copy_ref(authority,p,candidate)
 plan=reconciled_plan(authority);write_json(candidate/PLAN,plan)
 plan_raw=(candidate/PLAN).read_bytes()
 c0r=json.loads(show(R,C0R));c0r["input_bindings"]["plan_sha256"]=sha(plan_raw);write_json(candidate/C0R,c0r)
 paths=list(dict.fromkeys(INHERITED+[PLAN,C0R]))
 subprocess.run(["git","add","--"]+paths,cwd=candidate,check=True)
 commit,tree=commit_tree(candidate,[R,authority],"T10: freeze exact final reviewed repair candidate\n\nOrdered parents are reviewed source R then canonical authority H. No approval claim; this candidate must pass all fresh final gates.")
 return commit,tree,candidate

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--admission",required=True);ap.add_argument("--caller",required=True);ap.add_argument("--out",required=True);a=ap.parse_args()
 out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
 if run("rev-parse",R+"^{tree}").decode().strip()!=R_TREE:raise ValueError("reviewed tree mismatch")
 current=remote_tip()
 if current!=EXPECTED_OLD_H:raise ValueError("canonical moved before authority publication: "+current)
 evidence,lowest=validate_reviews(a.admission,a.caller)
 record=build_record(evidence,lowest)
 with tempfile.TemporaryDirectory(prefix="t10-promotion-") as tmp:
  h2,h2_tree=build_authority(current,record,tmp)
  p,p_tree,candidate=build_candidate(h2,tmp)
  # Pre-publication structural checks. No remote mutation has occurred yet.
  parents=run("rev-list","--parents","-n","1",p).decode().strip().split()[1:]
  if parents!=[R,h2]:raise ValueError("candidate parent order invalid")
  if show(p,VERIFIER)!=show(h2,VERIFIER):raise ValueError("candidate verifier differs from authority")
  for path in INHERITED:
   if show(p,path)!=show(h2,path):raise ValueError("candidate inherited bytes mismatch: "+path)
  plan=json.loads(show(p,PLAN));c0r=json.loads(show(p,C0R))
  if plan["reconciled_integration_head"]!=h2 or c0r["input_bindings"]["plan_sha256"]!=sha(show(p,PLAN)):raise ValueError("candidate reconciliation binding invalid")
  write_json(out/"prepublication.json",{"reviewed_source":R,"reviewed_tree":R_TREE,"old_canonical":current,"authority":h2,"authority_tree":h2_tree,"candidate":p,"candidate_tree":p_tree,"parents":parents,"source_review_lowest_score":lowest,"task_approved":False,"t11_unlocked":False})
  # Publish authority metadata only, forward-only, after all independent source reviews.
  if remote_tip()!=current:raise ValueError("canonical advanced before authority push")
  subprocess.run(["git","push","--porcelain","origin",f"{h2}:refs/heads/{BRANCH}"],check=True,stdout=(out/"authority-push.log").open("w"),stderr=subprocess.STDOUT)
  run("fetch","--no-tags","origin",BRANCH)
  if remote_tip()!=h2:raise ValueError("authority publication did not land exactly")
  # Verify exact P using canonical authority bytes and live remote H.
  verifier_out=out/"owner-verifier.json"
  subprocess.run(["python3","-I",VERIFIER,"--repo",".","--canonical-head",h2,"--candidate",p,"--task",TASK,"--output",str(verifier_out),"--promotion-check"],cwd=candidate,check=True,stdout=(out/"owner-verifier.log").open("w"),stderr=subprocess.STDOUT)
  verdict=json.loads(verifier_out.read_text())
  if verdict.get("passed") is not True:raise ValueError("owner verifier did not pass")
  if remote_tip()!=h2:raise ValueError("canonical advanced after verification")
  subprocess.run(["git","push","--porcelain","origin",f"{p}:refs/heads/{BRANCH}"],check=True,stdout=(out/"candidate-push.log").open("w"),stderr=subprocess.STDOUT)
  final=remote_tip()
  if final!=p:raise ValueError("exact candidate publication failed")
  write_json(out/"promotion-result.json",{"task":"T10","reviewed_source":R,"authority":h2,"candidate":p,"candidate_tree":p_tree,"parents":[R,h2],"canonical_before":current,"canonical_after":final,"owner_verifier_passed":True,"source_review_lowest_score":lowest,"task_approved":False,"t11_unlocked":False,"next_required":"fresh C1/C2/C3/C4/C6/C7 + G1-G14 + regression + integrated-source closeout"})
  print(json.dumps({"authority":h2,"candidate":p,"canonical_after":final,"task_approved":False}))
if __name__=="__main__":main()
