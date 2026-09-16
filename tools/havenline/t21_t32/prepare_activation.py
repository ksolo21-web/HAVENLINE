#!/usr/bin/env python3
"""Fail-closed Havenline T21-T32 preparation and read-only activation preflight."""
from __future__ import annotations
import argparse, fnmatch, functools, json, pathlib, subprocess
ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "Docs" / "Production"
TASKS = [f"T{i:02d}" for i in range(21, 33)]

def load(p): return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
def _has_glob(s): return any(ch in s for ch in "*?[")
def _segment_overlap(a,b):
    if a==b: return True
    ag,bg=_has_glob(a),_has_glob(b)
    if not ag and not bg: return False
    if not ag: return fnmatch.fnmatchcase(a,b)
    if not bg: return fnmatch.fnmatchcase(b,a)
    ai=min([i for i in (a.find("*"),a.find("?"),a.find("[")) if i>=0],default=len(a)); bi=min([i for i in (b.find("*"),b.find("?"),b.find("[")) if i>=0],default=len(b))
    ap,bp=a[:ai],b[:bi]
    if ap and bp and not (ap.startswith(bp) or bp.startswith(ap)): return False
    if "[" not in a and "[" not in b:
        al=max(a.rfind("*"),a.rfind("?")); bl=max(b.rfind("*"),b.rfind("?")); asuf=a[al+1:] if al>=0 else a; bsuf=b[bl+1:] if bl>=0 else b
        if asuf and bsuf and not (asuf.endswith(bsuf) or bsuf.endswith(asuf)): return False
    return True
def overlap(a,b):
    aa=tuple(x for x in a.strip("/").split("/") if x); bb=tuple(x for x in b.strip("/").split("/") if x)
    @functools.lru_cache(maxsize=None)
    def walk(i,j):
        if i==len(aa): return all(x=="**" for x in bb[j:])
        if j==len(bb): return all(x=="**" for x in aa[i:])
        if aa[i]=="**": return walk(i+1,j) or walk(i,j+1)
        if bb[j]=="**": return walk(i,j+1) or walk(i+1,j)
        return _segment_overlap(aa[i],bb[j]) and walk(i+1,j+1)
    return walk(0,0)
def registry_status(reg,tid):
    if tid in reg.get("legacy_approvals",{}): return "APPROVED"
    row=next((x for x in reg.get("workstreams",[]) if x.get("task_id")==tid),None)
    return (row or {}).get("status")
def path_collisions(paths,own):
    integration=[]; active=[]
    for candidate in paths:
        for p in own.get("aliases",{}).get("@integration-only",[]):
            if overlap(candidate,p): integration.append({"candidate":candidate,"protected":p})
        for o in own.get("active_owners",[]):
            for p in own.get("aliases",{}).get(o.get("paths_alias"),[]):
                if overlap(candidate,p): active.append({"task":o.get("task_id"),"candidate":candidate,"foreign":p})
    return integration,active

def prep(tid):
    graph=load(DOCS/"DEPENDENCY_GRAPH.json"); reg=load(DOCS/"WORKSTREAM_REGISTRY.json"); own=load(DOCS/"PATH_OWNERSHIP.json"); cm=load(DOCS/"CRITIC_MATRIX.json")
    base=DOCS/tid; req=[base/"FROZEN_SCOPE.md",base/"TASK_PACKET.md",base/"PREBUILD_CONTRACT.json",base/"defect-ledger.json",base/"ACTIVATION_CHECKLIST.json"]
    errors=[f"missing/empty {p.relative_to(ROOT)}" for p in req if not p.exists() or not p.read_text(encoding="utf-8").strip()]
    if errors: return {"task_id":tid,"mode":"preparation","passed":False,"errors":errors}
    ck=load(base/"ACTIVATION_CHECKLIST.json"); defect=load(base/"defect-ledger.json"); row=graph.get("tasks",{}).get(tid,{})
    if ck.get("dependencies")!=row.get("dependencies"): errors.append(f"dependency mismatch checklist={ck.get('dependencies')} graph={row.get('dependencies')}")
    planned=set(ck.get("required_critics",[])); graphc=set(row.get("critics",[])); matrix=set(cm.get("task_applicability",{}).get(tid,[]))
    if not graphc.issubset(planned): errors.append(f"missing graph critics {sorted(graphc-planned)}")
    if not matrix.issubset(planned): errors.append(f"missing critic-matrix critics {sorted(matrix-planned)}")
    if tid in ("T21","T23") and "C5" not in planned: errors.append("C5 required by task scope override")
    if ck.get("runtime_build_allowed_before_activation") is not False: errors.append("runtime_build_allowed_before_activation must be false")
    if ck.get("runtime_status")!="LOCKED": errors.append("runtime status must remain LOCKED")
    paths=ck.get("planned_owned_paths",[])
    if not paths or len(paths)!=len(set(paths)): errors.append("planned paths empty/duplicate")
    integ,active=path_collisions(paths,own)
    if integ: errors.append("integration-only collision: "+json.dumps(integ))
    if active: errors.append("active-workstream collision: "+json.dumps(active))
    if defect.get("unresolved_preparation_defects"): errors.append("unresolved preparation defects")
    return {"task_id":tid,"mode":"preparation","graph_status":row.get("status"),"registry_status":registry_status(reg,tid),"planned_paths":len(paths),"required_critics":ck.get("required_critics"),"integration_only_collisions":len(integ),"active_collisions":len(active),"runtime_build_allowed":False,"passed":not errors,"errors":errors}
def head(): return subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
def activate(tid,base):
    result=prep(tid)
    if not result.get("passed"): return {**result,"mode":"activation-preflight","base":base,"passed":False}
    ck=load(DOCS/tid/"ACTIVATION_CHECKLIST.json"); graph=load(DOCS/"DEPENDENCY_GRAPH.json"); reg=load(DOCS/"WORKSTREAM_REGISTRY.json"); gates=load(DOCS/"task-gates.json"); own=load(DOCS/"PATH_OWNERSHIP.json"); errors=[]
    h=head()
    if h!=base: errors.append(f"base/head mismatch head={h} base={base}")
    for dep in ck.get("dependencies",[]):
        if graph.get("tasks",{}).get(dep,{}).get("status")!="APPROVED": errors.append(f"{dep} graph not APPROVED")
        if registry_status(reg,dep)!="APPROVED": errors.append(f"{dep} registry not APPROVED")
        if dep not in gates.get("approved_tasks",[]): errors.append(f"{dep} missing task-gates approval")
        if any(x.get("task_id")==dep for x in own.get("active_owners",[])): errors.append(f"{dep} still owns active paths")
    if graph.get("tasks",{}).get(tid,{}).get("status") not in ("LOCKED","PREPARED"): errors.append("unexpected pre-activation state")
    integ,active=path_collisions(ck.get("planned_owned_paths",[]),own)
    if integ or active: errors.append("planned ownership no longer disjoint")
    return {"task_id":tid,"mode":"activation-preflight","base":base,"head":h,"dependencies":ck.get("dependencies",[]),"future_branch":ck.get("future_builder_branch"),"future_owner":ck.get("future_owner"),"reservation_patch":{"alias":ck.get("planned_owned_alias"),"paths":ck.get("planned_owned_paths",[])},"claim_command":ck.get("claim_template","").replace("<EXACT_CURRENT_INTEGRATION_HEAD>",base),"passed":not errors,"errors":errors}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--task",choices=TASKS); ap.add_argument("--all",action="store_true"); ap.add_argument("--activate",action="store_true"); ap.add_argument("--base"); a=ap.parse_args()
    if a.all:
        if a.task or a.activate or a.base: raise SystemExit("--all is preparation validation only")
        r=[prep(t) for t in TASKS]; out={"wave":"T21-T32","mode":"preparation","results":r,"passed":all(x["passed"] for x in r)}
    else:
        if not a.task: raise SystemExit("use --all or --task T21..T32")
        if a.activate and not a.base: raise SystemExit("--activate requires --base")
        out=activate(a.task,a.base) if a.activate else prep(a.task)
    print(json.dumps(out,indent=2))
    if not out.get("passed"): raise SystemExit(1)
if __name__=="__main__": main()
