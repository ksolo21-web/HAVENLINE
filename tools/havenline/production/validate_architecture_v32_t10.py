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
BUILDER_INHERIT_REQUEST = "Docs/Production/ChangeRequests/T10-repair-base-inherited-governance.json"
BUILDER_INHERIT_REQUEST_SHA256 = "6c1abc343d0b6837612e47a9ae222b81d167b28743b6651fb2cf217b88d7392a"
BUILDER_C0R_REQUEST = "Docs/Production/ChangeRequests/T10-c0r-builder-enforcement.json"
BUILDER_C0R_REQUEST_SHA256 = "f55b6906f492901e9cebe755a94ac73577935ca01e42e0f7af8de6c00a43e2ca"
BUILDER_PRE_C0R_SHA256 = "f2b93756d6f9e70b9533ff2fde44525c7fb305778f80bb8c4eef49f02aa18eb4"
BUILDER_C0R_CURRENT_SHA256 = "2ea7da4e0ebed2ebd88d76ad9d08395af5cd05f9f50322fcf4db4627a374fe5f"
WORKSTREAM = "tools/havenline/production/workstream.py"
WORKSTREAM_BASE_SHA256 = "9f322e6d02d4a0b2896a83bd0ef525803d6033db18e07fbe7aa06df65161bae4"
WORKSTREAM_CURRENT_SHA256 = "38c28d372acead6fe416fe822333a3cb2b9881fe5ad6924b7b9677afd6bcfe81"
WORKSTREAM_REQUEST = "Docs/Production/ChangeRequests/T10-c0r-workstream-authorization-schema.json"
WORKSTREAM_REQUEST_SHA256 = "5c52bc606a1ac4d6cce06bcfa0420614879cb22948908d91f8ec945dee0ebb7d"
GUARD = ".github/workflows/havenline-candidate-guard.yml"
GUARD_BASE_SHA256 = "1aad9fba33b2a03d798065573c4bd9f9cd157dbf9559d60efb61913713a9c185"
GUARD_CURRENT_SHA256 = "071cfb7143b42dc903919da4a6a340fcd9eb3ef71656667dde6b5a1da233716a"
GUARD_REQUEST = "Docs/Production/ChangeRequests/T10-candidate-guard-integration-branch.json"
GUARD_REQUEST_SHA256 = "c2557fbdd0d4ce12660997d12fc46c9b7abf1d8ed337a9832acee6f32908fb9c"
BUILDER_DELTAS = [('    errors=[]\n', '    errors=[]\n    task=c0.get("task_id")\n    canonical_c0=f"Docs/Production/{task}/C0_ROOT_CAUSE.json"\n    canonical_plan=f"Docs/Production/{task}/REPAIR_PLAN.json"\n    bookkeeping={canonical_c0,canonical_plan}\n    if plan.get("c0_report_path")!=canonical_c0 or plan.get("plan_path")!=canonical_plan:\n        errors.append("canonical C0 and repair plan paths required")\n'), ('        if not fix.get("causal_change"):errors.append(f"{bid} causal_change missing")\n', '        if set(files)&bookkeeping:errors.append(f"{bid} bookkeeping cannot be causal files")\n        causal_files=set(files)-bookkeeping\n        if not causal_files:errors.append(f"{bid} non-bookkeeping causal files required")\n        if not fix.get("causal_change"):errors.append(f"{bid} causal_change missing")\n'), ('        allowed.update(files)\n', '        allowed.update(causal_files)\n'), ('        plan_path=plan.get("plan_path")\n        allowed_actual=set(allowed)\n        if isinstance(plan_path,str) and plan_path:allowed_actual.add(plan_path)\n', '        allowed_actual=set(allowed)|bookkeeping\n'), ('            if not set(fix.get("files",[]))&set(actual_changed):errors.append(f"{fix.get(\'blocker_id\')} causal files did not change")\n', '            if not (set(fix.get("files",[]))-bookkeeping)&set(actual_changed):errors.append(f"{fix.get(\'blocker_id\')} causal files did not change")\n')]
BUILDER_INHERIT_DELTAS = [
    ('import pathlib\n\nfrom lib import ROOT, changed_files\n', 'import pathlib\nimport os\nimport subprocess\n\nfrom lib import ROOT, changed_files\n'),
    ('def load(path:pathlib.Path)->dict:\n    return json.loads(path.read_text())\n\n\ndef validate(c0:dict,plan:dict,actual_changed:list[str]|None=None,actual_base:str|None=None)->list[str]:\n',
     'def load(path:pathlib.Path)->dict:\n    return json.loads(path.read_text())\n\n\ndef _inherited_noncausal(plan:dict)->list[str]:\n    rows=plan.get("inherited_noncausal_files",[])\n    return [str(path) for path in rows] if isinstance(rows,list) else []\n\n\ndef verify_inherited_noncausal(plan:dict,head:str,integration_head:str|None,read_ref=None,is_ancestor=None)->list[str]:\n    inherited=_inherited_noncausal(plan)\n    if not inherited:return []\n    errors=[]\n    source=plan.get("reconciled_integration_head")\n    if not isinstance(source,str) or len(source)!=40:\n        return ["inherited noncausal files require exact reconciled_integration_head"]\n    if not isinstance(integration_head,str) or len(integration_head)!=40 or source!=integration_head:\n        errors.append("reconciled integration head does not match active integration head")\n    if read_ref is None:\n        def read_ref(ref,path):\n            return subprocess.check_output(["git","show",f"{ref}:{path}"])\n    if is_ancestor is None:\n        def is_ancestor(ancestor,descendant):\n            return subprocess.run(["git","merge-base","--is-ancestor",ancestor,descendant],check=False).returncode==0\n    if integration_head and not is_ancestor(source,head):\n        errors.append("reconciled integration head is not an ancestor of repair candidate")\n    for path in inherited:\n        try:\n            source_bytes=read_ref(source,path);head_bytes=read_ref(head,path)\n        except Exception:\n            errors.append("inherited noncausal file missing at integration/head: "+path);continue\n        if source_bytes!=head_bytes:\n            errors.append("inherited noncausal file differs from exact integration bytes: "+path)\n    return errors\n\n\ndef validate(c0:dict,plan:dict,actual_changed:list[str]|None=None,actual_base:str|None=None)->list[str]:\n'),
    ('    bookkeeping={canonical_c0,canonical_plan}\n    if plan.get("c0_report_path")!=canonical_c0 or plan.get("plan_path")!=canonical_plan:\n',
     '    bookkeeping={canonical_c0,canonical_plan}\n    inherited=_inherited_noncausal(plan)\n    if plan.get("inherited_noncausal_files",[]) is not None and not isinstance(plan.get("inherited_noncausal_files",[]),list):\n        errors.append("inherited_noncausal_files must be list")\n    if len(inherited)!=len(set(inherited)) or any(not path or path.startswith("/") or ".." in pathlib.PurePosixPath(path).parts for path in inherited):\n        errors.append("inherited noncausal file paths must be unique safe repository paths")\n    if inherited and (not isinstance(plan.get("reconciled_integration_head"),str) or len(plan.get("reconciled_integration_head"))!=40):\n        errors.append("inherited noncausal files require exact reconciled_integration_head")\n    if set(inherited)&bookkeeping:\n        errors.append("canonical repair bookkeeping cannot be inherited noncausal")\n    if plan.get("c0_report_path")!=canonical_c0 or plan.get("plan_path")!=canonical_plan:\n'),
    ('        allowed.update(causal_files)\n    blast=plan.get("blast_radius_checks",[])\n',
     '        allowed.update(causal_files)\n    inherited_set=set(inherited)\n    if inherited_set&allowed:\n        errors.append("inherited noncausal files cannot also be blocker causal files")\n    blast=plan.get("blast_radius_checks",[])\n'),
    ('        allowed_actual=set(allowed)|bookkeeping\n', '        allowed_actual=set(allowed)|bookkeeping|set(inherited)\n'),
    ('    actual=changed_files(a.base,a.head) if a.base else None\n    errors=validate(c0_copy,plan,actual,a.base)\n    result={"schema_version":1,"task_id":c0.get("task_id"),"diagnosis_id":c0.get("diagnosis_id"),"passed":not errors,"mode":"post-build" if actual is not None else "pre-build","repair_base":plan.get("repair_base"),"actual_changed_files":actual or [],"errors":errors}\n',
     '    actual=changed_files(a.base,a.head) if a.base else None\n    errors=validate(c0_copy,plan,actual,a.base)\n    inherited_errors=verify_inherited_noncausal(plan,a.head,os.environ.get("INTEGRATION_HEAD")) if actual is not None else []\n    errors.extend(inherited_errors)\n    result={"schema_version":1,"task_id":c0.get("task_id"),"diagnosis_id":c0.get("diagnosis_id"),"passed":not errors,"mode":"post-build" if actual is not None else "pre-build","repair_base":plan.get("repair_base"),"reconciled_integration_head":plan.get("reconciled_integration_head"),"inherited_noncausal_files":_inherited_noncausal(plan),"actual_changed_files":actual or [],"errors":errors}\n'),
]


C0_WORKFLOW = ".github/workflows/havenline-c0-root-cause.yml"
C0_REQUEST = 'Docs/Production/ChangeRequests/T10-c0-in-progress-job-log-collection.json'
C0_REQUEST_SHA256 = 'abf213d874982c33c479c0c88e19383f7e3efae398046dbe78be501f0a3f7648'
C0_LOG_OLD = '          gh run view "$FAILED_RUN_ID" --log-failed > c0-input/failed.log 2>&1 || gh run view "$FAILED_RUN_ID" --log > c0-input/failed.log 2>&1 || true\n'
C0_LOG_NEW = '          python3 tools/havenline/production/collect_failure_job_logs.py --run c0-input/run.json --jobs c0-input/jobs.json --run-id "$FAILED_RUN_ID" --repository "$GITHUB_REPOSITORY" --output c0-input/failed.log\n'

OWNER_BASE = "c1957696c6f716d3cd6f8528c95edbb7542cd4a6"
SPECIALIST = "tools/havenline/production/specialist_critic_runner.py"
SPECIALIST_BASE_SHA256 = "ddf0849d034033ae9df61d671953127e4e40bc80a0601ee735b9c68c9e2cdb00"
SPECIALIST_CURRENT_SHA256 = "febb56d2cfdce0e71e3af637199a314447d7593508cad0c0b18998e85ddac373"
SPECIALIST_BRANCH_REQUEST = "Docs/Production/ChangeRequests/T10-specialist-complete-grammar-branches.json"
SPECIALIST_BRANCH_REQUEST_SHA256 = "b5be20435029b1b407427366c8d9dd2aa87bdee5f682966e8a8c109e8f5e1d4a"
SPECIALIST_REQUEST = "Docs/Production/ChangeRequests/T10-specialist-actionable-defect-schema.json"
SPECIALIST_REQUEST_SHA256 = "25c8544a37587fdbbd527de7606c0517e67781ee879fdb72e502b6fe2d1c513d"
C0_ADVISOR = "tools/havenline/production/c0_root_cause_advisor.py"
C0_ADVISOR_BASE_SHA256 = "d66e551eadf4dcdd1363da3da41d64e314a074292b2531cf99c0f5028a24beee"
C0_ADVISOR_CURRENT_SHA256 = "f375814f19399b11e1228f1e2af90ad2f3aa80a955009e57649b0df4f62a25f2"
C0R_MACHINE_PROSE_REQUEST = "Docs/Production/ChangeRequests/T10-c0r-structured-mechanism-detection.json"
C0R_MACHINE_PROSE_REQUEST_SHA256 = "21f1fe42e4ad98de61400191374aace5827ed967cacb1b156c34d58f502417c8"
BENCHMARK_LIVENESS_REQUEST = "Docs/Production/ChangeRequests/T10-benchmark-liveness-contract.json"
BENCHMARK_LIVENESS_REQUEST_SHA256 = "2d20cdb5d8b761e8ff6c2d7c3486e5cf3a87a1c8de89f2e0f18e4ffbbea0a59a"
C0_COMPLETE_EVIDENCE_REQUEST = "Docs/Production/ChangeRequests/T10-c0-decoded-complete-evidence.json"
C0_COMPLETE_EVIDENCE_REQUEST_SHA256 = "ac7faaa137cb020419daf661a2188296fbe9f91f60bb23cc1e5a4dc81d56f96f"
C0_TERMINAL_JOB_LOG_REQUEST = "Docs/Production/ChangeRequests/T10-c0-terminal-job-log-priority.json"
C0_TERMINAL_JOB_LOG_REQUEST_SHA256 = "08a3d20890dc37532c70fa22baa040116543474eceaad0879c9dc9d7d21559e2"
C0_TERMINAL_REQUEST = "Docs/Production/ChangeRequests/T10-c0-terminal-evidence-priority.json"
C0_TERMINAL_REQUEST_SHA256 = "d348b08f9dae57cc56fb9ba1cbb40053a31c8d598ad87531bc11d381395f8d6a"
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
    for old, new in BUILDER_INHERIT_DELTAS:
        if expected.count(old) != 1:
            return ["V3.2 builder inherited-governance anchor missing"]
        expected = expected.replace(old, new, 1)
    if hashlib.sha256(expected.encode()).hexdigest()!=BUILDER_PRE_C0R_SHA256:
        return ["pre-C0R builder authorization baseline drifted"]
    if hashlib.sha256(current.encode()).hexdigest()!=BUILDER_C0R_CURRENT_SHA256:
        return ["Only the exact authorized causal-bookkeeping, inherited-governance and canonical C0R builder enforcement bytes are permitted"]
    return []


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
        f"V3.1 locked file changed: {WORKSTREAM}",
        f"V3.1 locked file changed: {GUARD}",
    }
    errors = [error for error in baseline["errors"] if error not in allowed]
    try:
        accepted_c0 = v31._git("show", f"{v31.ACCEPTED_SOURCE}:{C0_WORKFLOW}").stdout.decode()
        errors += c0_workflow_delta_errors(accepted_c0, (v31.ROOT / C0_WORKFLOW).read_text())
        if hashlib.sha256((v31.ROOT / C0_REQUEST).read_bytes()).hexdigest() != C0_REQUEST_SHA256:
            errors.append("Bounded C0 job log authorization changed or missing")
        errors += exact_owner_source_errors(C0_ADVISOR,C0_ADVISOR_BASE_SHA256,C0_ADVISOR_CURRENT_SHA256)
        complete_request_bytes=(v31.ROOT/C0_COMPLETE_EVIDENCE_REQUEST).read_bytes()
        complete_request=json.loads(complete_request_bytes)
        if hashlib.sha256(complete_request_bytes).hexdigest()!=C0_COMPLETE_EVIDENCE_REQUEST_SHA256:
            errors.append("Decoded complete C0 evidence authorization changed or missing")
        if complete_request.get("status")!="AUTHORIZED" or complete_request.get("blockers")!=["C0-T10-B059","C0-T10-B061"] or complete_request.get("advisor_sha256")!=C0_ADVISOR_CURRENT_SHA256:
            errors.append("Explicit bounded decoded complete C0 evidence authorization missing")
        machine_request_bytes=(v31.ROOT/C0R_MACHINE_PROSE_REQUEST).read_bytes()
        machine_request=json.loads(machine_request_bytes)
        if hashlib.sha256(machine_request_bytes).hexdigest()!=C0R_MACHINE_PROSE_REQUEST_SHA256:
            errors.append("C0R machine-prose authorization changed or missing")
        if machine_request.get("status")!="AUTHORIZED" or machine_request.get("blocker")!="C0-T10-B062":
            errors.append("Explicit B062 machine-prose authorization missing")
        for source_path,key in [("tools/havenline/production/repair_sufficiency_critic.py","source_sha256"),("tools/havenline/production/tests/test_repair_sufficiency_critic.py","tests_sha256"),("tools/havenline/production/builder_repair_gate.py","builder_sha256"),("tools/havenline/production/tests/test_c0_builder.py","builder_tests_sha256"),("Docs/Production/C0R_REPORT_SCHEMA.json","contract_schema_sha256"),("Docs/Production/C0R_REPAIR_SUFFICIENCY_STANDARD.md","standard_sha256"),("tools/havenline/production/verify_python_repair_bindings.py","canonical_verifier_sha256"),("tools/havenline/production/tests/test_python_repair_bindings.py","canonical_verifier_tests_sha256")]:
            if hashlib.sha256((v31.ROOT/source_path).read_bytes()).hexdigest()!=machine_request.get(key):
                errors.append("C0R machine-prose source exceeds owner authorization: "+source_path)
        benchmark_request_bytes=(v31.ROOT/BENCHMARK_LIVENESS_REQUEST).read_bytes()
        benchmark_request=json.loads(benchmark_request_bytes)
        if hashlib.sha256(benchmark_request_bytes).hexdigest()!=BENCHMARK_LIVENESS_REQUEST_SHA256:
            errors.append("Bounded benchmark liveness authorization changed or missing")
        if benchmark_request.get("status")!="AUTHORIZED" or benchmark_request.get("blocker")!="C0-T10-B063":
            errors.append("Explicit B063 benchmark liveness authorization missing")
        for source_path,expected_hash in benchmark_request.get("implementation_sha256",{}).items():
            if hashlib.sha256((v31.ROOT/source_path).read_bytes()).hexdigest()!=expected_hash:
                errors.append("Benchmark liveness source exceeds exact owner authorization: "+source_path)
        if hashlib.sha256((v31.ROOT/"Docs/Production/T10/Proofs/benchmark-supervisor-trace-proof.json").read_bytes()).hexdigest()!=benchmark_request.get("trace_proof_sha256"):
            errors.append("Benchmark liveness trace proof changed or missing")
        errors += exact_owner_source_errors(SPECIALIST,SPECIALIST_BASE_SHA256,SPECIALIST_CURRENT_SHA256)
        if hashlib.sha256((v31.ROOT/SPECIALIST_BRANCH_REQUEST).read_bytes()).hexdigest()!=SPECIALIST_BRANCH_REQUEST_SHA256:
            errors.append("Complete specialist grammar branch authorization changed or missing")
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
        c0_terminal_request=json.loads((v31.ROOT/C0_TERMINAL_REQUEST).read_text())
        if hashlib.sha256((v31.ROOT/C0_TERMINAL_REQUEST).read_bytes()).hexdigest()!=C0_TERMINAL_REQUEST_SHA256:
            errors.append("Bounded C0 terminal-evidence authorization changed or missing")
        if c0_terminal_request.get("status")!="AUTHORIZED" or c0_terminal_request.get("blockers")!=["C0-T10-B059","C0-T10-B060","C0-T10-B061"]:
            errors.append("Explicit B059/B060/B061 terminal-evidence C0 authorization missing")
        c0_terminal_job_request=json.loads((v31.ROOT/C0_TERMINAL_JOB_LOG_REQUEST).read_text())
        if hashlib.sha256((v31.ROOT/C0_TERMINAL_JOB_LOG_REQUEST).read_bytes()).hexdigest()!=C0_TERMINAL_JOB_LOG_REQUEST_SHA256:
            errors.append("Bounded C0 terminal job-log authorization changed or missing")
        if c0_terminal_job_request.get("status")!="AUTHORIZED" or c0_terminal_job_request.get("blockers")!=["C0-T10-B059","C0-T10-B060","C0-T10-B061"]:
            errors.append("Explicit B059/B060/B061 terminal job-log C0 authorization missing")
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
        inherited_request=json.loads((v31.ROOT/BUILDER_INHERIT_REQUEST).read_text())
        if hashlib.sha256((v31.ROOT/BUILDER_INHERIT_REQUEST).read_bytes()).hexdigest()!=BUILDER_INHERIT_REQUEST_SHA256:
            errors.append("Bounded builder inherited-governance authorization changed or missing")
        if inherited_request.get("status")!="AUTHORIZED" or inherited_request.get("blocker")!="C0R-T10-RECONCILED-INHERITANCE":
            errors.append("Explicit T10 inherited-governance builder authorization missing")
        c0r_builder_request=json.loads((v31.ROOT/BUILDER_C0R_REQUEST).read_text())
        if hashlib.sha256((v31.ROOT/BUILDER_C0R_REQUEST).read_bytes()).hexdigest()!=BUILDER_C0R_REQUEST_SHA256:
            errors.append("Bounded canonical C0R builder authorization changed or missing")
        if c0r_builder_request.get("status")!="AUTHORIZED" or c0r_builder_request.get("blocker")!="C0R-T10-BUILDER-ENFORCEMENT":
            errors.append("Explicit canonical C0R builder enforcement authorization missing")
        errors += exact_owner_source_errors(WORKSTREAM,WORKSTREAM_BASE_SHA256,WORKSTREAM_CURRENT_SHA256)
        errors += exact_owner_source_errors(GUARD,GUARD_BASE_SHA256,GUARD_CURRENT_SHA256)
        if hashlib.sha256((v31.ROOT/GUARD_REQUEST).read_bytes()).hexdigest()!=GUARD_REQUEST_SHA256:
            errors.append("Exact candidate guard branch authorization changed or missing")
        workstream_request=json.loads((v31.ROOT/WORKSTREAM_REQUEST).read_text())
        if hashlib.sha256((v31.ROOT/WORKSTREAM_REQUEST).read_bytes()).hexdigest()!=WORKSTREAM_REQUEST_SHA256:
            errors.append("Bounded C0R workstream authorization-schema record changed or missing")
        if (
            workstream_request.get("status")!="AUTHORIZED"
            or workstream_request.get("blocker")!="C0-T10-B062"
            or workstream_request.get("integration_owner_disposition")!="APPROVED_BOUNDED_C0R_WORKSTREAM_SCHEMA"
            or WORKSTREAM not in workstream_request.get("target_path",[])
        ):
            errors.append("Explicit bounded C0R workstream authorization-schema repair missing")
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
        "scope": "T09 workflow reactivation, T10 authority canary, T10-only C7 proof runner, exact C0 failure evidence transport, causal repair bookkeeping, exact-byte inherited integration governance, canonical C0R builder enforcement for T10+, bounded workstream authorization-schema compatibility, actionable critic defects, bounded C0 model packets, grounded artifact diagnostics, terminal-first artifact evidence, latest-terminal failed-job log projection, and subject-isolated C0 execution",
        "predecessor_accepted_source": v31.ACCEPTED_SOURCE,
        "predecessor_manifest_sha256": baseline["manifest_sha256"],
        "unchanged_locked_files": baseline["locked_files_matching"],
        "authorized_changes": [POLICY, CANARY, FORWARD, FAILURE, BUILDER, WORKSTREAM, GUARD, C0_WORKFLOW, C0_ADVISOR, C0_DIAGNOSTICS, SPECIALIST],
        "authorization_record": REQUEST,
        "c7_authorization_record": C7_REQUEST,
        "failure_packet_authorization_record": FAILURE_REQUEST,
        "builder_authorization_record": BUILDER_REQUEST,
        "builder_inherited_governance_authorization_record": BUILDER_INHERIT_REQUEST,
        "builder_c0r_authorization_record": BUILDER_C0R_REQUEST,
        "workstream_authorization_schema_record": WORKSTREAM_REQUEST,
        "c0_job_log_authorization_record": C0_REQUEST,
        "c0_bounded_packet_authorization_record": C0_BOUNDED_REQUEST,
        "c0_grounding_authorization_record": C0_GROUNDING_REQUEST,
        "c0_complete_evidence_authorization_record": C0_COMPLETE_EVIDENCE_REQUEST,
        "c0_terminal_evidence_authorization_record": C0_TERMINAL_REQUEST,
        "c0_terminal_job_log_authorization_record": C0_TERMINAL_JOB_LOG_REQUEST,
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
