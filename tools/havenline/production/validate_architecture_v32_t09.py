#!/usr/bin/env python3
"""Authorized V3.2 T09 reactivation; retain the complete V3.1 byte lock."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import validate_architecture_release_lock as v31

POLICY = "Docs/Production/CI_TOOLCHAIN_LOCK.json"
WORKFLOW = ".github/workflows/havenline-task09-harvesting.yml"
REQUEST = "Docs/Production/ChangeRequests/T09-reviewed-repair-reactivation.json"

def policy_errors(accepted, current):
    expected = json.loads(json.dumps(accepted))
    if WORKFLOW not in expected.get("retired_workflows", {}):
        return ["V3.1 baseline does not contain the expected retired T09 workflow"]
    del expected["retired_workflows"][WORKFLOW]
    expected["critical_workflows"].append(WORKFLOW)
    return [] if current == expected else ["V3.2 permits only T09 retirement removal and critical-workflow registration"]

def validate():
    baseline = v31.validate()
    errors = [e for e in baseline["errors"] if e != f"V3.1 locked file changed: {POLICY}"]
    try:
        accepted = json.loads(v31._git("show", f"{v31.ACCEPTED_SOURCE}:{POLICY}").stdout)
        current = json.loads((v31.ROOT / POLICY).read_text())
        errors += policy_errors(accepted, current)
        request = json.loads((v31.ROOT / REQUEST).read_text())
        if request.get("authorization") != "User explicitly answered yes to the bounded V3.2 T09 reactivation request in this session.":
            errors.append("Explicit bounded V3.2 authorization record missing")
        from ci_toolchain_lock import validate as validate_ci
        errors += validate_ci()["errors"]
    except Exception as exc:
        errors.append(str(exc))
    return {"passed": not errors, "architecture_version": "3.2", "scope": "T09 workflow reactivation only",
            "predecessor_accepted_source": v31.ACCEPTED_SOURCE,
            "predecessor_manifest_sha256": baseline["manifest_sha256"],
            "unchanged_locked_files": baseline["locked_files_matching"],
            "authorized_policy_changes": [POLICY], "errors": errors}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()
    result = validate()
    text = json.dumps(result, indent=2) + "\n"
    print(text, end="")
    if args.output:
        Path(args.output).write_text(text)
    return 0 if result["passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
