#!/usr/bin/env python3
from __future__ import annotations
import datetime, pathlib, sys
from lib import DOCS, ROOT, load_json, expand_alias, sha256_file

RESOURCE_REGISTRY = DOCS / "RESOURCE_ACTION_REGISTRY.json"
ACTOR_MATRIX = DOCS / "ACTOR_CAPABILITY_MATRIX.json"
ANIMATION_MATRIX = DOCS / "ANIMATION_ACTION_MATRIX.json"

def _contract_file(rel):
    if not rel:return None
    p=ROOT/rel
    return p if p.exists() else None

def main():
    if len(sys.argv)!=2:raise SystemExit("usage: task_packet.py T04")
    task_id=sys.argv[1].upper();graph=load_json(DOCS/"DEPENDENCY_GRAPH.json");registry=load_json(DOCS/"WORKSTREAM_REGISTRY.json");ownership=load_json(DOCS/"PATH_OWNERSHIP.json");critics=load_json(DOCS/"CRITIC_MATRIX.json");execution=load_json(DOCS/"CRITIC_EXECUTION.json");task_gates=load_json(DOCS/"task-gates.json")
    resources=load_json(RESOURCE_REGISTRY);actors=load_json(ACTOR_MATRIX);animations=load_json(ANIMATION_MATRIX)
    if task_id not in graph["tasks"]:raise SystemExit(f"unknown task {task_id}")
    task=graph["tasks"][task_id];ws=next((w for w in registry["workstreams"] if w["task_id"]==task_id),None)
    owned=expand_alias(ws.get("owned_paths",[]),ownership) if ws else [];protected=expand_alias(ws.get("protected_paths",[]),ownership) if ws else []
    branch=ws.get("branch") if ws else None;base=ws.get("base_commit") if ws else None;owner=ws.get("owner") if ws else None;workstream=ws.get("workstream_id") if ws else None
    required=list(critics["task_applicability"].get(task_id,[]))
    policy=resources.get("task_policy",{})
    contract_applicable=task_id in policy.get("applicable_tasks",[])
    conditional_c5=task_id in policy.get("conditional_motion_critic_tasks",[])
    if task_id in policy.get("always_motion_critic_tasks",[]) and "C5" not in required: required.append("C5")
    gates=[f"G{i}" for i in range(1,15)]
    text=f"""# Havenline frozen task packet — {task_id}

Generated: {datetime.datetime.now(datetime.timezone.utc).isoformat()}

## Identity
- Task ID: {task_id}
- Task name: {task['name']}
- Workstream ID: {workstream or 'UNASSIGNED'}
- Owner: {owner or 'UNASSIGNED'}
- Isolated branch: {branch or 'UNASSIGNED'}
- Exact base integration commit: {base or 'UNASSIGNED'}

## Dependencies
Required APPROVED upstream tasks: {', '.join(task['dependencies']) or 'none'}

## Owned paths
"""
    text+="\n".join(f"- `{p}`" for p in owned) or "- UNASSIGNED"
    text+="\n\n## Protected paths\n"+("\n".join(f"- `{p}`" for p in protected) or "- resolve from PATH_OWNERSHIP.json")
    text+="\n\n## Acceptance gates\n"+"\n".join(f"- {g}: REQUIRED unless this packet records explicit N/A rationale." for g in gates)
    text+="\n\n## Required critics and executable safeguards\n"
    if not required:text+="- none\n"
    for cid in required:
        row=execution["critics"][cid];text+=f"- **{cid} — {critics['critics'][cid]['name']}**: `{row['runner']}`; dimensions: {', '.join(row['dimensions'])}.\n"
        if row.get('deterministic_runner'):text+=f"  - deterministic supplement: `{row['deterministic_runner']}`\n"
        if row.get('capture_runner'):text+=f"  - required capture harness: `{row['capture_runner']}`\n"
        if row.get('device_runner'):text+=f"  - device/layout harness: `{row['device_runner']}`\n"
        if row.get('required_categories'):text+=f"  - evidence categories: {', '.join(row['required_categories'])}\n"
    if contract_applicable:
        text+="\n## Resource / tool / actor / animation contract\n"
        text+="- REQUIRED by `Docs/Production/RESOURCE_TOOL_ACTOR_STANDARD.md`.\n"
        text+=f"- Resource registry SHA256: `{sha256_file(RESOURCE_REGISTRY)}`\n"
        text+=f"- Actor capability matrix SHA256: `{sha256_file(ACTOR_MATRIX)}`\n"
        text+=f"- Animation action matrix SHA256: `{sha256_file(ANIMATION_MATRIX)}`\n"
        rr=policy.get("resource_resolution_tasks",{}).get(task_id,[])
        ra=actors.get("required_actor_keys_by_task",{}).get(task_id,[])
        rp=animations.get("required_profiles_by_task",{}).get(task_id,[])
        text+=f"- Resources this task must resolve/prove: {', '.join(rr) or 'none predeclared; any introduced resource must still be registered'}\n"
        text+=f"- Actor capability keys this task must prove: {', '.join(ra) or 'none predeclared'}\n"
        text+=f"- Animation profiles this task must prove: {', '.join(rp) or 'none predeclared'}\n"
        text+="- Run `python3 tools/havenline/production/resource_actor_contract.py --task %s --manifest <candidate-manifest> --output <proof.json>` before closure.\n" % task_id
        if conditional_c5:text+="- C5 becomes mandatory if this candidate introduces any new actor action or animation profile (`animation_delta=true`).\n"
    else:
        text+="\n## Resource / tool / actor / animation contract\n- N/A for this task under the current forward policy. Do not expand frozen scope merely because the contract exists.\n"

    text+="\n## Registered forward contracts\n"
    matched=[]
    for contract_id,row in task_gates.get("forward_contracts",{}).items():
        if task_id not in row.get("applicable_tasks",[]):continue
        matched.append(contract_id)
        text+=f"- **{contract_id}**: REQUIRED for {task_id}.\n"
        for field in ("standard","policy"):
            rel=row.get(field);fp=_contract_file(rel)
            if rel:text+=f"  - {field}: `{rel}`"+(f"; SHA256 `{sha256_file(fp)}`" if fp else "; MISSING")+"\n"
        policy_path=_contract_file(row.get("policy"))
        if policy_path:
            cfg=load_json(policy_path)
            flags=cfg.get("task_policy",{}).get("required_proof_flags_by_task",{}).get(task_id,[])
            if flags:text+=f"  - required proof flags: {', '.join(flags)}\n"
    if not matched:text+="- none registered for this task.\n"

    text+="""

## Score rule
Every applicable mandatory reviewed dimension must be strictly >9.0 unrounded.
Target 10/10. No averaging and no unresolved mandatory defects.

## Critic independence
C1/C2 and every specialist critic marked independent-model-required must run in a separate review job/runtime. A builder prompt, persona swap, or self-review never qualifies. If the zero-cost independent runtime is unavailable, construction/testing may continue but approval remains BLOCKED.

## Evidence
Exact-source hashes, changed-file manifest, deterministic engine views, performance records, applicable save/device matrices, raw critic inputs/outputs, deterministic supplements, known failures and final dispositions are mandatory before APPROVED. Use `specialist_evidence_manifest.py` for C3/C4/C5/C7/C8/C10/C11; C9 uses `security_exploit_harness.py`.

## Scope
Use the authoritative task-specific frozen scope when present. This generated packet does not expand runtime scope.
"""
    out=DOCS/"Evidence"/task_id/"TASK_PACKET.md";out.parent.mkdir(parents=True,exist_ok=True);out.write_text(text,encoding="utf-8");print(out.relative_to(ROOT))
if __name__=="__main__":main()
