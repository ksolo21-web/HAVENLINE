#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, re, subprocess, sys
from lib import ROOT, DOCS, load_json, git, any_match, ensure_score_strictly_above_nine
from workstream import registry_errors

EXPECTED_TOOLS={
"task_packet.py","workstream.py","change_impact.py","regression_runner.py","evidence_capture.py",
"motion_capture.py","save_state_matrix.py","device_matrix.py","evidence_packager.py",
"closure_validator.py","critic_harness.py","validate_migration.py","validate_repair_cycle.py","lib.py"
}
ALLOWED_MIGRATION_PATTERNS=[
"Docs/Production/**","tools/havenline/production/**","AGENTS.md",
".github/workflows/havenline-production-governance.yml",".github/workflows/havenline-candidate-guard.yml",".github/workflows/havenline-apply-governance-v2.yml",
"HavenlineGodot/tests/production_capture_harness.gd","HavenlineGodot/tests/production_motion_capture.gd"
]

T05_ACCEPTED_SOURCE="fa6fa70f154f3757d22303522ca3f6de2c3d391f"

def _strict_score_errors(label,scores):
    errors=[]
    if not isinstance(scores,dict) or not scores:
        return [f"{label} scores missing"]
    for dimension,value in scores.items():
        if isinstance(value,bool) or not isinstance(value,(int,float)) or value<=9.0:
            errors.append(f"{label} score must be strictly above 9.0: {dimension}={value}")
    return errors

def t05_completion_errors(record,ledger):
    """Fail closed on the complete, exact-source T05 approval contract."""
    errors=[]
    if record.get("status")!="PASS" or record.get("accepted_gameplay_source")!=T05_ACCEPTED_SOURCE:
        errors.append("T05 verified completion record is not bound to the accepted source")
    acceptance=record.get("acceptance_rule",{})
    if acceptance.get("mandatory_dimension_operator")!=">" or acceptance.get("mandatory_dimension_threshold")!=9.0 or acceptance.get("unrounded") is not True or acceptance.get("score_averaging_used") is not False:
        errors.append("T05 verified completion strict acceptance rule is incomplete")
    mechanical=record.get("mechanical_evidence",{})
    if mechanical.get("all_passed") is not True or mechanical.get("functional_suites")!=18 or mechanical.get("total_assertions_checks",0)<1119 or mechanical.get("source_bound_images",0)<77:
        errors.append("T05 mechanical or integration regression evidence is incomplete")
    visual=record.get("visual_review",{})
    if visual.get("passed") is not True or visual.get("status") not in {"PASS","PASS_BY_QUORUM"} or visual.get("source")!=T05_ACCEPTED_SOURCE or visual.get("score_averaging_used") is not False or visual.get("valid_unresolved_defects")!=[]:
        errors.append("T05 C1/C2 visual closure is incomplete")
    for critic,scores in visual.get("scores",{}).items():
        errors += _strict_score_errors(f"T05 {critic}",scores)
    if set(visual.get("scores",{}))!={"C1","C2"}:
        errors.append("T05 C1/C2 score sets are incomplete")
    performance=record.get("performance_critic",{})
    if performance.get("critic")!="C6" or performance.get("passed") is not True or performance.get("coverage_complete") is not True or performance.get("candidate_source")!=T05_ACCEPTED_SOURCE or performance.get("defects")!=[]:
        errors.append("T05 C6 closure is incomplete")
    errors += _strict_score_errors("T05 C6",performance.get("scores"))
    final_gate=record.get("final_gate",{})
    if final_gate.get("passed") is not True or final_gate.get("source")!=T05_ACCEPTED_SOURCE or final_gate.get("ready_for_final_pixel_signoff") is not True or final_gate.get("errors")!=[]:
        errors.append("T05 final machine gate is incomplete")
    signoff=record.get("pixel_signoff",{})
    if signoff.get("performed_against_accepted_gameplay_source") is not True or signoff.get("unresolved_mandatory_task_defects")!=[]:
        errors.append("T05 final pixel signoff is incomplete")
    if ledger.get("task_id")!="T05" or ledger.get("candidate_commit")!=T05_ACCEPTED_SOURCE:
        errors.append("T05 defect ledger is not bound to the accepted source")
    allowed={"VERIFIED_CLOSED","REJECTED_AS_INVALID_FINDING"}
    unresolved=[row.get("id") for row in ledger.get("defects",[]) if row.get("status") not in allowed]
    if unresolved:
        errors.append("T05 defect ledger has unresolved entries: "+",".join(str(x) for x in unresolved))
    return errors

def git_blob_sha(path:pathlib.Path)->str:
    data=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--base");a=ap.parse_args()
    errors=[]
    required=[
      "HAVENLINE_BUILD_PLAN_V2.md","ANTI_LOOP_ROOT_CAUSE_STANDARD.md","SEQUENTIAL_REPAIR_PLAN.md","DEPENDENCY_GRAPH.json",
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
    t03_status=graph["tasks"]["T03"]["status"]
    t04_status=graph["tasks"]["T04"]["status"]
    t05_status=graph["tasks"]["T05"]["status"]
    if t03_status not in {"FIX_REQUIRED","APPROVED"}:errors.append("T03 must be FIX_REQUIRED or APPROVED")
    if t03_status=="FIX_REQUIRED":
        if any(graph["tasks"][t]["status"]!="LOCKED" for t in ids[3:]):errors.append("T04+ must remain LOCKED until T03 approval")
    else:
        if t04_status not in {"LOCKED","PREPARED","ASSIGNED","BUILDING_ISOLATED","INTEGRATION_READY","INTEGRATING","UNDER_REVIEW","FIX_REQUIRED","APPROVED","BLOCKED"}:
            errors.append("invalid T04 post-T03 state")
        if t04_status!="APPROVED":
            if any(graph["tasks"][t]["status"]!="LOCKED" for t in ids[4:]):errors.append("T05+ must remain LOCKED until T04 is approved and T05 is separately prepared")
        else:
            if t05_status not in {"LOCKED","PREPARED","ASSIGNED","BUILDING_ISOLATED","INTEGRATION_READY","INTEGRATING","UNDER_REVIEW","FIX_REQUIRED","APPROVED","BLOCKED"}:
                errors.append("invalid T05 post-T04 state")
            if any(graph["tasks"][t]["status"]!="LOCKED" for t in ids[5:]):errors.append("T06+ must remain LOCKED until separately prepared")
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
    if t03_status=="APPROVED":
        expected_approved=(
            ["T01","T02","T03","T04","T05"] if t05_status=="APPROVED" else
            ["T01","T02","T03","T04"] if t04_status=="APPROVED" else
            ["T01","T02","T03"]
        )
        if tg.get("approved_tasks")!=expected_approved:errors.append("task-gates approved list does not match T04 state")
        completion=DOCS/"T03/verified-completion.json"
        if not completion.exists():errors.append("T03 verified completion record missing")
        else:
            record=load_json(completion)
            if record.get("status")!="PASS" or record.get("accepted_gameplay_source")!="5df9726e0b1c33f0f8865385b1c49aca229fd461":
                errors.append("T03 verified completion record is not bound to the accepted source")
            if record.get("visual_review",{}).get("status")!="PASS_BY_QUORUM" or record.get("performance_critic",{}).get("passed") is not True:
                errors.append("T03 verified completion gates are incomplete")
        if t04_status=="LOCKED":
            if tg.get("active_task") is not None or tg.get("active_status") is not None:errors.append("task-gates must have no active task while T04 is locked")
        elif t04_status=="APPROVED":
            t04_completion=DOCS/"T04/verified-completion.json"
            if not t04_completion.exists():errors.append("T04 verified completion record missing")
            else:
                record=load_json(t04_completion)
                if record.get("status")!="PASS" or record.get("accepted_gameplay_source")!="e08fd37e9a999d878644c03089c4b4b253bd7472":
                    errors.append("T04 verified completion record is not bound to the accepted source")
                if record.get("visual_review",{}).get("status")!="PASS_BY_CORROBORATED_EVIDENCE" or record.get("performance_critic",{}).get("passed") is not True:
                    errors.append("T04 verified completion gates are incomplete")
                if record.get("pixel_signoff",{}).get("unresolved_mandatory_task_defects")!=[]:
                    errors.append("T04 final pixel signoff is incomplete")
            if t05_status=="LOCKED":
                if tg.get("active_task") is not None or tg.get("active_status") is not None:errors.append("task-gates must clear active task while T05 is locked")
            elif t05_status=="APPROVED":
                if tg.get("active_task") is not None or tg.get("active_status") is not None:errors.append("task-gates must clear active task after T05 approval")
                t05_completion=DOCS/"T05/verified-completion.json"
                t05_ledger=DOCS/"T05/DEFECT_LEDGER.json"
                if not t05_completion.exists() or not t05_ledger.exists():
                    errors.append("T05 verified completion record or defect ledger missing")
                else:
                    errors += t05_completion_errors(load_json(t05_completion),load_json(t05_ledger))
            else:
                if tg.get("active_task")!="T05" or tg.get("active_status")!=t05_status:errors.append("task-gates must match active T05 state")
                packet=DOCS/"T05/TASK_PACKET.md";scope=DOCS/"T05/FROZEN_SCOPE.md"
                if not packet.exists() or not scope.exists():errors.append("active T05 packet/frozen scope missing")
        else:
            if tg.get("active_task")!="T04" or tg.get("active_status")!=t04_status:errors.append("task-gates must match active T04 state")
            packet=DOCS/"T04/TASK_PACKET.md";scope=DOCS/"T04/FROZEN_SCOPE.md"
            if not packet.exists() or not scope.exists():errors.append("active T04 packet/frozen scope missing")
    else:
        if tg.get("active_task")!="T03" or tg.get("active_status")!="FIX_REQUIRED":errors.append("task-gates current T03 state not recovered")
        if tg.get("approved_tasks")!=["T01","T02"]:errors.append("task-gates approvals changed")
    result={"passed":not errors,"errors":errors,"checked_tasks":70,"checked_critics":11,"migration_base":a.base}
    print(json.dumps(result,indent=2))
    if errors:raise SystemExit(1)
if __name__=="__main__":main()
