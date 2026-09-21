#!/usr/bin/env python3
"""Validate T12 evidence index template or future resolved evidence index."""
from __future__ import annotations

import argparse
import json
import pathlib
import re
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[3]
DEFAULT_PATH = ROOT / "Docs" / "Production" / "T12" / "EVIDENCE_INDEX_TEMPLATE.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_FIELDS = {"artifact_id", "category", "uri", "sha256", "candidate_source", "producer", "content_verified"}
EXPECTED_CATEGORIES = {
    "authorized_changed_files",
    "static_report",
    "engine_parity_output",
    "engine_parity_comparator",
    "regression",
    "functional_sequence",
    "adaptive_readability",
    "performance_c6",
    "critic_review",
    "critic_dimension",
    "binding_resolution",
}


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def required_ref_categories(candidate: dict[str, Any], critics: dict[str, Any]) -> dict[str, set[str]]:
    refs: dict[str, set[str]] = {}

    def add(uri: Any, category: str) -> None:
        if nonempty(uri):
            refs.setdefault(uri, set()).add(category)

    source = candidate.get("exact_source", {}) if isinstance(candidate.get("exact_source"), dict) else {}
    manifest_ref = source.get("authorized_changed_file_manifest_ref")
    if nonempty(manifest_ref):
        add(manifest_ref, "authorized_changed_files")

    reports = candidate.get("static_reports", {}) if isinstance(candidate.get("static_reports"), dict) else {}
    for row in reports.values():
        if isinstance(row, dict) and nonempty(row.get("evidence_ref")):
            add(row["evidence_ref"], "static_report")

    parity = candidate.get("engine_parity", {}) if isinstance(candidate.get("engine_parity"), dict) else {}
    if nonempty(parity.get("output_ref")):
        add(parity["output_ref"], "engine_parity_output")
    if nonempty(parity.get("comparator_output_ref")):
        add(parity["comparator_output_ref"], "engine_parity_comparator")

    regression = candidate.get("regression", {}) if isinstance(candidate.get("regression"), dict) else {}
    if nonempty(regression.get("artifact_ref")):
        add(regression["artifact_ref"], "regression")

    sequences = candidate.get("functional_sequences", {}) if isinstance(candidate.get("functional_sequences"), dict) else {}
    for row in sequences.values():
        if isinstance(row, dict) and isinstance(row.get("evidence_refs"), list):
            for ref in row["evidence_refs"]:
                add(ref, "functional_sequence")

    adaptive = candidate.get("adaptive_readability", {}) if isinstance(candidate.get("adaptive_readability"), dict) else {}
    if adaptive.get("player_facing_presentation_exists") is True:
        for key in ("phone_landscape_ref", "tablet_landscape_ref", "foldable_landscape_ref", "native_3840x2160_scale1_ref"):
            if nonempty(adaptive.get(key)):
                add(adaptive[key], "adaptive_readability")

    performance = candidate.get("performance_c6", {}) if isinstance(candidate.get("performance_c6"), dict) else {}
    if nonempty(performance.get("evidence_ref")):
        add(performance["evidence_ref"], "performance_c6")

    packet_critics = candidate.get("critic_reviews", {}) if isinstance(candidate.get("critic_reviews"), dict) else {}
    for row in packet_critics.values():
        if isinstance(row, dict) and nonempty(row.get("evidence_ref")):
            add(row["evidence_ref"], "critic_review")

    critic_rows = critics.get("critics", {}) if isinstance(critics.get("critics"), dict) else {}
    for row in critic_rows.values():
        if not isinstance(row, dict):
            continue
        if nonempty(row.get("review_evidence_ref")):
            add(row["review_evidence_ref"], "critic_review")
        dimensions = row.get("dimensions")
        if isinstance(dimensions, list):
            for dimension in dimensions:
                if isinstance(dimension, dict) and isinstance(dimension.get("evidence_refs"), list):
                    for ref in dimension["evidence_refs"]:
                        add(ref, "critic_dimension")
    return refs


def required_refs(candidate: dict[str, Any], critics: dict[str, Any]) -> set[str]:
    return set(required_ref_categories(candidate, critics))


def validate_index(data: dict[str, Any], *, require_resolved: bool = False, candidate: dict[str, Any] | None = None, critics: dict[str, Any] | None = None) -> dict[str, Any]:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if data.get("task_id") != "T12":
        errors.append("task_id must be T12")
    expected_status = "EVIDENCE_INDEX_COMPLETE" if require_resolved else "PREPARATION_ONLY_EVIDENCE_INDEX_TEMPLATE"
    if data.get("status") != expected_status:
        errors.append(f"status must be {expected_status}")
    if set(data.get("allowed_categories", [])) != EXPECTED_CATEGORIES:
        errors.append("allowed_categories drifted")
    contract = data.get("entry_contract", {}) if isinstance(data.get("entry_contract"), dict) else {}
    if set(contract.get("required_fields", [])) != EXPECTED_FIELDS:
        errors.append("entry_contract required_fields drifted")

    candidate_source = data.get("candidate_source")
    if require_resolved:
        if not isinstance(candidate_source, str) or SHA40.fullmatch(candidate_source) is None:
            errors.append("resolved candidate_source must be exact lowercase 40-hex SHA")
    elif candidate_source != "<T12_CANDIDATE_SHA>":
        errors.append("template candidate_source placeholder drifted")

    entries = data.get("entries")
    if not isinstance(entries, list):
        errors.append("entries must be a list")
        entries = []
    if not require_resolved and entries != []:
        errors.append("template entries must remain empty")

    ids: set[str] = set()
    uris: set[str] = set()
    for index, row in enumerate(entries):
        if not isinstance(row, dict):
            errors.append(f"entries[{index}] must be an object")
            continue
        if set(row) != EXPECTED_FIELDS:
            errors.append(f"entries[{index}] fields mismatch")
        artifact_id = row.get("artifact_id")
        uri = row.get("uri")
        if not nonempty(artifact_id):
            errors.append(f"entries[{index}].artifact_id must be non-empty")
        elif artifact_id in ids:
            errors.append(f"duplicate artifact_id {artifact_id}")
        else:
            ids.add(artifact_id)
        if not nonempty(uri):
            errors.append(f"entries[{index}].uri must be non-empty")
        elif uri in uris:
            errors.append(f"duplicate uri {uri}")
        else:
            uris.add(uri)
        if row.get("category") not in EXPECTED_CATEGORIES:
            errors.append(f"entries[{index}] category is not allowed")
        if require_resolved:
            if not isinstance(row.get("sha256"), str) or SHA256.fullmatch(row["sha256"]) is None:
                errors.append(f"entries[{index}].sha256 must be exact lowercase SHA-256")
            if row.get("candidate_source") != candidate_source:
                errors.append(f"entries[{index}].candidate_source mismatch")
            if not nonempty(row.get("producer")):
                errors.append(f"entries[{index}].producer must be non-empty")
            if row.get("content_verified") is not True:
                errors.append(f"entries[{index}].content_verified must be true")

    missing_refs: list[str] = []
    if require_resolved:
        if candidate is None or critics is None:
            errors.append("resolved evidence index validation requires candidate and critic records")
        else:
            candidate_exact = candidate.get("exact_source", {}) if isinstance(candidate.get("exact_source"), dict) else {}
            if candidate_exact.get("candidate_source") != candidate_source:
                errors.append("evidence index candidate_source does not match candidate packet")
            if critics.get("candidate_source") != candidate_source:
                errors.append("evidence index candidate_source does not match critic records")
            required = required_refs(candidate, critics)
            missing_refs = sorted(required - uris)
            if missing_refs:
                errors.append(f"required evidence refs missing from index: {missing_refs}")

    return {
        "passed": not errors,
        "mode": "resolved" if require_resolved else "template",
        "entry_count": len(entries),
        "required_ref_count": len(required_refs(candidate, critics)) if require_resolved and candidate is not None and critics is not None else 0,
        "missing_required_ref_count": len(missing_refs),
        "errors": errors,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=str(DEFAULT_PATH.relative_to(ROOT)))
    ap.add_argument("--require-resolved", action="store_true")
    ap.add_argument("--candidate-evidence")
    ap.add_argument("--critic-records")
    args = ap.parse_args()
    data = json.loads((ROOT / args.input).read_text())
    candidate = json.loads((ROOT / args.candidate_evidence).read_text()) if args.candidate_evidence else None
    critics = json.loads((ROOT / args.critic_records).read_text()) if args.critic_records else None
    result = validate_index(data, require_resolved=args.require_resolved, candidate=candidate, critics=critics)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
