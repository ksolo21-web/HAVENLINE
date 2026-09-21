#!/usr/bin/env python3
"""Cross-check the future resolved T12 candidate evidence bundle.

This is a future pre-disposition gate, not a preparation approval. It requires a
resolved candidate-evidence packet, resolved per-dimension critic records, exact
engine-parity output, complete evidence digest index, resolved T10/T11 binding
record, and the real shipping data files. It refuses candidate/hash/provenance
mismatches across otherwise-valid artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import re
import subprocess
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[3]
TASK = ROOT / "tools" / "havenline" / "task12"
DOCS = ROOT / "Docs" / "Production" / "T12"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
WORKSTREAM_VALIDATOR = ROOT / "tools" / "havenline" / "production" / "workstream.py"


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, TASK / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


candidate_validator = load_module("t12_candidate_evidence", "validate_candidate_evidence.py")
critic_validator = load_module("t12_critic_reviews", "validate_critic_review_records.py")
parity_comparator = load_module("t12_engine_parity", "compare_engine_parity.py")
evidence_index_validator = load_module("t12_evidence_index", "validate_evidence_index.py")
progression_validator = load_module("t12_progression_contract", "validate_progression_contract.py")
binding_verifier = load_module("t12_binding_resolution", "verify_binding_resolution.py")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_candidate_guard(base: str, candidate: str, integration_head: str) -> dict[str, Any]:
    proc = subprocess.run(
        [
            sys.executable,
            str(WORKSTREAM_VALIDATOR),
            "validate-candidate",
            "T12",
            "--base",
            base,
            "--head",
            candidate,
            "--integration-head",
            integration_head,
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    try:
        result = json.loads(proc.stdout)
    except Exception:
        return {
            "passed": False,
            "errors": [f"candidate guard produced non-JSON output: {proc.stdout.strip()}"],
        }
    if proc.returncode != 0 and result.get("passed") is True:
        result = dict(result)
        result["passed"] = False
        result.setdefault("errors", []).append(f"candidate guard exited {proc.returncode}")
    return result


def validate_consistency(
    candidate: dict[str, Any],
    critic_records: dict[str, Any],
    parity_output: dict[str, Any],
    evidence_index: dict[str, Any],
    binding_resolution: dict[str, Any],
    *,
    progression_validation_result: dict[str, Any],
    binding_verification_result: dict[str, Any],
    candidate_guard_result: dict[str, Any],
    checked_out_head: str,
    levels_sha256: str,
    milestones_sha256: str,
    binding_resolution_sha256: str,
    vectors: dict[str, Any],
    parity_schema: dict[str, Any],
) -> dict[str, Any]:
    errors: list[str] = []

    candidate_result = candidate_validator.validate_packet(candidate, require_resolved=True)
    if not candidate_result["passed"]:
        errors.append("resolved candidate evidence packet failed: " + json.dumps(candidate_result["errors"]))

    critic_result = critic_validator.validate_record(critic_records, require_resolved=True)
    if not critic_result["passed"]:
        errors.append("resolved critic review records failed: " + json.dumps(critic_result["errors"]))

    parity_result = parity_comparator.compare(parity_output, vectors, parity_schema)
    if not parity_result["passed"]:
        errors.append("engine parity output failed: " + json.dumps(parity_result["errors"]))

    evidence_index_result = evidence_index_validator.validate_index(
        evidence_index,
        require_resolved=True,
        candidate=candidate,
        critics=critic_records,
    )
    if not evidence_index_result["passed"]:
        errors.append("complete evidence digest index failed: " + json.dumps(evidence_index_result["errors"]))

    if not isinstance(progression_validation_result, dict) or progression_validation_result.get("passed") is not True:
        errors.append(
            "actual split shipping progression data failed validation: "
            + json.dumps((progression_validation_result or {}).get("errors", []))
        )
    if not isinstance(binding_verification_result, dict) or binding_verification_result.get("passed") is not True:
        errors.append(
            "resolved binding record failed exact accepted-source verification: "
            + json.dumps((binding_verification_result or {}).get("errors", []))
        )

    source = candidate.get("exact_source", {}) if isinstance(candidate.get("exact_source"), dict) else {}
    candidate_sha = source.get("candidate_source")
    if not isinstance(candidate_sha, str) or SHA40.fullmatch(candidate_sha) is None:
        errors.append("candidate evidence exact source is not a valid candidate SHA")
    if checked_out_head != candidate_sha:
        errors.append(
            f"final candidate gate must run on exact candidate checkout: head={checked_out_head!r} candidate={candidate_sha!r}"
        )

    activation_base = source.get("activation_base")
    integration_head = source.get("integration_head")
    if not isinstance(candidate_guard_result, dict) or candidate_guard_result.get("passed") is not True:
        errors.append(
            "canonical T12 candidate path guard failed: "
            + json.dumps((candidate_guard_result or {}).get("errors", []))
        )
    else:
        if candidate_guard_result.get("task_id") != "T12":
            errors.append("candidate guard task_id does not match T12")
        if candidate_guard_result.get("base") != activation_base:
            errors.append("candidate guard base does not match candidate activation_base")
        if candidate_guard_result.get("head") != candidate_sha:
            errors.append("candidate guard head does not match candidate_source")
        if candidate_guard_result.get("integration_head") != integration_head:
            errors.append("candidate guard integration_head does not match candidate evidence")

    if critic_records.get("candidate_source") != candidate_sha:
        errors.append("critic records candidate_source does not match candidate evidence")
    if parity_output.get("candidate_source") != candidate_sha:
        errors.append("engine parity candidate_source does not match candidate evidence")
    if evidence_index.get("candidate_source") != candidate_sha:
        errors.append("evidence index candidate_source does not match candidate evidence")

    hashes = source.get("shipping_data_hashes", {}) if isinstance(source.get("shipping_data_hashes"), dict) else {}
    expected_hashes = {
        "progression_levels_v1_json_sha256": levels_sha256,
        "progression_milestones_v1_json_sha256": milestones_sha256,
        "binding_resolution_json_sha256": binding_resolution_sha256,
    }
    for key, actual_digest in expected_hashes.items():
        if hashes.get(key) != actual_digest:
            errors.append(f"candidate evidence {key} does not match actual file digest")

    if binding_resolution.get("task_id") != "T12" or binding_resolution.get("status") != "RESOLVED_FOR_ACTIVATION":
        errors.append("binding resolution is not a resolved T12 activation record")
    if binding_resolution.get("promotion_allowed") is not True:
        errors.append("binding resolution promotion_allowed must be true")

    deps = binding_resolution.get("dependencies")
    if not isinstance(deps, dict):
        errors.append("binding resolution dependencies must be an object")
        deps = {}
    upstream = source.get("upstream_sources", {}) if isinstance(source.get("upstream_sources"), dict) else {}
    for task in ("T10", "T11"):
        row = deps.get(task)
        if not isinstance(row, dict):
            errors.append(f"binding resolution missing {task}")
            continue
        resolved_sha = row.get("accepted_integrated_source")
        if upstream.get(task) != resolved_sha:
            errors.append(f"candidate evidence upstream {task} does not match binding resolution")
        ids = row.get("resolved_public_ids")
        if not isinstance(ids, list) or not ids:
            errors.append(f"binding resolution {task} has no resolved public IDs")

    packet_critics = candidate.get("critic_reviews")
    record_critics = critic_records.get("critics")
    if not isinstance(packet_critics, dict) or not isinstance(record_critics, dict):
        errors.append("critic records missing from candidate or critic bundle")
    else:
        minima = critic_result.get("minimum_by_critic", {})
        for critic in ("C2", "C3", "C4", "C6", "C7"):
            packet_row = packet_critics.get(critic, {})
            record_row = record_critics.get(critic, {})
            if packet_row.get("minimum_mandatory_dimension_score") != minima.get(critic):
                errors.append(f"{critic} candidate packet minimum score does not match per-dimension record")
            if packet_row.get("reviewer_runtime_id") != record_row.get("reviewer_runtime_id"):
                errors.append(f"{critic} reviewer_runtime_id mismatch between packet and critic record")
            if packet_row.get("evidence_ref") != record_row.get("review_evidence_ref"):
                errors.append(f"{critic} evidence reference mismatch between packet and critic record")
            if packet_row.get("independent") != record_row.get("independent"):
                errors.append(f"{critic} independence flag mismatch between packet and critic record")

    engine_parity = candidate.get("engine_parity") if isinstance(candidate.get("engine_parity"), dict) else {}
    if engine_parity.get("candidate_source") != candidate_sha:
        errors.append("candidate packet engine_parity candidate_source mismatch")

    performance = candidate.get("performance_c6") if isinstance(candidate.get("performance_c6"), dict) else {}
    if performance.get("candidate_source") != candidate_sha:
        errors.append("candidate packet performance_c6 candidate_source mismatch")
    if performance.get("prebuild_python_benchmark_used_as_shipping_c6") is not False:
        errors.append("prebuild benchmark may not be promoted to shipping C6")

    return {
        "passed": not errors,
        "candidate_source": candidate_sha,
        "candidate_packet_passed": candidate_result["passed"],
        "critic_records_passed": critic_result["passed"],
        "engine_parity_passed": parity_result["passed"],
        "evidence_index_passed": evidence_index_result["passed"],
        "shipping_progression_validation_passed": progression_validation_result.get("passed") is True,
        "binding_verification_passed": binding_verification_result.get("passed") is True,
        "candidate_guard_passed": candidate_guard_result.get("passed") is True,
        "exact_candidate_checkout_passed": checked_out_head == candidate_sha,
        "evidence_index_entry_count": evidence_index_result.get("entry_count"),
        "evidence_index_required_ref_count": evidence_index_result.get("required_ref_count"),
        "global_minimum_mandatory_dimension_score": critic_result.get("global_minimum_mandatory_dimension_score"),
        "score_averaging_used": False,
        "errors": errors,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate-evidence", required=True)
    ap.add_argument("--critic-records", required=True)
    ap.add_argument("--engine-parity", required=True)
    ap.add_argument("--evidence-index", required=True)
    ap.add_argument("--binding-resolution", required=True)
    ap.add_argument("--levels", required=True)
    ap.add_argument("--milestones", required=True)
    ap.add_argument("--vectors", default="Docs/Production/T12/ENGINE_TEST_VECTORS.json")
    ap.add_argument("--parity-schema", default="Docs/Production/T12/ENGINE_PARITY_OUTPUT_SCHEMA.json")
    args = ap.parse_args()

    paths = {
        "candidate": ROOT / args.candidate_evidence,
        "critics": ROOT / args.critic_records,
        "parity": ROOT / args.engine_parity,
        "evidence_index": ROOT / args.evidence_index,
        "binding": ROOT / args.binding_resolution,
        "levels": ROOT / args.levels,
        "milestones": ROOT / args.milestones,
        "vectors": ROOT / args.vectors,
        "parity_schema": ROOT / args.parity_schema,
    }
    for label, path in paths.items():
        if not path.is_file():
            raise SystemExit(f"required {label} file missing: {path}")

    candidate_data = json.loads(paths["candidate"].read_text())
    binding_bytes = paths["binding"].read_bytes()
    binding_data = json.loads(binding_bytes.decode("utf-8"))

    try:
        split_manifest = progression_validator.load_split_manifest(paths["levels"], paths["milestones"])
        progression_result = progression_validator.validate_manifest(split_manifest)
    except Exception as exc:
        progression_result = {"passed": False, "errors": [f"split shipping progression load failed: {exc}"]}

    candidate_source = (
        candidate_data.get("exact_source", {}).get("candidate_source")
        if isinstance(candidate_data.get("exact_source"), dict)
        else None
    )
    binding_result = binding_verifier.validate_resolution(
        binding_data,
        require_resolved=True,
        root=ROOT,
        activation_head=candidate_source if isinstance(candidate_source, str) else None,
    )
    checked_out_head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()

    result = validate_consistency(
        candidate_data,
        json.loads(paths["critics"].read_text()),
        json.loads(paths["parity"].read_text()),
        json.loads(paths["evidence_index"].read_text()),
        binding_data,
        progression_validation_result=progression_result,
        binding_verification_result=binding_result,
        checked_out_head=checked_out_head,
        levels_sha256=sha256_bytes(paths["levels"].read_bytes()),
        milestones_sha256=sha256_bytes(paths["milestones"].read_bytes()),
        binding_resolution_sha256=sha256_bytes(binding_bytes),
        vectors=json.loads(paths["vectors"].read_text()),
        parity_schema=json.loads(paths["parity_schema"].read_text()),
    )
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
