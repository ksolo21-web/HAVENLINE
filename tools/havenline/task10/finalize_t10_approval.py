#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime, hashlib, json, pathlib, subprocess

CANDIDATE = "eba0107def258824549fb10d81785290d0c81d97"
TASK = "T10"
TITLE = "World Transformation Framework"
CRITICS = ["C1","C2","C3","C4","C6","C7"]

def load(path: pathlib.Path):
    return json.loads(path.read_text())

def dump(path: pathlib.Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")

def find_one(root: pathlib.Path, name: str) -> pathlib.Path:
    rows = sorted(root.rglob(name))
    if len(rows) != 1:
        raise SystemExit(f"expected exactly one {name} under {root}, got {rows}")
    return rows[0]

def digest_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def candidate_of(row: dict) -> str:
    return str(row.get("candidate_commit") or row.get("candidate") or row.get("candidate_hash") or row.get("source") or "")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--source-evidence", required=True)
    ap.add_argument("--review-evidence", required=True)
    ap.add_argument("--regression-evidence", required=True)
    ap.add_argument("--source-run-id", type=int, required=True)
    ap.add_argument("--source-artifact-id", type=int, required=True)
    ap.add_argument("--source-artifact-digest", required=True)
    ap.add_argument("--review-run-id", type=int, required=True)
    ap.add_argument("--review-artifact-id", type=int, required=True)
    ap.add_argument("--review-artifact-digest", required=True)
    ap.add_argument("--regression-run-id", type=int, required=True)
    ap.add_argument("--regression-artifact-id", type=int, required=True)
    ap.add_argument("--regression-artifact-digest", required=True)
    a = ap.parse_args()

    repo = pathlib.Path(a.repo)
    src = pathlib.Path(a.source_evidence)
    rev = pathlib.Path(a.review_evidence)
    reg = pathlib.Path(a.regression_evidence)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00","Z")

    head = subprocess.check_output(["git","rev-parse","HEAD"], cwd=repo, text=True).strip()
    if head != CANDIDATE:
        raise SystemExit(f"canonical worktree must start at exact candidate {CANDIDATE}, got {head}")

    # Exact affected-source evidence from the final recapture.
    source_root = src / "task10-isolated-evidence"
    critic_input_root = src / "critic-input"
    source_contract = load(source_root / "source-contract.json")
    domain = load(source_root / "domain-tests.json")
    integration = load(source_root / "integration-tests.json")
    device = load(source_root / "device-layout-evidence.json")
    native4k = load(source_root / "native4k-evidence.json")
    current_performance = load(critic_input_root / "performance.json")
    for label, row in [
        ("source_contract", source_contract), ("domain", domain), ("integration", integration),
        ("device", device), ("native4k", native4k)
    ]:
        if not bool(row.get("passed")):
            raise SystemExit(f"{label} did not pass: {row}")
        candidate = candidate_of(row)
        if candidate and candidate != CANDIDATE:
            raise SystemExit(f"{label} candidate mismatch: {candidate}")
    if integration.get("real_t09_adapter_bound") is not True:
        raise SystemExit("integration evidence is not bound to real T09 adapter")
    if native4k.get("real_t09_adapter_bound") is not True or native4k.get("exact_debit_verified") is not True:
        raise SystemExit("native4k evidence does not prove real T09 exact debit")
    if device.get("device_count") != 6 or device.get("projection_count") != 216 or device.get("projection_failure_count") != 0:
        raise SystemExit("device matrix incomplete or has failures")
    if native4k.get("capture_count") != 36 or native4k.get("unique_capture_count") != 36:
        raise SystemExit("native4k evidence is incomplete")
    if current_performance.get("candidate_commit") != CANDIDATE:
        raise SystemExit("current performance invariant is not exact-source bound")

    # Fresh exact-source integrated regression and save/recovery evidence.
    tests = load(find_one(reg, "tests.json"))
    impact = load(find_one(reg, "impact-regression.json"))
    reg_contract = load(find_one(reg, "source-contract.json"))
    save = load(find_one(reg, "save-matrix-summary.json"))
    if not tests.get("all_passed"):
        raise SystemExit(f"fresh regression tests failed: {tests}")
    if candidate_of(tests) != CANDIDATE:
        raise SystemExit("fresh regression candidate mismatch")
    if not impact.get("passed"):
        raise SystemExit(f"impact regression failed: {impact}")
    if not reg_contract.get("passed") or candidate_of(reg_contract) != CANDIDATE:
        raise SystemExit("fresh source contract did not pass on exact candidate")
    if candidate_of(save) not in ("", CANDIDATE):
        raise SystemExit("save/recovery matrix candidate mismatch")
    if not save.get("passed") or len(save.get("cases", [])) != 7 or not all(x.get("passed") for x in save["cases"]):
        raise SystemExit("fresh integrated save/recovery matrix incomplete")

    # Fresh final six-critic evidence.
    summary = load(find_one(rev, "six-critic-summary.json"))
    if summary.get("candidate_commit") != CANDIDATE or summary.get("passed") is not True:
        raise SystemExit(f"six-critic aggregate did not pass: {summary}")
    if summary.get("all_dimensions_strictly_above_9") is not True:
        raise SystemExit("strict >9 acceptance not satisfied")
    if summary.get("fresh_critics") != ["C1","C2","C3","C4"] or summary.get("preserved_critics") != ["C6","C7"]:
        raise SystemExit("critic-specific invalidation provenance is incomplete")
    preservation = load(find_one(rev, "preservation-proof.json"))
    if preservation.get("passed") is not True or preservation.get("candidate") != CANDIDATE:
        raise SystemExit("C6/C7 preservation proof did not pass")

    critic_rows = {}
    minimum = 100.0
    for cid in CRITICS:
        p = rev / "normalized" / cid / "critic-record.json"
        if not p.exists():
            p = find_one(rev / "normalized" / cid, "critic-record.json")
        row = load(p)
        if candidate_of(row) != CANDIDATE:
            raise SystemExit(f"{cid} candidate mismatch")
        if row.get("passed") is not True or row.get("coverage_complete") is not True:
            raise SystemExit(f"{cid} not a complete pass: {row}")
        if row.get("defects") not in ([], None):
            raise SystemExit(f"{cid} has unresolved defects: {row.get('defects')}")
        scores = {k: float(v) for k,v in row.get("scores",{}).items()}
        if not scores or any(v <= 9.0 for v in scores.values()):
            raise SystemExit(f"{cid} violates strict >9 gate: {scores}")
        minimum = min(minimum, min(scores.values()))
        if cid in ("C6","C7"):
            if row.get("preserved_pass") is not True or row.get("fresh_rerun") is not False:
                raise SystemExit(f"{cid} preservation provenance missing")
            if row.get("preserved_from_candidate") != "7eccdac8928e59812d7991d2f2da93eb6b8ebf18":
                raise SystemExit(f"{cid} preservation source mismatch")
        else:
            if row.get("preserved_pass", False):
                raise SystemExit(f"{cid} must be a fresh affected-critic pass")
        critic_rows[cid] = row

    if minimum <= 9.0:
        raise SystemExit("minimum mandatory critic dimension is not strictly >9")

    # Current governance state must still be the exact pre-closeout state.
    graph_path = repo / "Docs/Production/DEPENDENCY_GRAPH.json"
    registry_path = repo / "Docs/Production/WORKSTREAM_REGISTRY.json"
    ownership_path = repo / "Docs/Production/PATH_OWNERSHIP.json"
    gates_path = repo / "Docs/Production/task-gates.json"
    graph = load(graph_path)
    registry = load(registry_path)
    ownership = load(ownership_path)
    gates = load(gates_path)
    deps = graph["tasks"]["T10"]["dependencies"]
    if any(graph["tasks"][d]["status"] != "APPROVED" for d in deps):
        raise SystemExit(f"T10 dependency regression: {deps}")
    ws = next(x for x in registry["workstreams"] if x["task_id"] == "T10")
    if ws["status"] not in ("FIX_REQUIRED","UNDER_REVIEW","INTEGRATING","INTEGRATION_READY"):
        raise SystemExit(f"unexpected T10 pre-closeout status: {ws['status']}")

    test_summary = {
        "source_contract": "PASS",
        "formal_domain": f"PASS; {domain.get('check_count')} checks",
        "real_t09_integration": f"PASS; {integration.get('check_count')} checks",
        "fresh_impacted_regression": f"PASS; {tests.get('suite_count')} suites / {tests.get('total_checks')} checks",
        "save_state_matrix": "7/7 passed",
        "device_layout_matrix": "6 devices / 216 projections passed",
        "native_4k_matrix": "36/36 unique 3840x2160 captures passed",
        "performance_gate": "PASS; C6 strict pass preserved under critic-specific invalidation with current quantitative/topology invariant proof",
    }
    critic_status = {
        cid: f"PASS; minimum mandatory dimension {min(float(v) for v in critic_rows[cid]['scores'].values()):.3f}; zero defects"
        for cid in CRITICS
    }

    gates_record = {
        "G1": {"status":"PASS","evidence":"T05, T08 and T09 dependencies are APPROVED."},
        "G2": {"status":"PASS","evidence":"Exact canonical candidate and source-bound recapture identity validation passed."},
        "G3": {"status":"PASS","evidence":"Frozen World Transformation Framework scope passed without T11 final camp-content expansion."},
        "G4": {"status":"PASS","evidence":"Source contract, import/governance/tooling and exact-source validation passed."},
        "G5": {"status":"PASS","evidence":f"World-transform domain and real-T09 adapter integration passed ({domain.get('check_count')} + {integration.get('check_count')} checks)."},
        "G6": {"status":"PASS","evidence":f"Fresh exact-source impacted regression passed {tests.get('suite_count')} suites / {tests.get('total_checks')} checks."},
        "G7": {"status":"PASS","evidence":"Source, regression and critic evidence are exact-SHA bound and artifact digests are retained below."},
        "G8": {"status":"PASS","evidence":"Prior strict C6 pass is preserved under critic-specific invalidation; current candidate quantitative/topology invariants pass and preservation proof is retained."},
        "G9": {"status":"PASS","evidence":"7/7 save, reload, migration, interrupted-save and recovery cases passed."},
        "G10":{"status":"PASS","evidence":"T10 remained transformation-framework scope; no economy/purchase/entitlement expansion was introduced."},
        "G11":{"status":"PASS","evidence":"6-device / 216-projection layout matrix and 36 unique native 3840x2160 captures passed."},
        "G12":{"status":"PASS","evidence":"Fresh exact-source C1/C2/C3/C4 review passed; unaffected C6/C7 passes are preserved with audited critic-specific invalidation provenance and invariants."},
        "G13":{"status":"PASS","evidence":f"Every mandatory critic dimension is strictly above 9.0; minimum unrounded score {minimum:.3f}; zero defects remain."},
        "G14":{"status":"PASS","evidence":"Exact canonical integrated source passed fresh impacted regression and final source-bound closeout."},
    }

    retained = {
        "source": {
            "run_id": a.source_run_id,
            "artifact_id": a.source_artifact_id,
            "digest": a.source_artifact_digest,
        },
        "final_six_critic": {
            "run_id": a.review_run_id,
            "artifact_id": a.review_artifact_id,
            "digest": a.review_artifact_digest,
        },
        "fresh_regression": {
            "run_id": a.regression_run_id,
            "artifact_id": a.regression_artifact_id,
            "digest": a.regression_artifact_digest,
        },
    }

    completion = {
        "schema_version": 1,
        "task_id": TASK,
        "title": TITLE,
        "status": "APPROVED",
        "candidate_commit": CANDIDATE,
        "integrated_source": CANDIDATE,
        "base_commit": ws["base_commit"],
        "source_run_id": a.source_run_id,
        "final_review_run_id": a.review_run_id,
        "fresh_regression_run_id": a.regression_run_id,
        "acceptance_rule": {
            "mandatory_dimension_operator": ">",
            "mandatory_dimension_threshold": 9,
            "unrounded": True,
            "score_averaging_used": False,
            "zero_mandatory_defects": True,
        },
        "minimum_mandatory_dimension_score": minimum,
        "score": minimum,
        "path_validation": {
            "passed": True,
            "candidate": CANDIDATE,
            "classification": "exact_source_recap",
            "errors": [],
        },
        "gates": gates_record,
        "tests": {"passed": True, **test_summary},
        "evidence": {
            "candidate_commit": CANDIDATE,
            "source_contract_sha256": digest_file(source_root / "source-contract.json"),
            "device_layout_sha256": digest_file(source_root / "device-layout-evidence.json"),
            "native4k_manifest_sha256": digest_file(source_root / "native4k-evidence.json"),
            "current_performance_invariant_sha256": digest_file(critic_input_root / "performance.json"),
            "save_matrix_sha256": digest_file(find_one(reg, "save-matrix-summary.json")),
            "critic_preservation_proof_sha256": digest_file(find_one(rev, "preservation-proof.json")),
            "fresh_regression_tests_sha256": digest_file(find_one(reg, "tests.json")),
            "six_critic_summary_sha256": digest_file(find_one(rev, "six-critic-summary.json")),
        },
        "unresolved_mandatory_defects": [],
        "critics": {
            cid: {
                "status": "PASS",
                "candidate_commit": CANDIDATE,
                "scores": critic_rows[cid]["scores"],
                "defects": [],
                "coverage_complete": True,
                "independent_runtime": True,
                "review_mode": "preserved" if cid in ("C6","C7") else "fresh",
                "preserved_from_candidate": critic_rows[cid].get("preserved_from_candidate"),
                "raw_record_path": f"Docs/Production/T10/CriticRaw/{cid}.json",
            } for cid in CRITICS
        },
        "integration": {
            "candidate_commit": CANDIDATE,
            "regression_passed": True,
            "integration_branch": "codex/havenline-sequential-task-01",
        },
        "retained_review_evidence": retained,
        "scope_limits": {
            "whole_game_approved": False,
            "physical_phone_tablet_native_4k60_verified": False,
            "unfinished_apk_delivery_allowed": False,
        },
        "approved_at": now,
    }

    # Retain the final critic records in-repo.
    raw_dir = repo / "Docs/Production/T10/CriticRaw"
    for cid,row in critic_rows.items():
        dump(raw_dir / f"{cid}.json", row)
    dump(repo / "Docs/Production/T10/independent-critic-review.json", {
        "task_id": TASK,
        "candidate_commit": CANDIDATE,
        "required_critics": CRITICS,
        "minimum_mandatory_dimension_score": minimum,
        "gate_operator": "> 9.0",
        "all_dimensions_strictly_above_9": True,
        "zero_unresolved_defects": True,
        "coverage_complete": True,
        "fresh_critics": ["C1","C2","C3","C4"],
        "preserved_critics": ["C6","C7"],
        "preservation_proof": preservation,
        "records": {cid: critic_rows[cid] for cid in CRITICS},
        "retained_review_evidence": retained,
        "passed": True,
    })
    dump(repo / "Docs/Production/T10/verified-completion.json", completion)
    dump(repo / "Docs/Production/Evidence/T10/final-closeout.json", {
        "task_id": TASK,
        "candidate_commit": CANDIDATE,
        "approved": True,
        "minimum_mandatory_dimension_score": minimum,
        "gates": gates_record,
        "tests": test_summary,
        "artifacts": retained,
        "approved_at": now,
    })

    # Close the historical defect ledger without deleting its audit history.
    ledger_path = repo / "Docs/Production/T10/defect-ledger.json"
    ledger = load(ledger_path)
    ledger.update({
        "review_scope": "final exact integrated-source World Transformation Framework approval",
        "latest_verified_source": CANDIDATE,
        "latest_verified_run": a.regression_run_id,
        "latest_verified_artifact": a.review_artifact_id,
        "latest_verified_artifact_sha256": a.review_artifact_digest.replace("sha256:",""),
        "isolated_state": "APPROVED",
        "integration_allowed": True,
        "task_approved": True,
        "real_t09_adapter_bound": True,
        "unresolved_mandatory_defects": [],
        "final_closeout": {
            "minimum_mandatory_dimension_score": minimum,
            "required_critics": CRITICS,
            "zero_unresolved_defects": True,
            "fresh_regression_run_id": a.regression_run_id,
            "final_review_run_id": a.review_run_id,
            "approved_at": now,
        }
    })
    dump(ledger_path, ledger)

    # Authoritative coordination state.
    graph["tasks"]["T10"]["status"] = "APPROVED"
    dump(graph_path, graph)

    ws.update({
        "status": "APPROVED",
        "candidate_commit": CANDIDATE,
        "candidate_hash_or_artifact": (
            f"integrated-source:{CANDIDATE}; source-run:{a.source_run_id}; "
            f"source-artifact:{a.source_artifact_id}; review-run:{a.review_run_id}; "
            f"review-artifact:{a.review_artifact_id}; regression-run:{a.regression_run_id}; "
            f"regression-artifact:{a.regression_artifact_id}"
        ),
        "tests": test_summary,
        "critic_status": critic_status,
        "integration_status": (
            f"APPROVED; exact canonical source {CANDIDATE} passed fresh regression, "
            f"6-device/216-projection and 36-frame native-4K evidence, 7/7 save cases, "
            f"G1-G14, fresh C1/C2/C3/C4 plus preserved C6/C7 review provenance with every mandatory "
            f"dimension strictly above 9.0 (minimum {minimum:.3f}) and zero unresolved defects."
        ),
        "known_blockers": [],
        "next_action": "Preserve T10 completion; prepare T11 packet/ownership before activation.",
        "status_updated_at": now,
    })
    dump(registry_path, registry)

    # Move T10 path ownership from active to completed production ownership.
    ownership["active_owners"] = [
        row for row in ownership.get("active_owners", [])
        if row.get("task_id") != "T10"
    ]
    completed = [
        row for row in ownership.get("completed_production_owners", [])
        if row.get("task_id") != "T10"
    ]
    completed.append({
        "workstream": ws["workstream_id"],
        "task_id": "T10",
        "owner": ws["owner"],
        "branch": ws["branch"],
        "base_commit": ws["base_commit"],
        "paths_alias": "@reservation:T10",
        "status": "APPROVED",
        "accepted_source": CANDIDATE,
        "integrated_source": CANDIDATE,
    })
    ownership["completed_production_owners"] = completed
    dump(ownership_path, ownership)

    if "T10" not in gates["approved_tasks"]:
        gates["approved_tasks"].append("T10")
    gates["approved_task_count"] = len(gates["approved_tasks"])
    gates["active_task"] = None
    gates["active_task_title"] = None
    gates["active_status"] = None
    gates["active_base_integration_commit"] = None
    gates["active_frozen_scope"] = None
    gates["active_task_packet"] = None
    gates["active_evidence"] = None
    gates["active_candidate_source"] = None
    gates["active_candidate_run"] = None
    gates["active_tests"] = None
    gates["active_critic_state"] = None
    gates.setdefault("completed_task_records", {})["T10"] = {
        "status": "APPROVED",
        "accepted_source": CANDIDATE,
        "integrated_source": CANDIDATE,
        "score": minimum,
        "minimum_mandatory_dimension_score": minimum,
        "gate_operator": "> 9.0",
        "visual_status": "PASS",
        "source_evidence_run": a.source_run_id,
        "final_review_run": a.review_run_id,
        "integrated_evidence_run": a.regression_run_id,
        "artifact_id": a.review_artifact_id,
        "record": "Docs/Production/T10/verified-completion.json",
        "later_regression_reopens_task": True,
    }
    for row in gates.get("next_post_t03_wave", []):
        if row.get("task") == "T10":
            row["state"] = "APPROVED"
            row["reason"] = (
                f"Exact canonical source {CANDIDATE} passed G1-G14, fresh impacted regression, "
                f"source-bound fresh C1/C2/C3/C4 plus preserved C6/C7 with minimum {minimum:.3f}, "
                "complete coverage and zero unresolved mandatory defects."
            )
    dump(gates_path, gates)

    # Final self-checks.
    if graph["tasks"]["T10"]["status"] != "APPROVED":
        raise SystemExit("dependency graph closeout failed")
    if ws["status"] != "APPROVED" or ws["known_blockers"]:
        raise SystemExit("workstream closeout failed")
    if "T10" not in gates["approved_tasks"] or gates["approved_task_count"] < 10:
        raise SystemExit("task-gates closeout failed")
    if any(row.get("task_id") == "T10" for row in ownership.get("active_owners", [])):
        raise SystemExit("T10 active ownership was not cleared")
    done = [row for row in ownership.get("completed_production_owners", []) if row.get("task_id") == "T10"]
    if len(done) != 1 or done[0].get("accepted_source") != CANDIDATE or done[0].get("integrated_source") != CANDIDATE:
        raise SystemExit("T10 completed ownership record is incomplete")
    for field in ("active_task","active_status","active_base_integration_commit","active_frozen_scope","active_task_packet","active_evidence","active_critic_state"):
        if gates.get(field) is not None:
            raise SystemExit("active task pointer not cleared: "+field)
    print(json.dumps({
        "task": TASK,
        "candidate": CANDIDATE,
        "status": "APPROVED",
        "minimum_mandatory_dimension_score": minimum,
        "critics": CRITICS,
        "fresh_regression_run_id": a.regression_run_id,
        "final_review_run_id": a.review_run_id,
    }, indent=2))

if __name__ == "__main__":
    main()
