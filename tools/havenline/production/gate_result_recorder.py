#!/usr/bin/env python3
from __future__ import annotations
import argparse,datetime,hashlib,json,re,subprocess
from pathlib import Path
from forward_execution import DOCS,ROOT
from gate_fingerprint import INDEX,fingerprint,validate_policy

OWNER_DISPOSITION="PROMOTE_VERIFIED_GATE_PASS"
SHA40=re.compile(r"^[0-9a-f]{40}$")
SHA64=re.compile(r"^[0-9a-f]{64}$")

def _load(path): return json.loads(Path(path).read_text())
def _sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()
def _git_commit(sha):
    if not SHA40.fullmatch(str(sha or "")):return False
    return subprocess.run(["git","cat-file","-e",f"{sha}^{{commit}}"],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
def _evidence_path(value):
    p=Path(value)
    if not p.is_absolute():p=ROOT/p
    p=p.resolve()
    if ROOT.resolve()!=p and ROOT.resolve() not in p.parents:raise ValueError("evidence must be inside repository")
    if not p.is_file():raise ValueError("evidence file missing")
    return p

def proposal(task_id,gate,candidate,evidence,workflow_run_id=None,workflow_job_id=None):
    task_id=task_id.upper()
    if not _git_commit(candidate):raise ValueError("candidate must be an available exact commit")
    fp=fingerprint(task_id,gate,candidate);path=_evidence_path(evidence)
    env=fp["environment"];promotion_eligible=not fp["environment_sensitive"] or bool(env.get("complete"))
    row={
      "schema_version":1,"record_type":"gate_pass_proposal","task_id":task_id,"gate":gate,"candidate":candidate,
      "result":"PASS","fingerprint":fp["fingerprint"],"reuse_class":fp["reuse_class"],
      "environment_sensitive":fp["environment_sensitive"],"environment_fingerprint":env.get("fingerprint") if env.get("complete") else None,
      "evidence":{"path":str(path.relative_to(ROOT)),"sha256":_sha(path)},
      "workflow_run_id":int(workflow_run_id) if workflow_run_id else None,
      "workflow_job_id":int(workflow_job_id) if workflow_job_id else None,
      "recorded_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
      "promotion_eligible":promotion_eligible,
      "integration_owner_promotion_required":True,
      "approval_authority_granted":False,
      "quality_thresholds_unchanged":True
    }
    row["proposal_id"]="GATE-"+hashlib.sha256(json.dumps({k:row[k] for k in ("task_id","gate","candidate","fingerprint","evidence")},sort_keys=True).encode()).hexdigest()[:16]
    return row

def validate_proposal(row):
    errors=[]
    if row.get("schema_version")!=1 or row.get("record_type")!="gate_pass_proposal":errors.append("invalid proposal schema/type")
    if row.get("result")!="PASS":errors.append("only PASS results may be proposed for reuse")
    task=row.get("task_id");gate=row.get("gate");candidate=row.get("candidate")
    if not _git_commit(candidate):errors.append("candidate unavailable or invalid")
    if not isinstance(task,str) or not re.fullmatch(r"T[0-9]{2}",task):errors.append("invalid task_id")
    ev=row.get("evidence",{})
    try:
        path=_evidence_path(ev.get("path",""))
        if not SHA64.fullmatch(str(ev.get("sha256",""))) or _sha(path)!=ev.get("sha256"):errors.append("evidence digest mismatch")
    except Exception as exc:errors.append(str(exc))
    if not errors:
        try:
            fp=fingerprint(task,gate,candidate)
            if row.get("fingerprint")!=fp["fingerprint"]:errors.append("fingerprint no longer matches candidate inputs")
            if row.get("reuse_class")!=fp["reuse_class"]:errors.append("reuse class mismatch")
            if fp["environment_sensitive"]:
                if not row.get("environment_fingerprint"):errors.append("environment-sensitive proposal missing environment fingerprint")
                elif fp["environment"].get("complete") and row.get("environment_fingerprint")!=fp["environment"].get("fingerprint"):errors.append("environment fingerprint mismatch")
        except Exception as exc:errors.append(str(exc))
    if row.get("approval_authority_granted") is not False:errors.append("proposal may not grant approval")
    if row.get("quality_thresholds_unchanged") is not True:errors.append("proposal may not alter thresholds")
    if row.get("integration_owner_promotion_required") is not True:errors.append("owner promotion boundary missing")
    return {"passed":not errors,"errors":errors}

def apply_proposal(proposal_path,index_path=INDEX,owner_disposition=None):
    proposal_row=_load(proposal_path);checked=validate_proposal(proposal_row);errors=list(checked["errors"])
    if owner_disposition!=OWNER_DISPOSITION:errors.append("exact integration-owner promotion disposition required")
    if proposal_row.get("promotion_eligible") is not True:errors.append("proposal is not promotion-eligible")
    index_path=Path(index_path);index=_load(index_path)
    key=(proposal_row.get("task_id"),proposal_row.get("gate"),proposal_row.get("candidate"),proposal_row.get("fingerprint"))
    for row in index.get("records",[]):
        if (row.get("task_id"),row.get("gate"),row.get("candidate"),row.get("fingerprint"))==key and row.get("result")=="PASS":
            errors.append("duplicate durable gate PASS record")
    if errors:return {"passed":False,"errors":errors}
    durable=dict(proposal_row);durable["record_type"]="gate_pass";durable["promoted_by"]=OWNER_DISPOSITION;durable["proposal_id"]=proposal_row["proposal_id"];durable["approval_authority_granted"]=False
    index.setdefault("records",[]).append(durable);index_path.write_text(json.dumps(index,indent=2)+"\n")
    return {"passed":True,"record":durable,"index":str(index_path),"errors":[]}

def validate_index():
    report=validate_policy()
    return {"passed":report.get("passed") is True,"gate_policy":report,"owner_promotion_required":True,"ci_repo_write_required":False,"errors":report.get("errors",[])}

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True);sub.add_parser("validate")
    p=sub.add_parser("proposal");p.add_argument("--task",required=True);p.add_argument("--gate",required=True);p.add_argument("--candidate",required=True);p.add_argument("--evidence",required=True);p.add_argument("--workflow-run-id");p.add_argument("--workflow-job-id");p.add_argument("--output",required=True)
    v=sub.add_parser("validate-proposal");v.add_argument("proposal")
    a=sub.add_parser("apply");a.add_argument("proposal");a.add_argument("--index",default=str(INDEX));a.add_argument("--owner-disposition",required=True)
    args=ap.parse_args()
    if args.cmd=="validate":out=validate_index()
    elif args.cmd=="proposal":
        try:out=proposal(args.task,args.gate,args.candidate,args.evidence,args.workflow_run_id,args.workflow_job_id)
        except Exception as exc:print(json.dumps({"passed":False,"errors":[str(exc)]},indent=2));raise SystemExit(2)
        outpath=Path(args.output);outpath.parent.mkdir(parents=True,exist_ok=True);outpath.write_text(json.dumps(out,indent=2)+"\n");out={"passed":True,"proposal":out,"output":str(outpath),"errors":[]}
    elif args.cmd=="validate-proposal":out=validate_proposal(_load(args.proposal))
    else:out=apply_proposal(args.proposal,args.index,args.owner_disposition)
    print(json.dumps(out,indent=2));raise SystemExit(0 if out.get("passed") else 2)
if __name__=="__main__":main()
