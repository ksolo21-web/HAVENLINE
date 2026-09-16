#!/usr/bin/env python3
"""Validate T44-T52 local upstream region snapshots; rebind to T12 only at activation."""
from __future__ import annotations
import json
import pathlib
import subprocess

ROOT=pathlib.Path(__file__).resolve().parents[3]
DOCS=ROOT/"Docs"/"Production"
CONTRACT=DOCS/"T12"/"DOWNSTREAM_CONSUMER_CONTRACT.json"
BINDINGS=DOCS/"T44_T52_T12_CONSUMER_BINDINGS.json"
TASKS=[f"T{i:02d}" for i in range(44,53)]

def load(path): return json.loads(path.read_text(encoding="utf-8"))
def blob_sha(path): return subprocess.check_output(["git","hash-object",str(path)],cwd=ROOT,text=True).strip()

def main():
    errors=[]; results=[]
    if not BINDINGS.exists():
        errors.append("local T44-T52 upstream binding registry missing"); registry={}
    else:
        registry=load(BINDINGS)
        prepared=registry.get("prepared_contract_git_blob_sha")
        if not isinstance(prepared,str) or len(prepared)!=40: errors.append("prepared upstream contract blob SHA missing/invalid")
    bindings=registry.get("bindings",{})
    bands=[]; level_slots=[]
    for tid in TASKS:
        task_errors=[]; binding=bindings.get(tid)
        if binding is None:
            task_errors.append("missing from local region binding registry")
        else:
            if not binding.get("owned_band"): task_errors.append("owned_band missing")
            levels=binding.get("owned_levels")
            if not isinstance(levels,list) or len(levels)!=2 or not all(isinstance(x,int) for x in levels):
                task_errors.append("owned_levels invalid")
            else:
                bands.append(binding.get("owned_band")); level_slots.extend(range(levels[0],levels[1]+1))
        errors.extend(f"{tid}: {e}" for e in task_errors); results.append({"task_id":tid,"passed":not task_errors,"errors":task_errors})
    if len(bands)!=len(set(bands)): errors.append("duplicate local region band ownership")
    if sorted(level_slots)!=list(range(11,101)): errors.append("local region bindings must cover Levels 11-100 exactly once")
    present=CONTRACT.exists(); current=blob_sha(CONTRACT) if present else None
    if present:
        contract=load(CONTRACT); consumers=contract.get("consumers",{})
        if registry.get("prepared_contract_git_blob_sha")!=current: errors.append("stale T12 contract binding; activation rebind required")
        for tid in TASKS:
            row=consumers.get(tid); binding=bindings.get(tid)
            if row is None: errors.append(f"{tid}: missing from current upstream contract")
            elif binding is not None:
                for key in ("owned_band","owned_levels","may_read","boundary"):
                    if binding.get(key)!=row.get(key): errors.append(f"{tid}: consumer field mismatch: {key}")
    out={"upstream_contract_present":present,"activation_rebind_required":not present,"contract_blob_sha":current,"results":results,"level_coverage":[11,100],"passed":not errors,"errors":errors}
    print(json.dumps(out,indent=2)); return 0 if not errors else 1

if __name__=="__main__": raise SystemExit(main())
