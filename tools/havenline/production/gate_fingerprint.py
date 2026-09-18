#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from forward_execution import DOCS, ROOT, resolve_task
from ci_toolchain_lock import provenance as runner_provenance

POLICY = DOCS / "GATE_FINGERPRINT_POLICY.json"
INDEX = DOCS / "GATE_RESULT_INDEX.json"
REGISTRY = DOCS / "WORKSTREAM_REGISTRY.json"
RUNNERS = DOCS / "FORWARD_GATE_RUNNERS.json"
TOOLCHAIN = DOCS / "CI_TOOLCHAIN_LOCK.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=check)


def _assert_commit(commit: str) -> None:
    if len(commit) != 40 or any(c not in "0123456789abcdefABCDEF" for c in commit):
        raise ValueError("candidate must be an exact 40-character commit")
    result = _git("cat-file", "-e", f"{commit}^{{commit}}", check=False)
    if result.returncode != 0:
        raise ValueError(f"candidate commit unavailable locally: {commit}")


def _tree_entries(commit: str, rel: str) -> list[str]:
    result = _git("ls-tree", "-r", "--full-tree", commit, "--", rel, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git ls-tree failed for {rel}")
    entries = []
    for line in result.stdout.splitlines():
        if not line.strip(): continue
        meta, path = line.split("\t", 1); parts = meta.split()
        if len(parts) >= 3: entries.append(f"{parts[2]} {path}")
    return sorted(entries)


def _accepted_dependency_sources(task_id: str) -> dict[str, str]:
    plan = resolve_task(task_id); registry = load_json(REGISTRY); workstreams = {w.get("task_id"): w for w in registry.get("workstreams", [])}; legacy = registry.get("legacy_approvals", {}); out = {}
    for dep in plan["dependencies"]:
        ws = workstreams.get(dep, {}); source = ws.get("candidate_commit") or ws.get("integrated_source") or legacy.get(dep, {}).get("accepted_source")
        if not source: raise ValueError(f"approved dependency {dep} lacks accepted source identity")
        out[dep] = source
    return out


def environment_identity() -> dict[str, Any]:
    prov=runner_provenance(); lock=load_json(TOOLCHAIN); complete=bool(prov.get('provenance_complete'))
    material={'runner':{k:prov.get(k) for k in ('ImageOS','ImageVersion','RUNNER_OS','RUNNER_ARCH')},'tools':lock.get('tools',{}),'runner_label':lock.get('runner',{}).get('required_label')}
    digest=hashlib.sha256(json.dumps(material,sort_keys=True,separators=(',',':')).encode()).hexdigest() if complete else None
    return {'complete':complete,'fingerprint':digest,'material':material}


def fingerprint(task_id: str, gate: str, candidate: str) -> dict[str, Any]:
    task_id = task_id.upper(); gate = gate.strip(); _assert_commit(candidate); plan = resolve_task(task_id)
    if gate not in plan["ordered_gates"]: raise ValueError(f"gate {gate} is not selected for {task_id}")
    policy = load_json(POLICY); row = policy.get("gates", {}).get(gate)
    if not row: raise ValueError(f"gate fingerprint policy missing {gate}")
    runner_row = load_json(RUNNERS)["gates"].get(gate)
    if not runner_row: raise ValueError(f"runner contract missing {gate}")
    rels = list(policy.get("global_inputs", []))
    rels += [t.format(task=task_id, task_lower=task_id.lower()) for t in policy.get("task_inputs", [])]
    rels += row.get("extra_inputs", []); rels = sorted(dict.fromkeys(rels)); manifest={};missing=[]
    for rel in rels:
        entries=_tree_entries(candidate,rel)
        if entries:manifest[rel]=entries
        elif rel != f"tools/havenline/{task_id.lower()}":missing.append(rel)
    if missing: raise ValueError("fingerprint inputs missing: " + ", ".join(missing))
    material={"schema_version":1,"task_id":task_id,"gate":gate,"reuse_class":row["reuse"],"runtime_and_input_manifest":manifest,"runner_contract":runner_row,"accepted_dependency_sources":_accepted_dependency_sources(task_id),"task_archetype":plan["archetype"],"execution_mode":plan["execution_mode"],"critics":plan["critics"]}
    digest=hashlib.sha256(json.dumps(material,sort_keys=True,separators=(",", ":")).encode()).hexdigest();env=environment_identity();sensitive=gate in set(load_json(TOOLCHAIN).get('environment_sensitive_reuse_gates',[]))
    return {"task_id":task_id,"gate":gate,"candidate":candidate,"fingerprint":digest,"reuse_class":row["reuse"],"input_count":sum(len(v) for v in manifest.values()),"accepted_dependency_sources":material["accepted_dependency_sources"],"environment_sensitive":sensitive,"environment":env,"material":material}


def lookup(task_id: str, gate: str, candidate: str) -> dict[str, Any]:
    current=fingerprint(task_id,gate,candidate);index=load_json(INDEX);matches=[r for r in index.get("records",[]) if r.get("task_id")==task_id.upper() and r.get("gate")==gate and r.get("fingerprint")==current["fingerprint"] and r.get("result")=="PASS"];matches.sort(key=lambda r:str(r.get('recorded_at','')),reverse=True)
    reuse=current["reuse_class"];decision="RUN_FRESH";reason="no matching prior PASS fingerprint";prior=matches[0] if matches else None
    if prior:
        if current['environment_sensitive']:
            env=current['environment']
            if not env['complete']:
                return {"current":current,"decision":"RUN_FRESH","reason":"runner provenance unavailable; environment-sensitive proof cannot be reused","prior_record":prior}
            if prior.get('environment_fingerprint') != env['fingerprint']:
                return {"current":current,"decision":"RUN_FRESH","reason":"runner/toolchain environment fingerprint changed","prior_record":prior}
        if reuse=="exact_source_required":
            if prior.get("candidate")==candidate:decision,reason="REUSE_EXACT_SOURCE","same exact candidate and fingerprint"
            else:decision,reason="RUN_FRESH","gate requires exact source even though logical inputs match"
        elif reuse=="deterministic_reusable":decision,reason="REUSE_PASS","complete gate-input and environment fingerprints match prior deterministic PASS"
        elif reuse=="rebind_with_provenance":decision,reason="REUSE_WITH_PROVENANCE_BRIDGE","heavy evidence inputs and environment match; bind prior immutable evidence with provenance"
    return {"current":current,"decision":decision,"reason":reason,"prior_record":prior}


def provenance_bridge(task_id: str, gate: str, candidate: str) -> dict[str, Any]:
    result=lookup(task_id,gate,candidate)
    if result["decision"]!="REUSE_WITH_PROVENANCE_BRIDGE":raise ValueError("provenance bridge is only valid for a matching rebind_with_provenance PASS")
    prior=result["prior_record"]
    return {"schema_version":1,"task_id":task_id.upper(),"gate":gate,"new_candidate":candidate,"fingerprint":result["current"]["fingerprint"],"environment_fingerprint":result['current']['environment']['fingerprint'],"prior_candidate":prior["candidate"],"prior_evidence":prior.get("evidence"),"prior_result":prior["result"],"statement":"Relevant runtime, harness, authority, accepted-dependency and runner/toolchain inputs match under the V3.1 proof policy. Evidence bytes may be reused only through this provenance bridge; fresh-only gates remain fresh."}


def validate_policy() -> dict[str, Any]:
    policy=load_json(POLICY);runners=load_json(RUNNERS);lock=load_json(TOOLCHAIN);errors=[];allowed=set(policy.get("allowed_reuse_values",[]));gate_order=load_json(DOCS/"FORWARD_EXECUTION_PROFILES.json").get("gate_order",[])
    if set(policy.get("gates",{}))!=set(gate_order):errors.append("fingerprint policy must cover every forward gate exactly")
    for gate,row in policy.get("gates",{}).items():
        if row.get("reuse") not in allowed:errors.append(f"{gate} invalid reuse class")
        if gate not in runners.get("gates",{}):errors.append(f"{gate} missing runner contract")
    for gate in ("physical_device","critic_review","integration","post_integration_regression","closeout","release_manifest"):
        if policy.get("gates",{}).get(gate,{}).get("reuse")!="exact_source_required":errors.append(f"{gate} must remain exact_source_required")
    if policy.get("fail_result_reuse")!="forbidden":errors.append("failed results must never be reused as PASS")
    index=load_json(INDEX)
    if not isinstance(index.get("records"),list):errors.append("gate result index records must be a list")
    for row in index.get('records',[]):
        if row.get('record_type')=='exact_source_provenance':
            if row.get('result')!='PASS' or row.get('reuse_eligible') is not False:errors.append('exact-source provenance must be PASS and non-reusable')
            if len(str(row.get('candidate','')))!=40:errors.append('exact-source provenance candidate must be exact SHA')
            evidence=row.get('evidence',{})
            for key in ('original_artifact_sha256','complete_evidence_index_sha256','retained_artifact_sha256'):
                if not re.fullmatch(r'[0-9a-f]{64}',str(evidence.get(key,''))):errors.append('exact-source provenance invalid '+key)
            provenance=row.get('runner_provenance',{})
            for key in ('ImageOS','ImageVersion','RUNNER_OS','RUNNER_ARCH'):
                if not provenance.get(key):errors.append('exact-source provenance missing '+key)
            continue
        if row.get('gate') in set(lock.get('environment_sensitive_reuse_gates',[])) and row.get('result')=='PASS' and not row.get('environment_fingerprint'):errors.append(f"environment-sensitive PASS record missing environment_fingerprint: {row.get('task_id')} {row.get('gate')}")
    return {"passed":not errors,"gate_count":len(policy.get("gates",{})),"errors":errors}


def main() -> int:
    ap=argparse.ArgumentParser(description="Havenline V3.1 content-addressed gate proof");sub=ap.add_subparsers(dest="command",required=True);sub.add_parser("validate")
    for command in ("fingerprint","lookup","bridge"):
        p=sub.add_parser(command);p.add_argument("task_id");p.add_argument("gate");p.add_argument("candidate");p.add_argument("--output")
    args=ap.parse_args();report=validate_policy() if args.command=="validate" else (fingerprint(args.task_id,args.gate,args.candidate) if args.command=="fingerprint" else (lookup(args.task_id,args.gate,args.candidate) if args.command=="lookup" else provenance_bridge(args.task_id,args.gate,args.candidate)))
    text=json.dumps(report,indent=2)+"\n";out=getattr(args,"output",None)
    if out:p=(ROOT/out).resolve();p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    print(text,end="");return 0 if not report.get("errors") else 2
if __name__=="__main__":raise SystemExit(main())
