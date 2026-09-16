#!/usr/bin/env python3
"""Fail-closed final acceptance/release prep validator for Havenline T62-T70."""
from __future__ import annotations
import argparse,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[3]; DOCS=ROOT/"Docs"/"Production"; TASKS=[f"T{i:02d}" for i in range(62,71)]
def load(p): return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
def prefix(p):
    cut=len(p)
    for t in ("*","?","["):
        i=p.find(t)
        if i>=0: cut=min(cut,i)
    return p[:cut].rstrip("/")
def overlap(a,b):
    pa,pb=prefix(a),prefix(b); return a==b or not pa or not pb or pa==pb or pa.startswith(pb+"/") or pb.startswith(pa+"/")
def reg_status(reg,tid):
    if tid in reg.get("legacy_approvals",{}): return "APPROVED"
    row=next((x for x in reg.get("workstreams",[]) if x.get("task_id")==tid),None); return (row or {}).get("status")
def prep(tid):
    errs=[]; d=DOCS/tid
    for n in ("FROZEN_SCOPE.md","TASK_PACKET.md","PREBUILD_CONTRACT.json","defect-ledger.json","ACTIVATION_CHECKLIST.json"):
        p=d/n
        if not p.exists() or not p.read_text(encoding="utf-8").strip(): errs.append(f"missing/empty {p.relative_to(ROOT)}")
    if errs: return {"task_id":tid,"passed":False,"errors":errs}
    c=load(d/"ACTIVATION_CHECKLIST.json"); p=load(d/"PREBUILD_CONTRACT.json"); defect=load(d/"defect-ledger.json"); graph=load(DOCS/"DEPENDENCY_GRAPH.json"); own=load(DOCS/"PATH_OWNERSHIP.json"); gm=load(DOCS/"GAME_MASTER_POLICY.json"); row=graph.get("tasks",{}).get(tid,{})
    if c.get("dependencies")!=row.get("dependencies"): errs.append("dependency mismatch")
    if set(c.get("required_critics",[]))!=set(row.get("critics",[])): errs.append("critic mismatch")
    if c.get("runtime_status")!="LOCKED" or c.get("runtime_build_allowed_before_activation") is not False: errs.append("runtime must remain locked")
    if c.get("acceptance_only") is not True or p.get("acceptance_only") is not True: errs.append("final wave task must be acceptance-only")
    if c.get("production_patch_forbidden_during_acceptance") is not True or p.get("production_patch_forbidden_during_acceptance") is not True: errs.append("production patch prohibition missing")
    required=gm.get("task_policy",{}).get("required_proof_flags_by_task",{}).get(tid,[]); supplied=c.get("game_master_required_proof_flags",[])
    if required!=supplied: errs.append(f"Game Master flags mismatch required={required} supplied={supplied}")
    if tid=="T63" and (c.get("game_master_excluded_from_population") is not True or p.get("game_master_excluded_from_population") is not True): errs.append("T63 must exclude Game Master population")
    if tid in ("T68","T69"):
        for k,v in (("physical_device_only",True),("native_internal_min_width",3840),("native_internal_min_height",2160),("sustained_min_fps",60),("completed_game_load_required",True),("emulator_software_renderer_cannot_certify",True)):
            if c.get(k)!=v or p.get(k)!=v: errs.append(f"{tid} physical certification rule mismatch {k}")
    if tid=="T70":
        if c.get("owner_slot_count_required")!=2 or p.get("owner_slot_count_required")!=2: errs.append("T70 requires exactly two owner slots")
        if c.get("physical_certifications_must_match_release_candidate") is not True: errs.append("T70 exact-candidate physical certification binding missing")
    paths=c.get("planned_owned_paths",[])
    for cand in paths:
        for protected in own.get("aliases",{}).get("@integration-only",[]):
            if overlap(cand,protected): errs.append(f"integration-only collision {cand} vs {protected}")
        for owner in own.get("active_owners",[]):
            for foreign in own.get("aliases",{}).get(owner.get("paths_alias"),[]):
                if overlap(cand,foreign): errs.append(f"active collision {cand} vs {owner.get('task_id')}:{foreign}")
    if defect.get("unresolved_preparation_defects"): errs.append("unresolved preparation defects")
    return {"task_id":tid,"graph_status":row.get("status"),"paths":len(paths),"acceptance_only":True,"passed":not errs,"errors":errs}
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
        rs=[prep(t) for t in TASKS]; collisions=cross(); out={"wave":"T62-T70","results":rs,"cross_task_path_collisions":collisions,"passed":all(x["passed"] for x in rs) and not collisions}
    else:
        if not a.task: raise SystemExit("use --all or --task")
        if a.activate and not a.base: raise SystemExit("--activate requires --base")
        out=activate(a.task,a.base) if a.activate else prep(a.task)
    print(json.dumps(out,indent=2)); raise SystemExit(0 if out.get("passed") else 1)
if __name__=="__main__": main()
