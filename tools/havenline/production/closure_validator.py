#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, pathlib
from lib import ROOT, DOCS, load_json, ensure_score_strictly_above_nine, sha256_file

ALL_GATES=[f"G{i}" for i in range(1,15)]
RESOURCE_REGISTRY=DOCS/"RESOURCE_ACTION_REGISTRY.json"
ACTOR_MATRIX=DOCS/"ACTOR_CAPABILITY_MATRIX.json"
ANIMATION_MATRIX=DOCS/"ANIMATION_ACTION_MATRIX.json"
GAME_MASTER_POLICY=DOCS/"GAME_MASTER_POLICY.json"

def has_placeholder(value,tokens):
    if isinstance(value,str):return any(token in value for token in tokens)
    if isinstance(value,list):return any(has_placeholder(v,tokens) for v in value)
    if isinstance(value,dict):return any(has_placeholder(v,tokens) for v in value.values())
    return False

def main():
    ap=argparse.ArgumentParser();ap.add_argument("manifest");a=ap.parse_args()
    p=pathlib.Path(a.manifest)
    if not p.is_absolute():p=ROOT/p
    d=json.loads(p.read_text());errors=[]
    task=d.get("task_id");candidate=d.get("candidate_commit");base=d.get("base_commit")
    graph=load_json(DOCS/"DEPENDENCY_GRAPH.json");critcfg=load_json(DOCS/"CRITIC_MATRIX.json");execfg=load_json(DOCS/"CRITIC_EXECUTION.json")
    resources=load_json(RESOURCE_REGISTRY);actors=load_json(ACTOR_MATRIX);animations=load_json(ANIMATION_MATRIX);gm_policy=load_json(GAME_MASTER_POLICY)
    if task not in graph["tasks"]:errors.append("unknown task")
    for dep in graph["tasks"].get(task,{}).get("dependencies",[]):
        if graph["tasks"][dep]["status"]!="APPROVED":errors.append("dependency not approved: "+dep)
    if not candidate or len(candidate)!=40:errors.append("invalid candidate commit")
    if not base or len(base)!=40:errors.append("invalid base commit")
    pv=d.get("path_validation",{})
    if pv.get("passed") is not True or pv.get("candidate")!=candidate or pv.get("base")!=base:errors.append("missing/invalid exact-candidate path validation")
    gates=d.get("gates",{})
    for gate in ALL_GATES:
        row=gates.get(gate)
        if not row:errors.append("missing gate "+gate);continue
        if row.get("status")=="N/A":
            if not row.get("rationale"):errors.append("N/A gate lacks rationale "+gate)
        elif row.get("status")!="PASS":errors.append("gate not PASS "+gate)
    tests=d.get("tests",{})
    if tests.get("passed") is not True or not tests.get("records"):errors.append("tests incomplete")
    evidence=d.get("evidence",{})
    if evidence.get("candidate_commit")!=candidate or not evidence.get("provenance_hash") or not evidence.get("files"):errors.append("evidence provenance incomplete/stale")
    else:
        root=(ROOT/evidence.get("root","")).resolve()
        for rel,h in evidence["files"].items():
            fp=root/rel
            if not fp.exists() or sha256_file(fp)!=h:errors.append("evidence hash mismatch "+rel)
    if d.get("unresolved_mandatory_defects"):errors.append("unresolved mandatory defects")

    policy=resources.get("task_policy",{})
    contract_applicable=task in policy.get("applicable_tasks",[])
    contract=d.get("resource_actor_contract",{})
    contract_c5_required=False
    if contract_applicable:
        if contract.get("applicable") is not True:errors.append("resource/actor contract not marked applicable")
        if contract.get("validation_passed") is not True:errors.append("resource/actor contract validation not passed")
        expected_hashes={
            "resource_action_registry":sha256_file(RESOURCE_REGISTRY),
            "actor_capability_matrix":sha256_file(ACTOR_MATRIX),
            "animation_action_matrix":sha256_file(ANIMATION_MATRIX),
        }
        got_hashes=contract.get("registry_hashes",{})
        for key,value in expected_hashes.items():
            if got_hashes.get(key)!=value:errors.append("resource/actor registry hash mismatch: "+key)

        introduced=set(contract.get("introduced_resource_ids",[]))
        covered_resources=set(contract.get("resource_ids_covered",[]))
        tokens=resources.get("placeholder_tokens",[])
        required_resources=set(policy.get("resource_resolution_tasks",{}).get(task,[]))
        for rid in sorted(required_resources|introduced):
            row=resources.get("resources",{}).get(rid)
            if not row:
                errors.append("unregistered resource: "+rid);continue
            if row.get("production_ready") is not True:errors.append("resource not production_ready: "+rid)
            if has_placeholder(row,tokens):errors.append("resource still unresolved: "+rid)
            if rid not in covered_resources:errors.append("resource missing contract coverage: "+rid)

        covered_actors=set(contract.get("actor_keys_covered",[]))
        for actor_key in actors.get("required_actor_keys_by_task",{}).get(task,[]):
            if actor_key not in covered_actors:errors.append("actor capability missing contract coverage: "+actor_key)

        covered_profiles=set(contract.get("animation_profiles_covered",[]))
        for profile_id in animations.get("required_profiles_by_task",{}).get(task,[]):
            if profile_id not in covered_profiles:errors.append("animation profile missing contract coverage: "+profile_id)

        animation_delta=bool(contract.get("animation_delta"))
        contract_c5_required=(task in policy.get("always_motion_critic_tasks",[]) or
            (task in policy.get("conditional_motion_critic_tasks",[]) and animation_delta))

        proof_path=contract.get("validator_output_path")
        proof_hash=contract.get("validator_output_sha256")
        if not proof_path or not proof_hash:
            errors.append("resource/actor validator proof missing")
        else:
            fp=(ROOT/proof_path).resolve()
            if not fp.exists() or sha256_file(fp)!=proof_hash:
                errors.append("resource/actor validator proof hash mismatch")
            else:
                proof=json.loads(fp.read_text())
                if proof.get("passed") is not True or proof.get("task_id")!=task:
                    errors.append("resource/actor validator proof failed/stale")
                proof_candidate=proof.get("candidate_commit")
                if proof_candidate and proof_candidate!=candidate:
                    errors.append("resource/actor validator candidate mismatch")
    elif contract and contract.get("applicable") is True:
        errors.append("resource/actor contract incorrectly marked applicable for task")

    gm_task_policy=gm_policy.get("task_policy",{})
    gm_applicable=task in gm_task_policy.get("applicable_tasks",[])
    gm_contract=d.get("game_master_contract",{})
    if gm_applicable:
        if gm_contract.get("applicable") is not True:errors.append("Game Master contract not marked applicable")
        if gm_contract.get("validation_passed") is not True:errors.append("Game Master contract validation not passed")
        if gm_contract.get("policy_sha256")!=sha256_file(GAME_MASTER_POLICY):errors.append("Game Master policy hash mismatch")
        flags=gm_contract.get("proof_flags",{})
        for flag in gm_task_policy.get("required_proof_flags_by_task",{}).get(task,[]):
            if flags.get(flag) is not True:errors.append("missing Game Master proof flag: "+flag)
        if task in gm_task_policy.get("owner_binding_tasks",[]):
            if gm_contract.get("owner_slots_bound_count")!=2:errors.append("Game Master owner-slot count must be two")
            if not gm_contract.get("server_binding_proof_hash"):errors.append("Game Master binding proof missing")
        proof_path=gm_contract.get("validator_output_path")
        proof_hash=gm_contract.get("validator_output_sha256")
        if not proof_path or not proof_hash:
            errors.append("Game Master validator proof missing")
        else:
            fp=(ROOT/proof_path).resolve()
            if not fp.exists() or sha256_file(fp)!=proof_hash:
                errors.append("Game Master validator proof hash mismatch")
            else:
                proof=json.loads(fp.read_text())
                if proof.get("passed") is not True or proof.get("task_id")!=task:
                    errors.append("Game Master validator proof failed/stale")
                proof_candidate=proof.get("candidate_commit")
                if proof_candidate and proof_candidate!=candidate:
                    errors.append("Game Master validator candidate mismatch")
    elif gm_contract and gm_contract.get("applicable") is True:
        errors.append("Game Master contract incorrectly marked applicable for task")

    required=list(critcfg["task_applicability"].get(task,[]))
    if contract_c5_required and "C5" not in required:required.append("C5")
    critics=d.get("critics",{})
    for cid in required:
        row=critics.get(cid)
        if not row:errors.append("missing critic "+cid);continue
        if row.get("status")!="PASS":errors.append("critic not PASS "+cid)
        if row.get("candidate_commit")!=candidate:errors.append("critic candidate mismatch "+cid)
        errors += [f"{cid}: {x}" for x in ensure_score_strictly_above_nine(row.get("scores",{}))]
        if row.get("defects"):errors.append("critic defects "+cid)
        if row.get("coverage_complete") is not True:errors.append("critic incomplete "+cid)
        if critcfg["critics"][cid].get("independent_model_required") and row.get("independent_runtime") is not True:errors.append("independent runtime not proven "+cid)
        expected=set(execfg["critics"].get(cid,{}).get("dimensions",[]))
        if expected and set(row.get("scores",{}))!=expected:errors.append("critic dimension coverage mismatch "+cid)
        if cid in ("C7","C8","C10","C11"):
            supplement=row.get("deterministic_supplement",{})
            if supplement.get("passed") is not True or supplement.get("candidate_commit")!=candidate:errors.append("deterministic supplement missing/failed "+cid)
        if cid=="C9":
            if len(row.get("scores",{}))!=10:errors.append("C9 attack coverage incomplete")
    integ=d.get("integration",{})
    if integ.get("candidate_commit")!=candidate or integ.get("regression_passed") is not True:errors.append("integration candidate regression missing")
    result={"task_id":task,"candidate_commit":candidate,"passed":not errors,"errors":errors,"approval_allowed":not errors}
    print(json.dumps(result,indent=2))
    if errors:raise SystemExit(1)
if __name__=="__main__":main()
