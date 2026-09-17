#!/usr/bin/env python3
from __future__ import annotations
import datetime, pathlib, sys
from lib import DOCS, ROOT, load_json, expand_alias, sha256_file
from forward_execution import resolve_task
from architecture_v3 import task_readiness
from architecture_v31 import task_readiness as task_readiness_v31

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

    if task_id.startswith("T") and task_id[1:].isdigit() and int(task_id[1:]) >= 10:
        forward=resolve_task(task_id)
        text+="\n## Forward execution profile — machine resolved\n"
        text+=f"- Standard: `Docs/Production/FORWARD_EXECUTION_STANDARD.md`\n"
        text+=f"- Resolver: `python3 tools/havenline/production/forward_execution.py plan {task_id}`\n"
        text+=f"- Archetype: `{forward['archetype']}`\n"
        text+=f"- Execution mode: `{forward['execution_mode']}`\n"
        text+=f"- Dependency states: `{', '.join(f'{k}={v}' for k,v in forward['dependency_status'].items()) or 'none'}`\n"
        text+=f"- Dependencies currently approved: `{str(forward['dependencies_approved']).lower()}`\n"
        text+=f"- Canonical packet currently present: `{str(forward['canonical_packet_present']).lower()}`\n"
        text+=f"- Activation ready now: `{str(forward['activation_ready']).lower()}`\n"
        text+=f"- Early sentinel: {forward['early_sentinel']}\n"
        text+="- Ordered fail-fast gates:\n"+"\n".join(f"  {idx+1}. `{gate}`" for idx,gate in enumerate(forward['ordered_gates']))+"\n"
        text+=f"- Terminal-failure disposition: {forward['failure_disposition']}\n"
        text+="- Exact-SHA rule: finish the candidate already under review; newer candidates queue. Do not use `cancel-in-progress: true` for task candidate review.\n"
        text+="- Do not run expensive downstream evidence after an earlier required gate fails. Preserve the exact failure and invoke C0.\n"
        if forward['execution_mode'] != 'build':
            text+="- This task is not a runtime-repair owner. A discovered runtime defect must be routed through C0/change request to the owning build task.\n"

        v3=task_readiness(task_id);feas=v3['feasibility'];sched=v3.get('scheduler') or {};contracts=v3['contracts']
        text+="\n## Production Architecture V3 — machine resolved\n"
        text+="- Standard: `Docs/Production/PRODUCTION_ARCHITECTURE_V3.md`\n"
        text+=f"- V3 readiness: `python3 tools/havenline/production/architecture_v3.py readiness {task_id}`\n"
        text+=f"- Feasibility state: `{feas['activation_state']}`\n"
        text+=f"- Runtime activation allowed now: `{str(feas['runtime_activation_allowed']).lower()}`\n"
        text+=f"- Capability blockers: {', '.join(feas['capability_blockers']) or 'none'}\n"
        if sched:text+=f"- Scheduler class: `{sched['classification']}`; deterministic priority score: `{sched['priority_score']}` (scheduling heuristic only, never an acceptance score).\n"
        text+=f"- Produces versioned contracts: {', '.join(x['contract_id'] for x in contracts['produces']) or 'none'}\n"
        text+=f"- Consumes versioned contracts: {', '.join(x['contract_id'] for x in contracts['consumes']) or 'none'}\n"
        text+="- Before runtime activation: resolve all required capabilities; unknown external/hardware prerequisites are not READY.\n"
        text+="- Before integration: run `synthetic_merge_forecast.py` against the current integration head and validate any affected shared contract change.\n"
        text+="- Gate proof reuse is allowed only through `gate_fingerprint.py`; exact-source-only gates remain fresh and failed results can never be reused as PASS.\n"
        text+="- C0 must query `FAILURE_INTELLIGENCE.json` before repair; historical matches are advisory and require confirmation from current evidence.\n"
        if not feas['runtime_activation_allowed']:text+="- **DO NOT start runtime implementation from this packet yet.** Preparation is allowed, but the recorded V3 activation blocker(s) must clear first.\n"

        v31=task_readiness_v31(task_id)
        text+="\n## Production Architecture V3.1 — machine resolved\n"
        text+="- Standard: `Docs/Production/PRODUCTION_ARCHITECTURE_V31_STANDARD.md`\n"
        text+=f"- V3.1 readiness: `python3 tools/havenline/production/architecture_v31.py readiness {task_id}`\n"
        text+=f"- Canonical task-state snapshot: `python3 tools/havenline/production/task_state_snapshot.py {task_id}`\n"
        text+="- Persistent flake history may change diagnosis/retry routing only; a mandatory flaky gate still blocks approval.\n"
        text+="- Pipeline telemetry records queue/run/gate cost for factory optimization; it cannot change quality thresholds.\n"
        text+="- Environment-sensitive proof reuse requires matching runner/toolchain provenance under `CI_TOOLCHAIN_LOCK.json`.\n"
        text+="- Approval closeout must satisfy `EVIDENCE_RETENTION_POLICY.json`; artifact expiry cannot erase approval provenance.\n"
        text+="- Runtime-observed dependencies are additive only and may add regression suites, never remove static mandatory coverage.\n"
        text+="- Mutation canaries must pass before architecture closeout.\n"
        text+=f"- If this task or a consumed contract is reopened, run `python3 tools/havenline/production/proof_invalidation.py task {task_id}` or the affected contract form before reusing downstream proof.\n"
        text+=f"- V3.1 runtime activation allowed now: `{str(v31['runtime_activation_allowed']).lower()}`\n"

    text+="""

## Score rule
Every applicable mandatory reviewed dimension must be strictly >9.0 unrounded.
Target 10/10. No averaging and no unresolved mandatory defects.

## Critic independence
C1/C2 and every specialist critic marked independent-model-required must run in a separate review job/runtime. A builder prompt, persona swap, or self-review never qualifies. If the zero-cost independent runtime is unavailable, construction/testing may continue but approval remains BLOCKED.

## Evidence
Exact-source hashes, changed-file manifest, deterministic engine views, performance records, applicable save/device matrices, raw critic inputs/outputs, deterministic supplements, known failures and final dispositions are mandatory before APPROVED. Use `specialist_evidence_manifest.py` for C3/C4/C5/C7/C8/C10/C11; C9 uses `security_exploit_harness.py`. Approval provenance must also satisfy the V3.1 retention policy.

## Scope
Use the authoritative task-specific frozen scope when present. This generated packet does not expand runtime scope.
"""
    out=DOCS/"Evidence"/task_id/"TASK_PACKET.md";out.parent.mkdir(parents=True,exist_ok=True);out.write_text(text,encoding="utf-8");print(out.relative_to(ROOT))
if __name__=="__main__":main()
