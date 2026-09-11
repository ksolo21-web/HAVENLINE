#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime, json, pathlib
from lib import DOCS, ROOT, load_json, expand_alias, any_match, changed_files, json_dump, fail

ACTIVE_STATES = {"PREPARED","ASSIGNED","BUILDING_ISOLATED","BUILT_PENDING_DEPENDENCY","INTEGRATION_READY","INTEGRATING","UNDER_REVIEW","FIX_REQUIRED","BLOCKED"}
ALLOWED_STATES = {"LOCKED","PREPARED","ASSIGNED","BUILDING_ISOLATED","BUILT_PENDING_DEPENDENCY","INTEGRATION_READY","INTEGRATING","UNDER_REVIEW","FIX_REQUIRED","APPROVED","BLOCKED"}

def approved_change_requests(task_id: str) -> set[str]:
    root = DOCS / "ChangeRequests";result=set()
    if not root.exists():return result
    for p in root.glob("*.json"):
        try:d=json.loads(p.read_text())
        except Exception:continue
        if d.get("requesting_task")==task_id and d.get("status")=="APPROVED" and d.get("integration_owner_disposition")=="AUTHORIZED":
            result.add(d.get("target_path",""))
    return result

def registry_errors(registry=None):
    registry=registry or load_json(DOCS/"WORKSTREAM_REGISTRY.json")
    ownership=load_json(DOCS/"PATH_OWNERSHIP.json")
    graph=load_json(DOCS/"DEPENDENCY_GRAPH.json")
    errors=[];ids=set();active=[]
    for ws in registry["workstreams"]:
        wid=ws["workstream_id"]
        if wid in ids:errors.append(f"duplicate workstream_id {wid}")
        ids.add(wid)
        if ws["status"] not in ALLOWED_STATES:errors.append(f"invalid state {wid}: {ws['status']}")
        if ws["task_id"].startswith("T") and ws["task_id"] not in graph["tasks"]:errors.append(f"unknown task in registry: {ws['task_id']}")
        if ws["status"] in ACTIVE_STATES and ws.get("owner"):
            active.append((wid,ws["task_id"],expand_alias(ws.get("owned_paths",[]),ownership)))
    for i,(wa,ta,pa) in enumerate(active):
        for wb,tb,pb in active[i+1:]:
            for a in pa:
                for b in pb:
                    prefix_a=a[:-3] if a.endswith("/**") else None
                    prefix_b=b[:-3] if b.endswith("/**") else None
                    collide=a==b
                    if not collide and "*" not in a and any_match(a,[b]):collide=True
                    if not collide and "*" not in b and any_match(b,[a]):collide=True
                    if not collide and prefix_a and prefix_b and (prefix_a.startswith(prefix_b) or prefix_b.startswith(prefix_a)):collide=True
                    if collide:errors.append(f"ownership collision {wa}/{ta} <-> {wb}/{tb}: {a} <> {b}")
    return errors

def deps_approved(task_id,graph):
    return [d for d in graph["tasks"][task_id]["dependencies"] if graph["tasks"][d]["status"]!="APPROVED"]

def claim(task_id,owner,branch,base,owned_alias,status):
    registry=load_json(DOCS/"WORKSTREAM_REGISTRY.json");graph=load_json(DOCS/"DEPENDENCY_GRAPH.json")
    if task_id not in graph["tasks"]:fail("unknown task "+task_id)
    if status not in ("PREPARED","ASSIGNED"):fail("claim status must be PREPARED or ASSIGNED")
    blocked=deps_approved(task_id,graph)
    if status=="ASSIGNED" and blocked:fail("cannot ASSIGN; dependencies not approved: "+",".join(blocked))
    existing=next((w for w in registry["workstreams"] if w["task_id"]==task_id),None)
    row=existing or {"task_id":task_id,"task_name":graph["tasks"][task_id]["name"],"workstream_id":f"{task_id}-{owner}"}
    row.update({"status":status,"owner":owner,"branch":branch,"base_commit":base,"dependencies":graph["tasks"][task_id]["dependencies"],
                "owned_paths":[owned_alias],"protected_paths":["@protected:approved","@integration-only"],"candidate_commit":None,
                "candidate_hash_or_artifact":None,"tests":{},"evidence_path":f"Docs/Production/Evidence/{task_id}/",
                "critic_requirements":graph["tasks"][task_id]["critics"],"critic_status":{},"integration_status":"not integrated",
                "known_blockers":[f"waiting on {x}" for x in blocked],"next_action":"Build isolated candidate only after ASSIGNED."})
    if not existing:registry["workstreams"].append(row)
    errs=registry_errors(registry)
    if errs:fail("claim rejected:\n"+"\n".join(errs))
    json_dump(DOCS/"WORKSTREAM_REGISTRY.json",registry)
    print(json.dumps(row,indent=2))

def set_status(task_id,status):
    if status not in ALLOWED_STATES:fail("invalid status")
    registry=load_json(DOCS/"WORKSTREAM_REGISTRY.json")
    ws=next((w for w in registry["workstreams"] if w["task_id"]==task_id),None)
    if not ws:fail("unregistered task")
    ws["status"]=status;ws["status_updated_at"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
    errs=registry_errors(registry)
    if errs:fail("\n".join(errs))
    json_dump(DOCS/"WORKSTREAM_REGISTRY.json",registry);print(json.dumps(ws,indent=2))

def validate_candidate(task_id: str, base: str, head: str, integration_head: str|None):
    registry=load_json(DOCS/"WORKSTREAM_REGISTRY.json");ownership=load_json(DOCS/"PATH_OWNERSHIP.json");graph=load_json(DOCS/"DEPENDENCY_GRAPH.json")
    ws=next((x for x in registry["workstreams"] if x["task_id"]==task_id),None)
    if not ws:fail(f"{task_id} not registered")
    errors=registry_errors()
    expected_base=ws.get("base_commit")
    if expected_base and base!=expected_base:errors.append(f"base mismatch: registry {expected_base}, candidate {base}")
    for dep in deps_approved(task_id,graph):errors.append(f"dependency not approved: {dep}")
    if integration_head and base!=integration_head:errors.append(f"stale base: candidate {base}, current integration {integration_head}; reconcile before integration")
    owned=expand_alias(ws.get("owned_paths",[]),ownership);protected=expand_alias(ws.get("protected_paths",[]),ownership);authorized=approved_change_requests(task_id)
    foreign=[]
    for other in registry["workstreams"]:
        if other["task_id"]==task_id or other["status"] not in ACTIVE_STATES or not other.get("owner"):continue
        foreign+=expand_alias(other.get("owned_paths",[]),ownership)
    files=changed_files(base,head)
    for path in files:
        if not(any_match(path,owned) or path in authorized):errors.append(f"unauthorized path for {task_id}: {path}")
        if any_match(path,foreign) and path not in authorized:errors.append(f"foreign-owned path for {task_id}: {path}")
        if any_match(path,protected) and not any_match(path,owned) and path not in authorized:errors.append(f"protected path for {task_id}: {path}")
    result={"task_id":task_id,"base":base,"head":head,"integration_head":integration_head,"changed_files":files,"authorized_change_requests":sorted(authorized),"passed":not errors,"errors":errors}
    print(json.dumps(result,indent=2))
    if errors:raise SystemExit(1)

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("validate-registry")
    c=sub.add_parser("validate-candidate");c.add_argument("task_id");c.add_argument("--base",required=True);c.add_argument("--head",default="HEAD");c.add_argument("--integration-head")
    cl=sub.add_parser("claim");cl.add_argument("task_id");cl.add_argument("--owner",required=True);cl.add_argument("--branch",required=True);cl.add_argument("--base",required=True);cl.add_argument("--owned-alias",required=True);cl.add_argument("--status",default="PREPARED")
    ss=sub.add_parser("set-status");ss.add_argument("task_id");ss.add_argument("status")
    a=ap.parse_args()
    if a.cmd=="validate-registry":
        errors=registry_errors();print(json.dumps({"passed":not errors,"errors":errors},indent=2))
        if errors:raise SystemExit(1)
    elif a.cmd=="validate-candidate":validate_candidate(a.task_id,a.base,a.head,a.integration_head)
    elif a.cmd=="claim":claim(a.task_id,a.owner,a.branch,a.base,a.owned_alias,a.status)
    else:set_status(a.task_id,a.status)

if __name__=="__main__":main()
