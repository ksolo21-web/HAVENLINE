#!/usr/bin/env python3
"""Exact authorized V3.2 policy, T10 canary and C7 deltas over immutable V3.1."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import validate_architecture_release_lock as v31
from validate_architecture_v32_t09 import POLICY, policy_errors

CANARY = "tools/havenline/production/mutation_canary.py"
REQUEST = "Docs/Production/ChangeRequests/T10-task-state-canary-reactivation.json"
AUTHORIZATION = "Authorize the bounded V3.2 T10 canary repair."

FORWARD = "tools/havenline/production/forward_execution.py"
C7_REQUEST = "Docs/Production/ChangeRequests/T10-C7-transactional-progression.json"
C7_AUTHORIZATION = "Approve the bounded T10 C7 governance repair, preserving all critics and thresholds."
C7_REQUEST_SHA256 = "8f24a3216fa5d4d87f88227a4eb64074b8efea2f6d71b2218f5a3157061aebe1"
C7_DELTA = "    # T10 owns transactional progression, while T12/T13 own Level 1-100 pacing.\n    # Keep C7 and progression_sim mandatory; specialize only its proof runner.\n    if task_id == \"T10\":\n        gate_execution[\"progression_sim\"] = {\n            \"execution\": \"task_adapter_required\",\n            \"runner\": \"python3 tools/havenline/task10/validate_progression.py --candidate <SHA> --output <record>\",\n            \"rule\": \"Source-bound executable recipe/state graph, prerequisites, exact-once debit, no-skip/replay, branching/inverse and recovery proof; independent C7 remains required.\",\n        }\n"


FAILURE = "tools/havenline/production/failure_intelligence.py"
FAILURE_REQUEST = "Docs/Production/ChangeRequests/T10-failure-packet-log-compatibility.json"
FAILURE_REQUEST_SHA256 = "d388a6fe33d1a45a2c475c2874b039ef1d136c6bc61c5119b8159e83c54006f9"


BUILDER = "tools/havenline/production/builder_repair_gate.py"
BUILDER_REQUEST = "Docs/Production/ChangeRequests/T10-builder-repair-causal-bookkeeping.json"
BUILDER_REQUEST_SHA256 = "92986f20ded72d4b22fb6ebe1e82d01d2dd2003e1f453b02b8ae392bd5d438c7"
BUILDER_DELTAS = [('    errors=[]\n', '    errors=[]\n    task=c0.get("task_id")\n    canonical_c0=f"Docs/Production/{task}/C0_ROOT_CAUSE.json"\n    canonical_plan=f"Docs/Production/{task}/REPAIR_PLAN.json"\n    bookkeeping={canonical_c0,canonical_plan}\n    if plan.get("c0_report_path")!=canonical_c0 or plan.get("plan_path")!=canonical_plan:\n        errors.append("canonical C0 and repair plan paths required")\n'), ('        if not fix.get("causal_change"):errors.append(f"{bid} causal_change missing")\n', '        if set(files)&bookkeeping:errors.append(f"{bid} bookkeeping cannot be causal files")\n        causal_files=set(files)-bookkeeping\n        if not causal_files:errors.append(f"{bid} non-bookkeeping causal files required")\n        if not fix.get("causal_change"):errors.append(f"{bid} causal_change missing")\n'), ('        allowed.update(files)\n', '        allowed.update(causal_files)\n'), ('        plan_path=plan.get("plan_path")\n        allowed_actual=set(allowed)\n        if isinstance(plan_path,str) and plan_path:allowed_actual.add(plan_path)\n', '        allowed_actual=set(allowed)|bookkeeping\n'), ('            if not set(fix.get("files",[]))&set(actual_changed):errors.append(f"{fix.get(\'blocker_id\')} causal files did not change")\n', '            if not (set(fix.get("files",[]))-bookkeeping)&set(actual_changed):errors.append(f"{fix.get(\'blocker_id\')} causal files did not change")\n')]


C0_WORKFLOW = ".github/workflows/havenline-c0-root-cause.yml"
C0_REQUEST = 'Docs/Production/ChangeRequests/T10-c0-in-progress-job-log-collection.json'
C0_REQUEST_SHA256 = 'abf213d874982c33c479c0c88e19383f7e3efae398046dbe78be501f0a3f7648'
C0_LOG_OLD = '          gh run view "$FAILED_RUN_ID" --log-failed > c0-input/failed.log 2>&1 || gh run view "$FAILED_RUN_ID" --log > c0-input/failed.log 2>&1 || true\n'
C0_LOG_NEW = '          python3 tools/havenline/production/collect_failure_job_logs.py --run c0-input/run.json --jobs c0-input/jobs.json --run-id "$FAILED_RUN_ID" --repository "$GITHUB_REPOSITORY" --output c0-input/failed.log\n'

OWNER_BASE = "c1957696c6f716d3cd6f8528c95edbb7542cd4a6"
SPECIALIST = "tools/havenline/production/specialist_critic_runner.py"
SPECIALIST_BASE_SHA256 = "ddf0849d034033ae9df61d671953127e4e40bc80a0601ee735b9c68c9e2cdb00"
SPECIALIST_CURRENT_SHA256 = "961d6daa2ae42297e703c17b16f34db540fbdee294dccbaebf29c81351c0f980"
SPECIALIST_REQUEST = "Docs/Production/ChangeRequests/T10-specialist-actionable-defect-schema.json"
SPECIALIST_REQUEST_SHA256 = "25c8544a37587fdbbd527de7606c0517e67781ee879fdb72e502b6fe2d1c513d"
C0_ADVISOR = "tools/havenline/production/c0_root_cause_advisor.py"
C0_ADVISOR_BASE_SHA256 = "d66e551eadf4dcdd1363da3da41d64e314a074292b2531cf99c0f5028a24beee"
C0_ADVISOR_CURRENT_SHA256 = "5d6788905504c61bfeb3ddcd24a283614b58486c524e2f508f98de08dd2f1bab"
C0_BOUNDED_REQUEST = "Docs/Production/ChangeRequests/T10-c0-bounded-model-packet.json"
C0_BOUNDED_REQUEST_SHA256 = "c54e6bd4c572f71673272a4b4e20ca4ba54da7c353643a1268d17c66c575f94e"
C0_GROUNDING_REQUEST = "Docs/Production/ChangeRequests/T10-c0-grounded-artifact-diagnostics.json"
C0_GROUNDING_REQUEST_SHA256 = "42e4cc3e8dac7759d912196fe2eb4e8ef836ad82eb1cdafd8f3922a2188a490f"
C0_DIAGNOSTICS = "tools/havenline/production/collect_artifact_diagnostics.py"
C0_DIAGNOSTICS_SHA256 = "ad701a1a6c005ff45b6052c68886677dd9c513ad25fabb979a7b6cca2fa8993b"
C0_PACKET_IMPORT_OLD = "          import json,os,pathlib,subprocess\n"
C0_PACKET_IMPORT_NEW = "          import hashlib,json,os,pathlib,subprocess\n"
C0_PACKET_LOG_OLD = "          log=(root/'c0-input/failed.log').read_text(errors='replace') if (root/'c0-input/failed.log').exists() else ''\n"
C0_PACKET_LOG_NEW = C0_PACKET_LOG_OLD + """          records=[]
          for path in sorted((root/'c0-input/artifacts').rglob('critic-record.json')):
              raw=path.read_bytes()
              if len(raw)>200000:raise SystemExit(f'critic record exceeds bounded size: {path}')
              value=json.loads(raw)
              if not isinstance(value,dict):raise SystemExit(f'critic record is not an object: {path}')
              value=dict(value);value.update(path=str(path.relative_to(root)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
              records.append(value)
          if len(records)>20:raise SystemExit('too many critic records in failed run artifacts')
          log_bytes=log.encode('utf-8')
"""
C0_PACKET_ENTRY_OLD = "            'changed_files':changed,'failed_logs':log[-60000:],'task_scope':scope.read_text(errors='replace')[:30000] if scope.exists() else '',\n"
C0_PACKET_ENTRY_NEW = "            'changed_files':changed,'failed_logs':log,'failed_logs_bytes':len(log_bytes),'failed_logs_sha256':hashlib.sha256(log_bytes).hexdigest(),\n            'structured_failure_records':records,'task_scope':scope.read_text(errors='replace')[:30000] if scope.exists() else '',\n"
C0_GROUNDING_DELTAS = [
    (
        "          gh run download \"$FAILED_RUN_ID\" -D c0-input/artifacts >/dev/null 2>&1 || true\n          python3 - <<'PY'\n",
        "          gh run download \"$FAILED_RUN_ID\" -D c0-input/artifacts >/dev/null 2>&1 || true\n          python3 tools/havenline/production/collect_artifact_diagnostics.py --root c0-input/artifacts --output c0-input/artifact-diagnostics.json\n          python3 - <<'PY'\n",
    ),
    (
        "          log_bytes=log.encode('utf-8')\n          packet={\n",
        "          log_bytes=log.encode('utf-8')\n          artifact_diagnostics=json.loads((root/'c0-input/artifact-diagnostics.json').read_text())\n          packet={\n",
    ),
    (
        "            'defect_ledger':ledger.read_text(errors='replace')[:30000] if ledger else '',\n            'protected_files':[],\n",
        "            'defect_ledger':ledger.read_text(errors='replace')[:30000] if ledger else '',\n            'artifact_diagnostics':artifact_diagnostics,'repository_paths':subprocess.check_output(['git','ls-files'],text=True).splitlines(),\n            'strict_evidence_grounding':task=='T10',\n            'protected_files':[],\n",
    ),
    (
        "            c0-input/artifacts.json\n            c0-output/\n",
        "            c0-input/artifacts.json\n            c0-input/artifact-diagnostics.json\n            c0-output/\n",
    ),
]


def c0_workflow_delta_errors(accepted: str, current: str) -> list[str]:
    if accepted.count(C0_LOG_OLD) != 1:
        return ["V3.1 C0 log collection anchor missing"]
    expected=accepted.replace(C0_LOG_OLD,C0_LOG_NEW,1)
    for old,new,label in ((C0_PACKET_IMPORT_OLD,C0_PACKET_IMPORT_NEW,"packet import"),(C0_PACKET_LOG_OLD,C0_PACKET_LOG_NEW,"structured failure records"),(C0_PACKET_ENTRY_OLD,C0_PACKET_ENTRY_NEW,"complete packet evidence")):
        if expected.count(old)!=1:return [f"V3.2 C0 {label} anchor missing"]
        expected=expected.replace(old,new,1)
    for old,new in C0_GROUNDING_DELTAS:
        if expected.count(old)!=1:return ["V3.2 C0 grounded artifact diagnostic anchor missing"]
        expected=expected.replace(old,new,1)
    return [] if current == expected else ["Only the authorized completed-job collection and bounded complete C0 packet deltas are permitted"]


def exact_owner_source_errors(path:str,base_sha256:str,current_sha256:str)->list[str]:
    try:
        base=v31._git("show",f"{OWNER_BASE}:{path}").stdout
        current=(v31.ROOT/path).read_bytes()
    except Exception as exc:return [str(exc)]
    errors=[]
    if hashlib.sha256(base).hexdigest()!=base_sha256:errors.append(f"{path} authorized base changed")
    if hashlib.sha256(current).hexdigest()!=current_sha256:errors.append(f"{path} exceeds exact bounded T10 authorization")
    return errors


def builder_delta_errors(accepted: str, current: str) -> list[str]:
    expected = accepted
    for old, new in BUILDER_DELTAS:
        if expected.count(old) != 1:
            return ["V3.1 builder causal bookkeeping anchor missing"]
        expected = expected.replace(old, new, 1)
    return [] if current == expected else ["Only the authorized causal bookkeeping builder delta is permitted"]


def failure_delta_errors(accepted: str, current: str) -> list[str]:
    old = 'packet.get("failure_excerpt", packet.get("logs", ""))'
    new = 'packet.get("failure_excerpt", packet.get("failed_logs", packet.get("logs", "")))'
    if accepted.count(old) != 1:
        return ["V3.1 failure packet log anchor missing"]
    return [] if current == accepted.replace(old, new, 1) else ["Only the authorized failed_logs compatibility expression is permitted"]


def c7_delta_errors(accepted: str, current: str) -> list[str]:
    anchor = "        for gate in ordered\n    }\n"
    if accepted.count(anchor) != 1:
        return ["V3.1 baseline lacks the expected forward execution anchor"]
    expected = accepted.replace(anchor, anchor + C7_DELTA, 1)
    return [] if current == expected else ["Only the authorized T10 C7 runner specialization is permitted"]


def canary_delta_errors(accepted: str, current: str) -> list[str]:
    expected = accepted
    import_old = "from __future__ import annotations\nimport json\n"
    import_new = "from __future__ import annotations\nimport copy\nimport json\n"
    canary_old = "    state=snapshot('T10');results.append({'id':'CANARY-TASK-STATE-AUTHORITY','rejected':validate_snapshot(state)['passed'] and state['snapshot_is_derived_not_authority'] and state['lifecycle_status']=='LOCKED' and 'lifecycle_status_LOCKED' in state['blockers'] and 'ownership_not_assigned' in state['blockers']})\n"
    canary_new = "    state=snapshot('T10');mutated_state=copy.deepcopy(state);mutated_state['snapshot_is_derived_not_authority']=False\n    results.append({'id':'CANARY-TASK-STATE-AUTHORITY','rejected':validate_snapshot(state)['passed'] and not validate_snapshot(mutated_state)['passed']})\n"
    if expected.count(import_old) != 1 or expected.count(canary_old) != 1:
        return ["V3.1 baseline does not contain the expected T10 canary implementation"]
    expected = expected.replace(import_old, import_new, 1).replace(canary_old, canary_new, 1)
    return [] if current == expected else ["V3.2 permits only the authorized lifecycle-independent T10 authority canary repair"]


def validate() -> dict:
    baseline = v31.validate()
    allowed = {
        f"V3.1 locked file changed: {POLICY}",
        f"V3.1 locked file changed: {CANARY}",
        f"V3.1 locked file changed: {FORWARD}",
        f"V3.1 locked file changed: {FAILURE}",
        f"V3.1 locked file changed: {BUILDER}",
        f"V3.1 locked file changed: {C0_WORKFLOW}",
        f"V3.1 locked file changed: {C0_ADVISOR}",
    }
    errors = [error for error in baseline["errors"] if error not in allowed]
    try:
        accepted_c0 = v31._git("show", f"{v31.ACCEPTED_SOURCE}:{C0_WORKFLOW}").stdout.decode()
        errors += c0_workflow_delta_errors(accepted_c0, (v31.ROOT / C0_WORKFLOW).read_text())
        if hashlib.sha256((v31.ROOT / C0_REQUEST).read_bytes()).hexdigest() != C0_REQUEST_SHA256:
            errors.append("Bounded C0 job log authorization changed or missing")
        errors += exact_owner_source_errors(C0_ADVISOR,C0_ADVISOR_BASE_SHA256,C0_ADVISOR_CURRENT_SHA256)
        errors += exact_owner_source_errors(SPECIALIST,SPECIALIST_BASE_SHA256,SPECIALIST_CURRENT_SHA256)
        c0_bounded_request=json.loads((v31.ROOT/C0_BOUNDED_REQUEST).read_text())
        if hashlib.sha256((v31.ROOT/C0_BOUNDED_REQUEST).read_bytes()).hexdigest()!=C0_BOUNDED_REQUEST_SHA256:
            errors.append("Bounded C0 model packet authorization changed or missing")
        if c0_bounded_request.get("status")!="AUTHORIZED" or c0_bounded_request.get("blocker")!="C0-T10-B059":
            errors.append("Explicit B059 C0 model packet authorization missing")
        c0_grounding_request=json.loads((v31.ROOT/C0_GROUNDING_REQUEST).read_text())
        if hashlib.sha256((v31.ROOT/C0_GROUNDING_REQUEST).read_bytes()).hexdigest()!=C0_GROUNDING_REQUEST_SHA256:
            errors.append("Bounded C0 grounding authorization changed or missing")
        if c0_grounding_request.get("status")!="AUTHORIZED" or c0_grounding_request.get("blockers")!=["C0-T10-B060","C0-T10-B061"]:
            errors.append("Explicit B060/B061 C0 grounding authorization missing")
        if hashlib.sha256((v31.ROOT/C0_DIAGNOSTICS).read_bytes()).hexdigest()!=C0_DIAGNOSTICS_SHA256:
            errors.append("Bounded C0 artifact diagnostic collector changed or missing")
        specialist_request=json.loads((v31.ROOT/SPECIALIST_REQUEST).read_text())
        if hashlib.sha256((v31.ROOT/SPECIALIST_REQUEST).read_bytes()).hexdigest()!=SPECIALIST_REQUEST_SHA256:
            errors.append("Bounded actionable-defect schema authorization changed or missing")
        if specialist_request.get("status")!="AUTHORIZED" or specialist_request.get("blocker")!="C0-T10-B058":
            errors.append("Explicit B058 critic schema authorization missing")
        accepted_builder = v31._git("show", f"{v31.ACCEPTED_SOURCE}:{BUILDER}").stdout.decode()
        errors += builder_delta_errors(accepted_builder, (v31.ROOT / BUILDER).read_text())
        if hashlib.sha256((v31.ROOT / BUILDER_REQUEST).read_bytes()).hexdigest() != BUILDER_REQUEST_SHA256:
            errors.append("Bounded builder causal bookkeeping authorization changed or missing")
        accepted_failure = v31._git("show", f"{v31.ACCEPTED_SOURCE}:{FAILURE}").stdout.decode()
        errors += failure_delta_errors(accepted_failure, (v31.ROOT / FAILURE).read_text())
        if hashlib.sha256((v31.ROOT / FAILURE_REQUEST).read_bytes()).hexdigest() != FAILURE_REQUEST_SHA256:
            errors.append("Bounded failure packet authorization changed or missing")
        accepted_policy = json.loads(v31._git("show", f"{v31.ACCEPTED_SOURCE}:{POLICY}").stdout)
        current_policy = json.loads((v31.ROOT / POLICY).read_text())
        errors += policy_errors(accepted_policy, current_policy)
        accepted_canary = v31._git("show", f"{v31.ACCEPTED_SOURCE}:{CANARY}").stdout.decode()
        current_canary = (v31.ROOT / CANARY).read_text()
        errors += canary_delta_errors(accepted_canary, current_canary)
        accepted_forward = v31._git("show", f"{v31.ACCEPTED_SOURCE}:{FORWARD}").stdout.decode()
        errors += c7_delta_errors(accepted_forward, (v31.ROOT / FORWARD).read_text())
        c7_request = json.loads((v31.ROOT / C7_REQUEST).read_text())
        if hashlib.sha256((v31.ROOT / C7_REQUEST).read_bytes()).hexdigest() != C7_REQUEST_SHA256:
            errors.append("C7 authorization scope, forbidden changes or acceptance contract changed")
        if c7_request.get("task_id") != "T10" or c7_request.get("status") != "AUTHORIZED" or c7_request.get("authorization") != C7_AUTHORIZATION:
            errors.append("Explicit bounded T10 C7 authorization record missing")
        request = json.loads((v31.ROOT / REQUEST).read_text())
        if request.get("task_id") != "T10" or request.get("status") != "AUTHORIZED" or request.get("authorization") != AUTHORIZATION:
            errors.append("Explicit bounded V3.2 T10 authorization record missing")
        from mutation_canary import run_canaries
        canaries = run_canaries()
        authority = next((row for row in canaries.get("results",[]) if row.get("id")=="CANARY-TASK-STATE-AUTHORITY"),{})
        if not canaries.get("passed") or authority.get("rejected") is not True:
            errors.append("Authorized T10 authority mutation canary does not reject the synthetic mutation")
    except Exception as exc:
        errors.append(str(exc))
    return {
        "passed": not errors,
        "architecture_version": "3.2",
        "scope": "T09 workflow reactivation, T10 authority canary, T10-only C7 proof runner, exact C0 failure evidence transport, causal repair bookkeeping, actionable critic defects, bounded C0 model packets and grounded artifact diagnostics",
        "predecessor_accepted_source": v31.ACCEPTED_SOURCE,
        "predecessor_manifest_sha256": baseline["manifest_sha256"],
        "unchanged_locked_files": baseline["locked_files_matching"],
        "authorized_changes": [POLICY, CANARY, FORWARD, FAILURE, BUILDER, C0_WORKFLOW, C0_ADVISOR, C0_DIAGNOSTICS, SPECIALIST],
        "authorization_record": REQUEST,
        "c7_authorization_record": C7_REQUEST,
        "failure_packet_authorization_record": FAILURE_REQUEST,
        "builder_authorization_record": BUILDER_REQUEST,
        "c0_job_log_authorization_record": C0_REQUEST,
        "c0_bounded_packet_authorization_record": C0_BOUNDED_REQUEST,
        "c0_grounding_authorization_record": C0_GROUNDING_REQUEST,
        "specialist_actionable_defect_authorization_record": SPECIALIST_REQUEST,
        "errors": errors,
    }


def main() -> int:
    parser=argparse.ArgumentParser();parser.add_argument("--output");args=parser.parse_args()
    result=validate();text=json.dumps(result,indent=2)+"\n";print(text,end="")
    if args.output:Path(args.output).write_text(text)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
