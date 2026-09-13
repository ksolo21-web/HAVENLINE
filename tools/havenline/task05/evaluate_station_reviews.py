#!/usr/bin/env python3
"""Resolve T05 C1/C2 judgments under the strict isolated-dissent rule."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from review_protocol import (
    FILES, GROUP_FAMILIES, build_review_prompt, build_review_schema,
    build_slice_contract, expected_request_settings, reference_family_for,
)


SOURCE_GROUPS = {
    "core-families",
    "loop-families",
    "resources-and-details",
    "shipping-device-and-tracking",
    "shipping-contexts-and-native",
}
DIMS = {
    "C1": {"reference_fidelity", "visual_language", "cross_view_consistency"},
    "C2": {"geometry_contact", "clipping_seams", "intentional_gap_integrity", "cross_view_integrity"},
}
EXPECTED_PROVIDER = "local-checksum-pinned-public-model"
EXPECTED_MODEL = "Qwen/Qwen3.5-9B"
EXPECTED_MODEL_REVISION = "3885219b6810b007914f3a7950a8d1b469d598a5"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def provenance_errors(row: dict, result: dict, folder: Path, role: str) -> list[str]:
    errors = []
    if row.get("execution_complete") is not True or row.get("error") is not None:
        return ["critic row incomplete: " + str(row.get("error") or "execution_complete is false")]
    required_equal = {
        "provider": EXPECTED_PROVIDER,
        "model": EXPECTED_MODEL,
        "model_revision": EXPECTED_MODEL_REVISION,
    }
    for key, expected in required_equal.items():
        if row.get(key) != expected or result.get(key) != expected:
            errors.append(f"invalid {key}")
    for key in ("runtime_release_sha256", "request_or_run_id"):
        if not isinstance(row.get(key), str) or not row[key]:
            errors.append(f"missing {key}")
    if row.get("runtime_release_sha256") != result.get("runtime_release_sha256"):
        errors.append("runtime release mismatch")
    for key in ("runtime_release_sha256", "input_manifest_hash", "board_sha256", "raw_output_sha256"):
        value = row.get(key)
        if not isinstance(value, str) or len(value) != 64:
            errors.append(f"invalid {key}")
    bound_files = (
        ("raw_output_path", "raw_output_sha256", "raw output"),
        ("input_manifest_path", "input_manifest_hash", "input manifest"),
        ("board_path", "board_sha256", "review board"),
    )
    input_manifest = None
    board_manifest = None
    raw_bundle = None
    for path_key, hash_key, label in bound_files:
        name = row.get(path_key)
        if not isinstance(name, str) or Path(name).name != name:
            errors.append(f"invalid {path_key}")
            continue
        path = folder / name
        if not path.is_file() or digest(path) != row.get(hash_key):
            errors.append(f"missing or changed {label}")
        elif path_key == "input_manifest_path":
            try:
                input_manifest = json.loads(path.read_text())
                row["_input_manifest"] = input_manifest
                if input_manifest.get("candidate_commit") != row.get("source") or input_manifest.get("critic_id") != role or input_manifest.get("group") != row.get("group"):
                    errors.append("input manifest identity mismatch")
                if input_manifest.get("board_sha256") != row.get("board_sha256") or input_manifest.get("pixel_manifest", {}).get("board_sha256") != row.get("board_sha256"):
                    errors.append("input manifest board mismatch")
            except Exception:
                errors.append("invalid input manifest JSON")
        elif path_key == "board_path":
            try:
                board_manifest = json.loads(path.read_text())
            except Exception:
                errors.append("invalid board manifest JSON")
        elif path_key == "raw_output_path":
            try:
                raw_bundle = json.loads(path.read_text())
            except Exception:
                errors.append("invalid raw-output bundle JSON")
    if board_manifest is not None:
        slices = board_manifest.get("slices", [])
        contract = board_manifest.get("layout_contract", {})
        if board_manifest.get("schema_version") != 3 or board_manifest.get("protocol") != "family-matched-local-scope-v3" or board_manifest.get("task") != "T05" or board_manifest.get("source") != row.get("source") or board_manifest.get("group") != row.get("group"):
            errors.append("board manifest identity mismatch")
        if not slices or contract.get("canvas_size") != [1600, 1200] or contract.get("maximum_model_input") != [1664, 1664]:
            errors.append("invalid board resolution contract")
        if contract.get("minimum_reference_display_width", 0) < 420 or contract.get("minimum_candidate_display_height", 0) < 480 or contract.get("maximum_candidates_per_board") != 2:
            errors.append("review panels are too small for strict visual grading")
        board_inputs = {}
        candidates = []
        references = set()
        reference_families = set()
        expected_scopes = {}
        bindings = board_manifest.get("reference_bindings", {})
        required_families = set(GROUP_FAMILIES.get(row.get("group"), ()))
        if set(board_manifest.get("required_reference_families", [])) != required_families or set(bindings) != required_families:
            errors.append("wrong or incomplete reference-family bindings")
        for item in slices:
            name = item.get("path")
            if not isinstance(name, str) or Path(name).name != name or not isinstance(item.get("sha256"), str):
                errors.append("invalid board slice identity")
                continue
            slice_path = folder / name
            if not slice_path.is_file() or digest(slice_path) != item["sha256"]:
                errors.append("missing or changed board slice")
            board_inputs[name] = item["sha256"]
            if item.get("canvas_size") != [1600, 1200] or item.get("reference_display_size", [0])[0] < 420:
                errors.append("board slice violates reference resolution contract")
            reference_path = item.get("reference_path")
            reference_family = item.get("reference_family")
            references.add(reference_path)
            reference_families.add(reference_family)
            if reference_family not in required_families or reference_path not in bindings.get(reference_family, []):
                errors.append("wrong-family reference on board slice")
            if item.get("unseen_assets_out_of_scope") is not True or item.get("comparison_mode") not in ("direct_family_reference", "style_feature_authority_not_scene_identity"):
                errors.append("missing local unseen-asset scope guard")
            candidate_paths = [candidate.get("path") for candidate in item.get("candidates", [])]
            if item.get("reviewed_candidate_paths") != candidate_paths or not candidate_paths:
                errors.append("board slice candidate scope mismatch")
            for candidate_path in candidate_paths:
                try:
                    if candidate_path not in FILES[row.get("group")] or reference_family_for(candidate_path) != reference_family:
                        errors.append("candidate is not paired with its protocol-declared reference family")
                except (KeyError, TypeError, ValueError):
                    errors.append("candidate path is outside the declared protocol")
            expected_scopes[name] = {
                "reference_family": reference_family,
                "reference_path": reference_path,
                "candidate_paths": candidate_paths,
                "comparison_mode": item.get("comparison_mode"),
                "unseen_assets_out_of_scope": True,
            }
            for candidate in item.get("candidates", []):
                candidates.append(candidate.get("path"))
                size = candidate.get("display_size", [0, 0])
                if len(size) != 2 or size[1] < 480:
                    errors.append("board slice violates candidate resolution contract")
        if input_manifest is None or input_manifest.get("pixel_manifest", {}).get("board_inputs") != board_inputs:
            errors.append("input manifest does not bind all board slices")
        if input_manifest is not None:
            if len(candidates) != len(set(candidates)) or set(candidates) != set(FILES.get(row.get("group"), [])):
                errors.append("board slices do not cover the exact protocol candidate set once")
            if set(candidates) != set(input_manifest.get("inputs", {})):
                errors.append("board slices do not cover every candidate exactly once")
            if references != set(input_manifest.get("pixel_manifest", {}).get("reference_inputs", {})):
                errors.append("board slices do not cover every required reference")
            if reference_families != required_families:
                errors.append("board slices do not cover every required reference family")
            pixel_manifest = input_manifest.get("pixel_manifest", {})
            if pixel_manifest.get("reference_bindings") != bindings or pixel_manifest.get("slice_scopes") != expected_scopes:
                errors.append("input manifest does not bind local slice scope")
    if raw_bundle is not None:
        if raw_bundle.get("schema_version") != 3 or raw_bundle.get("execution_complete") is not True or raw_bundle.get("source") != row.get("source") or raw_bundle.get("critic_id") != role or raw_bundle.get("group") != row.get("group") or raw_bundle.get("attempt") != row.get("attempt") or raw_bundle.get("seed") != row.get("seed"):
            errors.append("raw-output bundle identity mismatch")
        raw_slices = raw_bundle.get("slices", [])
        if raw_bundle.get("aggregate_review") != row.get("review"):
            errors.append("row review does not match bound raw-output aggregate")
        if board_manifest is None or len(raw_slices) != len(board_manifest.get("slices", [])):
            errors.append("raw-output bundle does not cover every board slice")
        board_hashes = {item.get("path"): item.get("sha256") for item in (board_manifest or {}).get("slices", [])}
        board_scopes = {item.get("path"): item for item in (board_manifest or {}).get("slices", [])}
        bound_reviews = []
        raw_board_paths = []
        bound_output_paths = []
        for slice_index, item in enumerate(raw_slices, 1):
            raw_board_paths.append(item.get("board_path"))
            if board_hashes.get(item.get("board_path")) != item.get("board_sha256"):
                errors.append("raw-output slice is not bound to its board")
            scope = board_scopes.get(item.get("board_path"), {})
            if item.get("reviewed_candidate_paths") != scope.get("reviewed_candidate_paths") or item.get("reference_family") != scope.get("reference_family") or item.get("reference_path") != scope.get("reference_path"):
                errors.append("raw-output slice scope mismatch")
            answer_review = None
            raw_review = None
            for path_key, hash_key in (("raw_output_path", "raw_output_sha256"), ("request_path", "request_sha256"), ("answer_path", "answer_sha256")):
                name = item.get(path_key)
                bound_output_paths.append(name)
                if not isinstance(name, str) or Path(name).name != name:
                    errors.append("invalid bound slice output path")
                    continue
                path = folder / name
                if not path.is_file() or digest(path) != item.get(hash_key):
                    errors.append("missing or changed bound slice output")
                elif path_key == "request_path":
                    try:
                        request = json.loads(path.read_text())
                        if request.get("source_image_path") != item.get("board_path") or request.get("source_image_sha256") != item.get("board_sha256") or request.get("original_size") != [1600, 1200] or request.get("input_size") != [1600, 1200]:
                            errors.append("model request is not bound to the full-resolution board slice")
                        expected_contract = build_slice_contract(
                            row.get("source"), role, row.get("attempt"), row.get("group"),
                            slice_index, len(raw_slices), scope,
                        )
                        expected_schema = build_review_schema(role, scope.get("reviewed_candidate_paths"), scope.get("reference_path"))
                        expected_settings = expected_request_settings(role, row.get("attempt"), row.get("seed"))
                        if request.get("request_contract") != expected_contract:
                            errors.append("model request contract does not match exact protocol slice scope")
                        if request.get("prompt") != build_review_prompt(row.get("source"), role, expected_contract):
                            errors.append("model request does not contain the exact protocol prompt")
                        if request.get("schema") != expected_schema:
                            errors.append("model request does not contain the exact dynamic response schema")
                        if request.get("request_settings") != expected_settings or request.get("model") != expected_settings["model"] or request.get("seed") != row.get("seed"):
                            errors.append("model request settings do not match claimed role, attempt, and seed")
                    except Exception:
                        errors.append("invalid bound slice request JSON")
                elif path_key == "raw_output_path":
                    try:
                        raw_response = json.loads(path.read_text())
                        choice = raw_response["choices"][0]
                        if choice.get("finish_reason") != "stop":
                            errors.append("bound model response was truncated")
                        raw_review = json.loads(choice["message"]["content"])
                    except Exception:
                        errors.append("invalid bound raw model response JSON")
                elif path_key == "answer_path":
                    try:
                        answer_review = json.loads(path.read_text())
                    except Exception:
                        errors.append("invalid bound slice answer JSON")
            if raw_review != answer_review:
                errors.append("bound raw model response does not match parsed slice answer")
            if answer_review != item.get("review"):
                errors.append("bound slice answer does not match recorded slice review")
            elif isinstance(answer_review, dict):
                if answer_review.get("reviewed_candidate_paths") != scope.get("reviewed_candidate_paths"):
                    errors.append("model did not acknowledge exact candidate paths")
                if answer_review.get("reference_path_used") != scope.get("reference_path"):
                    errors.append("model did not acknowledge exact reference path")
                if answer_review.get("unseen_assets_out_of_scope_acknowledged") is not True:
                    errors.append("model did not acknowledge unseen-asset scope")
                bound_reviews.append(answer_review)
        if len(raw_board_paths) != len(set(raw_board_paths)) or set(raw_board_paths) != set(board_hashes):
            errors.append("raw-output slices do not map one-to-one onto every board slice")
        if len(bound_output_paths) != len(set(bound_output_paths)):
            errors.append("bound raw/request/answer paths must be unique per slice")
        try:
            confidence_order = {"low": 0, "medium": 1, "high": 2}
            recomputed = {
                "observations": list(dict.fromkeys(value for part in bound_reviews for value in part["observations"])),
                "defects": list(dict.fromkeys(value for part in bound_reviews for value in part["defects"])),
                "coverage_complete": len(bound_reviews) == len(raw_slices) and all(part["coverage_complete"] is True for part in bound_reviews),
                "confidence": min((part["confidence"] for part in bound_reviews), key=confidence_order.get),
                "scores": {dimension: min(part["scores"][dimension] for part in bound_reviews) for dimension in DIMS[role]},
            }
            if recomputed != raw_bundle.get("aggregate_review"):
                errors.append("aggregate review was not recomputed conservatively from every slice")
        except Exception:
            errors.append("invalid slice reviews for conservative aggregation")
    if row.get("candidate_hash") != row.get("source") or result.get("candidate_hash") != row.get("source"):
        errors.append("candidate hash mismatch")
    if result.get("independent_runtime") is not True or result.get("request_or_run_id") in (None, ""):
        errors.append("unverified independent execution")
    if role == "C1" and row.get("reference_scope_complete") is not True:
        errors.append("family-complete authoritative reference pixels unavailable")
    return errors


def classify(row: dict, source: str, role: str, group: str) -> str:
    if row.get("source") != source or row.get("critic_id") != role or row.get("group") != group:
        return "INCOMPLETE"
    if row.get("independent_execution") is not True or row.get("execution_complete") is not True or row.get("error") is not None or row.get("_provenance_errors"):
        return "INCOMPLETE"
    review = row.get("review", {})
    scores = review.get("scores", {})
    if set(scores) != DIMS[role] or any(
        isinstance(value, bool) or not isinstance(value, (int, float))
        or not math.isfinite(value) or not 0 <= value <= 10
        for value in scores.values()
    ):
        return "INCOMPLETE"
    if not review.get("observations") or review.get("coverage_complete") is not True:
        return "INCOMPLETE"
    if review.get("confidence") not in ("medium", "high") or not isinstance(review.get("defects"), list):
        return "INCOMPLETE"
    return "PASS" if all(value > 9.0 for value in scores.values()) and review["defects"] == [] else "DISSENT"


def load_rows(root: Path | None, source: str, attempts: set[str]) -> dict[tuple[str, str], list[dict]]:
    rows: dict[tuple[str, str], list[dict]] = {}
    if root is None:
        return rows
    for path in root.rglob("review-result.json"):
        result = json.loads(path.read_text())
        role = result.get("critic_id")
        if result.get("source") != source or role not in DIMS or result.get("attempt") not in attempts:
            continue
        if result.get("competency_passed") is not True:
            for group in result.get("groups", []):
                rows.setdefault((role, group), []).append({
                    "source": source, "critic_id": role, "group": group,
                    "error": result.get("error") or "invalid critic execution",
                    "_provenance_errors": [result.get("error") or "invalid critic execution"],
                })
            continue
        for row in result.get("reviews", []):
            if row.get("error") is not None or row.get("execution_complete") is not True:
                row["_provenance_errors"] = ["critic row incomplete: " + str(row.get("error") or "execution_complete is false")]
            else:
                row["_provenance_errors"] = provenance_errors(row, result, path.parent, role)
            rows.setdefault((role, row.get("group")), []).append(row)
    return rows


def compact_vote(row: dict, state: str) -> dict:
    review = row.get("review", {})
    return {
        "state": state,
        "scores": review.get("scores", {}),
        "minimum": min(review.get("scores", {}).values()) if review.get("scores") else None,
        "defects": review.get("defects", []),
        "observations": review.get("observations", []),
        "confidence": review.get("confidence"),
        "attempt": row.get("attempt"),
        "seed": row.get("seed"),
        "request_or_run_id": row.get("request_or_run_id"),
        "raw_output_sha256": row.get("raw_output_sha256"),
        "provenance_errors": row.get("_provenance_errors", []),
    }


def validate_human_adjudication(path: Path | None, source: str, requests: list[dict], primary_rows: dict[tuple[str, str], dict]) -> tuple[list[str], str | None]:
    if not requests:
        return [], None
    if path is None or not path.is_file():
        return ["full-resolution human adjudication record is required before supplemental votes"], None
    try:
        record = json.loads(path.read_text())
    except Exception as error:
        return ["invalid human adjudication record: " + str(error)], None
    errors = []
    if record.get("candidate_source") != source or record.get("inspection_method") != "full_resolution_original_pixels":
        errors.append("human adjudication is not exact-source/full-resolution bound")
    if record.get("inspector_kind") != "human" or not isinstance(record.get("inspector"), str) or not record["inspector"].strip():
        errors.append("named human inspector is required")
    if not isinstance(record.get("inspected_at_utc"), str) or not record["inspected_at_utc"].endswith("Z"):
        errors.append("UTC human inspection timestamp is required")
    decisions = {(row.get("critic_id"), row.get("group")): row for row in record.get("decisions", [])}
    required_keys = {(row["critic_id"], row["group"]) for row in requests}
    if set(decisions) != required_keys:
        errors.append("human adjudication decision set does not exactly match isolated dissents")
    for key in required_keys & set(decisions):
        decision = decisions[key]
        if decision.get("disposition") != "not_corroborated":
            errors.append(f"human inspection corroborated or did not clear {key[0]}/{key[1]}")
        expected_inputs = primary_rows[key].get("_input_manifest", {}).get("pixel_manifest")
        if decision.get("inspected_items") != expected_inputs or not expected_inputs:
            errors.append(f"human inspection pixels do not exactly match {key[0]}/{key[1]}")
    return errors, digest(path)


def evaluate(primary_root: Path, source: str, supplemental_root: Path | None, adjudication_path: Path | None = None) -> dict:
    primary = load_rows(primary_root, source, {"primary"})
    supplemental = load_rows(supplemental_root, source, {"supplement-1", "supplement-2"})
    errors: list[str] = []
    primary_rows: dict[tuple[str, str], dict] = {}
    states: dict[tuple[str, str], str] = {}
    decisions: list[dict] = []
    requests: list[dict] = []
    quorums: list[dict] = []

    for role in sorted(DIMS):
        for group in sorted(SOURCE_GROUPS):
            key = (role, group)
            found = primary.get(key, [])
            if len(found) != 1:
                errors.append(f"expected one primary {role}/{group}, got {len(found)}")
                continue
            primary_rows[key] = found[0]
            states[key] = classify(found[0], source, role, group)
            if states[key] == "INCOMPLETE":
                details = found[0].get("_provenance_errors", [])
                suffix = ": " + "; ".join(details) if details else ""
                errors.append(f"incomplete primary {role}/{group}{suffix}")

    for group in sorted(SOURCE_GROUPS):
        c1 = states.get(("C1", group))
        c2 = states.get(("C2", group))
        if c1 is None or c2 is None or "INCOMPLETE" in (c1, c2):
            continue
        votes = {
            "C1": compact_vote(primary_rows[("C1", group)], c1),
            "C2": compact_vote(primary_rows[("C2", group)], c2),
        }
        if c1 == c2 == "PASS":
            decisions.append({"group": group, "status": "PASS", "primary": votes})
            continue
        if c1 == c2 == "DISSENT":
            decisions.append({"group": group, "status": "FAIL", "reason": "both required primary roles found defects", "primary": votes})
            continue

        dissent_role = "C1" if c1 == "DISSENT" else "C2"
        requests.append({"critic_id": dissent_role, "group": group})
        if supplemental_root is None:
            decisions.append({"group": group, "status": "ADJUDICATION_REQUIRED", "dissent_role": dissent_role, "primary": votes})
            continue
        extra = supplemental.get((dissent_role, group), [])
        if len(extra) != 2:
            errors.append(f"expected two supplemental judgments {dissent_role}/{group}, got {len(extra)}")
            continue
        extra_states = [classify(row, source, dissent_role, group) for row in extra]
        if "INCOMPLETE" in extra_states:
            details = [
                detail
                for row, state in zip(extra, extra_states)
                if state == "INCOMPLETE"
                for detail in row.get("_provenance_errors", [])
            ]
            suffix = ": " + "; ".join(details) if details else ""
            errors.append(f"incomplete supplemental judgment {dissent_role}/{group}{suffix}")
            continue
        attempts = {row.get("attempt") for row in extra}
        seeds = {row.get("seed") for row in extra}
        request_ids = {row.get("request_or_run_id") for row in extra}
        raw_hashes = {row.get("raw_output_sha256") for row in extra}
        primary_row = primary_rows[(dissent_role, group)]
        primary_inputs = primary_row.get("_input_manifest", {}).get("pixel_manifest")
        if any(row.get("_input_manifest", {}).get("pixel_manifest") != primary_inputs for row in extra) or not primary_inputs:
            errors.append(f"supplemental pixel set mismatch {dissent_role}/{group}")
            continue
        if attempts != {"supplement-1", "supplement-2"} or len(seeds) != 2 or len(request_ids) != 2 or len(raw_hashes) != 2:
            errors.append(f"supplemental freshness/identity failure {dissent_role}/{group}")
            continue
        if primary_row.get("seed") in seeds or primary_row.get("request_or_run_id") in request_ids or primary_row.get("raw_output_sha256") in raw_hashes:
            errors.append(f"supplement duplicates primary execution {dissent_role}/{group}")
            continue
        supplement_votes = [compact_vote(row, state) for row, state in zip(extra, extra_states)]
        if extra_states.count("PASS") == 2:
            decisions.append({
                "group": group, "status": "PASS_BY_QUORUM", "dissent_role": dissent_role,
                "primary": votes, "supplemental": supplement_votes,
            })
            quorums.append({
                "critic_id": dissent_role, "group": group,
                "primary": "DISSENT", "supplemental": extra_states,
                "clean_votes": 2, "total_votes": 3,
            })
        else:
            decisions.append({
                "group": group, "status": "FAIL", "reason": "same-role 2-of-3 quorum not achieved",
                "dissent_role": dissent_role, "primary": votes, "supplemental": supplement_votes,
            })

    should_validate_adjudication = supplemental_root is not None or adjudication_path is not None
    adjudication_errors, adjudication_hash = validate_human_adjudication(
        adjudication_path if should_validate_adjudication else None, source,
        requests if should_validate_adjudication else [], primary_rows,
    )
    errors.extend(adjudication_errors)
    failed = any(row["status"] == "FAIL" for row in decisions)
    pending = supplemental_root is None and bool(requests) and not failed and not errors
    passed = not errors and not failed and not pending and len(decisions) == len(SOURCE_GROUPS)
    status = "PASS_BY_QUORUM" if passed and quorums else "PASS" if passed else "ADJUDICATION_REQUIRED" if pending else "FAIL"
    return {
        "task": "T05", "source": source, "status": status, "passed": passed,
        "strict_rule": ">9.0 unrounded; no averaging; only one-role dissent may use same-role 2-of-3 quorum",
        "decisions": decisions, "adjudication_requests": requests, "quorums": quorums,
        "errors": errors, "completed_low_scores_retried": False, "score_averaging": False,
        "human_adjudication_sha256": adjudication_hash,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--primary", type=Path, required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--supplemental", type=Path)
    parser.add_argument("--adjudication", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(args.primary, args.source, args.supplemental, args.adjudication)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if report["passed"]:
        return 0
    return 3 if report["status"] == "ADJUDICATION_REQUIRED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
