#!/usr/bin/env python3
"""Initialize a future T12 candidate evidence packet from exact source material.

This tool is intentionally unusable as an approval shortcut. It fills provenance
and hashes only. Static reports, regression, functional evidence, C6, critics,
G1-G14 and defects remain pending/unset until their real evidence exists.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import pathlib
import re
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[3]
TASK = ROOT / "tools" / "havenline" / "task12"
DEFAULT_TEMPLATE = ROOT / "Docs" / "Production" / "T12" / "CANDIDATE_EVIDENCE_TEMPLATE.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")

_validator_spec = importlib.util.spec_from_file_location("t12_validator_bundle", TASK / "validator_bundle.py")
validator_bundle = importlib.util.module_from_spec(_validator_spec)
assert _validator_spec and _validator_spec.loader
_validator_spec.loader.exec_module(validator_bundle)


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def exact_sha(value: str, label: str) -> str:
    if not isinstance(value, str) or SHA40.fullmatch(value) is None:
        raise ValueError(f"{label} must be exact lowercase 40-hex commit SHA")
    return value


def initialize_packet(
    template: dict[str, Any],
    resolution: dict[str, Any],
    *,
    activation_base: str,
    candidate_source: str,
    integration_head: str,
    levels_sha256: str,
    milestones_sha256: str,
    bindings_sha256: str,
    binding_resolution_sha256: str,
    changed_file_manifest_ref: str,
    validator_source: str | None = None,
) -> dict[str, Any]:
    activation_base = exact_sha(activation_base, "activation_base")
    candidate_source = exact_sha(candidate_source, "candidate_source")
    integration_head = exact_sha(integration_head, "integration_head")
    if resolution.get("task_id") != "T12":
        raise ValueError("binding resolution task_id must be T12")
    if resolution.get("status") != "RESOLVED_FOR_ACTIVATION":
        raise ValueError("binding resolution must have status RESOLVED_FOR_ACTIVATION")
    if resolution.get("promotion_allowed") is not True:
        raise ValueError("binding resolution promotion_allowed must be true")
    deps = resolution.get("dependencies")
    if not isinstance(deps, dict):
        raise ValueError("binding resolution dependencies must be an object")
    upstream: dict[str, str] = {}
    for task in ("T10", "T11"):
        row = deps.get(task)
        if not isinstance(row, dict):
            raise ValueError(f"binding resolution missing {task}")
        upstream[task] = exact_sha(row.get("accepted_integrated_source", ""), f"{task} accepted_integrated_source")
        ids = row.get("resolved_public_ids")
        if not isinstance(ids, list) or not ids:
            raise ValueError(f"binding resolution {task} must contain resolved_public_ids")

    for label, digest in (
        ("levels_sha256", levels_sha256),
        ("milestones_sha256", milestones_sha256),
        ("bindings_sha256", bindings_sha256),
        ("binding_resolution_sha256", binding_resolution_sha256),
    ):
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ValueError(f"{label} must be exact lowercase SHA-256")
    if not isinstance(changed_file_manifest_ref, str) or not changed_file_manifest_ref.strip():
        raise ValueError("changed_file_manifest_ref must be non-empty")
    expected_validator_source = validator_bundle.bundle_digest(ROOT)
    if validator_source is None:
        validator_source = expected_validator_source
    elif validator_source != expected_validator_source:
        raise ValueError(
            f"validator_source does not match current acceptance-critical validator bundle: "
            f"expected {expected_validator_source}, got {validator_source}"
        )

    packet = copy.deepcopy(template)
    if packet.get("task_id") != "T12":
        raise ValueError("candidate evidence template task_id must be T12")
    packet["status"] = "CANDIDATE_EVIDENCE_PENDING_REVIEW"
    source = packet["exact_source"]
    source["activation_base"] = activation_base
    source["candidate_source"] = candidate_source
    source["integration_head"] = integration_head
    source["authorized_changed_file_manifest_ref"] = changed_file_manifest_ref
    source["shipping_data_hashes"] = {
        "progression_levels_v1_json_sha256": levels_sha256,
        "progression_milestones_v1_json_sha256": milestones_sha256,
        "progression_bindings_v1_json_sha256": bindings_sha256,
        "binding_resolution_json_sha256": binding_resolution_sha256,
    }
    source["upstream_sources"]["T10"] = upstream["T10"]
    source["upstream_sources"]["T11"] = upstream["T11"]
    source["validator_source"] = validator_source

    packet["engine_parity"]["candidate_source"] = candidate_source
    packet["regression"]["candidate_source"] = candidate_source
    packet["performance_c6"]["candidate_source"] = candidate_source
    for row in packet["critic_reviews"].values():
        row["candidate_source"] = candidate_source

    # Fail-safe invariant: initializer may not manufacture acceptance.
    if any(row.get("status") != "PENDING" for row in packet["static_reports"].values()):
        raise ValueError("initializer template unexpectedly contains pre-passed static report")
    if packet["engine_parity"].get("status") != "PENDING":
        raise ValueError("initializer may not pre-pass engine parity")
    if packet["regression"].get("status") != "PENDING":
        raise ValueError("initializer may not pre-pass regression")
    if packet["performance_c6"].get("status") != "PENDING" or packet["performance_c6"].get("score") is not None:
        raise ValueError("initializer may not pre-pass C6")
    if any(row.get("status") != "PENDING" or row.get("minimum_mandatory_dimension_score") is not None for row in packet["critic_reviews"].values()):
        raise ValueError("initializer may not pre-pass or pre-score critics")
    for gate, row in packet["gates"].items():
        if not isinstance(row, dict) or row.get("status") != "PENDING" or row.get("evidence_ref") != "":
            raise ValueError(f"initializer may not pre-pass or pre-evidence gate {gate}")
    if packet["defects"].get("unresolved_mandatory") != []:
        raise ValueError("initializer template must begin with empty unresolved-defect ledger")
    return packet


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", default=str(DEFAULT_TEMPLATE.relative_to(ROOT)))
    ap.add_argument("--binding-resolution", required=True)
    ap.add_argument("--activation-base", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--integration-head", required=True)
    ap.add_argument("--levels", required=True)
    ap.add_argument("--milestones", required=True)
    ap.add_argument("--bindings", required=True)
    ap.add_argument("--changed-file-manifest-ref", required=True)
    ap.add_argument(
        "--validator-source",
        help="Optional expected sha256:<digest>; when omitted it is computed from the acceptance-critical validator bundle",
    )
    ap.add_argument("--output", help="Optional output JSON path; otherwise prints packet to stdout")
    args = ap.parse_args()

    template_path = ROOT / args.template
    resolution_path = ROOT / args.binding_resolution
    levels_path = ROOT / args.levels
    milestones_path = ROOT / args.milestones
    bindings_path = ROOT / args.bindings
    for label, path in (
        ("template", template_path),
        ("binding resolution", resolution_path),
        ("levels", levels_path),
        ("milestones", milestones_path),
        ("bindings", bindings_path),
    ):
        if not path.is_file():
            raise SystemExit(f"{label} file does not exist: {path}")

    template = json.loads(template_path.read_text())
    resolution = json.loads(resolution_path.read_text())
    packet = initialize_packet(
        template,
        resolution,
        activation_base=args.activation_base,
        candidate_source=args.candidate,
        integration_head=args.integration_head,
        levels_sha256=sha256_file(levels_path),
        milestones_sha256=sha256_file(milestones_path),
        bindings_sha256=sha256_file(bindings_path),
        binding_resolution_sha256=sha256_file(resolution_path),
        changed_file_manifest_ref=args.changed_file_manifest_ref,
        validator_source=args.validator_source,
    )
    serialized = json.dumps(packet, indent=2) + "\n"
    if args.output:
        output = ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(serialized)
        print(json.dumps({"created": str(output.relative_to(ROOT)), "status": packet["status"]}, indent=2))
    else:
        print(serialized, end="")


if __name__ == "__main__":
    main()
