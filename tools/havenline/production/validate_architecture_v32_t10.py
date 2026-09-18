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
    }
    errors = [error for error in baseline["errors"] if error not in allowed]
    try:
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
        "scope": "T09 workflow reactivation, T10 authority canary, T10-only C7 proof runner and exact C0 failure packet log compatibility",
        "predecessor_accepted_source": v31.ACCEPTED_SOURCE,
        "predecessor_manifest_sha256": baseline["manifest_sha256"],
        "unchanged_locked_files": baseline["locked_files_matching"],
        "authorized_changes": [POLICY, CANARY, FORWARD, FAILURE],
        "authorization_record": REQUEST,
        "c7_authorization_record": C7_REQUEST,
        "failure_packet_authorization_record": FAILURE_REQUEST,
        "errors": errors,
    }


def main() -> int:
    parser=argparse.ArgumentParser();parser.add_argument("--output");args=parser.parse_args()
    result=validate();text=json.dumps(result,indent=2)+"\n";print(text,end="")
    if args.output:Path(args.output).write_text(text)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
