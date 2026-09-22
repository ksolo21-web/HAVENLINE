#!/usr/bin/env python3
from __future__ import annotations
import argparse, fnmatch, json, pathlib, re, subprocess
from typing import Any

ROOT=pathlib.Path(__file__).resolve().parents[3]
DOCS=ROOT/"Docs"/"Production"
POLICY_PATH=DOCS/"SHIPPING_VISUAL_APPROVAL_POLICY.json"
INVALIDATIONS_PATH=DOCS/"APPROVAL_INVALIDATIONS.json"
HEX40=re.compile(r"^[0-9a-f]{40}$")

def load(path: pathlib.Path)->dict[str,Any]:
    return json.loads(path.read_text())

def git(*args: str, text: bool=True):
    return subprocess.check_output(["git",*args],cwd=ROOT,text=text)

def match(path: str, patterns: list[str])->bool:
    return any(fnmatch.fnmatchcase(path,p) for p in patterns)

def policy()->dict[str,Any]:
    return load(POLICY_PATH)

def registry()->dict[str,Any]:
    return load(DOCS/"WORKSTREAM_REGISTRY.json")

def ownership()->dict[str,Any]:
    return load(DOCS/"PATH_OWNERSHIP.json")

def graph()->dict[str,Any]:
    return load(DOCS/"DEPENDENCY_GRAPH.json")

def invalidations()->dict[str,Any]:
    return load(INVALIDATIONS_PATH)

def active_invalidation(task_id: str)->dict[str,Any]|None:
    return next((r for r in invalidations().get("records",[]) if r.get("task_id")==task_id and r.get("status")=="ACTIVE"),None)

def task_patterns(task_id: str)->list[str]:
    reg=registry(); own=ownership()
    row=next((w for w in reg.get("workstreams",[]) if w.get("task_id")==task_id),None)
    aliases=[]
    if row:
        aliases=list(row.get("owned_paths",[]))
    elif f"@protected:{task_id}" in own.get("aliases",{}):
        aliases=[f"@protected:{task_id}"]
    patterns=[]
    for item in aliases:
        if isinstance(item,str) and item.startswith("@"):
            patterns.extend(own.get("aliases",{}).get(item,[]))
        elif isinstance(item,str):
            patterns.append(item)
    return list(dict.fromkeys(patterns))

def tracked_files(ref: str)->list[str]:
    return [x for x in git("ls-tree","-r","--name-only",ref,"--","HavenlineGodot").splitlines() if x]

def text_at(ref: str,path: str)->str:
    return git("show",f"{ref}:{path}")

def scan_task(task_id: str, ref: str="HEAD")->dict[str,Any]:
    p=policy(); patterns=task_patterns(task_id); excluded=p.get("excluded_patterns",[])
    exts=set(p.get("text_extensions",[]))
    forbidden=[("render_type",x) for x in p.get("forbidden_render_types",[])]
    forbidden += [("material_type",x) for x in p.get("forbidden_material_types",[])]
    files=[]
    findings=[]
    for path in tracked_files(ref):
        if not match(path,patterns): continue
        if match(path,excluded): continue
        if pathlib.PurePosixPath(path).suffix not in exts: continue
        files.append(path)
        try: body=text_at(ref,path)
        except Exception as exc:
            findings.append({"path":path,"line":0,"token":"<unreadable>","category":"evidence","detail":str(exc)})
            continue
        for lineno,line in enumerate(body.splitlines(),1):
            for category,token in forbidden:
                if re.search(r"(?<![A-Za-z0-9_])"+re.escape(token)+r"(?![A-Za-z0-9_])",line):
                    findings.append({"path":path,"line":lineno,"token":token,"category":category,"text":line.strip()[:240]})
    critics=set(next((w.get("critic_requirements",[]) for w in registry().get("workstreams",[]) if w.get("task_id")==task_id),[]))
    visual=bool(critics.intersection(set(p.get("visual_critic_ids",[])))) or any(pathlib.PurePosixPath(x).suffix in {".tscn",".tres",".res",".gdshader"} for x in files)
    return {"schema_version":1,"task_id":task_id,"ref":git("rev-parse",f"{ref}^{{commit}}").strip(),"visual_task":visual,"scanned_files":files,"finding_count":len(findings),"findings":findings,"passed":not findings}

def signoff_path(task_id: str,candidate: str)->str:
    return f"Docs/Production/VisualApprovals/{task_id}/{candidate}.json"

def _read_record(path: str, integration_ref: str|None)->dict[str,Any]:
    if integration_ref:
        return json.loads(git("show",f"{integration_ref}:{path}"))
    return json.loads((ROOT/path).read_text())

def validate_signoff(task_id: str,candidate: str,integration_ref: str|None=None)->dict[str,Any]:
    p=policy(); req=p["human_visual_gate"]; errors=[]
    if not HEX40.fullmatch(candidate or ""): errors.append("candidate_sha must be exact 40-hex")
    path=signoff_path(task_id,candidate)
    try: rec=_read_record(path,integration_ref)
    except Exception as exc:
        return {"passed":False,"task_id":task_id,"candidate_sha":candidate,"record_path":path,"errors":[f"visual signoff record missing/unreadable: {exc}"]}
    if rec.get("schema_version")!=1 or rec.get("task_id")!=task_id or rec.get("candidate_sha")!=candidate:
        errors.append("visual signoff identity mismatch")
    primitive=rec.get("primitive_audit",{})
    if primitive.get("passed") is not True or primitive.get("findings_count")!=0:
        errors.append("primitive audit must pass with zero findings")
    evidence=rec.get("visual_evidence",{})
    if evidence.get("source_bound") is not True: errors.append("visual evidence must be exact-source bound")
    if not isinstance(evidence.get("workflow_run_id"),int) or evidence.get("workflow_run_id",0)<=0: errors.append("workflow_run_id missing")
    if not isinstance(evidence.get("artifact_id"),int) or evidence.get("artifact_id",0)<=0: errors.append("artifact_id missing")
    if int(evidence.get("stills_count",0))<int(req["minimum_stills"]): errors.append("not enough final stills")
    if float(evidence.get("motion_video_seconds",0))<float(req["minimum_motion_seconds"]): errors.append("motion proof too short")
    res=evidence.get("internal_resolution",[])
    minimum=req["minimum_internal_resolution"]
    if not isinstance(res,list) or len(res)!=2 or int(res[0])<minimum[0] or int(res[1])<minimum[1]: errors.append("visual proof is below native 4K minimum")
    if int(evidence.get("capture_fps",0))<int(req["minimum_capture_fps"]): errors.append("visual motion proof is below 60 FPS")
    if rec.get("user_visual_approval") is not True: errors.append("explicit user visual approval is required")
    return {"passed":not errors,"task_id":task_id,"candidate_sha":candidate,"record_path":path,"errors":errors}

def effective_approval(task_id: str, ref: str="HEAD")->dict[str,Any]:
    g=graph(); gates=load(DOCS/"task-gates.json"); errors=[]
    historical=g.get("tasks",{}).get(task_id,{}).get("status")=="APPROVED" and task_id in gates.get("approved_tasks",[])
    if not historical: errors.append("historical lifecycle/task-gate approval is absent")
    inv=active_invalidation(task_id)
    if inv: errors.append("active approval invalidation: "+str(inv.get("family")))
    scan=scan_task(task_id,ref)
    if not scan["passed"]: errors.append(f"shipping visual primitive audit has {scan['finding_count']} finding(s)")
    return {"passed":not errors,"task_id":task_id,"historical_approved":historical,"effective_approved":not errors,"active_invalidation":inv,"primitive_audit":scan,"errors":errors}

def audit_effective_approvals(ref: str="HEAD")->dict[str,Any]:
    gates=load(DOCS/"task-gates.json"); rows=[]; errors=[]
    for task_id in gates.get("approved_tasks",[]):
        scan=scan_task(task_id,ref); inv=active_invalidation(task_id)
        covered=bool(inv)
        if scan["findings"] and not covered:
            errors.append(f"{task_id} has uncovered primitive shipping-art findings")
        rows.append({"task_id":task_id,"finding_count":scan["finding_count"],"invalidation_active":covered,"effective_approved":scan["passed"] and not covered})
    return {"passed":not errors,"ref":git("rev-parse",f"{ref}^{{commit}}").strip(),"rows":rows,"errors":errors}

def main()->None:
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("audit-task");a.add_argument("task_id");a.add_argument("--candidate",default="HEAD");a.add_argument("--require-clean",action="store_true");a.add_argument("--output")
    e=sub.add_parser("effective-approval");e.add_argument("task_id");e.add_argument("--ref",default="HEAD")
    p=sub.add_parser("audit-effective-approvals");p.add_argument("--ref",default="HEAD")
    s=sub.add_parser("signoff");s.add_argument("task_id");s.add_argument("--candidate",required=True);s.add_argument("--integration-ref")
    args=ap.parse_args()
    if args.cmd=="audit-task":
        out=scan_task(args.task_id.upper(),args.candidate)
        if args.output: pathlib.Path(args.output).write_text(json.dumps(out,indent=2)+"\n")
        print(json.dumps(out,indent=2))
        if args.require_clean and not out["passed"]: raise SystemExit(2)
    elif args.cmd=="effective-approval":
        out=effective_approval(args.task_id.upper(),args.ref);print(json.dumps(out,indent=2));raise SystemExit(0 if out["passed"] else 2)
    elif args.cmd=="audit-effective-approvals":
        out=audit_effective_approvals(args.ref);print(json.dumps(out,indent=2));raise SystemExit(0 if out["passed"] else 2)
    else:
        out=validate_signoff(args.task_id.upper(),args.candidate,args.integration_ref);print(json.dumps(out,indent=2));raise SystemExit(0 if out["passed"] else 2)
if __name__=="__main__": main()
