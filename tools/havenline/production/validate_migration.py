#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, re, subprocess, sys
from lib import ROOT, DOCS, load_json, git, any_match, ensure_score_strictly_above_nine
from workstream import registry_errors

EXPECTED_TOOLS={
"task_packet.py","workstream.py","change_impact.py","regression_runner.py","evidence_capture.py",
"motion_capture.py","save_state_matrix.py","device_matrix.py","evidence_packager.py",
"closure_validator.py","critic_harness.py","validate_migration.py","lib.py"
}
ALLOWED_MIGRATION_PATTERNS=[
"Docs/Production/**","tools/havenline/production/**","AGENTS.md",
".github/workflows/havenline-production-governance.yml",".github/workflows/havenline-candidate-guard.yml",".github/workflows/havenline-apply-governance-v2.yml",
"HavenlineGodot/tests/production_capture_harness.gd","HavenlineGodot/tests/production_motion_capture.gd"
]

def git_blob_sha(path:pathlib.Path)->str:
    data=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--base");a=ap.parse_args()
    errors=[]
    required=[
      "HAVENLINE_BUILD_PLAN_V2.md","SEQUENTIAL_REPAIR_PLAN.md","DEPENDENCY_GRAPH.json",
      "WORKSTREAM_REGISTRY.json","PATH_OWNERSHIP.json","CRITIC_MATRIX.json",
      "PERFORMANCE_BUDGETS.json","TASK_PACKET_TEMPLATE.md","REGRESSION_MATRIX.json",
      "DEVICE_LAYOUT_MATRIX.json","SAVE_STATE_MATRIX.json","task-gates.json"
    ]
    for name in required:
        if not (DOCS/name).exists():errors.append("missing "+name)
    arc=DOCS/"Archive/SEQUENTIAL_REPAIR_PLAN.pre-v2.2026-09-11.md"
    prov=DOCS/"Archive/SEQUENTIAL_REPAIR_PLAN.pre-v2.2026-09-11.provenance.json"
    if not arc.exists() or not prov.exists():errors.append("archived pre-v2 plan/provenance missing")
    else:
        p=json.loads(prov.read_text())
        if git_blob_sha(arc)!=p.get("source_git_blob_sha1") or p.get("byte_identical") is not True:
            errors.append("archived plan is not byte-identical to recorded source blob")
    graph=load_json(DOCS/"DEPENDENCY_GRAPH.json")
    ids=[f"T{i:02d}" for i in range(1,71)]
    if list(graph["tasks"])!=ids:errors.append("dependency graph must contain ordered T01-T70 exactly")
    # DAG and references
    visiting=set();done=set()
    def visit(t):
        if t in done:return
        if t in visiting:errors.append("dependency cycle at "+t);return
        visiting.add(t)
        for d in graph["tasks"][t]["dependencies"]:
            if d not in graph["tasks"]:errors.append(f"{t} unknown dependency {d}")
            else:visit(d)
        visiting.remove(t);done.add(t)
    for t in ids:visit(t)
    if graph["tasks"]["T01"]["status"]!="APPROVED" or graph["tasks"]["T02"]["status"]!="APPROVED":errors.append("T01/T02 approval lost")
    if graph["tasks"]["T03"]["status"]!="FIX_REQUIRED":errors.append("T03 recovered state must be FIX_REQUIRED")
    if any(graph["tasks"][t]["status"]!="LOCKED" for t in ids[3:]):errors.append("T04+ must remain LOCKED during migration")
    acc=graph["acceptance_rule"]
    if acc.get("mandatory_dimension_operator")!=">" or acc.get("mandatory_dimension_threshold")!=9.0 or acc.get("unrounded") is not True:
        errors.append("forward strict >9.0 rule missing")
    if ensure_score_strictly_above_nine({"must_fail":9.0})==[]:errors.append("strict score helper incorrectly accepts 9.0")
    errors += registry_errors()
    critics=load_json(DOCS/"CRITIC_MATRIX.json")
    if set(critics["critics"])!={f"C{i}" for i in range(1,12)}:errors.append("C1-C11 definitions incomplete")
    if set(critics["task_applicability"])!=set(ids):errors.append("critic applicability not mapped for all 70 tasks")
    if critics["task_applicability"]["T03"]!=["C1","C2","C6"]:errors.append("T03 V2 critics must be C1+C2+C6")
    budgets=load_json(DOCS/"PERFORMANCE_BUDGETS.json")
    needed={"visible_triangles","draw_calls","materials_visible","texture_gpu_memory_mb","cpu_frame_ms","gpu_frame_ms_where_measurable","physics_active_bodies","animated_rigs_active","npc_companion_active_population","process_memory_mb","storage_download_mb"}
    if not needed.issubset(budgets["global_soft_budgets"]):errors.append("performance budgets incomplete")
    tools=ROOT/"tools/havenline/production"
    missing=EXPECTED_TOOLS-{p.name for p in tools.glob("*.py")}
    if missing:errors.append("missing production tools: "+",".join(sorted(missing)))
    for p in [ROOT/"HavenlineGodot/tests/production_capture_harness.gd",ROOT/"HavenlineGodot/tests/production_motion_capture.gd"]:
        if not p.exists():errors.append("missing QA harness "+str(p.relative_to(ROOT)))
    # Ensure migration itself did not modify unrelated runtime.
    if a.base:
        changed=[x for x in git("diff","--name-only",f"{a.base}..HEAD").splitlines() if x]
        bad=[x for x in changed if not any_match(x,ALLOWED_MIGRATION_PATTERNS)]
        if bad:errors.append("migration changed unauthorized runtime paths: "+",".join(bad))
    plan=(DOCS/"HAVENLINE_BUILD_PLAN_V2.md").read_text()
    for t in ids:
        if f"| {t} |" not in plan:errors.append("build plan missing "+t)
    tg=load_json(DOCS/"task-gates.json")
    if tg.get("active_task")!="T03" or tg.get("active_status")!="FIX_REQUIRED":errors.append("task-gates current T03 state not recovered")
    if tg.get("approved_tasks")!=["T01","T02"]:errors.append("task-gates approvals changed")
    result={"passed":not errors,"errors":errors,"checked_tasks":70,"checked_critics":11,"migration_base":a.base}
    print(json.dumps(result,indent=2))
    if errors:raise SystemExit(1)
if __name__=="__main__":main()
