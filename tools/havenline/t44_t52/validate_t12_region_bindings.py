#!/usr/bin/env python3
"""Fail closed if T44-T52 region bindings drift from T12's downstream consumer contract."""
from __future__ import annotations
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "Docs" / "Production"
CONTRACT = DOCS / "T12" / "DOWNSTREAM_CONSUMER_CONTRACT.json"
BINDINGS = DOCS / "T44_T52_T12_CONSUMER_BINDINGS.json"
TASKS = [f"T{i:02d}" for i in range(44, 53)]


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def blob_sha(path: pathlib.Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], cwd=ROOT, text=True).strip()


def main() -> int:
    contract = load(CONTRACT)
    registry = load(BINDINGS)
    current = blob_sha(CONTRACT)
    errors = []
    if registry.get("prepared_contract_git_blob_sha") != current:
        errors.append(
            f"stale T12 contract binding: prepared={registry.get('prepared_contract_git_blob_sha')} current={current}"
        )
    consumers = contract.get("consumers", {})
    bindings = registry.get("bindings", {})
    results = []
    for tid in TASKS:
        row = consumers.get(tid)
        binding = bindings.get(tid)
        task_errors = []
        if row is None:
            task_errors.append("missing from T12 downstream consumer contract")
        if binding is None:
            task_errors.append("missing from region binding registry")
        if row is not None and binding is not None:
            for key in ("owned_band", "owned_levels", "may_read", "boundary"):
                if binding.get(key) != row.get(key):
                    task_errors.append(f"consumer field mismatch: {key}")
        errors.extend(f"{tid}: {e}" for e in task_errors)
        results.append({"task_id":tid,"passed":not task_errors,"errors":task_errors})
    bands = [bindings[t]["owned_band"] for t in TASKS if t in bindings]
    if len(bands) != len(set(bands)):
        errors.append("duplicate T12 region band ownership")
    level_slots = []
    for tid in TASKS:
        if tid in bindings:
            start, end = bindings[tid]["owned_levels"]
            level_slots.extend(range(start, end + 1))
    if sorted(level_slots) != list(range(11, 101)):
        errors.append("region bindings must cover Levels 11-100 exactly once")
    out = {"contract_blob_sha":current,"results":results,"level_coverage":[11,100],"passed":not errors,"errors":errors}
    print(json.dumps(out, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
