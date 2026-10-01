#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
from forward_execution import DOCS,ROOT
from failure_intelligence import KB,VALID_CLASSES,validate as validate_kb

OWNER_DISPOSITION="PROMOTE_VERIFIED_FAILURE_INTELLIGENCE"
SHA40=re.compile(r"^[0-9a-f]{40}$")

def _load(path):return json.loads(Path(path).read_text())
def _digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def _rel(path):
    p=Path(path)
    if not p.is_absolute():p=ROOT/p
    p=p.resolve()
    if ROOT.resolve()!=p and ROOT.resolve() not in p.parents:raise ValueError("source must be inside repository")
    return str(p.relative_to(ROOT)),p
def _tokens(text):
    rows=[]
    for token in re.findall(r"[a-z0-9_+.-]+",str(text).lower()):
        if len(token)>=4 and token not in rows:rows.append(token)
    return rows[:12]

def propose(c0_path):
    rel,path=_rel(c0_path);c0=_load(path);errors=[]
    if c0.get("critic_id")!="C0" or c0.get("non_voting") is not True:errors.append("source is not non-voting C0")
    if c0.get("validated") is not True:errors.append("C0 diagnosis is not validated")
    task=c0.get("task_id");candidate=c0.get("failed_candidate");diagnosis=c0.get("diagnosis_id")
    if not isinstance(task,str) or not re.fullmatch(r"T[0-9]{2}",task):errors.append("invalid task_id")
    if not SHA40.fullmatch(str(candidate or "")):errors.append("invalid failed_candidate")
    blockers=c0.get("blockers")
    if not isinstance(blockers,list) or not blockers:errors.append("C0 blockers missing")
    if errors:return {"passed":False,"errors":errors}
    proposals=[]
    for b in blockers:
        required=("id","classification","symptom","root_cause","affected_object","causal_fix","files_not_to_change","verification")
        missing=[k for k in required if k not in b]
        if missing:
            errors.append(str(b.get("id","blocker"))+" missing "+",".join(missing));continue
        if b["classification"] not in VALID_CLASSES-{"MIXED"}:errors.append(str(b["id"])+" invalid classification");continue
        material={"task":task,"diagnosis":diagnosis,"blocker":b["id"],"candidate":candidate,"root_cause":b["root_cause"]}
        pid="FLP-"+task+"-"+hashlib.sha256(json.dumps(material,sort_keys=True).encode()).hexdigest()[:16]
        proposals.append({
          "schema_version":1,"proposal_id":pid,"state":"UNVERIFIED_C0_LESSON","task_id":task,"diagnosis_id":diagnosis,
          "failed_candidate":candidate,"blocker_id":b["id"],"classification":b["classification"],"affected_object":b["affected_object"],
          "symptom":b["symptom"],"root_cause":b["root_cause"],"suggested_causal_repair":b["causal_fix"],
          "protected_files":b["files_not_to_change"],"verification_steps":b["verification"],
          "suggested_signature_terms":_tokens(str(b["affected_object"])+" "+str(b["root_cause"])+" "+str(b["symptom"])),
          "source_c0":rel,"source_c0_sha256":_digest(path),"historical_match_advisory_only":True,
          "promotion_requires_verified_post_repair_proof":True,"approval_authority_granted":False
        })
    return {"passed":not errors,"schema_version":1,"task_id":task,"diagnosis_id":diagnosis,"proposal_count":len(proposals),"proposals":proposals,"errors":errors}

def validate_proposals(doc):
    errors=[]
    if doc.get("schema_version")!=1 or not isinstance(doc.get("proposals"),list):errors.append("invalid proposal document")
    for p in doc.get("proposals",[]):
        if p.get("state")!="UNVERIFIED_C0_LESSON":errors.append("proposal state must remain unverified")
        if p.get("approval_authority_granted") is not False:errors.append("failure-learning proposal may not grant approval")
        if p.get("promotion_requires_verified_post_repair_proof") is not True:errors.append("post-repair proof boundary missing")
        try:
            rel,path=_rel(p.get("source_c0",""))
            if _digest(path)!=p.get("source_c0_sha256"):errors.append("source C0 digest mismatch")
        except Exception as exc:errors.append(str(exc))
    return {"passed":not errors,"proposal_count":len(doc.get("proposals",[])),"errors":errors}

def promote(proposal_doc_path,proposal_id,verification_path,index_path=KB):
    doc=_load(proposal_doc_path);base_check=validate_proposals(doc);errors=list(base_check["errors"])
    matches=[p for p in doc.get("proposals",[]) if p.get("proposal_id")==proposal_id]
    if len(matches)!=1:errors.append("proposal_id must resolve exactly once");proposal=None
    else:proposal=matches[0]
    verification=_load(verification_path)
    if verification.get("owner_disposition")!=OWNER_DISPOSITION:errors.append("exact integration-owner learning disposition required")
    if verification.get("proposal_id")!=proposal_id:errors.append("verification proposal mismatch")
    if verification.get("causal_repair_verified") is not True:errors.append("causal repair not verified")
    if verification.get("full_regression_passed") is not True:errors.append("full regression proof required")
    if verification.get("thresholds_unchanged") is not True:errors.append("thresholds must remain unchanged")
    if not SHA40.fullmatch(str(verification.get("candidate_after_repair",""))):errors.append("candidate_after_repair must be exact SHA")
    if verification.get("scope") not in ("cross_task_reusable","task_local"):errors.append("verified scope required")
    if not str(verification.get("gate","")).strip():errors.append("verified gate required")
    if not isinstance(verification.get("signature_terms"),list) or not verification.get("signature_terms"):errors.append("verified signature_terms required")
    if not str(verification.get("prevention_rule","")).strip():errors.append("verified prevention_rule required")
    if not isinstance(verification.get("proof"),list) or not verification.get("proof"):errors.append("verified proof required")
    source=str(verification.get("source") or (proposal.get("source_c0")+"#"+proposal.get("blocker_id") if proposal else ""))
    try:_rel(source.split("#",1)[0])
    except Exception as exc:errors.append(str(exc))
    if errors:return {"passed":False,"errors":errors}
    index_path=Path(index_path);index=_load(index_path)
    rid="FI-"+proposal["task_id"]+"-L"+hashlib.sha256(proposal_id.encode()).hexdigest()[:10].upper()
    if any(r.get("id")==rid for r in index.get("records",[])):return {"passed":False,"errors":["durable failure-intelligence id already exists"]}
    record={
      "id":rid,"task_id":proposal["task_id"],"scope":verification["scope"],"gate":verification["gate"],
      "classification":proposal["classification"],"signature_terms":verification["signature_terms"],
      "symptom":proposal["symptom"],"root_cause":proposal["root_cause"],"causal_repair":proposal["suggested_causal_repair"],
      "protected_files":proposal["protected_files"],"proof":verification["proof"],"prevention_rule":verification["prevention_rule"],"source":source,
      "promotion":{"proposal_id":proposal_id,"candidate_after_repair":verification["candidate_after_repair"],"owner_disposition":OWNER_DISPOSITION},
      "advisory_only":True,"approval_authority_granted":False
    }
    index.setdefault("records",[]).append(record);index_path.write_text(json.dumps(index,indent=2)+"\n")
    return {"passed":True,"record":record,"index":str(index_path),"errors":[]}

def validate_tool():
    kb=validate_kb();return {"passed":kb.get("passed") is True,"kb":kb,"automatic_staging":True,"automatic_promotion":False,"owner_promotion_required":True,"errors":kb.get("errors",[])}

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True);sub.add_parser("validate")
    p=sub.add_parser("propose");p.add_argument("--c0",required=True);p.add_argument("--output",required=True)
    v=sub.add_parser("validate-proposals");v.add_argument("proposal_doc")
    m=sub.add_parser("promote");m.add_argument("proposal_doc");m.add_argument("proposal_id");m.add_argument("--verification",required=True);m.add_argument("--index",default=str(KB))
    a=ap.parse_args()
    if a.cmd=="validate":out=validate_tool()
    elif a.cmd=="propose":
        out=propose(a.c0);Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(json.dumps(out,indent=2)+"\n")
    elif a.cmd=="validate-proposals":out=validate_proposals(_load(a.proposal_doc))
    else:out=promote(a.proposal_doc,a.proposal_id,a.verification,a.index)
    print(json.dumps(out,indent=2));raise SystemExit(0 if out.get("passed") else 2)
if __name__=="__main__":main()
