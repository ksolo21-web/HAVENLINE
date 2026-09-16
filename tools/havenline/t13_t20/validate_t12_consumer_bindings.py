#!/usr/bin/env python3
"""Fail closed if T13/T14 preparation drifts from T12's downstream consumer contract."""
from __future__ import annotations
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "Docs" / "Production"
CONTRACT_PATH = DOCS / "T12" / "DOWNSTREAM_CONSUMER_CONTRACT.json"
TASKS = ("T13", "T14")


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def git_blob_sha(path: pathlib.Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], cwd=ROOT, text=True).strip()


def main() -> int:
    errors = []
    contract = load(CONTRACT_PATH)
    consumers = contract.get("consumers", {})
    current_sha = git_blob_sha(CONTRACT_PATH)
    results = []
    for tid in TASKS:
        binding_path = DOCS / tid / "T12_CONSUMER_BINDING.json"
        if not binding_path.exists():
            errors.append(f"{tid}: missing T12_CONSUMER_BINDING.json")
            continue
        binding = load(binding_path)
        row = consumers.get(tid)
        if row is None:
            errors.append(f"{tid}: missing from T12 downstream consumer contract")
            continue
        task_errors = []
        if binding.get("contract_path") != "Docs/Production/T12/DOWNSTREAM_CONSUMER_CONTRACT.json":
            task_errors.append("contract path mismatch")
        if binding.get("prepared_contract_git_blob_sha") != current_sha:
            task_errors.append(
                f"stale T12 contract binding: prepared={binding.get('prepared_contract_git_blob_sha')} current={current_sha}"
            )
        for key in ("may_read", "must_not_require_from_T12", "boundary"):
            if binding.get(key) != row.get(key):
                task_errors.append(f"consumer field mismatch: {key}")
        errors.extend(f"{tid}: {e}" for e in task_errors)
        results.append({"task_id": tid, "contract_blob_sha": current_sha, "passed": not task_errors, "errors": task_errors})
    out = {"contract": str(CONTRACT_PATH.relative_to(ROOT)), "contract_blob_sha": current_sha, "results": results, "passed": not errors, "errors": errors}
    print(json.dumps(out, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
