#!/usr/bin/env python3
"""Authorized bounded V3.2 T10 canary repair over the immutable V3.1 baseline."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import validate_architecture_release_lock as v31
from validate_architecture_v32_t09 import POLICY, policy_errors

CANARY = "tools/havenline/production/mutation_canary.py"
REQUEST = "Docs/Production/ChangeRequests/T10-task-state-canary-reactivation.json"
AUTHORIZATION = "Authorize the bounded V3.2 T10 canary repair."


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
    }
    errors = [error for error in baseline["errors"] if error not in allowed]
    try:
        accepted_policy = json.loads(v31._git("show", f"{v31.ACCEPTED_SOURCE}:{POLICY}").stdout)
        current_policy = json.loads((v31.ROOT / POLICY).read_text())
        errors += policy_errors(accepted_policy, current_policy)
        accepted_canary = v31._git("show", f"{v31.ACCEPTED_SOURCE}:{CANARY}").stdout.decode()
        current_canary = (v31.ROOT / CANARY).read_text()
        errors += canary_delta_errors(accepted_canary, current_canary)
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
        "scope": "T09 workflow reactivation plus T10 lifecycle-independent authority canary repair",
        "predecessor_accepted_source": v31.ACCEPTED_SOURCE,
        "predecessor_manifest_sha256": baseline["manifest_sha256"],
        "unchanged_locked_files": baseline["locked_files_matching"],
        "authorized_changes": [POLICY, CANARY],
        "authorization_record": REQUEST,
        "errors": errors,
    }


def main() -> int:
    parser=argparse.ArgumentParser();parser.add_argument("--output");args=parser.parse_args()
    result=validate();text=json.dumps(result,indent=2)+"\n";print(text,end="")
    if args.output:Path(args.output).write_text(text)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
