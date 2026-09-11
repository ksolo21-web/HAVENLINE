#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime, json, pathlib, subprocess, tempfile
from lib import ROOT, DOCS, load_json, ensure_score_strictly_above_nine, sha256_file

def validate_raw(path:pathlib.Path, critic_id:str, candidate:str):
    cfg=load_json(DOCS/"CRITIC_MATRIX.json")
    required=set(cfg["critics"])
    if critic_id not in required: raise SystemExit(f"unknown critic {critic_id}")
    d=json.loads(path.read_text())
    errors=[]
    for k in ("critic_id","provider","model","request_or_run_id","candidate_hash","input_manifest_hash","raw_output_path","raw_output_hash","scores","defects","coverage_complete","confidence"):
        if k not in d: errors.append("missing "+k)
    if d.get("critic_id")!=critic_id: errors.append("critic id mismatch")
    if d.get("candidate_hash")!=candidate: errors.append("candidate hash mismatch")
    errors += ensure_score_strictly_above_nine(d.get("scores",{}))
    if d.get("defects"): errors.append("unresolved defects present")
    if d.get("coverage_complete") is not True: errors.append("coverage incomplete")
    if d.get("confidence") not in ("medium","high"): errors.append("confidence insufficient")
    if cfg["critics"][critic_id].get("independent_model_required") and not d.get("independent_runtime",False):
        errors.append("required independent runtime not proven")
    return {"critic_id":critic_id,"candidate":candidate,"passed":not errors,"errors":errors,"record":d}

def c6(performance_path:pathlib.Path,candidate:str):
    budgets=load_json(DOCS/"PERFORMANCE_BUDGETS.json")
    perf=json.loads(performance_path.read_text())
    errors=[]
    if perf.get("candidate_commit")!=candidate: errors.append("candidate mismatch")
    soft=budgets["global_soft_budgets"]
    checks={
      "visible_triangles":soft["visible_triangles"],"draw_calls":soft["draw_calls"],
      "materials_visible":soft["materials_visible"],"texture_gpu_memory_mb":soft["texture_gpu_memory_mb"],
      "process_memory_mb":soft["process_memory_mb"],"physics_active_bodies":soft["physics_active_bodies"],
      "animated_rigs_active":soft["animated_rigs_active"],"npc_companion_active_population":soft["npc_companion_active_population"],
      "storage_download_mb":soft["storage_download_mb"]
    }
    for key,limit in checks.items():
        value=perf.get(key)
        if value is None:
            errors.append(f"missing metric {key}")
        elif value>limit:
            errors.append(f"{key} {value} exceeds {limit}")
    for key,limit in (("cpu_frame_ms",soft["cpu_frame_ms"]),("gpu_frame_ms_where_measurable",soft["gpu_frame_ms_where_measurable"])):
        value=perf.get(key)
        if value is not None and value>limit: errors.append(f"{key} {value} exceeds {limit}")
    return {"critic_id":"C6","candidate":candidate,"passed":not errors,"errors":errors,"measurement":perf,"note":"Quantitative specialist gate; not T68/T69 certification."}

def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd",required=True)
    v=sub.add_parser("validate-raw");v.add_argument("--critic",required=True);v.add_argument("--candidate",required=True);v.add_argument("--raw",required=True)
    p=sub.add_parser("performance");p.add_argument("--candidate",required=True);p.add_argument("--record",required=True)
    a=ap.parse_args()
    result=validate_raw(pathlib.Path(a.raw),a.critic,a.candidate) if a.cmd=="validate-raw" else c6(pathlib.Path(a.record),a.candidate)
    print(json.dumps(result,indent=2))
    if not result["passed"]: raise SystemExit(1)

if __name__=="__main__": main()
