#!/usr/bin/env python3
"""Fail-closed preparation and activation preflight for Havenline T33-T43."""
from __future__ import annotations
import argparse, json, pathlib, subprocess
ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "Docs" / "Production"
TASKS = [f"T{i:02d}" for i in range(33,44)]

def load(p): return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
def prefix(p):
    cut=len(p)
    for t in ("*","?","["):
        i=p.find(t)
        if i>=0: cut=min(cut,i)
    return p[:cut].rstrip("/")
def overlap(a,b):
    if a==b: return True
    pa,pb=prefix(a),prefix(b)
    return not pa or not pb or pa==pb or pa.startswith(pb+"/") or pb.startswith(pa+"/")
def registry_status(registry,tid):
    if tid in registry.get("legacy_approvals",{}): return "APPROVED"
    row=next((x for x in registry.get("workstreams",[]) if x.get("task_id")==tid),None)
    return (row or {}).get("status")
def files_for(tid):
    d=DOCS/tid
    return [d/"FROZEN_SCOPE.md",d/"TASK_PACKET.md",d/"PREBUILD_CONTRACT.json",d/"defect-ledger.json",d/"ACTIVATION_CHECKLIST.json"]
def ownership_collisions(paths,ownership):
    hits=[]
    foreign=[]
    for c in paths:
        for p in ownership.get("aliases",{}).get("@integration-only",[]):
            if overlap(c,p): hits.append({"candidate":c,"integration_only":p})
        for owner in ownership.get("active_owners",[]):
            for p in ownership.get("aliases",{}).get(owner.get("paths_alias"),[]):
                if overlap(c,p): foreign.append({"candidate":c,"task":owner.get("task_id"),"path":p})
    return hits,foreign

def validate_prep(tid):
    errors=[]
    for p in files_for(tid):
        if not p.exists() or not p.read_text(encoding="utf-8").strip(): errors.append(f"missing/empty {p.relative_to(ROOT)}")
    if errors: return {"task_id":tid,"passed":False,"errors":errors}
    check=load(DOCS/tid/"ACTIVATION_CHECKLIST.json")
    defect=load(DOCS/tid/"defect-ledger.json")
    graph=load(DOCS/"DEPENDENCY_GRAPH.json")
    ownership=load(DOCS/"PATH_OWNERSHIP.json")
    critics=load(DOCS/"CRITIC_MATRIX.json")
    gm=load(DOCS/"GAME_MASTER_POLICY.json")
    row=graph.get("tasks",{}).get(tid,{})
    if check.get("dependencies")!=row.get("dependencies"): errors.append("dependency mismatch")
    expected=set(row.get("critics",[]))
    planned=set(check.get("required_critics",[]))
    if expected!=planned: errors.append(f"critic mismatch graph={sorted(expected)} planned={sorted(planned)}")
    matrix=set(critics.get("task_applicability",{}).get(tid,[]))
    if matrix and matrix!=planned: errors.append(f"critic-matrix mismatch matrix={sorted(matrix)} planned={sorted(planned)}")
    gm_tasks=set(gm.get("task_policy",{}).get("applicable_tasks",[]))
    required=gm.get("task_policy",{}).get("required_proof_flags_by_task",{}).get(tid,[])
    supplied=check.get("game_master_required_proof_flags",[])
    if tid in gm_tasks and supplied!=required: errors.append(f"Game Master proof flags mismatch required={required} supplied={supplied}")
    if tid not in gm_tasks and supplied: errors.append("unexpected Game Master proof flags")
    if check.get("runtime_status")!="LOCKED": errors.append("runtime status must remain LOCKED")
    if check.get("runtime_build_allowed_before_activation") is not False: errors.append("runtime build must remain disabled")
    paths=check.get("planned_owned_paths",[])
    if not paths or len(paths)!=len(set(paths)): errors.append("planned paths empty/duplicate")
    integ,active=ownership_collisions(paths,ownership)
    if integ: errors.append("integration-only collision: "+json.dumps(integ))
    if active: errors.append("active ownership collision: "+json.dumps(active))
    if defect.get("unresolved_preparation_defects"): errors.append("unresolved preparation defects")
    return {"task_id":tid,"graph_status":row.get("status"),"planned_path_count":len(paths),"gm_applicable":tid in gm_tasks,"passed":not errors,"errors":errors}

def wave_collisions():
    checks={t:load(DOCS/t/"ACTIVATION_CHECKLIST.json") for t in TASKS}
    errors=[]
    for i,a in enumerate(TASKS):
        for b in TASKS[i+1:]:
            for pa in checks[a].get("planned_owned_paths",[]):
                for pb in checks[b].get("planned_owned_paths",[]):
                    if overlap(pa,pb): errors.append({"task_a":a,"path_a":pa,"task_b":b,"path_b":pb})
    return errors

def git_head(): return subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
def validate_activation(tid,base):
    prep=validate_prep(tid)
    if not prep["passed"]: return {**prep,"mode":"activation-preflight","base":base,"passed":False}
    check=load(DOCS/tid/"ACTIVATION_CHECKLIST.json")
    graph=load(DOCS/"DEPENDENCY_GRAPH.json"); registry=load(DOCS/"WORKSTREAM_REGISTRY.json"); gates=load(DOCS/"task-gates.json"); ownership=load(DOCS/"PATH_OWNERSHIP.json")
    errors=[]; head=git_head()
    if head!=base: errors.append(f"activation base/head mismatch head={head} base={base}")
    for dep in check.get("dependencies",[]):
        if graph.get("tasks",{}).get(dep,{}).get("status")!="APPROVED": errors.append(f"{dep} graph not APPROVED")
        if registry_status(registry,dep)!="APPROVED": errors.append(f"{dep} registry not APPROVED")
        if dep not in gates.get("approved_tasks",[]): errors.append(f"{dep} missing approved_tasks")
        if any(x.get("task_id")==dep for x in ownership.get("active_owners",[])): errors.append(f"{dep} ownership still active")
    return {"task_id":tid,"mode":"activation-preflight","base":base,"head":head,"future_branch":check.get("future_builder_branch"),"reservation_patch":{"alias":check.get("planned_owned_alias"),"paths":check.get("planned_owned_paths",[])},"claim_command":check.get("claim_template","").replace("<EXACT_CURRENT_INTEGRATION_HEAD>",base),"passed":not errors,"errors":errors}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--task",choices=TASKS); ap.add_argument("--all",action="store_true"); ap.add_argument("--activate",action="store_true"); ap.add_argument("--base"); a=ap.parse_args()
    if a.all:
        if a.task or a.activate or a.base: raise SystemExit("--all is preparation-only")
        results=[validate_prep(t) for t in TASKS]; cross=wave_collisions(); out={"wave":"T33-T43","mode":"preparation","results":results,"cross_task_path_collisions":cross,"passed":all(x["passed"] for x in results) and not cross}
    else:
        if not a.task: raise SystemExit("use --all or --task T33..T43")
        if a.activate and not a.base: raise SystemExit("--activate requires --base")
        out=validate_activation(a.task,a.base) if a.activate else validate_prep(a.task)
    print(json.dumps(out,indent=2)); raise SystemExit(0 if out.get("passed") else 1)
if __name__=="__main__": main()
