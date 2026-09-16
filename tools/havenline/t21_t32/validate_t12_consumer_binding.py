#!/usr/bin/env python3
"""Validate T32 local upstream binding snapshot; rebind to T12 only at activation."""
from __future__ import annotations
import json
import pathlib
import subprocess

ROOT=pathlib.Path(__file__).resolve().parents[3]
DOCS=ROOT/"Docs"/"Production"
CONTRACT=DOCS/"T12"/"DOWNSTREAM_CONSUMER_CONTRACT.json"
BINDING=DOCS/"T32"/"T12_CONSUMER_BINDING.json"
EXPECTED="Docs/Production/T12/DOWNSTREAM_CONSUMER_CONTRACT.json"

def load(path): return json.loads(path.read_text(encoding="utf-8"))
def blob_sha(path): return subprocess.check_output(["git","hash-object",str(path)],cwd=ROOT,text=True).strip()

def main():
    errors=[]
    if not BINDING.exists():
        errors.append("T32 local upstream binding snapshot missing")
        binding={}
    else:
        binding=load(BINDING)
        if binding.get("consumer_task")!="T32": errors.append("consumer_task mismatch")
        if binding.get("contract_path")!=EXPECTED: errors.append("contract path mismatch")
        prepared=binding.get("prepared_contract_git_blob_sha")
        if not isinstance(prepared,str) or len(prepared)!=40: errors.append("prepared upstream contract blob SHA missing/invalid")
        if binding.get("owned_levels")!=[1,10]: errors.append("T32 local opening-level ownership must remain [1,10]")
        if not binding.get("owned_band"): errors.append("T32 local owned_band missing")
        if not binding.get("activation_rule"): errors.append("activation-time fail-closed rebind rule missing")
    present=CONTRACT.exists(); current=blob_sha(CONTRACT) if present else None
    if present and not errors:
        contract=load(CONTRACT); row=contract.get("consumers",{}).get("T32")
        if row is None: errors.append("T32 missing from current T12 downstream consumer contract")
        else:
            if binding.get("prepared_contract_git_blob_sha")!=current: errors.append("stale T12 contract binding; activation rebind required")
            for key in ("may_read","owned_band","owned_levels","boundary"):
                if binding.get(key)!=row.get(key): errors.append(f"T32 consumer field mismatch: {key}")
    out={"task_id":"T32","upstream_contract_present":present,"activation_rebind_required":not present,"contract_blob_sha":current,"passed":not errors,"errors":errors}
    print(json.dumps(out,indent=2)); return 0 if not errors else 1

if __name__=="__main__": raise SystemExit(main())
