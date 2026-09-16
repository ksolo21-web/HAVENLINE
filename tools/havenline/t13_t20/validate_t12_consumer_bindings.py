#!/usr/bin/env python3
"""Validate T13/T14 local upstream binding snapshots; rebind to T12 only at activation."""
from __future__ import annotations
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "Docs" / "Production"
CONTRACT_PATH = DOCS / "T12" / "DOWNSTREAM_CONSUMER_CONTRACT.json"
EXPECTED_CONTRACT_PATH = "Docs/Production/T12/DOWNSTREAM_CONSUMER_CONTRACT.json"
TASKS = ("T13", "T14")


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def git_blob_sha(path: pathlib.Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], cwd=ROOT, text=True).strip()


def main() -> int:
    errors = []
    contract_present = CONTRACT_PATH.exists()
    contract = load(CONTRACT_PATH) if contract_present else {}
    consumers = contract.get("consumers", {})
    current_sha = git_blob_sha(CONTRACT_PATH) if contract_present else None
    results = []
    for tid in TASKS:
        binding_path = DOCS / tid / "T12_CONSUMER_BINDING.json"
        task_errors = []
        if not binding_path.exists():
            task_errors.append("missing T12_CONSUMER_BINDING.json")
        else:
            binding = load(binding_path)
            if binding.get("consumer_task") != tid:
                task_errors.append("consumer_task mismatch")
            if binding.get("contract_path") != EXPECTED_CONTRACT_PATH:
                task_errors.append("contract path mismatch")
            prepared = binding.get("prepared_contract_git_blob_sha")
            if not isinstance(prepared, str) or len(prepared) != 40:
                task_errors.append("prepared upstream contract blob SHA missing/invalid")
            if not binding.get("activation_rule"):
                task_errors.append("activation-time fail-closed rebind rule missing")
            if contract_present:
                row = consumers.get(tid)
                if row is None:
                    task_errors.append("missing from current T12 downstream consumer contract")
                else:
                    if prepared != current_sha:
                        task_errors.append(f"stale T12 binding: prepared={prepared} current={current_sha}")
                    for key in ("may_read", "must_not_require_from_T12", "boundary"):
                        if binding.get(key) != row.get(key):
                            task_errors.append(f"consumer field mismatch: {key}")
        errors.extend(f"{tid}: {e}" for e in task_errors)
        results.append({"task_id":tid,"upstream_contract_present":contract_present,"activation_rebind_required":not contract_present,"contract_blob_sha":current_sha,"passed":not task_errors,"errors":task_errors})
    out={"contract":EXPECTED_CONTRACT_PATH,"upstream_contract_present":contract_present,"activation_rebind_required":not contract_present,"results":results,"passed":not errors,"errors":errors}
    print(json.dumps(out,indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
