#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, re, subprocess, sys
from datetime import datetime,timezone
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
T06_ACCEPTED_SOURCE="47f86fae25b099abb5c7096c37ca7495453b2b8f"
T06_INTEGRATED_SOURCE="91f35f331aaabe2b1785b10c0d911f20da6f12d9"
T07_ACCEPTED_SOURCE="0a30dc0859541626eb6aa9a9bb749abc93dcb355"
T07_INTEGRATED_SOURCE="94b3f6c5097356a3857ebd13a77fb1e316eb06ae"
T07_INTEGRATED_RUN=34991148246
T07_ARTIFACT_ID=10405978547
T07_ARTIFACT_DIGEST="sha256:c243bb1df0625a7fabce9c6a842d88a76e08bca89d416f88ad0ea0a972ec0ada"
T08_INTEGRATED_SOURCE="9d56ea8ae972d0a0705ff8b985e13fab31dde493"
T08_INTEGRATED_RUN=35035980827
T08_ARTIFACT_ID=10423956033
T09_OWNER="harvesting-acquisition-builder"
T09_BRANCH="havenline/T09-harvesting"
T09_BASE="7492074e40a0b061f31d8c32602b7a581b2610f3"
T09_ALIAS="@reservation:T09"
T09_WORKSTREAM="T09-harvesting-acquisition-builder"
T08_ARTIFACT_DIGEST="sha256:d2e58a9b4736e690b3b9817536b90940fb605e25b47a3ae24146aa8f9440c5c7"
T08_EVIDENCE_INDEX_SHA256="17f27e449466524f9838cc592d4f637738f8e4cafd9475f1dc25bc7c2ca72c16"
T05_SCORE_DIMENSIONS={
    "C1":{"reference_fidelity","visual_language","cross_view_consistency"},
    "C2":{"geometry_contact","clipping_seams","intentional_gap_integrity","cross_view_integrity"},
    "C6":{"frame_time","draw_calls","geometry","texture_memory","shader_cost","physics","animation","population","thermal_risk"},
}

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
    else:
        for critic in ("C1","C2"):
            if set(visual["scores"][critic])!=T05_SCORE_DIMENSIONS[critic]:
                errors.append(f"T05 {critic} mandatory dimensions are incomplete")
    performance=record.get("performance_critic",{})
    if performance.get("critic")!="C6" or performance.get("passed") is not True or performance.get("coverage_complete") is not True or performance.get("candidate_source")!=T05_ACCEPTED_SOURCE or performance.get("defects")!=[]:
        errors.append("T05 C6 closure is incomplete")
    errors += _strict_score_errors("T05 C6",performance.get("scores"))
    if set(performance.get("scores",{}))!=T05_SCORE_DIMENSIONS["C6"]:
        errors.append("T05 C6 mandatory dimensions are incomplete")
    final_gate=record.get("final_gate",{})
    if final_gate.get("passed") is not True or final_gate.get("source")!=T05_ACCEPTED_SOURCE or final_gate.get("ready_for_final_pixel_signoff") is not True or final_gate.get("errors")!=[]:
        errors.append("T05 final machine gate is incomplete")
    signoff=record.get("pixel_signoff",{})
    if signoff.get("performed_against_accepted_gameplay_source") is not True or signoff.get("unresolved_mandatory_task_defects")!=[]:
        errors.append("T05 final pixel signoff is incomplete")
    gates=record.get("gates",{})
    if set(gates)!={f"G{i}" for i in range(1,15)} or any(value is not True for value in gates.values()):
        errors.append("T05 G1-G14 closure is incomplete")
    artifacts=record.get("artifacts",{})
    required_artifacts={"integrated_precritic","visual_resolution","C6","final_gate"}
    digest_pattern=re.compile(r"^sha256:[0-9a-f]{64}$")
    if set(artifacts)<required_artifacts:
        errors.append("T05 required artifact identities are incomplete")
    else:
        for name in required_artifacts:
            artifact=artifacts[name]
            if not isinstance(artifact.get("id"),int) or artifact["id"]<=0 or not digest_pattern.fullmatch(str(artifact.get("digest",""))):
                errors.append(f"T05 {name} artifact identity is invalid")
    if ledger.get("task_id")!="T05" or ledger.get("candidate_commit")!=T05_ACCEPTED_SOURCE:
        errors.append("T05 defect ledger is not bound to the accepted source")
    allowed={"VERIFIED_CLOSED","REJECTED_AS_INVALID_FINDING"}
    unresolved=[row.get("id") for row in ledger.get("defects",[]) if row.get("status") not in allowed]
    if unresolved:
        errors.append("T05 defect ledger has unresolved entries: "+",".join(str(x) for x in unresolved))
    return errors

def t06_completion_errors(record,ledger):
    """Fail closed on T06 exact-source integration, critic and defect closure."""
    errors=[]
    if record.get("status")!="PASS" or record.get("accepted_gameplay_source")!=T06_ACCEPTED_SOURCE or record.get("integrated_source")!=T06_INTEGRATED_SOURCE:
        errors.append("T06 verified completion record is not bound to accepted and integrated sources")
    acceptance=record.get("acceptance_rule",{})
    if acceptance.get("mandatory_dimension_operator")!=">" or acceptance.get("mandatory_dimension_threshold")!=9.0 or acceptance.get("unrounded") is not True or acceptance.get("score_averaging_used") is not False:
        errors.append("T06 verified completion strict acceptance rule is incomplete")
    identity=record.get("source_identity",{})
    if identity.get("immutable_character1_glb_sha256")!="95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099" or identity.get("runtime_review_glb_sha256")!="739a7abf669194ac656ce9f05b864a3e5c4cd666b64a84f1db045de5e7982738" or identity.get("reviewed_source_is_integrated_ancestor") is not True or identity.get("reviewed_runtime_and_gate_files_byte_identical") is not True or identity.get("shipping_main_call_site_exercised") is not True:
        errors.append("T06 exact-source or shipping integration identity is incomplete")
    mechanical=record.get("mechanical_evidence",{})
    if mechanical.get("all_passed") is not True or mechanical.get("functional_suites")!=19 or mechanical.get("total_assertions_checks",0)<1345 or mechanical.get("surface_violations")!=0 or mechanical.get("coverage_nonpass_rows")!=0 or mechanical.get("task_images",0)<970 or mechanical.get("continuous_motion_videos",0)<76:
        errors.append("T06 mechanical, surface, coverage or integration evidence is incomplete")
    reviews=record.get("independent_reviews",{})
    if reviews.get("status")!="PASS" or reviews.get("source")!=T06_ACCEPTED_SOURCE or reviews.get("integrated_source")!=T06_INTEGRATED_SOURCE or reviews.get("score_averaging_used") is not False or reviews.get("critic_blockers")!=[] or reviews.get("valid_unresolved_defects")!=[]:
        errors.append("T06 independent critic closure is incomplete")
    scores=reviews.get("scores",{})
    if set(scores)!={"C1","C2","C5"}:
        errors.append("T06 C1/C2/C5 score set is incomplete")
    else:
        errors += _strict_score_errors("T06 critics",scores)
    performance=record.get("performance_critic",{})
    if performance.get("critic")!="C6" or performance.get("candidate_source")!=T06_INTEGRATED_SOURCE or performance.get("run_id")!=34970154124 or performance.get("passed") is not True or performance.get("errors")!=[]:
        errors.append("T06 fresh integrated C6 closure is incomplete")
    gates=record.get("gates",{})
    if set(gates)!={f"G{i}" for i in range(1,15)} or any(value is not True for value in gates.values()):
        errors.append("T06 G1-G14 closure is incomplete")
    artifact=record.get("artifacts",{}).get("integrated_regression_and_evidence",{})
    if artifact.get("id")!=10397129519 or artifact.get("run_id")!=34970154124 or artifact.get("digest")!="sha256:751a23d978ffc9f5e18754a0830c6c79f766dcf49e1a5501dc1464574245ae13":
        errors.append("T06 integrated artifact identity is invalid")
    if ledger.get("task_id")!="T06" or ledger.get("candidate_commit")!=T06_ACCEPTED_SOURCE or ledger.get("integrated_commit")!=T06_INTEGRATED_SOURCE:
        errors.append("T06 defect ledger is not bound to accepted and integrated sources")
    allowed={"VERIFIED_CLOSED","REJECTED_AS_INVALID_FINDING"}
    unresolved=[row.get("id") for row in ledger.get("defects",[]) if row.get("status") not in allowed]
    if unresolved:
        errors.append("T06 defect ledger has unresolved entries: "+",".join(str(x) for x in unresolved))
    return errors

def t07_completion_errors(record,ledger,critic_review):
    """Fail closed on T07 exact integrated evidence and independent review."""
    errors=[]
    if record.get("status")!="PASS" or record.get("accepted_isolated_source")!=T07_ACCEPTED_SOURCE or record.get("integrated_source")!=T07_INTEGRATED_SOURCE:
        errors.append("T07 verified completion record is not bound to accepted and integrated sources")
    acceptance=record.get("acceptance_rule",{})
    if acceptance.get("mandatory_dimension_operator")!=">" or acceptance.get("mandatory_dimension_threshold")!=9.0 or acceptance.get("unrounded") is not True or acceptance.get("score_averaging_used") is not False:
        errors.append("T07 verified completion strict acceptance rule is incomplete")
    identity=record.get("source_identity",{})
    if identity.get("shipping_call_site_exercised") is not True or identity.get("simulation_remains_outcome_authority") is not True or identity.get("choose_action_is_pure_preview") is not True or identity.get("context_focus_is_ephemeral") is not True or identity.get("save_schema_changed") is not False or identity.get("exact_artifact_index_hashes_verified")!=156 or identity.get("exact_artifact_index_hash_mismatches")!=0:
        errors.append("T07 source, authority, persistence or evidence identity is incomplete")
    mechanical=record.get("mechanical_evidence",{})
    if mechanical.get("all_passed") is not True or mechanical.get("functional_suites")!=21 or mechanical.get("total_assertions_checks",0)<1441 or mechanical.get("save_matrix_cases")!=7 or mechanical.get("adaptive_device_cases")!=6 or mechanical.get("capture_manifests")!=14 or mechanical.get("unique_pngs")!=19 or mechanical.get("sequence_video_frames")!=60 or mechanical.get("render_log_errors")!=0 or mechanical.get("native_3840x2160_scale1_evidence") is not True:
        errors.append("T07 regression, matrix, capture or native evidence is incomplete")
    reviews=record.get("independent_reviews",{})
    scores=reviews.get("scores",{})
    if reviews.get("status")!="PASS" or reviews.get("integrated_source")!=T07_INTEGRATED_SOURCE or reviews.get("workflow_run")!=T07_INTEGRATED_RUN or reviews.get("artifact_id")!=T07_ARTIFACT_ID or reviews.get("artifact_digest")!=T07_ARTIFACT_DIGEST or reviews.get("score_averaging_used") is not False or reviews.get("critic_blockers")!=[] or reviews.get("valid_unresolved_defects")!=[] or set(scores)!={"C2","C3","C4","C6","C11"}:
        errors.append("T07 independent critic closure is incomplete")
    else:
        errors += _strict_score_errors("T07 critics",scores)
    performance=record.get("performance_critic",{})
    if performance.get("critic")!="C6" or performance.get("candidate_source")!=T07_INTEGRATED_SOURCE or performance.get("run_id")!=T07_INTEGRATED_RUN or performance.get("score")!=9.53 or performance.get("passed") is not True or performance.get("errors")!=[]:
        errors.append("T07 fresh integrated C6 closure is incomplete")
    gates=record.get("gates",{})
    if set(gates)!={f"G{i}" for i in range(1,15)} or any(value is not True for value in gates.values()):
        errors.append("T07 G1-G14 closure is incomplete")
    artifact=record.get("artifacts",{}).get("integrated_regression_and_evidence",{})
    if artifact.get("id")!=T07_ARTIFACT_ID or artifact.get("run_id")!=T07_INTEGRATED_RUN or artifact.get("digest")!=T07_ARTIFACT_DIGEST:
        errors.append("T07 integrated artifact identity is invalid")
    if ledger.get("task_id")!="T07" or ledger.get("candidate_commit")!=T07_ACCEPTED_SOURCE or ledger.get("integrated_commit")!=T07_INTEGRATED_SOURCE or ledger.get("integrated_verification_run")!=T07_INTEGRATED_RUN or ledger.get("unresolved_mandatory_count")!=0 or ledger.get("critic_approval_pending") is not False or ledger.get("task_approved") is not True:
        errors.append("T07 defect ledger is not bound to completed sources")
    unresolved=[row.get("id") for row in ledger.get("defects",[]) if row.get("status") not in {"VERIFIED_CLOSED","REJECTED_AS_INVALID_FINDING"}]
    if unresolved:
        errors.append("T07 defect ledger has unresolved entries: "+",".join(str(x) for x in unresolved))
    review_scores=critic_review.get("scores",{})
    if critic_review.get("status")!="PASS" or critic_review.get("approval") is not True or critic_review.get("integrated_source")!=T07_INTEGRATED_SOURCE or critic_review.get("workflow_run")!=T07_INTEGRATED_RUN or critic_review.get("artifact_id")!=T07_ARTIFACT_ID or critic_review.get("artifact_digest")!=T07_ARTIFACT_DIGEST or critic_review.get("indexed_files_verified")!=156 or critic_review.get("indexed_hash_mismatches")!=0 or critic_review.get("unresolved_mandatory_defects")!=[] or set(review_scores)!={"C2","C3","C4","C6","C11"}:
        errors.append("T07 independent critic record is incomplete")
    else:
        errors += _strict_score_errors("T07 recorded critics",review_scores)
    return errors

def t08_completion_errors(record,ledger,critic_review):
    """Fail closed on T08 exact integrated evidence and complete-reference review."""
    errors=[]
    if record.get("status")!="PASS" or record.get("accepted_source")!=T08_INTEGRATED_SOURCE or record.get("integrated_source")!=T08_INTEGRATED_SOURCE:
        errors.append("T08 verified completion record is not bound to the exact integrated source")
    acceptance=record.get("acceptance_rule",{})
    if acceptance.get("mandatory_dimension_operator")!=">" or acceptance.get("mandatory_dimension_threshold")!=9.0 or acceptance.get("unrounded") is not True or acceptance.get("score_averaging_used") is not False:
        errors.append("T08 verified completion strict acceptance rule is incomplete")
    identity=record.get("source_identity",{})
    if identity.get("shipping_call_site_exercised") is not True or identity.get("simulation_remains_inventory_authority") is not True or identity.get("t07_remains_action_selector") is not True or identity.get("t06_remains_character_motion_authority") is not True or identity.get("save_schema_changed") is not False or identity.get("exact_artifact_index_hashes_verified")!=534 or identity.get("exact_artifact_index_hash_mismatches")!=0 or identity.get("locked_reference_frames_verified")!=44 or identity.get("locked_source_recordings_verified")!=2:
        errors.append("T08 source authority or complete evidence identity is incomplete")
    mechanical=record.get("mechanical_evidence",{})
    if mechanical.get("all_passed") is not True or mechanical.get("functional_suites")!=23 or mechanical.get("total_assertions_checks",0)<1535 or mechanical.get("source_contract_checks")!=24 or mechanical.get("save_matrix_cases")!=7 or mechanical.get("adaptive_device_cases")!=6 or mechanical.get("capture_manifests")!=18 or mechanical.get("unique_pngs")!=39 or mechanical.get("candidate_video_frames")!=[60,148,148] or mechanical.get("route_trace_rows")!=448 or mechanical.get("routes_accepted")!=6 or mechanical.get("routes_completed")!=6 or mechanical.get("routes_rejected")!=0 or mechanical.get("active_transfers_at_end")!=0 or mechanical.get("destination_pulse_samples_per_route")!=26 or mechanical.get("conservation_passed") is not True or mechanical.get("render_log_errors")!=0 or mechanical.get("native_3840x2160_scale1_evidence") is not True or mechanical.get("physical_device_native_4k60_certified") is not False:
        errors.append("T08 regression, route, conservation, matrix or capture evidence is incomplete")
    reviews=record.get("independent_reviews",{})
    scores=reviews.get("scores",{})
    if reviews.get("status")!="PASS" or reviews.get("integrated_source")!=T08_INTEGRATED_SOURCE or reviews.get("workflow_run")!=T08_INTEGRATED_RUN or reviews.get("artifact_id")!=T08_ARTIFACT_ID or reviews.get("artifact_digest")!=T08_ARTIFACT_DIGEST or reviews.get("complete_evidence_index_sha256")!=T08_EVIDENCE_INDEX_SHA256 or reviews.get("score_averaging_used") is not False or reviews.get("critic_blockers")!=[] or reviews.get("valid_unresolved_defects")!=[] or set(scores)!={"C2","C3","C4","C6"}:
        errors.append("T08 independent critic closure is incomplete")
    else:
        errors += _strict_score_errors("T08 critics",scores)
    performance=record.get("performance_critic",{})
    if performance.get("critic")!="C6" or performance.get("candidate_source")!=T08_INTEGRATED_SOURCE or performance.get("run_id")!=T08_INTEGRATED_RUN or performance.get("score")!=9.61 or performance.get("passed") is not True or performance.get("post_warmup_equal_adjacent_windows_passed")!=12 or performance.get("post_warmup_equal_adjacent_windows_total")!=12 or performance.get("errors")!=[]:
        errors.append("T08 fresh integrated C6 closure is incomplete")
    gates=record.get("gates",{})
    if set(gates)!={f"G{i}" for i in range(1,15)} or any(value is not True for value in gates.values()):
        errors.append("T08 G1-G14 closure is incomplete")
    artifact=record.get("artifacts",{}).get("integrated_regression_and_evidence",{})
    if artifact.get("id")!=T08_ARTIFACT_ID or artifact.get("run_id")!=T08_INTEGRATED_RUN or artifact.get("digest")!=T08_ARTIFACT_DIGEST:
        errors.append("T08 integrated artifact identity is invalid")
    if ledger.get("task_id")!="T08" or ledger.get("candidate_commit")!=T08_INTEGRATED_SOURCE or ledger.get("integrated_commit")!=T08_INTEGRATED_SOURCE or ledger.get("integrated_verification_run")!=T08_INTEGRATED_RUN or ledger.get("unresolved_mandatory_count")!=0 or ledger.get("critic_approval_pending") is not False or ledger.get("task_approved") is not True:
        errors.append("T08 defect ledger is not bound to the completed source")
    unresolved=[row.get("id") for row in ledger.get("defects",[]) if row.get("status") not in {"VERIFIED_CLOSED","REJECTED_AS_INVALID_FINDING"}]
    if unresolved:
        errors.append("T08 defect ledger has unresolved entries: "+",".join(str(x) for x in unresolved))
    review_scores=critic_review.get("scores",{})
    if critic_review.get("status")!="PASS" or critic_review.get("approval") is not True or critic_review.get("integrated_source")!=T08_INTEGRATED_SOURCE or critic_review.get("workflow_run")!=T08_INTEGRATED_RUN or critic_review.get("artifact_id")!=T08_ARTIFACT_ID or critic_review.get("artifact_digest")!=T08_ARTIFACT_DIGEST or critic_review.get("complete_evidence_index_sha256")!=T08_EVIDENCE_INDEX_SHA256 or critic_review.get("indexed_files_verified")!=534 or critic_review.get("indexed_hash_mismatches")!=0 or critic_review.get("unresolved_mandatory_defects")!=[] or set(review_scores)!={"C2","C3","C4","C6"}:
        errors.append("T08 independent critic record is incomplete")
    else:
        errors += _strict_score_errors("T08 recorded critics",review_scores)
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
    t06_status=graph["tasks"]["T06"]["status"]
    t07_status=graph["tasks"]["T07"]["status"]
    t08_status=graph["tasks"]["T08"]["status"]
    t09_status=graph["tasks"]["T09"]["status"]
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
            if t05_status=="APPROVED":
                if t06_status not in {"LOCKED","PREPARED","ASSIGNED","BUILDING_ISOLATED","INTEGRATION_READY","INTEGRATING","UNDER_REVIEW","FIX_REQUIRED","APPROVED","BLOCKED"}:
                    errors.append("invalid T06 post-T05 state")
                if t06_status!="APPROVED" and any(graph["tasks"][t]["status"]!="LOCKED" for t in ids[6:]):
                    errors.append("T07+ must remain LOCKED until T06 is approved and each later task is separately prepared")
                if t06_status=="APPROVED":
                    if t07_status not in {"LOCKED","PREPARED","ASSIGNED","BUILDING_ISOLATED","INTEGRATION_READY","INTEGRATING","UNDER_REVIEW","FIX_REQUIRED","APPROVED","BLOCKED"}:
                        errors.append("invalid T07 post-T06 state")
                    if t07_status!="APPROVED" and any(graph["tasks"][t]["status"]!="LOCKED" for t in ids[7:]):
                        errors.append("T08+ must remain LOCKED until T07 is approved and each later task is separately prepared")
                    if t07_status=="APPROVED":
                        if t08_status not in {"LOCKED","PREPARED","ASSIGNED","BUILDING_ISOLATED","INTEGRATION_READY","INTEGRATING","UNDER_REVIEW","FIX_REQUIRED","APPROVED","BLOCKED"}:
                            errors.append("invalid T08 post-T07 state")
                        if t08_status!="APPROVED" and any(graph["tasks"][t]["status"]!="LOCKED" for t in ids[8:]):
                            errors.append("T09+ must remain LOCKED until T08 is approved and each later task is separately prepared")
                        if t08_status=="APPROVED" and t09_status not in {"LOCKED","PREPARED","ASSIGNED","BUILDING_ISOLATED","INTEGRATION_READY","INTEGRATING","UNDER_REVIEW","FIX_REQUIRED","APPROVED","BLOCKED"}:
                            errors.append("invalid T09 post-T08 state")
                        if t09_status!="APPROVED" and any(graph["tasks"][t]["status"]!="LOCKED" for t in ids[9:]):
                            errors.append("T10+ must remain LOCKED until T09 is approved and each later task is separately prepared")
            elif any(graph["tasks"][t]["status"]!="LOCKED" for t in ids[5:]):
                errors.append("T06+ must remain LOCKED until T05 is approved and T06 is separately prepared")
    acc=graph["acceptance_rule"]
    if acc.get("mandatory_dimension_operator")!=">" or acc.get("mandatory_dimension_threshold")!=9.0 or acc.get("unrounded") is not True:
        errors.append("forward strict >9.0 rule missing")
    if ensure_score_strictly_above_nine({"must_fail":9.0})==[]:errors.append("strict score helper incorrectly accepts 9.0")
    errors += registry_errors()
    critics=load_json(DOCS/"CRITIC_MATRIX.json")
    if set(critics["critics"])!={f"C{i}" for i in range(1,12)}:errors.append("C1-C11 definitions incomplete")
    if set(critics["task_applicability"])!=set(ids):errors.append("critic applicability not mapped for all 70 tasks")
    if critics["task_applicability"]["T03"]!=["C1","C2","C6"]:errors.append("T03 V2 critics must be C1+C2+C6")
    if t09_status!="LOCKED":
        required_t09_critics={"C2","C3","C4","C5","C6"}
        if set(critics["task_applicability"]["T09"])!=required_t09_critics:
            errors.append("T09 critics must be C2+C3+C4+C5+C6")
        if set(graph["tasks"]["T09"].get("critics",[]))!=required_t09_critics:
            errors.append("T09 dependency graph critics must include C2+C3+C4+C5+C6")
        packet=DOCS/"T09/TASK_PACKET.md";scope=DOCS/"T09/FROZEN_SCOPE.md"
        if not packet.exists() or not scope.exists():
            errors.append("active T09 packet/frozen scope missing")
        registry=load_json(DOCS/"WORKSTREAM_REGISTRY.json")
        t09_rows=[row for row in registry.get("workstreams",[]) if row.get("task_id")=="T09"]
        if len(t09_rows)!=1 or t09_rows[0].get("status")!=t09_status:
            errors.append("T09 workstream registration missing or status mismatch")
        elif (t09_rows[0].get("workstream_id"),t09_rows[0].get("owner"),t09_rows[0].get("branch"),t09_rows[0].get("base_commit"),t09_rows[0].get("owned_paths")) != (T09_WORKSTREAM,T09_OWNER,T09_BRANCH,T09_BASE,[T09_ALIAS]):
            errors.append("T09 workstream owner/branch/base/path identity mismatch")
        if t09_rows:
            try:
                updated=datetime.fromisoformat(str(t09_rows[0].get("status_updated_at")).replace("Z","+00:00"))
                if updated>datetime.now(timezone.utc):errors.append("T09 status_updated_at is in the future")
            except ValueError:errors.append("T09 status_updated_at is invalid")
        ownership=load_json(DOCS/"PATH_OWNERSHIP.json")
        if T09_ALIAS not in ownership.get("aliases",{}):
            errors.append("T09 path reservation alias missing")
        if t09_status=="APPROVED":
            t09_owners=[row for row in ownership.get("completed_production_owners",[]) if row.get("task_id")=="T09"]
            if len(t09_owners)!=1 or t09_owners[0].get("status")!="APPROVED":
                errors.append("T09 completed owner missing or status mismatch")
            elif (t09_owners[0].get("workstream"),t09_owners[0].get("paths_alias"),t09_owners[0].get("accepted_source"),t09_owners[0].get("integrated_source")) != (T09_WORKSTREAM,T09_ALIAS,"9bc735502b265bfdd365004fb863b19c613e27dd","9bc735502b265bfdd365004fb863b19c613e27dd"):
                errors.append("T09 completed path owner identity mismatch")
        else:
            t09_owners=[row for row in ownership.get("active_owners",[]) if row.get("task_id")=="T09"]
            if len(t09_owners)!=1 or t09_owners[0].get("status")!=t09_status:
                errors.append("T09 active owner missing or status mismatch")
            elif (t09_owners[0].get("workstream"),t09_owners[0].get("owner"),t09_owners[0].get("branch"),t09_owners[0].get("base_commit"),t09_owners[0].get("paths_alias")) != (T09_WORKSTREAM,T09_OWNER,T09_BRANCH,T09_BASE,T09_ALIAS):
                errors.append("T09 path owner identity mismatch")
        resources=load_json(DOCS/"RESOURCE_ACTION_REGISTRY.json")
        expected_resources={
            "wood": ("RESOLVED_BASELINE","natural","chop","axe","human_player_chop","human_helper_chop","visible_wood_stack","contextual_storage_furnace_build"),
            "stone": ("RESOLVED_BASELINE","natural","mine","pickaxe","human_player_mine","human_helper_mine","visible_stone_stack","contextual_storage_furnace_build"),
            "metal": ("T09_FROZEN_ORE","ore","mine","pickaxe","human_player_mine","human_helper_mine","visible_metal_stack","contextual_storage_processing_build"),
            "fuel": ("T09_FROZEN_SALVAGE","fuel_salvage","dismantle","salvage_pry_tool","human_player_dismantle","human_helper_dismantle","visible_fuel_stack","contextual_furnace_storage"),
        }
        for rid,expected in expected_resources.items():
            row=resources.get("resources",{}).get(rid,{})
            actual=tuple(row.get(field) for field in ("status","resource_class","collection_method","tool_profile","player_animation_profile","helper_animation_profile","carry_visual","delivery_destination"))
            if row.get("production_ready") is not True or actual!=expected:
                errors.append(f"T09 frozen resource mapping mismatch for {rid}")
        packet_text=packet.read_text() if packet.exists() else ""
        registry_hash=hashlib.sha256((DOCS/"RESOURCE_ACTION_REGISTRY.json").read_bytes()).hexdigest()
        if registry_hash not in packet_text:
            errors.append("T09 packet is not bound to the exact resource registry hash")
        for token in (T09_WORKSTREAM,T09_OWNER,T09_BRANCH,T09_BASE,T09_ALIAS):
            if token not in packet_text:
                errors.append(f"T09 packet identity missing {token}")
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
            ["T01","T02","T03","T04","T05","T06","T07","T08","T09"] if t09_status=="APPROVED" else
            ["T01","T02","T03","T04","T05","T06","T07","T08"] if t08_status=="APPROVED" else
            ["T01","T02","T03","T04","T05","T06","T07"] if t07_status=="APPROVED" else
            ["T01","T02","T03","T04","T05","T06"] if t06_status=="APPROVED" else
            ["T01","T02","T03","T04","T05"] if t05_status=="APPROVED" else
            ["T01","T02","T03","T04"] if t04_status=="APPROVED" else
            ["T01","T02","T03"]
        )
        if tg.get("approved_tasks")!=expected_approved:errors.append("task-gates approved list does not match dependency graph state")
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
                t05_completion=DOCS/"T05/verified-completion.json"
                t05_ledger=DOCS/"T05/DEFECT_LEDGER.json"
                if not t05_completion.exists() or not t05_ledger.exists():
                    errors.append("T05 verified completion record or defect ledger missing")
                else:
                    errors += t05_completion_errors(load_json(t05_completion),load_json(t05_ledger))
                if t06_status=="LOCKED":
                    if tg.get("active_task") is not None or tg.get("active_status") is not None:errors.append("task-gates must clear active task while T06 is locked")
                elif t06_status=="APPROVED":
                    t06_completion=DOCS/"T06/verified-completion.json"
                    t06_ledger=DOCS/"T06/DEFECT_LEDGER.json"
                    if not t06_completion.exists() or not t06_ledger.exists():
                        errors.append("T06 verified completion record or defect ledger missing")
                    else:
                        errors += t06_completion_errors(load_json(t06_completion),load_json(t06_ledger))
                    if t07_status=="LOCKED":
                        if tg.get("active_task") is not None or tg.get("active_status") is not None:errors.append("task-gates must clear active task while T07 is locked")
                    elif t07_status=="APPROVED":
                        t07_completion=DOCS/"T07/verified-completion.json"
                        t07_ledger=DOCS/"T07/defect-ledger.json"
                        t07_review=DOCS/"T07/independent-critic-review.json"
                        if not t07_completion.exists() or not t07_ledger.exists() or not t07_review.exists():
                            errors.append("T07 verified completion, defect ledger or critic record missing")
                        else:
                            errors += t07_completion_errors(load_json(t07_completion),load_json(t07_ledger),load_json(t07_review))
                        if graph["tasks"]["T08"]["status"]=="LOCKED":
                            if tg.get("active_task") is not None or tg.get("active_status") is not None:errors.append("task-gates must clear active task while T08 is locked")
                        elif graph["tasks"]["T08"]["status"]=="APPROVED":
                            t08_completion=DOCS/"T08/verified-completion.json"
                            t08_ledger=DOCS/"T08/defect-ledger.json"
                            t08_review=DOCS/"T08/independent-critic-review.json"
                            if not t08_completion.exists() or not t08_ledger.exists() or not t08_review.exists():
                                errors.append("T08 verified completion, defect ledger or critic record missing")
                            else:
                                errors += t08_completion_errors(load_json(t08_completion),load_json(t08_ledger),load_json(t08_review))
                            if t09_status=="APPROVED":
                                if tg.get("active_task") is not None or tg.get("active_status") is not None:
                                    errors.append("task-gates must clear active task after T09 approval")
                                t09_record=tg.get("completed_task_records",{}).get("T09",{})
                                if t09_record.get("status")!="APPROVED" or t09_record.get("accepted_source")!="9bc735502b265bfdd365004fb863b19c613e27dd":
                                    errors.append("task-gates T09 completion record mismatch")
                                if not (DOCS/"T09/verified-completion.json").exists():
                                    errors.append("T09 verified completion record missing")
                            else:
                                if tg.get("active_task")!="T09" or tg.get("active_status")!=graph["tasks"]["T09"]["status"]:
                                    errors.append("task-gates must identify T09 and match its post-T08 state")
                                if t09_status!="LOCKED":
                                    t09_gate_rows=[row for row in tg.get("next_post_t03_wave",[]) if row.get("task")=="T09"]
                                    if len(t09_gate_rows)!=1 or (tg.get("active_base_integration_commit"),t09_gate_rows[0].get("owner"),t09_gate_rows[0].get("branch"),t09_gate_rows[0].get("base_commit")) != (T09_BASE,T09_OWNER,T09_BRANCH,T09_BASE):
                                        errors.append("task-gates T09 owner/branch/base identity mismatch")
                                    if tg.get("active_frozen_scope")!="Docs/Production/T09/FROZEN_SCOPE.md":
                                        errors.append("task-gates active T09 frozen scope mismatch")
                                    if tg.get("active_task_packet")!="Docs/Production/T09/TASK_PACKET.md":
                                        errors.append("task-gates active T09 packet mismatch")
                        elif tg.get("active_task")!="T08" or tg.get("active_status")!=graph["tasks"]["T08"]["status"]:
                            errors.append("task-gates must match active T08 state")
                    else:
                        if tg.get("active_task")!="T07" or tg.get("active_status")!=t07_status:errors.append("task-gates must match active T07 state")
                        packet=DOCS/"T07/TASK_PACKET.md";scope=DOCS/"T07/FROZEN_SCOPE.md"
                        if not packet.exists() or not scope.exists():errors.append("active T07 packet/frozen scope missing")
                else:
                    if tg.get("active_task")!="T06" or tg.get("active_status")!=t06_status:errors.append("task-gates must match active T06 state")
                    packet=DOCS/"T06/TASK_PACKET.md";scope=DOCS/"T06/FROZEN_SCOPE.md"
                    if not packet.exists() or not scope.exists():errors.append("active T06 packet/frozen scope missing")
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
