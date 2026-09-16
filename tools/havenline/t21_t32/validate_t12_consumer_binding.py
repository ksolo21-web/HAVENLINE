#!/usr/bin/env python3
"""Fail closed if T32 drifts from T12's downstream consumer contract."""
from __future__ import annotations
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "Docs" / "Production"
CONTRACT = DOCS / "T12" / "DOWNSTREAM_CONSUMER_CONTRACT.json"
BINDING = DOCS / "T32" / "T12_CONSUMER_BINDING.json"


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def blob_sha(path: pathlib.Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], cwd=ROOT, text=True).strip()


def main() -> int:
    contract = load(CONTRACT)
    binding = load(BINDING)
    row = contract.get("consumers", {}).get("T32")
    errors = []
    current = blob_sha(CONTRACT)
    if row is None:
        errors.append("T32 missing from T12 downstream consumer contract")
    else:
        if binding.get("prepared_contract_git_blob_sha") != current:
            errors.append(f"stale T12 contract binding: prepared={binding.get('prepared_contract_git_blob_sha')} current={current}")
        for key in ("may_read", "owned_band", "owned_levels", "boundary"):
            if binding.get(key) != row.get(key):
                errors.append(f"T32 consumer field mismatch: {key}")
    out = {"task_id":"T32","contract_blob_sha":current,"passed":not errors,"errors":errors}
    print(json.dumps(out, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
