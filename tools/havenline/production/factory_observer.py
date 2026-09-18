#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from lib import DOCS, ROOT, load_json
from runtime_dependency_learning import validate_trace
from task_state_snapshot import snapshot, validate as validate_snapshot

TELEMETRY_POLICY = DOCS / "PIPELINE_TELEMETRY_POLICY.json"
TOOLCHAIN_LOCK = DOCS / "CI_TOOLCHAIN_LOCK.json"
TASK_RE = re.compile(r"\bT([0-9]{2})\b", re.IGNORECASE)


def _load(path: str | Path | None, default: dict | None = None) -> dict:
    if not path:return default or {}
    return json.loads(Path(path).read_text())

def _iso(value: str | None) -> datetime | None:
    if not value:return None
    text=str(value).strip().replace("Z","+00:00")
    try:parsed=datetime.fromisoformat(text)
    except ValueError:return None
    if parsed.tzinfo is None:parsed=parsed.replace(tzinfo=timezone.utc)
    return parsed

def _seconds(start: str | None,end: str | None) -> float | None:
    a=_iso(start);b=_iso(end)
    if not a or not b:return None
    return round(max(0.0,(b-a).total_seconds()),3)
def _sha256_bytes(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def _toolchain_digest()->str:return _sha256_bytes(TOOLCHAIN_LOCK.read_bytes())
def _canonical_fingerprint(provenance:dict)->str|None:
    required=("ImageOS","ImageVersion","RUNNER_OS","RUNNER_ARCH")
    if not all(str(provenance.get(k,"")).strip() for k in required):return None
    material={k:provenance[k] for k in required};material["ci_toolchain_lock_sha256"]=_toolchain_digest()
    return _sha256_bytes(json.dumps(material,sort_keys=True,separators=(",",":")).encode())
def _find_runtime_provenance(artifact_root:str|Path|None)->dict:
    if not artifact_root:return {}
    root=Path(artifact_root)
    if not root.exists():return {}
    candidates=sorted(root.rglob("runtime-provenance.json"));valid=[]
    for path in candidates:
        try:row=json.loads(path.read_text())
        except Exception:continue
        if isinstance(row,dict):valid.append(row)
    if not valid:return {}
    core=("ImageOS","ImageVersion","RUNNER_OS","RUNNER_ARCH")
    identities={tuple(str(row.get(k,"")) for k in core) for row in valid}
    if len(identities)!=1:return {"ambiguous":True,"candidate_count":len(valid)}
    merged={k:valid[0].get(k) for k in core};merged["source_files"]=[str(p) for p in candidates];return merged
def _jobs_list(jobs:dict)->list[dict]:
    rows=jobs.get("jobs",[]) if isinstance(jobs,dict) else []
    return [row for row in rows if isinstance(row,dict)]
def _artifact_bytes(artifacts:dict)->int:
    total=0
    for row in artifacts.get("artifacts",[]) if isinstance(artifacts,dict) else []:
        try:total+=max(0,int(row.get("size_in_bytes",0)))
        except Exception:pass
    return total
def _terminal_from_jobs(jobs:list[dict],run:dict)->tuple[str,str]:
    failures=[];completed=[]
    for job in jobs:
        job_name=str(job.get("name") or "unnamed-job")
        for step in job.get("steps",[]) or []:
            if not isinstance(step,dict):continue
            name=str(step.get("name") or "unnamed-step");conclusion=str(step.get("conclusion") or "").lower();end=_iso(step.get("completed_at")) or datetime.min.replace(tzinfo=timezone.utc)
            if conclusion in {"failure","cancelled","timed_out","action_required","startup_failure"}:failures.append((end,f"{job_name}: {name}",conclusion))
            if conclusion:completed.append((end,f"{job_name}: {name}",conclusion))
    chosen=max(failures or completed,default=None,key=lambda x:x[0])
    if chosen:gate,conclusion=chosen[1],chosen[2]
    else:gate="workflow";conclusion=str(run.get("conclusion") or run.get("status") or "unknown").lower()
    mapping={"success":"SUCCESS","failure":"FAILURE","cancelled":"CANCELLED","timed_out":"TIMED_OUT","action_required":"ACTION_REQUIRED","startup_failure":"INFRASTRUCTURE_FAILURE","stale":"STALE","skipped":"SKIPPED","neutral":"NEUTRAL","completed":"COMPLETED_UNKNOWN","in_progress":"IN_PROGRESS","queued":"QUEUED","unknown":"UNKNOWN"}
    return gate,mapping.get(conclusion,conclusion.upper() or "UNKNOWN")
def _gate_durations(jobs:list[dict])->dict[str,float]:
    out={}
    for job in jobs:
        job_name=str(job.get("name") or "unnamed-job")
        for index,step in enumerate(job.get("steps",[]) or []):
            if not isinstance(step,dict):continue
            duration=_seconds(step.get("started_at"),step.get("completed_at"))
            if duration is not None:out[f"{job_name}::{index+1}:{step.get('name') or 'unnamed-step'}"]=duration
    return out
def _run_duration(run:dict,jobs:list[dict])->float|None:
    start=_iso(run.get("run_started_at"))
    if not start:
        starts=[_iso(j.get("started_at")) for j in jobs];starts=[x for x in starts if x];start=min(starts) if starts else None
    ends=[_iso(j.get("completed_at")) for j in jobs];ends=[x for x in ends if x];end=max(ends) if ends else _iso(run.get("updated_at"))
    if not start or not end:return None
    return round(max(0.0,(end-start).total_seconds()),3)
def _infer_task(run:dict,explicit:str|None)->str|None:
    if explicit:
        task=explicit.upper()
        if re.fullmatch(r"T[0-9]{2}",task):return task
        raise ValueError("task must be canonical TNN")
    text=" ".join(str(run.get(k,"")) for k in ("name","display_title","head_branch","path"));matches={f"T{m}" for m in TASK_RE.findall(text)}
    return next(iter(matches)) if len(matches)==1 else None
def _flake_observations(source:str,jobs:list[dict],env_fingerprint:str|None,run_id:int|None)->list[dict]:
    if not env_fingerprint or not re.fullmatch(r"[0-9a-f]{40}",source or ""):return []
    rows=[]
    for job in jobs:
        job_name=str(job.get("name") or "unnamed-job");conclusion=str(job.get("conclusion") or "").lower()
        if conclusion in {"success","failure"}:rows.append({"source_sha":source,"gate_id":"workflow_job","test_id":job_name,"environment_fingerprint":env_fingerprint,"result":"PASS" if conclusion=="success" else "FAIL","workflow_run_id":run_id})
        for step in job.get("steps",[]) or []:
            if not isinstance(step,dict):continue
            conclusion=str(step.get("conclusion") or "").lower();name=str(step.get("name") or "unnamed-step")
            if conclusion not in {"success","failure"} or name in {"Set up job","Complete job"} or name.startswith("Post Run "):continue
            rows.append({"source_sha":source,"gate_id":job_name,"test_id":name,"environment_fingerprint":env_fingerprint,"result":"PASS" if conclusion=="success" else "FAIL","workflow_run_id":run_id})
    return rows
def _runtime_dependency_traces(artifact_root:str|Path|None,source:str)->tuple[list[dict],list[str]]:
    if not artifact_root:return [],[]
    root=Path(artifact_root)
    if not root.exists():return [],[]
    rows=[];errors=[]
    for path in sorted(root.rglob("runtime-dependency-trace.json")):
        try:value=json.loads(path.read_text())
        except Exception as exc:errors.append(f"{path}: invalid JSON: {exc}");continue
        if not isinstance(value,dict):errors.append(f"{path}: trace must be object");continue
        if value.get("source_sha")!=source:errors.append(f"{path}: trace source does not match observed run");continue
        checked=validate_trace(value)
        if not checked.get("passed"):errors.extend(f"{path}: {e}" for e in checked.get("errors",[]));continue
        rows.append({"source_file":str(path),"trace":value,"validation":checked})
    return rows,errors

def observe(run:dict,jobs_doc:dict,artifacts:dict|None=None,task:str|None=None,provenance:dict|None=None,artifact_root:str|Path|None=None,proof_cache_hits:int=0,c0_cycles:int=0)->dict:
    jobs=_jobs_list(jobs_doc);artifacts=artifacts or {};source=str(run.get("head_sha") or "");run_id=run.get("id");resolved_task=_infer_task(run,task)
    provenance=provenance or _find_runtime_provenance(artifact_root);env_fingerprint=_canonical_fingerprint(provenance) if not provenance.get("ambiguous") else None
    terminal_gate,terminal_class=_terminal_from_jobs(jobs,run);queue_seconds=_seconds(run.get("created_at"),run.get("run_started_at"));run_seconds=_run_duration(run,jobs)
    telemetry={"workflow_run_id":run_id,"workflow_name":run.get("name"),"source_sha":source,"task_id":resolved_task,"environment_fingerprint":env_fingerprint,"queue_seconds":0.0 if queue_seconds is None else queue_seconds,"run_seconds":0.0 if run_seconds is None else run_seconds,"gate_durations":_gate_durations(jobs),"rerun_count":max(0,int(run.get("run_attempt") or 1)-1),"c0_cycles":max(0,int(c0_cycles)),"proof_cache_hits":max(0,int(proof_cache_hits)),"artifact_bytes":_artifact_bytes(artifacts),"terminal_gate":terminal_gate,"terminal_class":terminal_class}
    required=set(load_json(TELEMETRY_POLICY).get("required_metrics",[]));telemetry_missing=sorted(required-set(telemetry));flakes=_flake_observations(source,jobs,env_fingerprint,run_id)
    task_state=None;task_state_validation=None
    if resolved_task and resolved_task in load_json(DOCS/"DEPENDENCY_GRAPH.json").get("tasks",{}):
        task_state=snapshot(resolved_task,last_gate=terminal_gate,candidate=source if re.fullmatch(r"[0-9a-f]{40}",source) else None);task_state_validation=validate_snapshot(task_state)
    traces,trace_errors=_runtime_dependency_traces(artifact_root,source);errors=[]
    if telemetry_missing:errors.append("telemetry missing required fields: "+", ".join(telemetry_missing))
    if task_state_validation and not task_state_validation.get("passed"):errors.extend("task-state: "+e for e in task_state_validation.get("errors",[]))
    errors.extend("runtime-dependency-trace: "+e for e in trace_errors)
    return {"schema_version":1,"passed":not errors,"workflow_run_id":run_id,"source_sha":source,"task_id":resolved_task,"environment_provenance":provenance,"environment_fingerprint":env_fingerprint,"environment_exact":env_fingerprint is not None,"telemetry":telemetry,"flake_observations":flakes,"flake_observations_suppressed":env_fingerprint is None,"runtime_dependency_traces":traces,"task_state":task_state,"task_state_validation":task_state_validation,"bundle_is_observation_not_authority":True,"quality_thresholds_unchanged":True,"errors":errors}
def write_bundle(bundle:dict,output_dir:str|Path)->None:
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True);(out/"factory-observation.json").write_text(json.dumps(bundle,indent=2)+"\n");(out/"pipeline-telemetry-record.json").write_text(json.dumps(bundle["telemetry"],indent=2)+"\n");(out/"flake-observations.json").write_text(json.dumps({"schema_version":1,"observations":bundle["flake_observations"]},indent=2)+"\n")
    if bundle.get("task_state") is not None:(out/"task-state.json").write_text(json.dumps(bundle["task_state"],indent=2)+"\n")
    if bundle.get("runtime_dependency_traces"):(out/"runtime-dependency-traces.json").write_text(json.dumps({"schema_version":1,"traces":bundle["runtime_dependency_traces"]},indent=2)+"\n")
def main()->int:
    parser=argparse.ArgumentParser(description="Build a deterministic Havenline V3.1 factory observation bundle from GitHub run/job/artifact records");parser.add_argument("--run",required=True);parser.add_argument("--jobs",required=True);parser.add_argument("--artifacts");parser.add_argument("--task");parser.add_argument("--provenance");parser.add_argument("--artifact-root");parser.add_argument("--proof-cache-hits",type=int,default=0);parser.add_argument("--c0-cycles",type=int,default=0);parser.add_argument("--output-dir",required=True);args=parser.parse_args()
    bundle=observe(_load(args.run),_load(args.jobs),_load(args.artifacts),task=args.task,provenance=_load(args.provenance) if args.provenance else None,artifact_root=args.artifact_root,proof_cache_hits=args.proof_cache_hits,c0_cycles=args.c0_cycles);write_bundle(bundle,args.output_dir);print(json.dumps(bundle,indent=2));return 0 if bundle["passed"] else 2
if __name__=="__main__":raise SystemExit(main())
