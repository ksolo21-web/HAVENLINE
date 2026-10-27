#!/usr/bin/env python3
from __future__ import annotations
import argparse, fnmatch, hashlib, json, pathlib, re, subprocess
from typing import Any

ROOT=pathlib.Path(__file__).resolve().parents[3]
DOCS=ROOT/"Docs"/"Production"
POLICY_PATH=DOCS/"SHIPPING_VISUAL_APPROVAL_POLICY.json"
INVALIDATIONS_PATH=DOCS/"APPROVAL_INVALIDATIONS.json"
HEX40=re.compile(r"^[0-9a-f]{40}$")
HEX64=re.compile(r"^[0-9a-f]{64}$")

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

def task_invalidation_records(task_id: str)->list[dict[str,Any]]:
    return [r for r in invalidations().get("records",[]) if r.get("task_id")==task_id]

def active_invalidation(task_id: str)->dict[str,Any]|None:
    return next((r for r in task_invalidation_records(task_id) if r.get("status")=="ACTIVE"),None)

def task_number(task_id: str)->int:
    try: return int(task_id[1:])
    except Exception: return 0

def signoff_required(task_id: str)->bool:
    return task_number(task_id)>=12 or bool(task_invalidation_records(task_id))

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

def effective_candidate(task_id: str)->str|None:
    for record in reversed(task_invalidation_records(task_id)):
        candidate=record.get("repair_candidate_commit")
        if isinstance(candidate,str) and HEX40.fullmatch(candidate):
            return candidate
    row=next((w for w in registry().get("workstreams",[]) if w.get("task_id")==task_id),None)
    candidate=(row or {}).get("candidate_commit")
    return candidate if isinstance(candidate,str) and HEX40.fullmatch(candidate) else None

def signoff_path(task_id: str,candidate: str)->str:
    return f"Docs/Production/VisualApprovals/{task_id}/{candidate}.json"

def _read_record(path: str, integration_ref: str|None)->dict[str,Any]:
    if integration_ref:
        return json.loads(git("show",f"{integration_ref}:{path}"))
    return json.loads((ROOT/path).read_text())

def validate_material_critic_receipt(task_id: str,candidate: str,
                                     block: dict|None,
                                     integration_ref: str|None=None)->list[str]:
    """Require byte-hash-bound independent C1+C2 per-material release testimony.

    Private reference imagery is reviewed in a separate workspace. This public
    receipt is a governance record, not a substitute for that real independent
    review or a cryptographic signature from an external service.
    """
    errors=[]
    if not isinstance(block,dict):
        return ["per-material reference/Godot critic evidence missing"]
    path=f"Docs/Production/MaterialCriticApprovals/{task_id}/{candidate}.json"
    if block.get("report_path")!=path:
        errors.append("per-material critic receipt path must be exact task/candidate source")
    expected_hash=block.get("report_sha256")
    if not isinstance(expected_hash,str) or not HEX64.fullmatch(expected_hash):
        errors.append("per-material critic report byte hash missing")
    try:
        if integration_ref:
            raw=git("show",f"{integration_ref}:{path}",text=False)
        else:
            file_path=(ROOT/path).resolve()
            file_path.relative_to(ROOT.resolve())
            raw=file_path.read_bytes()
        if len(raw)>2*1024*1024 or not raw:
            raise ValueError("receipt missing or excessively large")
        if hashlib.sha256(raw).hexdigest()!=expected_hash:
            errors.append("per-material critic release report SHA mismatch")
        receipt=json.loads(raw)
    except (OSError,ValueError,TypeError,subprocess.SubprocessError) as exc:
        return errors+["per-material critic report missing or unreadable: "+str(exc)]
    if receipt.get("mode")!="release" or receipt.get("status")!="SOURCE_BOUND_MATERIAL_CRITIC_PASS_NOT_USER_APPROVAL" or receipt.get("passed") is not True:
        errors.append("per-material critic must pass actual shipping-scene review, not isolated candidate")
    if receipt.get("task_id")!=task_id or receipt.get("candidate_commit")!=candidate:
        errors.append("per-material critic candidate/task identity mismatch")
    if receipt.get("real_visual_review_completed") is not True or receipt.get("critic_ids_verified")!=["C1","C2"]:
        errors.append("both separate C1 and C2 visual critics must be verified")
    if receipt.get("reference_fidelity_10_required") is not True or receipt.get("other_dimensions_minimum_9_5") is not True:
        errors.append("per-material 10.0/9.5 score contract missing")
    if receipt.get("errors")!=[] or receipt.get("user_approved") is not False:
        errors.append("critic receipt contains unresolved defects or forged owner approval")
    if receipt.get("shipping_scene_material_proof_verified") is not True:
        errors.append("real shipping Godot material scene not proven")
    assets=receipt.get("asset_ids")
    paths=receipt.get("source_paths_covered")
    if not isinstance(assets,list) or not assets or len(set(assets))!=len(assets):
        errors.append("material critic asset census empty/duplicate")
        assets=[]
    if not isinstance(paths,list) or not paths or len(set(paths))!=len(paths) or any(
            not isinstance(p,str) or not p.startswith("HavenlineGodot/") for p in paths):
        errors.append("actual covered game material source paths missing/invalid")
        paths=[]
    if not isinstance(receipt.get("material_count"),int) or receipt["material_count"]<len(assets):
        errors.append("per-material critic has incomplete material inventory")
    policy_path="Docs/Production/GLOBAL_RENDERED_MATERIAL_CRITIC_POLICY.json"
    if receipt.get("policy_path")!=policy_path:
        errors.append("material critic did not use permanent global source lock")
    for k in ("private_manifest_raw_sha256","private_manifest_canonical_sha256"):
        v=receipt.get(k)
        if not isinstance(v,str) or not HEX64.fullmatch(v):
            errors.append("per-material critic private source proof hash absent: "+k)
    hashes=(("source_asset_hashes",False),("reference_image_hashes",True),
            ("native_godot_capture_hashes",True),("reviewed_material_ids",False),
            ("profiles_by_asset",False))
    for key,nested in hashes:
        mapping=receipt.get(key)
        if not isinstance(mapping,dict) or set(mapping)!=set(assets):
            errors.append("per-material critic incomplete: "+key)
            continue
        for asset_id,entry in mapping.items():
            if key=="source_asset_hashes" and (not isinstance(entry,str) or not HEX64.fullmatch(entry)):
                errors.append("source asset SHA missing: "+asset_id)
            if key=="reference_image_hashes" and (not isinstance(entry,list) or not entry or
                  any(not isinstance(x,str) or not HEX64.fullmatch(x) for x in entry)):
                errors.append("source reference bytes unproven: "+asset_id)
            if key=="reviewed_material_ids" and (not isinstance(entry,list) or not entry or len(set(entry))!=len(entry)):
                errors.append("authored material slots unproven: "+asset_id)
            if key=="profiles_by_asset" and entry not in ("static_3d","scene_or_terrain","dynamic_vfx","ui_and_2d"):
                errors.append("unrecognized material evidence profile: "+asset_id)
            if key=="native_godot_capture_hashes":
                if not isinstance(entry,dict) or not entry or any(
                     not isinstance(x,str) or not HEX64.fullmatch(x) for x in entry.values()):
                    errors.append("native Godot PNG SHA coverage incomplete: "+asset_id)
    reviewers=receipt.get("verified_review_sources")
    if not isinstance(reviewers,list) or len(reviewers)!=2 or {r.get("critic_id") for r in reviewers
            if isinstance(r,dict)}!={"C1","C2"}:
        errors.append("distinct C1/C2 raw critic provenance missing")
    else:
        ids=[r.get("independent_run_id") for r in reviewers]
        if any(type(x) is not int or x<=0 for x in ids) or ids[0]==ids[1]:
            errors.append("independent C1/C2 run identities invalid")
        if any(not isinstance(r.get("raw_sha256"),str) or not HEX64.fullmatch(r["raw_sha256"]) for r in reviewers):
            errors.append("unaltered raw C1/C2 reviewer byte hashes missing")
    if task_id=="T70":
        if receipt.get("full_shipped_material_census_verified") is not True:
            errors.append("T70 full shipped game material census not independently verified")
        try:
            from inventory_shipped_visual_sources import census as compute_census
            ref=integration_ref or "HEAD"
            material_census=compute_census(ref)
            census=[entry["shipping_path"] for entry in material_census["source_items"]]
            if sorted(paths)!=census:
                errors.append("T70 material paths fail actual shipping repository census")
        except (OSError,ValueError,subprocess.SubprocessError) as exc:
            errors.append("unable to census T70 live shipping materials: "+str(exc))
    return errors


def validate_signoff(task_id: str,candidate: str,integration_ref: str|None=None)->dict[str,Any]:
    p=policy(); req=p["human_visual_gate"]; errors=[]
    if not HEX40.fullmatch(candidate or ""): errors.append("candidate_sha must be exact 40-hex")
    path=signoff_path(task_id,candidate)
    try: rec=_read_record(path,integration_ref)
    except Exception as exc:
        return {"passed":False,"task_id":task_id,"candidate_sha":candidate,"record_path":path,"errors":[f"visual signoff record missing/unreadable: {exc}"]}
    if rec.get("schema_version")!=1 or rec.get("task_id")!=task_id or rec.get("candidate_sha")!=candidate:
        errors.append("visual signoff identity mismatch")
    if rec.get("user_visual_rejection") is True:
        errors.append("user explicitly rejected final visual reference fidelity")
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
    fidelity=rec.get("reference_fidelity",{})
    if fidelity.get("whole_frame_reviewed") is not True: errors.append("whole-frame reference review is required")
    if fidelity.get("side_by_side_reference_reviewed") is not True: errors.append("side-by-side reference review is required")
    if fidelity.get("passed") is not True: errors.append("whole-frame reference fidelity did not pass")
    failed=fidelity.get("failed_visible_classes",[])
    if not isinstance(failed,list) or failed: errors.append("zero failed visible asset classes are required")
    if req.get("per_asset_rendered_material_critic_required") is True:
        errors.extend(validate_material_critic_receipt(task_id,candidate,rec.get("rendered_material_critic"),integration_ref))
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
    signoff=None
    if not inv and scan.get("visual_task") and signoff_required(task_id):
        candidate=effective_candidate(task_id)
        if not isinstance(candidate,str) or not HEX40.fullmatch(candidate):
            errors.append("visual task has no exact candidate_commit for user signoff")
        else:
            signoff=validate_signoff(task_id,candidate,None)
            if not signoff.get("passed"): errors.extend(["visual signoff: "+e for e in signoff.get("errors",[])])
    return {"passed":not errors,"task_id":task_id,"historical_approved":historical,"effective_approved":not errors,"active_invalidation":inv,"primitive_audit":scan,"visual_signoff":signoff,"errors":errors}

def audit_effective_approvals(ref: str="HEAD")->dict[str,Any]:
    gates=load(DOCS/"task-gates.json"); reg=registry(); rows=[]; errors=[]
    approved=set(gates.get("approved_tasks",[]))
    for task_id in sorted(approved):
        scan=scan_task(task_id,ref); inv=active_invalidation(task_id); covered=bool(inv); signoff=None
        if scan["findings"] and not covered:
            errors.append(f"{task_id} has uncovered primitive shipping-art findings")
        effective=scan["passed"] and not covered
        if effective and scan.get("visual_task") and signoff_required(task_id):
            candidate=effective_candidate(task_id)
            if not isinstance(candidate,str) or not HEX40.fullmatch(candidate):
                effective=False;errors.append(f"{task_id} has no exact candidate_commit for mandatory user visual signoff")
            else:
                signoff=validate_signoff(task_id,candidate,None)
                if not signoff.get("passed"):
                    effective=False;errors.extend([f"{task_id} visual signoff: {e}" for e in signoff.get("errors",[])])
        rows.append({"task_id":task_id,"finding_count":scan["finding_count"],"invalidation_active":covered,"effective_approved":effective,"visual_signoff":signoff})
    for row in reg.get("workstreams",[]):
        task_id=row.get("task_id","")
        if row.get("status") not in {"INTEGRATION_READY","INTEGRATING","UNDER_REVIEW"}: continue
        scan=scan_task(task_id,ref); inv=active_invalidation(task_id)
        if inv: errors.append(f"{task_id} cannot be {row.get('status')} with active visual invalidation")
        if not scan["passed"]: errors.append(f"{task_id} cannot be {row.get('status')} with primitive shipping-art findings")
        if scan.get("visual_task"):
            candidate=row.get("candidate_commit")
            if not isinstance(candidate,str) or not HEX40.fullmatch(candidate):
                errors.append(f"{task_id} integration-ready visual task has no exact candidate_commit")
            else:
                signoff=validate_signoff(task_id,candidate,None)
                if not signoff.get("passed"): errors.extend([f"{task_id} integration-ready visual signoff: {e}" for e in signoff.get("errors",[])])
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
