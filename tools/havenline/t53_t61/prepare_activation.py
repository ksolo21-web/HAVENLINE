#!/usr/bin/env python3
"""Fail-closed prep/activation validator for Havenline T53-T61."""
from __future__ import annotations
import argparse,fnmatch,functools,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[3]; DOCS=ROOT/"Docs"/"Production"; TASKS=[f"T{i:02d}" for i in range(53,62)]
def load(p): return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
def _has_glob(s): return any(ch in s for ch in "*?[")
def _segment_overlap(a,b):
    if a==b: return True
    ag,bg=_has_glob(a),_has_glob(b)
    if not ag and not bg: return False
    if not ag: return fnmatch.fnmatchcase(a,b)
    if not bg: return fnmatch.fnmatchcase(b,a)
    ai=min([i for i in (a.find("*"),a.find("?"),a.find("[")) if i>=0],default=len(a)); bi=min([i for i in (b.find("*"),b.find("?"),b.find("[")) if i>=0],default=len(b)); ap,bp=a[:ai],b[:bi]
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
def reg_status(reg,tid):
    if tid in reg.get("legacy_approvals",{}): return "APPROVED"
    row=next((x for x in reg.get("workstreams",[]) if x.get("task_id")==tid),None); return (row or {}).get("status")
def prep(tid):
    errs=[]; d=DOCS/tid
    for n in ("FROZEN_SCOPE.md","TASK_PACKET.md","PREBUILD_CONTRACT.json","defect-ledger.json","ACTIVATION_CHECKLIST.json"):
        p=d/n
        if not p.exists() or not p.read_text(encoding="utf-8").strip(): errs.append(f"missing/empty {p.relative_to(ROOT)}")
    if errs: return {"task_id":tid,"passed":False,"errors":errs}
    c=load(d/"ACTIVATION_CHECKLIST.json"); p=load(d/"PREBUILD_CONTRACT.json"); defect=load(d/"defect-ledger.json"); graph=load(DOCS/"DEPENDENCY_GRAPH.json"); own=load(DOCS/"PATH_OWNERSHIP.json"); row=graph.get("tasks",{}).get(tid,{})
    if c.get("dependencies")!=row.get("dependencies"): errs.append("dependency mismatch")
    if set(c.get("required_critics",[]))!=set(row.get("critics",[])): errs.append("critic mismatch")
    if c.get("runtime_status")!="LOCKED" or c.get("runtime_build_allowed_before_activation") is not False: errs.append("runtime must remain locked")
    if tid=="T54" and (c.get("audio_playback_review_required") is not True or p.get("audio_playback_review_required") is not True): errs.append("T54 requires actual audio playback review")
    if tid=="T58" and (c.get("acceptance_only") is not True or c.get("final_physical_4k60_certification_forbidden_here") is not True): errs.append("T58 acceptance/certification boundary missing")
    if tid in ("T59","T60","T61"):
        for k in ("full_motion_review_required","tool_weapon_contact_compatibility_required","feet_toes_knees_clipping_review_required","protected_source_glb_change_requires_change_request"):
            if c.get(k) is not True or p.get(k) is not True: errs.append(f"{tid} missing {k}")
    paths=c.get("planned_owned_paths",[])
    for cand in paths:
        for protected in own.get("aliases",{}).get("@integration-only",[]):
            if overlap(cand,protected): errs.append(f"integration-only collision {cand} vs {protected}")
        for owner in own.get("active_owners",[]):
            for foreign in own.get("aliases",{}).get(owner.get("paths_alias"),[]):
                if overlap(cand,foreign): errs.append(f"active collision {cand} vs {owner.get('task_id')}:{foreign}")
    if defect.get("unresolved_preparation_defects"): errs.append("unresolved preparation defects")
    return {"task_id":tid,"graph_status":row.get("status"),"paths":len(paths),"passed":not errs,"errors":errs}
def cross():
    c={t:load(DOCS/t/"ACTIVATION_CHECKLIST.json") for t in TASKS}; out=[]
    for i,a in enumerate(TASKS):
        for b in TASKS[i+1:]:
            for pa in c[a].get("planned_owned_paths",[]):
                for pb in c[b].get("planned_owned_paths",[]):
                    if overlap(pa,pb): out.append({"a":a,"pa":pa,"b":b,"pb":pb})
    return out
def head(): return subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
def activate(tid,base):
    r=prep(tid)
    if not r["passed"]: return {**r,"mode":"activation-preflight","passed":False}
    c=load(DOCS/tid/"ACTIVATION_CHECKLIST.json"); graph=load(DOCS/"DEPENDENCY_GRAPH.json"); reg=load(DOCS/"WORKSTREAM_REGISTRY.json"); gates=load(DOCS/"task-gates.json"); own=load(DOCS/"PATH_OWNERSHIP.json"); errs=[]; h=head()
    if h!=base: errs.append(f"head/base mismatch {h} != {base}")
    for dep in c.get("dependencies",[]):
        if graph.get("tasks",{}).get(dep,{}).get("status")!="APPROVED": errs.append(f"{dep} graph not APPROVED")
        if reg_status(reg,dep)!="APPROVED": errs.append(f"{dep} registry not APPROVED")
        if dep not in gates.get("approved_tasks",[]): errs.append(f"{dep} missing approved_tasks")
        if any(x.get("task_id")==dep for x in own.get("active_owners",[])): errs.append(f"{dep} ownership still active")
    return {"task_id":tid,"mode":"activation-preflight","base":base,"head":h,"future_branch":c.get("future_builder_branch"),"reservation_patch":{"alias":c.get("planned_owned_alias"),"paths":c.get("planned_owned_paths",[])},"claim_command":c.get("claim_template","").replace("<EXACT_CURRENT_INTEGRATION_HEAD>",base),"passed":not errs,"errors":errs}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--task",choices=TASKS); ap.add_argument("--all",action="store_true"); ap.add_argument("--activate",action="store_true"); ap.add_argument("--base"); a=ap.parse_args()
    if a.all:
        if a.task or a.activate or a.base: raise SystemExit("--all is prep-only")
        rs=[prep(t) for t in TASKS]; collisions=cross(); out={"wave":"T53-T61","results":rs,"cross_task_path_collisions":collisions,"passed":all(x["passed"] for x in rs) and not collisions}
    else:
        if not a.task: raise SystemExit("use --all or --task")
        if a.activate and not a.base: raise SystemExit("--activate requires --base")
        out=activate(a.task,a.base) if a.activate else prep(a.task)
    print(json.dumps(out,indent=2)); raise SystemExit(0 if out.get("passed") else 1)
if __name__=="__main__": main()
