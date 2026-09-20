#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SCALAR_STRATEGIES = {"SCALAR_TUNING", "CONFIGURATION_TUNING", "CONSTANT_ADJUSTMENT"}
CAUSAL_STRATEGIES = {"ALGORITHM", "ARCHITECTURE", "CONTRACT", "PRODUCT_LOGIC", "TOOLING", "GOVERNANCE"} | SCALAR_STRATEGIES
NON_PRODUCT_STRATEGIES = {"EVIDENCE_ONLY", "TEST_ONLY", "DIAGNOSTIC_ONLY"}
ARCHITECTURAL_ESCALATIONS = {"PLACEMENT_ALGORITHM", "EVIDENCE_ARCHITECTURE", "CONTRACT_REDIRECT", "STATE_MACHINE", "DATA_MODEL"}
EXPECTED_THRESHOLD_REGISTRY_HASHES = {
    "critic_matrix_sha256": "cf8c435050e01b0f3a96cf73c57cbf1075f3da7d84584f680c8c4cb952debcaf",
    "task_gates_sha256": "84abb49c28d755b40576e09c4415e574b9780c1c58e7010a4826576e7cab1591",
}
LOCKED_REPAIR_INTELLIGENCE = {
    "C0-T10-c7a18d0-comprehensive-anti-loop": {
        "path": "Docs/Production/T10/C0_REPAIR_INTELLIGENCE_LOCK.json",
        "sha256": "2175f7a1b3a687674b59a5769d077ac15e4a2a3e3ad74a19ff795c75c9f1127d",
    }
}
ARCHITECTURAL_OPERATION_KINDS = {
    "ALGORITHM_REPLACEMENT", "EVIDENCE_ARCHITECTURE_CHANGE", "CONTRACT_REDIRECT", "STATE_MACHINE_CHANGE", "DATA_MODEL_CHANGE"
}
SCALAR_PATCH = re.compile((
    r"(?:reduce|decrease|increase|adjust|set|tune|tweak|change|alter|multiply|divide|apply|shrink|compress|contract|enlarge|expand|use|make|render|draw|halve).{0,120}(?:pixel[_ -]?size|width|height|scale|constant|threshold|timeout|limit|factor|ratio|coefficient|projection|glyph|label|text|geometry|footprint|dimension|percent|tenths?|twentieths?|half|quarter)"
    r"|(?:pixel[_ -]?size|width|height|scale|constant|threshold|timeout|limit|factor|ratio|coefficient|projection|glyph|label|text|geometry|footprint|dimension|percent|tenths?|twentieths?|half|quarter).{0,120}(?:reduce|decrease|increase|adjust|set|tune|tweak|change|alter|multiply|divide|apply|shrink|compress|contract|enlarge|expand|use|make|render|draw|halve)"
    r"|(?:multiply|divide|factor|ratio|coefficient|percent|tenths?|twentieths?|half|quarter).{0,80}\b\d+(?:\.\d+)?%?\b"
    r"|\b\d+(?:\.\d+)?%\b.{0,80}(?:glyph|label|text|geometry|footprint|dimension|size|scale)"
    ).replace("ratio", r"\bratio\b"), re.IGNORECASE,
)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _repair_intelligence(c0: dict) -> dict:
    return {key: c0.get(key) for key in ("failure_family_history", "full_domain_proofs", "failure_frontier")}


def _structured_mechanism(operations: list) -> str:
    parts=[]
    for row in operations:
        if not isinstance(row,dict):continue
        kind=_text(row.get("operation_kind")).upper()
        symbols=",".join(str(value) for value in _list(row.get("target_symbols")))
        parts.append(f"{kind}[{symbols}]")
    return ";".join(parts)


def _derived_parameter_binding(row: dict, domain: dict) -> str:
    payload={
        "target":row.get("target"),
        "mode":row.get("mode"),
        "normalized_rhs":row.get("normalized_rhs"),
        "dependency_symbols":row.get("dependency_symbols"),
        "bounds":row.get("bounds"),
        "proof_artifact_sha256":domain.get("artifact_sha256"),
        "proof_source_commit":row.get("proof_source_commit"),
        "proof_source_path":row.get("proof_source_path"),
        "proof_source_sha256":row.get("proof_source_sha256"),
    }
    return _stable_digest(payload)


def proof_relevant_digest(source: str, symbols: list[str]) -> str | None:
    lines=source.splitlines()
    slices=[]
    for symbol in symbols:
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*",str(symbol)) is None:return None
        constant=[line.rstrip() for line in lines if re.match(r"^(?:const|var)\s+"+re.escape(symbol)+r"\b",line)]
        starts=[index for index,line in enumerate(lines) if re.match(r"^(?:static\s+)?func\s+"+re.escape(symbol)+r"\s*\(",line)]
        if len(constant)==1 and not starts:
            body=constant
        elif len(starts)==1 and not constant:
            start=starts[0];end=len(lines)
            for index in range(start+1,len(lines)):
                if lines[index] and not lines[index][0].isspace():end=index;break
            body=[line.rstrip() for line in lines[start:end]]
        else:return None
        slices.append({"symbol":symbol,"source":"\n".join(body)})
    return _stable_digest(slices)


def whole_file_proof_digest(source: str, ignored_exact_lines: list[str]) -> str | None:
    lines=source.splitlines()
    if len(ignored_exact_lines)!=len(set(ignored_exact_lines)):return None
    ignored=set()
    if ignored_exact_lines:
        starts=[index for index,line in enumerate(lines) if re.match(r"^static\s+func\s+contract\s*\(",line)]
        if len(starts)!=1:return None
        contract_start=starts[0];contract_end=len(lines)
        for index in range(contract_start+1,len(lines)):
            if lines[index] and not lines[index][0].isspace():contract_end=index;break
        for expected in ignored_exact_lines:
            matches=[index for index,line in enumerate(lines) if line==expected]
            if len(matches)>1 or (matches and not contract_start<matches[0]<contract_end):return None
            ignored.update(matches)
    kept=[line.rstrip() for index,line in enumerate(lines) if index not in ignored]
    return hashlib.sha256(("\n".join(kept)+"\n").encode()).hexdigest()


def repair_intelligence_errors(c0: dict, root: Path = ROOT, expected_sha256: str | None = None) -> list[str]:
    errors: list[str] = []
    actual_sha256 = _stable_digest(_repair_intelligence(c0))
    if expected_sha256 is not None:
        return [] if actual_sha256 == expected_sha256 else ["C0_REPAIR_INTELLIGENCE_DIGEST_MISMATCH"]
    lock = LOCKED_REPAIR_INTELLIGENCE.get(_text(c0.get("diagnosis_id")))
    if not lock:
        return ["C0_REPAIR_INTELLIGENCE_LOCK_REQUIRED"]
    path = root / lock["path"]
    if not path.is_file() or _digest(path) != lock["sha256"]:
        return ["C0_REPAIR_INTELLIGENCE_LOCK_HASH_MISMATCH"]
    manifest = json.loads(path.read_text())
    if manifest.get("task_id") != c0.get("task_id") or manifest.get("diagnosis_id") != c0.get("diagnosis_id"):
        errors.append("C0_REPAIR_INTELLIGENCE_LOCK_IDENTITY_MISMATCH")
    if manifest.get("repair_intelligence_sha256") != actual_sha256:
        errors.append("C0_REPAIR_INTELLIGENCE_DIGEST_MISMATCH")
    history_counts = {
        _text(row.get("failure_family_id")): sum(
            1 for attempt in _list(row.get("prior_attempts"))
            if isinstance(attempt, dict) and attempt.get("same_family") is True
        )
        for row in _list(c0.get("failure_family_history")) if isinstance(row, dict)
    }
    source_attempts = _list(manifest.get("prior_attempt_sources"))
    source_counts: dict[str, int] = {}
    for row in source_attempts:
        if not isinstance(row, dict):
            errors.append("C0_PRIOR_ATTEMPT_SOURCE_INVALID")
            continue
        family_id = _text(row.get("failure_family_id"))
        source_counts[family_id] = source_counts.get(family_id, 0) + 1
        if not isinstance(row.get("run_id"), int) or row.get("run_id") <= 0 or row.get("result") not in {"FAILED", "PARTIAL"}:
            errors.append("C0_PRIOR_ATTEMPT_SOURCE_INVALID")
    if source_counts != history_counts:
        errors.append("C0_PRIOR_ATTEMPT_SOURCES_INCOMPLETE")
    observations = _list(_dict(c0.get("failure_frontier")).get("observations"))
    frontier_pairs = {(row.get("run_id"), row.get("candidate")) for row in observations if isinstance(row, dict)}
    locked_frontier_pairs = {
        (row.get("run_id"), row.get("candidate"))
        for row in _list(manifest.get("frontier_sources")) if isinstance(row, dict)
    }
    if frontier_pairs != locked_frontier_pairs:
        errors.append("C0_FAILURE_FRONTIER_SOURCE_BINDING_MISMATCH")
    for row in source_attempts:
        if not isinstance(row, dict) or not row.get("result_sha256") or not _text(row.get("result_record")).startswith("canonical failure_frontier"):
            continue
        retained = [item for item in observations if isinstance(item, dict) and item.get("run_id") == row.get("run_id")]
        if _stable_digest(retained) != row.get("result_sha256"):
            errors.append("C0_PRIOR_ATTEMPT_RESULT_HASH_MISMATCH")
    proof = _dict(manifest.get("domain_proof"))
    summary_path = root / _text(proof.get("retained_summary_path"))
    if not summary_path.is_file() or _digest(summary_path) != proof.get("retained_summary_sha256"):
        errors.append("C0_DOMAIN_PROOF_RETAINED_SUMMARY_HASH_MISMATCH")
    else:
        summary = json.loads(summary_path.read_text())
        required = _dict(proof.get("required_summary"))
        if any(summary.get(key) != value for key, value in required.items()):
            errors.append("C0_DOMAIN_PROOF_MACHINE_RESULT_MISMATCH")
        if summary.get("projection_count") != summary.get("device_count", 0) * summary.get("state_count", 0) * summary.get("angle_count", 0):
            errors.append("C0_DOMAIN_PROOF_MACHINE_DIMENSIONS_MISMATCH")
        if summary.get("harness_commit") != proof.get("proof_source_commit") or summary.get("proof_source_path") != proof.get("proof_source_path") or summary.get("proof_source_sha256") != proof.get("proof_source_sha256"):
            errors.append("C0_DOMAIN_PROOF_SOURCE_BINDING_MISMATCH")
    try:
        source_bytes=subprocess.check_output(["git","show",f"{proof.get('proof_source_commit')}:{proof.get('proof_source_path')}"],cwd=root)
        if hashlib.sha256(source_bytes).hexdigest()!=proof.get("proof_source_sha256"):
            errors.append("C0_DOMAIN_PROOF_SOURCE_HASH_MISMATCH")
    except Exception:
        errors.append("C0_DOMAIN_PROOF_SOURCE_UNAVAILABLE")
    c0_proofs = _list(c0.get("full_domain_proofs"))
    bound_proof=_dict(_dict(c0_proofs[0]).get("proof")) if len(c0_proofs)==1 else {}
    manifest_bound_fields=(
        "artifact_id","artifact_sha256","proof_source_commit","proof_source_path","proof_source_sha256",
        "proof_slice_mode","proof_irrelevant_exact_lines","proof_relevant_sha256",
    )
    if len(c0_proofs) != 1 or any(bound_proof.get(key)!=proof.get(key) for key in manifest_bound_fields):
        errors.append("C0_DOMAIN_PROOF_MANIFEST_BINDING_MISMATCH")
    if bound_proof.get("derived_effect_bounds")!=_dict(proof.get("required_summary")).get("derived_effect_bounds"):
        errors.append("C0_DOMAIN_PROOF_BOUND_OBSERVATIONS_MISMATCH")
    sha_fields = [proof.get("artifact_sha256"), proof.get("retained_summary_sha256"),proof.get("proof_source_sha256")]
    for row in _list(manifest.get("prior_attempt_sources")):
        if isinstance(row, dict):
            sha_fields.extend(row.get(key) for key in ("artifact_sha256", "result_sha256") if row.get(key) is not None)
    if any(not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None for value in sha_fields):
        errors.append("C0_REPAIR_INTELLIGENCE_SOURCE_HASH_INVALID")
    return errors


def canonical_threshold_snapshot(root: Path = ROOT) -> dict:
    matrix_path = root / "Docs/Production/CRITIC_MATRIX.json"
    gates_path = root / "Docs/Production/task-gates.json"
    matrix = json.loads(matrix_path.read_text())
    gates = json.loads(gates_path.read_text())
    return {
        "critic_matrix_sha256": _digest(matrix_path),
        "task_gates_sha256": _digest(gates_path),
        "critic_matrix": matrix.get("forward_acceptance"),
        "task_gates": gates.get("forward_acceptance"),
    }


def _threshold_snapshot_valid(snapshot: dict) -> bool:
    matrix = _dict(snapshot.get("critic_matrix"))
    gates = _dict(snapshot.get("task_gates"))
    return (
        matrix.get("dimension_operator") == ">"
        and matrix.get("threshold") == 9.0
        and matrix.get("unrounded") is True
        and matrix.get("target") == 10.0
        and matrix.get("no_average_waiver") is True
        and matrix.get("no_unresolved_mandatory_defect") is True
        and gates.get("mandatory_dimension_operator") == ">"
        and gates.get("mandatory_dimension_threshold") == 9
        and gates.get("unrounded") is True
        and gates.get("target") == 10
        and gates.get("all_applicable_gates_must_pass") is True
        and gates.get("no_unresolved_mandatory_defects") is True
        and snapshot.get("critic_matrix_sha256") == EXPECTED_THRESHOLD_REGISTRY_HASHES["critic_matrix_sha256"]
        and snapshot.get("task_gates_sha256") == EXPECTED_THRESHOLD_REGISTRY_HASHES["task_gates_sha256"]
    )


def _group_review(
    group: dict,
    c0_blockers: dict[str, dict],
    c0_history: dict[str, dict],
    c0_domain_proofs: dict[str, dict],
) -> tuple[list[str], list[str], list[str]]:
    reject: list[str] = []
    evidence_gaps: list[str] = []
    risk_codes: list[str] = []

    group_id = _text(group.get("group_id")) or "<missing-group>"
    group_blockers = [str(x) for x in _list(group.get("blocker_ids")) if _text(x)]
    family = _dict(group.get("failure_family"))
    strategy = _text(group.get("strategy_kind")).upper()
    same_family_attempt_count = group.get("same_family_attempt_count")
    prior_attempts = _list(group.get("prior_attempts"))
    escalation = _dict(group.get("architectural_escalation"))
    repair_operations = _list(group.get("repair_operations"))
    structured_operations_valid = False
    scalar_parameters_changed = group.get("scalar_parameters_changed")
    diff_contract = _dict(group.get("implementation_diff_contract"))
    blocker_coverage = _list(group.get("blocker_coverage"))
    domain = _dict(group.get("full_domain_proof"))
    preflights = _list(group.get("cheap_disproof_preflight"))
    counterexamples = _list(group.get("counterexamples_considered"))
    blast = _list(group.get("blast_radius_hypotheses"))
    residual_unknowns = _list(group.get("residual_unknowns"))

    if group_id == "<missing-group>":
        reject.append("GROUP_ID_REQUIRED")
    if not group_blockers:
        reject.append(f"{group_id}:BLOCKER_IDS_REQUIRED")
    unknown_blocker_ids = sorted(set(group_blockers) - set(c0_blockers))
    if unknown_blocker_ids:
        reject.append(f"{group_id}:UNKNOWN_C0_BLOCKERS:{','.join(unknown_blocker_ids)}")

    for field in ("id", "invariant"):
        if not _text(family.get(field)):
            reject.append(f"{group_id}:FAILURE_FAMILY_{field.upper()}_REQUIRED")
    dimensions = _list(family.get("scope_dimensions"))
    if not dimensions or any(not _text(x) for x in dimensions):
        reject.append(f"{group_id}:FAILURE_FAMILY_SCOPE_DIMENSIONS_REQUIRED")
    if not _list(family.get("known_failed_cases")):
        reject.append(f"{group_id}:KNOWN_FAILED_CASES_REQUIRED")
    unknown_cases = _list(family.get("unexecuted_or_unknown_cases"))

    if strategy not in CAUSAL_STRATEGIES | NON_PRODUCT_STRATEGIES:
        reject.append(f"{group_id}:STRATEGY_KIND_INVALID")
    for key in ("causal_mechanism", "why_this_fixes_cause", "why_materially_different"):
        if not _text(group.get(key)):
            reject.append(f"{group_id}:{key.upper()}_REQUIRED")

    if not isinstance(same_family_attempt_count, int) or same_family_attempt_count < 0:
        reject.append(f"{group_id}:SAME_FAMILY_ATTEMPT_COUNT_INVALID")
        same_family_attempt_count = 0
    recorded_same_family = sum(1 for row in prior_attempts if isinstance(row, dict) and row.get("same_family") is True)
    history = c0_history.get(_text(family.get("id")))
    if history is not None:
        authoritative_attempts = _list(history.get("prior_attempts"))
        authoritative_count = sum(1 for row in authoritative_attempts if isinstance(row, dict) and row.get("same_family") is True)
        if sorted(group_blockers) != sorted(str(x) for x in _list(history.get("blocker_ids"))):
            reject.append(f"{group_id}:C0_FAILURE_FAMILY_BLOCKER_BINDING_MISMATCH")
        if prior_attempts != authoritative_attempts or same_family_attempt_count != authoritative_count:
            reject.append(f"{group_id}:C0_ATTEMPT_HISTORY_BINDING_MISMATCH")
    elif recorded_same_family or same_family_attempt_count:
        reject.append(f"{group_id}:C0_ATTEMPT_HISTORY_REQUIRED")
    if recorded_same_family != same_family_attempt_count:
        reject.append(f"{group_id}:PRIOR_ATTEMPTS_COUNT_MISMATCH")
    if same_family_attempt_count > 0 and not prior_attempts:
        reject.append(f"{group_id}:PRIOR_ATTEMPTS_REQUIRED")
    if same_family_attempt_count >= 2:
        risk_codes.append("REPEATED_FAILURE_FAMILY")
        if type(group.get("operation_contract_version")) is not int or group["operation_contract_version"] != 2:
            reject.append(f"{group_id}:REPEATED_REPAIR_OPERATION_CONTRACT_V2_REQUIRED")
        if len(_text(group.get("why_materially_different"))) < 24:
            reject.append(f"{group_id}:MATERIAL_DIFFERENCE_NOT_JUSTIFIED")
        if escalation.get("required") is not True or escalation.get("provided") is not True:
            reject.append(f"{group_id}:ARCHITECTURAL_ESCALATION_REQUIRED")
        if _text(escalation.get("kind")).upper() not in ARCHITECTURAL_ESCALATIONS:
            reject.append(f"{group_id}:ARCHITECTURAL_ESCALATION_KIND_INVALID")
        if len(_text(escalation.get("reason"))) < 24:
            reject.append(f"{group_id}:ARCHITECTURAL_ESCALATION_REASON_REQUIRED")
        operation_error_start = len(reject)
        if not repair_operations:
            reject.append(f"{group_id}:STRUCTURED_REPAIR_OPERATIONS_REQUIRED")
        for row in repair_operations:
            if not isinstance(row, dict) or _text(row.get("operation_kind")).upper() not in ARCHITECTURAL_OPERATION_KINDS:
                reject.append(f"{group_id}:ARCHITECTURAL_REPAIR_OPERATION_INVALID")
                continue
            for key in ("target", "replaces", "with", "invariant_enforced"):
                if not _text(row.get(key)):
                    reject.append(f"{group_id}:REPAIR_OPERATION_{key.upper()}_REQUIRED")
            symbols = _list(row.get("target_symbols"))
            valid_symbols = bool(symbols) and all(
                isinstance(symbol, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", symbol) is not None
                for symbol in symbols)
            if not valid_symbols or len(symbols) != len(set(symbols)):
                reject.append(f"{group_id}:REPAIR_OPERATION_TARGET_SYMBOLS_REQUIRED")
            elif row.get("with") != "IMPLEMENT_SYMBOLS[" + ",".join(symbols) + "]":
                risk_codes.append("SERIAL_SCALAR_PATCH_RISK")
                reject.append(f"{group_id}:REPEATED_REPAIR_REPLACEMENT_MUST_BE_MACHINE_STRUCTURED")
        structured_operations_valid = bool(repair_operations) and len(reject) == operation_error_start
        if not isinstance(scalar_parameters_changed, list):
            reject.append(f"{group_id}:SCALAR_PARAMETER_DECLARATION_REQUIRED")
        elif scalar_parameters_changed:
            for row in scalar_parameters_changed:
                target=_text(row.get("target")) if isinstance(row,dict) else ""
                rhs=_text(row.get("normalized_rhs")) if isinstance(row,dict) else ""
                dependencies=_list(row.get("dependency_symbols")) if isinstance(row,dict) else []
                bounds=_dict(row.get("bounds")) if isinstance(row,dict) else {}
                observed=dict(_dict(_dict(domain.get("derived_effect_bounds")).get(target)))
                observed_dependencies=_list(observed.pop("dependency_symbols",[]))
                if (
                    not isinstance(row,dict)
                    or row.get("mode")!="DERIVED_PER_CASE"
                    or not target or not rhs or not dependencies or not bounds
                    or any(not _text(symbol) or _text(symbol) not in rhs for symbol in dependencies)
                    or re.fullmatch(r"(?:[-+]?\d+(?:\.\d+)?|[A-Z_][A-Z0-9_]*)",rhs) is not None
                    or row.get("proof_source_commit")!=domain.get("proof_source_commit")
                    or row.get("proof_source_path")!=domain.get("proof_source_path")
                    or row.get("proof_source_sha256")!=domain.get("proof_source_sha256")
                    or dependencies!=observed_dependencies or bounds!=observed
                    or row.get("proof_binding_sha256")!=_derived_parameter_binding(row,domain)
                ):
                    risk_codes.append("SERIAL_SCALAR_PATCH_RISK")
                    reject.append(f"{group_id}:DERIVED_PARAMETER_PROOF_BINDING_INVALID")
                    break
            if domain.get("provided") is not True or family.get("full_failure_family_closed_by_design") is not True:
                reject.append(f"{group_id}:DERIVED_PARAMETER_REQUIRES_FULL_DOMAIN_PROOF")
        structured_mechanism=_structured_mechanism(repair_operations)
        if not structured_mechanism or group.get("causal_mechanism")!=structured_mechanism:
            risk_codes.append("SERIAL_SCALAR_PATCH_RISK")
            reject.append(f"{group_id}:REPEATED_REPAIR_REQUIRES_MACHINE_STRUCTURED_CAUSAL_MECHANISM")
        latest_candidate = next(
            (_text(row.get("candidate")) for row in reversed(authoritative_attempts)
             if isinstance(row, dict) and len(_text(row.get("candidate"))) == 40),
            "",
        )
        if not latest_candidate or diff_contract.get("comparison_base") != latest_candidate:
            reject.append(f"{group_id}:IMPLEMENTATION_DIFF_BASE_MUST_MATCH_LATEST_FAILED_ATTEMPT")
        markers = _list(diff_contract.get("required_added_markers"))
        if not _list(diff_contract.get("causal_files")) or not markers:
            reject.append(f"{group_id}:IMPLEMENTATION_DIFF_CONTRACT_REQUIRED")
        for marker in markers:
            if (
                not isinstance(marker, dict)
                or marker.get("kind") not in {"FUNCTION_DEFINITION", "CODE_IDENTIFIER"}
                or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", _text(marker.get("value"))) is None
            ):
                reject.append(f"{group_id}:IMPLEMENTATION_DIFF_MARKER_INVALID")
        operation_symbols = {
            str(symbol) for row in repair_operations if isinstance(row, dict)
            for symbol in _list(row.get("target_symbols")) if _text(symbol)
        }
        marker_symbols = {str(marker.get("value")) for marker in markers if isinstance(marker, dict) and marker.get("value")}
        if not marker_symbols <= operation_symbols:
            reject.append(f"{group_id}:DIFF_MARKERS_MUST_BIND_TO_OPERATION_SYMBOLS")
        if domain.get("provided") is True:
            proof_mode=_text(diff_contract.get("proof_slice_mode"))
            ignored_lines=[str(value) for value in _list(diff_contract.get("proof_irrelevant_exact_lines"))]
            proof_commit=_text(diff_contract.get("proof_source_commit"))
            proof_path=_text(diff_contract.get("proof_source_path"))
            expected_digest=_text(diff_contract.get("proof_relevant_sha256"))
            try:
                proof_source=subprocess.check_output(["git","show",f"{proof_commit}:{proof_path}"],cwd=ROOT,text=True,stderr=subprocess.DEVNULL)
            except Exception:
                proof_source=""
            if (
                proof_mode!="WHOLE_FILE_EXCEPT_EXACT_METADATA_LINES"
                or proof_commit!=domain.get("proof_source_commit")
                or proof_path!=domain.get("proof_source_path")
                or proof_mode!=domain.get("proof_slice_mode")
                or ignored_lines!=domain.get("proof_irrelevant_exact_lines")
                or expected_digest!=domain.get("proof_relevant_sha256")
                or whole_file_proof_digest(proof_source,ignored_lines)!=expected_digest
            ):
                reject.append(f"{group_id}:PROOF_RELEVANT_SOURCE_BINDING_INVALID")

    product_blockers = {
        bid for bid in group_blockers
        if c0_blockers.get(bid, {}).get("classification") == "PRODUCT_DEFECT"
    }
    if product_blockers and strategy in NON_PRODUCT_STRATEGIES:
        reject.append(f"{group_id}:PRODUCT_DEFECT_REQUIRES_CAUSAL_PRODUCT_STRATEGY")

    covered = [str(row.get("blocker_id")) for row in blocker_coverage if isinstance(row, dict) and row.get("blocker_id")]
    if set(group_blockers) != set(covered) or len(covered) != len(set(covered)):
        reject.append(f"{group_id}:GROUP_BLOCKERS_REQUIRE_EXACT_SUFFICIENCY_COVERAGE")
    for row in blocker_coverage:
        if not isinstance(row, dict):
            reject.append(f"{group_id}:BLOCKER_COVERAGE_ENTRY_INVALID")
            continue
        bid = _text(row.get("blocker_id")) or "<missing>"
        diagnosed = _text(row.get("diagnosed_root_cause"))
        expected_root = _text(c0_blockers.get(bid, {}).get("root_cause"))
        if not diagnosed:
            reject.append(f"{group_id}:{bid}:DIAGNOSED_ROOT_CAUSE_REQUIRED")
        elif diagnosed != expected_root:
            reject.append(f"{group_id}:{bid}:ROOT_CAUSE_BINDING_MISMATCH")
        for key in ("why_fix_changes_cause", "expected_result", "failure_if_wrong", "cheap_disproof"):
            if not _text(row.get(key)):
                reject.append(f"{group_id}:{bid}:{key.upper()}_REQUIRED")

    exhaustive_required = family.get("observable_exhaustive_collection_required") is True
    complete_observable = family.get("complete_observable_set_collected") is True
    if exhaustive_required and not complete_observable:
        evidence_gaps.append(f"{group_id}:OBSERVABLE_FAILURE_FAMILY_NOT_EXHAUSTIVELY_COLLECTED")
    if exhaustive_required and complete_observable and not _list(family.get("collection_evidence")):
        reject.append(f"{group_id}:EXHAUSTIVE_COLLECTION_EVIDENCE_REQUIRED")
    if family.get("full_failure_family_closed_by_design") is True:
        if unknown_cases or residual_unknowns:
            reject.append(f"{group_id}:OVERCLAIMED_FAILURE_FAMILY_CLOSURE")
        if not complete_observable or not _list(family.get("collection_evidence")):
            reject.append(f"{group_id}:FULL_FAMILY_CLOSURE_REQUIRES_COMPLETE_COLLECTION")

    domain_required = domain.get("required") is True
    domain_provided = domain.get("provided") is True
    expected_cases = domain.get("expected_cases")
    covered_cases = domain.get("covered_cases")
    if domain_required and not domain_provided:
        reject.append(f"{group_id}:FULL_DOMAIN_PROOF_REQUIRED")
    if domain_provided:
        authoritative_proof = c0_domain_proofs.get(_text(family.get("id")))
        if authoritative_proof is None:
            reject.append(f"{group_id}:C0_FULL_DOMAIN_PROOF_REQUIRED")
        elif domain != authoritative_proof:
            reject.append(f"{group_id}:C0_FULL_DOMAIN_PROOF_BINDING_MISMATCH")
        if not _text(domain.get("method")):
            reject.append(f"{group_id}:FULL_DOMAIN_PROOF_METHOD_REQUIRED")
        if isinstance(expected_cases, int) and expected_cases > 0 and covered_cases != expected_cases:
            reject.append(f"{group_id}:FULL_DOMAIN_PROOF_CASE_COUNT_MISMATCH")
        proof_dimensions = _dict(domain.get("dimensions"))
        if not proof_dimensions or any(not isinstance(value, int) or value <= 0 for value in proof_dimensions.values()):
            reject.append(f"{group_id}:FULL_DOMAIN_PROOF_DIMENSIONS_REQUIRED")
        elif expected_cases != math.prod(proof_dimensions.values()):
            reject.append(f"{group_id}:FULL_DOMAIN_PROOF_DIMENSION_PRODUCT_MISMATCH")
        if not isinstance(domain.get("artifact_id"), int) or domain.get("artifact_id") <= 0:
            reject.append(f"{group_id}:FULL_DOMAIN_PROOF_ARTIFACT_REQUIRED")
        if len(_text(domain.get("artifact_sha256"))) != 64:
            reject.append(f"{group_id}:FULL_DOMAIN_PROOF_ARTIFACT_HASH_REQUIRED")
        if not _text(domain.get("verifier")):
            reject.append(f"{group_id}:FULL_DOMAIN_PROOF_VERIFIER_REQUIRED")

    # Validated machine identifiers are not a natural-language scalar proposal.
    # Free-form/near-match mechanisms and all strategy/explanation prose remain scanned.
    mechanism = _text(group.get("causal_mechanism"))
    if structured_operations_valid and group.get("causal_mechanism") == _structured_mechanism(repair_operations):
        mechanism = ""
    proposal_prose = [_text(group.get("strategy_kind")), mechanism,
                      _text(group.get("why_this_fixes_cause")),
                      _text(group.get("why_materially_different")), _text(escalation.get("reason"))]
    for operation in repair_operations:
        if isinstance(operation, dict):
            # `replaces` describes history; these fields prescribe the new repair.
            proposal_prose.extend(_text(operation.get(key)) for key in ("target", "invariant_enforced"))
            if not structured_operations_valid:
                proposal_prose.append(_text(operation.get("with")))
    # Separate explanatory fields cannot form a synthetic prose instruction.
    scalar_patch = strategy in SCALAR_STRATEGIES or any(
        SCALAR_PATCH.search(current_strategy_text) for current_strategy_text in proposal_prose)
    if same_family_attempt_count >= 2 and scalar_patch:
        risk_codes.append("SERIAL_SCALAR_PATCH_RISK")
        reject.append(f"{group_id}:REPEATED_SCALAR_FIX_REQUIRES_ARCHITECTURAL_REPAIR")

    if same_family_attempt_count >= 1 and not counterexamples:
        reject.append(f"{group_id}:COUNTEREXAMPLES_REQUIRED_AFTER_PRIOR_FAILURE")
    for row in counterexamples:
        if not isinstance(row, dict) or not _text(row.get("case")) or not _text(row.get("why_covered")):
            reject.append(f"{group_id}:COUNTEREXAMPLE_ENTRY_INVALID")

    if not preflights:
        reject.append(f"{group_id}:CHEAP_DISPROOF_PREFLIGHT_REQUIRED")
    for row in preflights:
        if not isinstance(row, dict):
            reject.append(f"{group_id}:CHEAP_DISPROOF_PREFLIGHT_ENTRY_INVALID")
            continue
        for key in ("name", "command", "falsifies"):
            if not _text(row.get(key)):
                reject.append(f"{group_id}:PREFLIGHT_{key.upper()}_REQUIRED")

    if not blast:
        reject.append(f"{group_id}:BLAST_RADIUS_HYPOTHESES_REQUIRED")

    return reject, evidence_gaps, risk_codes


def review(
    c0: dict,
    plan: dict,
    c0_sha256: str | None = None,
    threshold_snapshot: dict | None = None,
    expected_repair_intelligence_sha256: str | None = None,
) -> dict:
    reject: list[str] = []
    evidence_gaps: list[str] = []
    risk_codes: set[str] = set()
    group_reports: list[dict] = []

    c0_ready = (
        c0.get("critic_id") == "C0"
        and c0.get("non_voting") is True
        and c0.get("validated") is True
        and c0.get("diagnosis_status") == "DIAGNOSIS_COMPLETE"
        and c0.get("complete_known_blocker_set") is True
        and c0.get("builder_action") in {"REPAIR", "FREEZE_AND_VALIDATE"}
    )
    if not c0_ready:
        evidence_gaps.append("C0_COMPLETE_DIAGNOSIS_REQUIRED")
    reject.extend(repair_intelligence_errors(c0, expected_sha256=expected_repair_intelligence_sha256))

    task = c0.get("task_id")
    if plan.get("schema_version") != 1 or plan.get("task_id") != task:
        reject.append("REPAIR_PLAN_TASK_BINDING_INVALID")
    if plan.get("failed_candidate") != c0.get("failed_candidate"):
        reject.append("REPAIR_PLAN_FAILED_CANDIDATE_MISMATCH")
    if plan.get("diagnosis_id") != c0.get("diagnosis_id"):
        reject.append("REPAIR_PLAN_DIAGNOSIS_MISMATCH")
    canonical_c0 = f"Docs/Production/{task}/C0_ROOT_CAUSE.json"
    if plan.get("c0_report_path") != canonical_c0:
        reject.append("CANONICAL_C0_REPORT_PATH_REQUIRED")
    declared_c0_hash = _text(plan.get("c0_report_sha256"))
    if c0_sha256 is not None:
        if len(c0_sha256) != 64 or declared_c0_hash != c0_sha256:
            reject.append("C0_REPORT_HASH_MISMATCH")
    elif declared_c0_hash and len(declared_c0_hash) != 64:
        reject.append("C0_REPORT_HASH_INVALID")

    c0_blockers = {
        str(row.get("id")): row
        for row in _list(c0.get("blockers"))
        if isinstance(row, dict) and row.get("id")
    }
    if c0_ready and not c0_blockers:
        reject.append("COMPLETE_FAILED_C0_REQUIRES_BLOCKERS")
    c0_history_rows = _list(c0.get("failure_family_history"))
    c0_history = {
        _text(row.get("failure_family_id")): row
        for row in c0_history_rows
        if isinstance(row, dict) and _text(row.get("failure_family_id"))
    }
    if len(c0_history) != len(c0_history_rows):
        reject.append("C0_FAILURE_FAMILY_HISTORY_INVALID_OR_DUPLICATE")
    c0_domain_proof_rows = _list(c0.get("full_domain_proofs"))
    c0_domain_proofs = {
        _text(row.get("failure_family_id")): _dict(row.get("proof"))
        for row in c0_domain_proof_rows
        if isinstance(row, dict) and _text(row.get("failure_family_id")) and isinstance(row.get("proof"), dict)
    }
    if len(c0_domain_proofs) != len(c0_domain_proof_rows):
        reject.append("C0_FULL_DOMAIN_PROOFS_INVALID_OR_DUPLICATE")

    suff = _dict(plan.get("repair_sufficiency"))
    if not suff:
        reject.append("REPAIR_SUFFICIENCY_SECTION_REQUIRED")
    groups = _list(suff.get("repair_groups"))
    if not groups:
        reject.append("REPAIR_GROUPS_REQUIRED")

    assigned: list[str] = []
    group_ids: list[str] = []
    for raw_group in groups:
        if not isinstance(raw_group, dict):
            reject.append("REPAIR_GROUP_ENTRY_INVALID")
            continue
        group_id = _text(raw_group.get("group_id")) or "<missing-group>"
        group_ids.append(group_id)
        assigned.extend(str(x) for x in _list(raw_group.get("blocker_ids")) if _text(x))
        group_reject, group_gaps, group_risks = _group_review(raw_group, c0_blockers, c0_history, c0_domain_proofs)
        reject.extend(group_reject)
        evidence_gaps.extend(group_gaps)
        risk_codes.update(group_risks)
        group_reports.append({
            "group_id": group_id,
            "blocker_ids": [str(x) for x in _list(raw_group.get("blocker_ids")) if _text(x)],
            "strategy_kind": _text(raw_group.get("strategy_kind")).upper(),
            "same_family_attempt_count": raw_group.get("same_family_attempt_count"),
            "rejections": sorted(set(group_reject)),
            "evidence_gaps": sorted(set(group_gaps)),
            "risk_codes": sorted(set(group_risks)),
            "passed": not group_reject and not group_gaps,
        })

    if len(group_ids) != len(set(group_ids)):
        reject.append("REPAIR_GROUP_IDS_MUST_BE_UNIQUE")
    if len(assigned) != len(set(assigned)):
        reject.append("C0_BLOCKER_ASSIGNED_TO_MULTIPLE_REPAIR_GROUPS")
    if set(assigned) != set(c0_blockers):
        reject.append("REPAIR_GROUPS_MUST_COVER_EVERY_C0_BLOCKER_EXACTLY_ONCE")

    frontier = _dict(suff.get("evidence_frontier"))
    if not frontier:
        reject.append("EVIDENCE_FRONTIER_REQUIRED")
        frontier = {}
    authoritative_frontier = _dict(c0.get("failure_frontier"))
    if not authoritative_frontier:
        reject.append("C0_FAILURE_FRONTIER_REQUIRED")
    elif frontier != authoritative_frontier:
        reject.append("C0_FAILURE_FRONTIER_BINDING_MISMATCH")
    expected_diagnosed_through = _text(c0.get("latest_failed_candidate")) or _text(c0.get("failed_candidate"))
    diagnosed_through = _text(frontier.get("diagnosed_through_candidate"))
    if diagnosed_through != expected_diagnosed_through:
        reject.append("EVIDENCE_FRONTIER_DIAGNOSIS_BOUNDARY_MISMATCH")
    latest_observed = _text(frontier.get("latest_observed_failed_candidate"))
    if not latest_observed or len(latest_observed) != 40:
        reject.append("LATEST_OBSERVED_FAILED_CANDIDATE_REQUIRED")
    if frontier.get("complete") is not True:
        evidence_gaps.append("EVIDENCE_FRONTIER_INCOMPLETE")

    observations = _list(frontier.get("observations"))
    unclassified = _list(frontier.get("unclassified_failures"))
    unclassified_candidates = {
        _text(row.get("candidate"))
        for row in unclassified
        if isinstance(row, dict) and len(_text(row.get("candidate"))) == 40
    }
    if unclassified:
        evidence_gaps.append("POST_DIAGNOSIS_FAILURES_UNCLASSIFIED")

    allowed_frontier_dispositions = {
        "BOUND_TO_EXISTING_GROUP",
        "SUPERSEDED",
        "INFRASTRUCTURE_ONLY",
        "NEW_FAILURE_REQUIRES_C0",
    }
    observation_candidates: set[str] = set()
    for index, row in enumerate(observations):
        prefix = f"FRONTIER[{index}]"
        if not isinstance(row, dict):
            reject.append(prefix + ":ENTRY_INVALID")
            continue
        candidate = _text(row.get("candidate"))
        if len(candidate) != 40:
            reject.append(prefix + ":CANDIDATE_INVALID")
        else:
            observation_candidates.add(candidate)
        run_id = row.get("run_id")
        if not isinstance(run_id, int) or run_id <= 0:
            reject.append(prefix + ":RUN_ID_INVALID")
        disposition = _text(row.get("disposition")).upper()
        if disposition not in allowed_frontier_dispositions:
            reject.append(prefix + ":DISPOSITION_INVALID")
        if not _list(row.get("evidence")):
            reject.append(prefix + ":EVIDENCE_REQUIRED")
        if not _text(row.get("reason")):
            reject.append(prefix + ":REASON_REQUIRED")
        if disposition == "BOUND_TO_EXISTING_GROUP":
            group_id = _text(row.get("group_id"))
            if group_id not in set(group_ids):
                reject.append(prefix + ":BOUND_GROUP_UNKNOWN")
        elif disposition == "NEW_FAILURE_REQUIRES_C0":
            evidence_gaps.append(prefix + ":NEW_FAILURE_REQUIRES_C0")
    if latest_observed and latest_observed != diagnosed_through and latest_observed not in observation_candidates and latest_observed not in unclassified_candidates:
        reject.append("LATEST_POST_DIAGNOSIS_FAILURE_NOT_REPRESENTED")
    if observations:
        risk_codes.add("POST_DIAGNOSIS_FAILURES_PRESENT")

    raw_threshold_changes = suff.get("threshold_changes")
    if not isinstance(raw_threshold_changes, list):
        reject.append("THRESHOLD_CHANGES_MUST_BE_EXPLICIT_LIST")
        threshold_changes = []
    else:
        threshold_changes = raw_threshold_changes
    if threshold_changes:
        reject.append("CRITIC_OR_QUALITY_THRESHOLD_CHANGE_FORBIDDEN")
    threshold_snapshot = threshold_snapshot if threshold_snapshot is not None else canonical_threshold_snapshot()
    canonical_thresholds_preserved = _threshold_snapshot_valid(threshold_snapshot)
    if not canonical_thresholds_preserved:
        reject.append("CANONICAL_THRESHOLD_POLICY_WEAKENED")
    if suff.get("loop_risk_acknowledged") is not True:
        reject.append("LOOP_RISK_ACKNOWLEDGEMENT_REQUIRED")
    interactions = suff.get("cross_group_interactions")
    if not isinstance(interactions, list) or not interactions or any(not _text(x) for x in interactions):
        reject.append("CROSS_GROUP_INTERACTIONS_REQUIRED")

    if c0_ready and reject:
        outcome = "REPAIR_PLAN_REJECTED"
        builder_action = "REVISE_REPAIR_PLAN"
    elif evidence_gaps:
        outcome = "INSUFFICIENT_EVIDENCE"
        builder_action = "COLLECT_NAMED_EVIDENCE"
    else:
        outcome = "REPAIR_PLAN_ACCEPTED"
        builder_action = "BUILD_BOUNDED_REPAIR"

    max_attempts = max(
        [g.get("same_family_attempt_count") for g in groups if isinstance(g, dict) and isinstance(g.get("same_family_attempt_count"), int)]
        or [0]
    )
    risk_rank = 0 if max_attempts == 0 else 1
    if max_attempts >= 2 or "SERIAL_SCALAR_PATCH_RISK" in risk_codes or reject:
        risk_rank = 2

    return {
        "schema_version": 1,
        "critic_id": "C0R",
        "name": "Repair Sufficiency Critic",
        "non_voting": True,
        "approval_critic": False,
        "repair_operation_contract": {
            "repeated_family_version": 2,
            "replacement": "IMPLEMENT_SYMBOLS[exact,ordered,validated,symbols]",
            "explanatory_prose_authorizes_source_or_parameters": False,
            "scalar_prose_heuristic": "defense_in_depth",
        },
        "read_only": True,
        "task_id": task,
        "diagnosis_id": c0.get("diagnosis_id"),
        "failed_candidate": c0.get("failed_candidate"),
        "outcome": outcome,
        "builder_action": builder_action,
        "loop_risk": ["LOW", "MEDIUM", "HIGH"][risk_rank],
        "risk_codes": sorted(risk_codes),
        "rejections": sorted(set(reject)),
        "evidence_gaps": sorted(set(evidence_gaps)),
        "group_reports": group_reports,
        "group_count": len(group_reports),
        "full_blocker_coverage": set(assigned) == set(c0_blockers) and len(assigned) == len(set(assigned)) and bool(c0_blockers),
        "thresholds_unchanged": not threshold_changes and canonical_thresholds_preserved,
        "threshold_registry": threshold_snapshot,
        "may_approve_task": False,
        "may_score_gameplay": False,
        "may_lower_C1_C11_thresholds": False,
        "passed": outcome == "REPAIR_PLAN_ACCEPTED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Non-voting C0R repair-sufficiency and anti-loop critic")
    parser.add_argument("--c0", required=True)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    c0_path = Path(args.c0)
    plan_path = Path(args.plan)
    c0 = json.loads(c0_path.read_text())
    plan = json.loads(plan_path.read_text())
    c0_sha256 = _digest(c0_path)
    report = review(c0, plan, c0_sha256)
    report["input_bindings"] = {
        "c0_path": str(c0_path),
        "c0_sha256": c0_sha256,
        "plan_path": str(plan_path),
        "plan_sha256": _digest(plan_path),
    }
    rendered = json.dumps(report, indent=2) + "\n"
    print(rendered, end="")
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered)
    return 0 if report["passed"] else (3 if report["outcome"] == "INSUFFICIENT_EVIDENCE" else 2)


if __name__ == "__main__":
    raise SystemExit(main())
