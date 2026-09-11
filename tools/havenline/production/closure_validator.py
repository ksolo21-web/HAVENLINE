#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, pathlib, subprocess, sys
from lib import ROOT, DOCS, load_json, ensure_score_strictly_above_nine, sha256_file

ALL_GATES=[f"G{i}" for i in range(1,15)]

def main():
    ap=argparse.ArgumentParser();ap.add_argument("manifest");a=ap.parse_args()
    p=pathlib.Path(a.manifest)
    if not p.is_absolute():p=ROOT/p
    d=json.loads(p.read_text());errors=[]
    task=d.get("task_id");candidate=d.get("candidate_commit");base=d.get("base_commit")
    graph=load_json(DOCS/"DEPENDENCY_GRAPH.json");critcfg=load_json(DOCS/"CRITIC_MATRIX.json")
    if task not in graph["tasks"]:errors.append("unknown task")
    for dep in graph["tasks"].get(task,{}).get("dependencies",[]):
        if graph["tasks"][dep]["status"]!="APPROVED":errors.append("dependency not approved: "+dep)
    if not candidate or len(candidate)!=40:errors.append("invalid candidate commit")
    if not base or len(base)!=40:errors.append("invalid base commit")
    # Path ownership/staleness proof must be preserved from workstream validator.
    pv=d.get("path_validation",{})
    if pv.get("passed") is not True or pv.get("candidate")!=candidate or pv.get("base")!=base:
        errors.append("missing/invalid exact-candidate path validation")
    # G1-G14: applicable must be explicit PASS. N/A requires rationale.
    gates=d.get("gates",{})
    for gate in ALL_GATES:
        row=gates.get(gate)
        if not row: errors.append("missing gate "+gate);continue
        if row.get("status")=="N/A":
            if not row.get("rationale"):errors.append("N/A gate lacks rationale "+gate)
        elif row.get("status")!="PASS":
            errors.append("gate not PASS "+gate)
    tests=d.get("tests",{})
    if tests.get("passed") is not True or not tests.get("records"):errors.append("tests incomplete")
    evidence=d.get("evidence",{})
    if evidence.get("candidate_commit")!=candidate or not evidence.get("provenance_hash") or not evidence.get("files"):
        errors.append("evidence provenance incomplete/stale")
    else:
        root=(ROOT/evidence.get("root","")).resolve()
        for rel,h in evidence["files"].items():
            fp=root/rel
            if not fp.exists() or sha256_file(fp)!=h:errors.append("evidence hash mismatch "+rel)
    if d.get("unresolved_mandatory_defects"):errors.append("unresolved mandatory defects")
    required=critcfg["task_applicability"].get(task,[])
    critics=d.get("critics",{})
    for cid in required:
        row=critics.get(cid)
        if not row:errors.append("missing critic "+cid);continue
        if row.get("status")!="PASS":errors.append("critic not PASS "+cid)
        if row.get("candidate_commit")!=candidate:errors.append("critic candidate mismatch "+cid)
        errors += [f"{cid}: {x}" for x in ensure_score_strictly_above_nine(row.get("scores",{}))]
        if row.get("defects"):errors.append("critic defects "+cid)
        if row.get("coverage_complete") is not True:errors.append("critic incomplete "+cid)
    # Exact integration candidate must be tested, not only isolated branch.
    integ=d.get("integration",{})
    if integ.get("candidate_commit")!=candidate or integ.get("regression_passed") is not True:
        errors.append("integration candidate regression missing")
    result={"task_id":task,"candidate_commit":candidate,"passed":not errors,"errors":errors,"approval_allowed":not errors}
    print(json.dumps(result,indent=2))
    if errors:raise SystemExit(1)

if __name__=="__main__":main()
