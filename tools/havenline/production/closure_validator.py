#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math, pathlib, re, subprocess
from datetime import datetime,timezone
from lib import ROOT, DOCS, ensure_score_strictly_above_nine, sha256_file
from evidence_retention import validate_manifest as validate_retention_manifest
from task_state_snapshot import validate as validate_task_state
from critic_profile import resolve_critic
from reference_style_lock import style_lock_required, validate_manifest as validate_reference_style_lock
from reference_acceptance import binding_errors, declared_reference_dimensions, final_rule, load_json_strict as load_json, nonapproving_scope_errors, record_errors, required_final_critics, strict_json_loads
from shipping_visual_gate import active_invalidation, effective_approval, validate_signoff

ALL_GATES=[f"G{i}" for i in range(1,15)]
RESOURCE_REGISTRY=DOCS/"RESOURCE_ACTION_REGISTRY.json"
ACTOR_MATRIX=DOCS/"ACTOR_CAPABILITY_MATRIX.json"
ANIMATION_MATRIX=DOCS/"ANIMATION_ACTION_MATRIX.json"
GAME_MASTER_POLICY=DOCS/"GAME_MASTER_POLICY.json"


T09_CLOSURE_CHECKPOINT="62f5a13753968c77a0feb47a18d93c82d8c5b581"
T09_COMPLETION_SHA256="2b69ffad9979b1620d3a48a77f049dc7756b85e1c7a6ee33c8c3dd75254c0059"

def t09_historical_lifecycle_errors(completion_bytes):
    """Bind closeout-time invariants to immutable history; all other checks stay current."""
    errors=[]
    try:
        def historical(name):
            return subprocess.check_output(["git","show",T09_CLOSURE_CHECKPOINT+":Docs/Production/"+name],cwd=ROOT,stderr=subprocess.PIPE)
        recorded=historical("T09/verified-completion.json")
        if recorded!=completion_bytes or hashlib.sha256(recorded).hexdigest()!=T09_COMPLETION_SHA256:
            return ["T09 completion differs from pinned historical closure"]
        completion=json.loads(recorded)
        if completion.get("task_id")!="T09":return ["historical closure task mismatch"]
        graph=json.loads(historical("DEPENDENCY_GRAPH.json"))
        ownership=json.loads(historical("PATH_OWNERSHIP.json"))
        task_gates=json.loads(historical("task-gates.json"))
        if graph["tasks"]["T09"]["status"]!="APPROVED":errors.append("historical T09 closure is not APPROVED")
        future=[tid for tid in (f"T{i:02d}" for i in range(10,71)) if graph["tasks"][tid]["status"]!="LOCKED"]
        if future:errors.append("T10+ must remain LOCKED at T09 historical closeout: "+",".join(future))
        active_future=[row["task_id"] for row in ownership["active_owners"] if str(row["task_id"])>="T10"]
        if active_future:errors.append("T10+ active ownership exists at T09 historical closeout")
        active_keys={key for key in task_gates if key.startswith("active_")}
        if not {"active_task","active_status","active_base_integration_commit"}<=active_keys:
            errors.append("historical task-gates activation fields missing")
        active_values={key:task_gates[key] for key in active_keys if task_gates[key] not in (None,[],{})}
        if active_values:errors.append("all task-gates active_* fields must be clear at T09 historical closeout")
    except (OSError,subprocess.SubprocessError,ValueError,KeyError,TypeError,AttributeError) as exc:
        errors.append("invalid or unavailable T09 historical closure: "+str(exc))
    return errors

def has_placeholder(value,tokens):
    if isinstance(value,str):return any(token in value for token in tokens)
    if isinstance(value,list):return any(has_placeholder(v,tokens) for v in value)
    if isinstance(value,dict):return any(has_placeholder(v,tokens) for v in value.values())
    return False

RAW_ACCEPTANCE_RULE=">9.0 unrounded in every mandatory dimension; no averaging; zero mandatory defects"

def valid_reviewer_confidence(value):
    """Accept original reviewer schemas without assigning or converting confidence."""
    if isinstance(value,str):
        return value in {"high","medium"}
    return isinstance(value,(int,float)) and not isinstance(value,bool) and 0<value<=1

def minimum_score(scores):
    values=list(scores.values()) if isinstance(scores,dict) else scores
    if not isinstance(values,list) or not values:return None
    if any(type(value) not in (int,float) or not 0<=value<=10 for value in values):return None
    return min(values)

def validate_original_review_transport(raw):
    """Current final exports must retain actual request and reviewer response bytes."""
    errors=nonapproving_scope_errors(raw);transport=raw.get('review_transport',{})
    if not isinstance(transport,dict):return ['original reviewer transport is missing']
    kind=transport.get('kind');cid=raw.get('critic_id')
    pointer_kinds={'external_independent_review_v1':{'C1','C2','C5'},
        'deterministic_security_harness_v1':{'C9'},'scored_performance_review_v1':{'C6'}}
    if kind in pointer_kinds:
        if cid not in pointer_kinds[kind]:return ['original review transport cannot waive this critic execution lane']
        from critic_harness import validate_raw
        rel=transport.get('critic_record_path');digest=transport.get('critic_record_sha256')
        if not isinstance(rel,str) or not rel or not isinstance(digest,str) or not re.fullmatch(r'[0-9a-f]{64}',digest):
            return ['external independent critic record path/hash missing']
        path=ROOT/rel
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT.resolve()) or not path.is_file() or sha256_file(path)!=digest:
            return ['external independent critic record bytes missing or mismatched']
        check=validate_raw(path,raw.get('critic_id'),raw.get('candidate_commit'))
        errors += ['external independent review: '+message for message in check.get('errors',[])]
        if check.get('passed') is not True:errors.append('external independent review did not pass')
        record=check.get('record',{})
        for key in ('scores','defects','coverage_complete','confidence','reference_acceptance','reference_sensitive_dimensions','provider','model','request_or_run_id'):
            if record.get(key)!=raw.get(key):errors.append('external normalized raw mismatch: '+key)
        if record.get('task_id')!=raw.get('task_id'):errors.append('external independent task identity mismatch')
        if record.get('complete_evidence_index_sha256')!=raw.get('complete_evidence_index_sha256'):
            errors.append('external independent review is not bound to this complete evidence index')
        return errors
    if kind!='automated_request_response_v1':
        return ['unsupported original review transport; legacy formats are historical-only']
    if cid in ('C6','C9'):
        return ['C6/C9 require their current validated measured-performance or deterministic-attack transport; score-only request/response cannot approve']
    if raw.get('critic_id')=='C5':
        errors.append('static request/response transport cannot approve C5; independent temporal playback transport is required')
    documents={}
    for label in ('request','response'):
        rel=transport.get(label+'_path');digest=transport.get(label+'_sha256')
        if not isinstance(rel,str) or not rel or not isinstance(digest,str) or not re.fullmatch(r'[0-9a-f]{64}',digest):
            errors.append('original reviewer '+label+' path/hash missing');continue
        path=ROOT/rel
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT.resolve()) or not path.is_file():
            errors.append('original reviewer '+label+' file missing or unsafe');continue
        body=path.read_bytes()
        if hashlib.sha256(body).hexdigest()!=digest:errors.append('original reviewer '+label+' hash mismatch');continue
        try:documents[label]=strict_json_loads(body)
        except ValueError as exc:errors.append('original reviewer '+label+' invalid JSON: '+str(exc))
    request=documents.get('request')
    if isinstance(request,dict):
        text=json.dumps(request,sort_keys=True)
        for field in ('candidate_commit','input_manifest_sha256'):
            value=raw.get(field)
            if not isinstance(value,str) or not value or value not in text:errors.append('original reviewer request lacks exact '+field)
    else:errors.append('original reviewer request must be a JSON object')
    response=documents.get('response')
    try:
        if isinstance(response,dict) and 'choices' in response:
            response=strict_json_loads(response['choices'][0]['message']['content'])
    except (ValueError,KeyError,IndexError,TypeError) as exc:
        errors.append('original model response cannot be decoded: '+str(exc));response=None
    if not isinstance(response,dict):errors.append('original reviewer response must be a JSON object')
    else:
        projected=dict(response)
        projected['reference_sensitive_dimensions']=raw.get('reference_sensitive_dimensions',[])
        errors += ['original reviewer response: '+error for error in record_errors(projected,
            list(raw.get('scores',{})),raw.get('critic_id'),require_binding=False,
            reference_dimensions=raw.get('reference_sensitive_dimensions',[]))]
        for field in ('scores','coverage_complete','defects','confidence'):
            if response.get(field)!=raw.get(field):errors.append('normalized raw '+field+' differs from original reviewer response')
    return errors


def forward_dependency_errors(task,base,graph):
    errors=[]
    for dep in graph.get('tasks',{}).get(task,{}).get('dependencies',[]):
        try:
            check=effective_approval(dep,base)
            if check.get('effective_approved') is not True or check.get('passed') is not True:
                errors.append('dependency not effectively approved: '+dep)
                errors += [dep+': '+str(message) for message in check.get('errors',[])]
        except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as exc:
            errors.append('dependency approval could not be validated: '+dep+': '+str(exc))
    return errors


def forward_visual_errors(task,candidate,style_required,required):
    errors=[]
    try:
        if active_invalidation(task):errors.append('active approval invalidation blocks current final approval')
        if style_required or set(required)&{'C1','C2','C3','C4','C5','C11'}:
            signoff=validate_signoff(task,candidate)
            errors += nonapproving_scope_errors(signoff)
            if signoff.get('passed') is not True:errors.append('mandatory current candidate visual signoff did not pass')
            errors += ['visual signoff: '+str(message) for message in signoff.get('errors',[])]
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as exc:
        errors.append('current visual approval could not be validated: '+str(exc))
    return errors


def validate_raw_critic_record(raw,cid,task,candidate,workflow_run_id,artifact_id,artifact_sha,evidence_hash,scores,review_export_commit,*,forward=False,expected_dimensions=None,reference_dimensions=None):
    """Validate receipt consistency; legacy mode alone never grants approval.

    The live closeout entrypoint always supplies forward=True. Historical
    migration callers separately bind exact immutable receipt bytes.
    """
    errors=[]
    if raw.get("task_id")!=task or raw.get("critic_id")!=cid or raw.get("candidate_commit")!=candidate:errors.append("identity mismatch")
    if raw.get("workflow_run_id")!=workflow_run_id or raw.get("artifact_id")!=artifact_id:errors.append("run/artifact mismatch")
    if raw.get("artifact_sha256")!=artifact_sha:errors.append("artifact digest mismatch")
    if raw.get("complete_evidence_index_sha256")!=evidence_hash or raw.get("input_manifest_sha256")!=evidence_hash:errors.append("input manifest mismatch")
    if raw.get("status")!="PASS" or raw.get("passed") is not True or raw.get("coverage_complete") is not True or raw.get("defects"):errors.append("disposition incomplete")
    if raw.get("scores")!=scores:errors.append("aggregate score mismatch")
    errors += record_errors(raw,expected_dimensions or [],cid,reference_dimensions=reference_dimensions) if forward else ensure_score_strictly_above_nine(raw.get("scores",{}))
    if forward:errors += validate_original_review_transport(raw)
    confidence=raw.get("confidence")
    if not valid_reviewer_confidence(confidence):errors.append("confidence invalid")
    if raw.get("score_reuse") is not False:errors.append("score reuse must be false")
    raw_scores=raw.get("scores",{})
    if not raw_scores or raw.get("minimum_dimension_score")!=minimum_score(raw_scores):errors.append("minimum score mismatch")
    if not re.fullmatch(r"[0-9a-f]{40}",str(review_export_commit or "")) or raw.get("review_export_commit")!=review_export_commit:errors.append("review export provenance mismatch")
    if raw.get("acceptance_rule")!=(final_rule() if forward else RAW_ACCEPTANCE_RULE):errors.append("acceptance rule mismatch")
    if not all(raw.get(k) for k in ("provider","model","request_or_run_id")):errors.append("provider provenance incomplete")
    return errors

def validate_critic_aggregate(aggregate,required,candidate,workflow_run_id,artifact_id,artifact_sha,evidence_hash,retained_review,critics,*,forward=False,task=None,execution=None,matrix=None,source_manifest=None):
    """Consistency validation; forward closeout additionally enforces current policy."""
    errors=[]
    if forward:errors += binding_errors(aggregate)
    if aggregate.get("status")!="PASS" or aggregate.get("disposition")!="APPROVED" or aggregate.get("coverage_complete") is not True or aggregate.get("unresolved_mandatory_defects"):errors.append("disposition incomplete")
    if (aggregate.get("candidate_commit"),aggregate.get("workflow_run_id"),aggregate.get("artifact_id"),aggregate.get("artifact_sha256"),aggregate.get("complete_evidence_index_sha256"))!=(candidate,workflow_run_id,artifact_id,artifact_sha,evidence_hash):errors.append("source identity mismatch")
    scores=[score for cid in required for score in aggregate.get("critics",{}).get(cid,{}).get("scores",{}).values()]
    if not scores or aggregate.get("minimum_mandatory_dimension_score")!=minimum_score(scores):errors.append("minimum score mismatch")
    ar=aggregate.get("retained_review_evidence",{})
    if (ar.get("workflow_run_id"),ar.get("artifact_id"),ar.get("artifact_sha256"),ar.get("expires_at"))!=(retained_review.get("run_id"),retained_review.get("artifact_id"),str(retained_review.get("digest","")).removeprefix("sha256:"),retained_review.get("expires_at")):errors.append("retained evidence mismatch")
    for cid in required:
        row=aggregate.get("critics",{}).get(cid,{});expected=critics.get(cid,{})
        expected_scores=expected.get("scores",{})
        if forward:
            spec,_=resolve_critic(task,cid,execution,matrix)
            try:reference_dimensions=declared_reference_dimensions(source_manifest,cid,spec.get('dimensions',[]))
            except ValueError as exc:errors.append(str(exc));reference_dimensions=[]
            errors += [cid+": "+x for x in record_errors(row,spec.get("dimensions",[]),cid,reference_dimensions=reference_dimensions)]
        if row.get("status")!="PASS" or row.get("coverage_complete") is not True or row.get("defects") or row.get("scores")!=expected_scores or not expected_scores or row.get("minimum_dimension_score")!=minimum_score(expected_scores) or row.get("raw_record_path")!=expected.get("raw_record_path") or row.get("raw_record_sha256")!=expected.get("raw_record_sha256"):errors.append("critic row mismatch "+cid)
    return errors

def validate_defect_ledger(ledger,candidate,aggregate,required):
    errors=[]
    if ledger.get("candidate_commit")!=candidate or ledger.get("integrated_commit")!=candidate:errors.append("source identity mismatch")
    if ledger.get("unresolved_mandatory_count")!=0 or ledger.get("unresolved_tooling_count")!=0 or ledger.get("critic_approval_pending") is not False:errors.append("unresolved state mismatch")
    if not ledger.get("defects") or any(row.get("status")!="VERIFIED_CLOSED" for row in ledger.get("defects",[])):errors.append("non-closed defect")
    minima={cid:minimum_score(aggregate.get("critics",{}).get(cid,{}).get("scores",{})) for cid in required if aggregate.get("critics",{}).get(cid,{}).get("scores")}
    if ledger.get("critic_scores")!=minima:errors.append("critic minima mismatch")
    return errors

def main():
    ap=argparse.ArgumentParser();ap.add_argument("manifest");a=ap.parse_args()
    p=pathlib.Path(a.manifest)
    if not p.is_absolute():p=ROOT/p
    try:d=load_json(p)
    except (OSError,ValueError) as exc:
        print(json.dumps({'passed':False,'approval_allowed':False,'errors':['invalid current closure JSON: '+str(exc)]}));raise SystemExit(1)
    errors=[]
    task=d.get("task_id");candidate=d.get("candidate_commit");base=d.get("base_commit")
    # This entrypoint always evaluates a new forward approval. Historical
    # receipt integrity is a separate non-approving migration operation.
    errors += binding_errors(d)
    graph=load_json(DOCS/"DEPENDENCY_GRAPH.json");critcfg=load_json(DOCS/"CRITIC_MATRIX.json");execfg=load_json(DOCS/"CRITIC_EXECUTION.json")
    resources=load_json(RESOURCE_REGISTRY);actors=load_json(ACTOR_MATRIX);animations=load_json(ANIMATION_MATRIX);gm_policy=load_json(GAME_MASTER_POLICY)
    if task not in graph["tasks"]:errors.append("unknown task")
    errors += forward_dependency_errors(task,base,graph)
    if not candidate or len(candidate)!=40:errors.append("invalid candidate commit")
    if not base or len(base)!=40:errors.append("invalid base commit")
    approval_path=DOCS/"Evidence"/str(task)/"APPROVAL_EVIDENCE_MANIFEST.json"
    review_path=DOCS/"Evidence"/str(task)/"REVIEW_EVIDENCE_MANIFEST.json"
    for label,path,tier in (("approval",approval_path,"approval_provenance"),("review",review_path,"review_evidence")):
        if not path.is_file():
            errors.append(f"missing {label} evidence manifest")
            continue
        retained=load_json(path)
        check=validate_retention_manifest(retained,path=path)
        errors += [f"{label} evidence: {x}" for x in check.get("errors",[])]
        if retained.get("task_id")!=task or retained.get("accepted_source")!=candidate:
            errors.append(f"{label} evidence source/task mismatch")
        if retained.get("retention_class")!=tier:
            errors.append(f"{label} evidence retention class mismatch")
    state_path=DOCS/str(task)/"task-state.json"
    if not state_path.is_file():
        errors.append("missing final derived task-state snapshot")
    else:
        state=load_json(state_path);state_check=validate_task_state(state)
        errors += ["task state: "+x for x in state_check.get("errors",[])]
        if state.get("task_id")!=task or state.get("candidate_commit")!=candidate:
            errors.append("task-state exact candidate mismatch")
        if state.get("lifecycle_status")!="APPROVED" or state.get("blockers"):
            errors.append("task-state is not final APPROVED with zero blockers")
    provenance_rows=load_json(DOCS/"GATE_RESULT_INDEX.json").get("records",[])
    provenance=next((row for row in provenance_rows if row.get("record_type")=="exact_source_provenance" and row.get("task_id")==task and row.get("candidate")==candidate and row.get("result")=="PASS"),None)
    if not provenance or provenance.get("reuse_eligible") is not False:
        errors.append("missing non-reusable exact-source provenance record")
    # Exact historical T09 byte checks belong only to the non-approving audit
    # helper, never to a new T09 candidate evaluated under current policy.
    review_record=load_json(DOCS/str(task)/"independent-critic-review.json")
    approved_at=review_record.get("approved_at")
    try:
        approved_time=datetime.fromisoformat(str(approved_at).replace("Z","+00:00"))
        if approved_time>datetime.now(timezone.utc):errors.append("critic approval timestamp is in the future")
    except ValueError:errors.append("critic approval timestamp is invalid")
    review_manifest=load_json(review_path) if review_path.is_file() else {}
    retained_review=d.get("retained_review_evidence",{})
    review_rows=review_manifest.get("records",[])
    if len(review_rows)!=1:
        errors.append("review evidence must have exactly one retained artifact record")
    else:
        rr=review_rows[0];identity=rr.get("content_identity",{});pe=(provenance or {}).get("evidence",{})
        expected_locator=f"github-actions://ksolo21-web/HAVENLINE/runs/{retained_review.get('run_id')}/artifacts/{retained_review.get('artifact_id')}"
        if rr.get("locator")!=expected_locator or rr.get("sha256")!=str(retained_review.get("digest","")).removeprefix("sha256:") or rr.get("expires_at")!=retained_review.get("expires_at"):
            errors.append("retained review artifact identity mismatch")
        if (rr.get("retention_days"),identity.get("original_run_id"),identity.get("original_artifact_id"),identity.get("original_artifact_sha256"),identity.get("complete_evidence_index_sha256"),identity.get("indexed_files_verified"))!=(90,d.get("workflow_run_id"),d.get("artifact_id"),d.get("artifact_sha256"),d.get("evidence",{}).get("provenance_hash"),load_json(DOCS/"Evidence"/str(task)/"complete-evidence-index.json").get("file_count")):
            errors.append("retained review content identity mismatch")
        if (pe.get("retained_artifact_id"),pe.get("retained_artifact_sha256"),pe.get("retained_until"))!=(retained_review.get("artifact_id"),str(retained_review.get("digest","")).removeprefix("sha256:"),retained_review.get("expires_at")):
            errors.append("retained review provenance index mismatch")
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
    durable_index_path=DOCS/"Evidence"/str(task)/"complete-evidence-index.json"
    durable_index={}
    if not durable_index_path.is_file():
        errors.append("missing durable complete evidence index")
    else:
        durable_index=load_json(durable_index_path)
        if sha256_file(durable_index_path)!=evidence.get("provenance_hash"):
            errors.append("durable evidence index hash mismatch")
        if durable_index.get("task_id")!=task or durable_index.get("candidate_commit")!=candidate:
            errors.append("durable evidence index source/task mismatch")

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
                proof=load_json(fp)
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
                proof=load_json(fp)
                if proof.get("passed") is not True or proof.get("task_id")!=task:
                    errors.append("Game Master validator proof failed/stale")
                proof_candidate=proof.get("candidate_commit")
                if proof_candidate and proof_candidate!=candidate:
                    errors.append("Game Master validator candidate mismatch")
    elif gm_contract and gm_contract.get("applicable") is True:
        errors.append("Game Master contract incorrectly marked applicable for task")

    required=list(critcfg["task_applicability"].get(task,[]))
    if contract_c5_required and "C5" not in required:required.append("C5")
    style_required=style_lock_required(d)
    try:
        required=required_final_critics(task,required,style_required=style_required)
    except ValueError as exc:
        errors.append("forward critic contract: "+str(exc))
    critics=d.get("critics",{})
    style_check=validate_reference_style_lock(d,critics)
    errors += ["reference style lock: "+x for x in style_check.get("errors",[])]
    errors += ['reference style lock: '+x for x in nonapproving_scope_errors(style_check)]
    if style_check.get('passed') is not True:errors.append('current reference style validation did not pass')
    errors += forward_visual_errors(task,candidate,style_required,required)
    aggregate=review_record
    if aggregate.get("status")!="PASS" or aggregate.get("disposition")!="APPROVED" or aggregate.get("coverage_complete") is not True or aggregate.get("unresolved_mandatory_defects"):
        errors.append("independent critic aggregate disposition incomplete")
    if (aggregate.get("candidate_commit"),aggregate.get("workflow_run_id"),aggregate.get("artifact_id"),aggregate.get("artifact_sha256"),aggregate.get("complete_evidence_index_sha256"))!=(candidate,d.get("workflow_run_id"),d.get("artifact_id"),d.get("artifact_sha256"),evidence.get("provenance_hash")):
        errors.append("independent critic aggregate source identity mismatch")
    aggregate_scores=[score for cid in required for score in aggregate.get("critics",{}).get(cid,{}).get("scores",{}).values()]
    if not aggregate_scores or aggregate.get("minimum_mandatory_dimension_score")!=minimum_score(aggregate_scores):
        errors.append("independent critic aggregate minimum score mismatch")
    aggregate_retained=aggregate.get("retained_review_evidence",{})
    if (aggregate_retained.get("workflow_run_id"),aggregate_retained.get("artifact_id"),aggregate_retained.get("artifact_sha256"),aggregate_retained.get("expires_at"))!=(retained_review.get("run_id"),retained_review.get("artifact_id"),str(retained_review.get("digest","")).removeprefix("sha256:"),retained_review.get("expires_at")):
        errors.append("independent critic aggregate retained evidence mismatch")
    errors += ["critic aggregate: "+x for x in validate_critic_aggregate(aggregate,required,candidate,d.get("workflow_run_id"),d.get("artifact_id"),d.get("artifact_sha256"),evidence.get("provenance_hash"),retained_review,critics,forward=True,task=task,execution=execfg,matrix=critcfg,source_manifest=durable_index)]
    ledger=load_json(DOCS/str(task)/"defect-ledger.json")
    errors += ["defect ledger: "+x for x in validate_defect_ledger(ledger,candidate,aggregate,required)]
    if ledger.get("candidate_commit")!=candidate or ledger.get("integrated_commit")!=candidate:
        errors.append("defect ledger source identity mismatch")
    if ledger.get("unresolved_mandatory_count")!=0 or ledger.get("unresolved_tooling_count")!=0 or ledger.get("critic_approval_pending") is not False:
        errors.append("defect ledger unresolved state mismatch")
    if not ledger.get("defects") or any(row.get("status")!="VERIFIED_CLOSED" for row in ledger.get("defects",[])):
        errors.append("defect ledger contains non-closed defect")
    expected_critic_minima={cid:minimum_score(aggregate.get("critics",{}).get(cid,{}).get("scores",{})) for cid in required if aggregate.get("critics",{}).get(cid,{}).get("scores")}
    if ledger.get("critic_scores")!=expected_critic_minima:
        errors.append("defect ledger critic minima mismatch")
    for cid in required:
        row=critics.get(cid)
        if not row:errors.append("missing critic "+cid);continue
        if row.get("status")!="PASS":errors.append("critic not PASS "+cid)
        if row.get("candidate_commit")!=candidate:errors.append("critic candidate mismatch "+cid)
        if task=="T10" and cid=="C7" and row.get("task_id")!=task:errors.append("C7 task identity mismatch")
        spec,_=resolve_critic(task,cid,execfg,critcfg)
        try:reference_dimensions=declared_reference_dimensions(durable_index,cid,spec.get('dimensions',[]))
        except ValueError as exc:errors.append(str(exc));reference_dimensions=[]
        errors += [f"{cid}: {x}" for x in record_errors(row,spec.get("dimensions",[]),cid,reference_dimensions=reference_dimensions)]
        if row.get("defects"):errors.append("critic defects "+cid)
        if row.get("coverage_complete") is not True:errors.append("critic incomplete "+cid)
        if critcfg["critics"][cid].get("independent_model_required") and row.get("independent_runtime") is not True:errors.append("independent runtime not proven "+cid)
        spec,_=resolve_critic(task,cid,execfg,critcfg)
        expected=set(spec.get("dimensions",[]))
        if expected and set(row.get("scores",{}))!=expected:errors.append("critic dimension coverage mismatch "+cid)
        if cid in ("C7","C8","C10","C11"):
            supplement=row.get("deterministic_supplement",{})
            if supplement.get("passed") is not True or supplement.get("candidate_commit")!=candidate:errors.append("deterministic supplement missing/failed "+cid)
        if cid=="C9":
            if len(row.get("scores",{}))!=10:errors.append("C9 attack coverage incomplete")
        raw_rel=row.get("raw_record_path")
        raw_hash=row.get("raw_record_sha256")
        if raw_rel!=f"Docs/Production/{task}/CriticRaw/{cid}.json":
            errors.append("raw critic record path is not canonical "+cid)
        if not raw_rel or not raw_hash:
            errors.append("raw critic record missing "+cid)
        else:
            raw_candidate=ROOT/raw_rel;raw_path=raw_candidate.resolve();raw_root=(DOCS/str(task)/"CriticRaw").resolve()
            if raw_path.parent!=raw_root or raw_candidate.is_symlink():
                errors.append("raw critic path escapes canonical directory "+cid)
            elif not raw_path.is_file() or sha256_file(raw_path)!=raw_hash:
                errors.append("raw critic record hash mismatch "+cid)
            else:
                raw=load_json(raw_path)
                errors += [f"{cid}: {x}" for x in validate_raw_critic_record(raw,cid,task,candidate,d.get("workflow_run_id"),d.get("artifact_id"),d.get("artifact_sha256"),evidence.get("provenance_hash"),row.get("scores",{}),d.get("critic_review_export_commit"),forward=True,expected_dimensions=spec.get("dimensions",[]),reference_dimensions=reference_dimensions)]
                aggregate_row=aggregate.get("critics",{}).get(cid,{})
                if aggregate_row.get("status")!="PASS" or aggregate_row.get("coverage_complete") is not True or aggregate_row.get("scores")!=row.get("scores") or aggregate_row.get("minimum_dimension_score")!=minimum_score(row.get("scores",{})) or aggregate_row.get("raw_record_path")!=raw_rel or aggregate_row.get("raw_record_sha256")!=raw_hash or aggregate_row.get("defects"):
                    errors.append("independent critic aggregate mismatch "+cid)
                if raw.get("task_id")!=task or raw.get("critic_id")!=cid or raw.get("candidate_commit")!=candidate:
                    errors.append("raw critic identity mismatch "+cid)
                if raw.get("workflow_run_id")!=d.get("workflow_run_id") or raw.get("artifact_id")!=d.get("artifact_id"):
                    errors.append("raw critic run/artifact mismatch "+cid)
                if raw.get("complete_evidence_index_sha256")!=evidence.get("provenance_hash") or raw.get("input_manifest_sha256")!=evidence.get("provenance_hash"):
                    errors.append("raw critic input manifest mismatch "+cid)
                if raw.get("status")!="PASS" or raw.get("passed") is not True or raw.get("coverage_complete") is not True or raw.get("defects"):
                    errors.append("raw critic disposition incomplete "+cid)
                if raw.get("scores")!=row.get("scores"):
                    errors.append("raw/aggregate critic score mismatch "+cid)
                if raw.get("artifact_sha256")!=d.get("artifact_sha256"):
                    errors.append("raw critic artifact digest mismatch "+cid)
                confidence=raw.get("confidence")
                if not valid_reviewer_confidence(confidence):
                    errors.append("raw critic confidence invalid "+cid)
                if raw.get("score_reuse") is not False:
                    errors.append("raw critic score reuse must be false "+cid)
                raw_scores=raw.get("scores",{})
                if not raw_scores or raw.get("minimum_dimension_score")!=minimum_score(raw_scores):
                    errors.append("raw critic minimum score mismatch "+cid)
                if not isinstance(raw.get("review_export_commit"),str) or len(raw.get("review_export_commit"))!=40:
                    errors.append("raw critic review export provenance incomplete "+cid)
                if not all(raw.get(k) for k in ("provider","model","request_or_run_id")):
                    errors.append("raw critic provider provenance incomplete "+cid)
                for item in raw.get("evidence",[]):
                    rel=item.get("path");h=item.get("sha256")
                    if not rel or not h or durable_index.get("files",{}).get(rel)!=h:
                        errors.append("raw critic indexed evidence mismatch "+cid+": "+str(rel))
    integ=d.get("integration",{})
    if integ.get("candidate_commit")!=candidate or integ.get("regression_passed") is not True:errors.append("integration candidate regression missing")
    result={"task_id":task,"candidate_commit":candidate,"passed":not errors,"errors":errors,"approval_allowed":not errors,"reference_style_lock_required":style_required}
    print(json.dumps(result,indent=2))
    if errors:raise SystemExit(1)
if __name__=="__main__":main()
