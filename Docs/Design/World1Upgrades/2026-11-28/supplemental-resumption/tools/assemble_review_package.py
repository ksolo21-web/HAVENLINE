#!/usr/bin/env python3
"""Assemble a local, source-bound review archive. Never performs remote writes.

Default is a dry run: only assembly-dry-run.json and its gallery preview are
written beside this script. Run --apply after root finalizes the image/review
records. Frozen design files are read, fingerprinted and never edited.

Optional root override JSON (statuses are copied verbatim, never inferred):
{
  "schema_version": 1,
  "authority": "ROOT_PUBLICATION_ASSEMBLY_OVERRIDE",
  "candidates": {
    "w1val-01-r4": {
      "sha256": "exact current PNG sha256",
      "current_status": "ROOT'S EXPLICIT CURRENT STATUS",
      "scope": "Static draft only",
      "note": "Why this is the current review draft",
      "review_report": "reviews/exact-report.json"
    }
  },
  "current_best_drafts": ["w1val-01-r4"],
  "armed_visual": {
    "status": "BLOCKED_ARMED_ILLUSTRATION",
    "note": "Unarmed architecture does not satisfy the armed requirement."
  },
  "owner_selected": false,
  "native_approved": false,
  "whole_task_complete": false
}

Example:
  python assemble_review_package.py --dry-run
  python assemble_review_package.py --apply --overrides review_status_overrides.json

The current-best list is a root display designation, not an art selection.
Without that explicit list the gallery honestly says no best draft is designated.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import sys
from typing import Any


DESIGN_REL = Path("package/Docs/Design/World1Upgrades/2026-11-28")
SUPERSEDED = {
    "01-counter-r1", "02-cooker-r1", "03-saw-r1",
    "w1up-04-r1", "w1up-05-r1", "w1up-06-r1",
}
STATUS_KEYS = ("current_status", "status", "verdict", "review_status", "disposition")
SCORE_KEYS = ("score", "architecture_scope_score", "intermediate_master_score", "overall_score", "document_score", "art_score")
NO_APPROVAL = {
    "owner_art_selection_claimed": False,
    "native_approval_claimed": False,
    "whole_task_complete": False,
}


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".assembling")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def fingerprints(path: Path) -> dict[str, Any]:
    size = path.stat().st_size
    sha = hashlib.sha256()
    blob = hashlib.sha1(b"blob " + str(size).encode("ascii") + b"\0")
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            sha.update(chunk)
            blob.update(chunk)
    return {"bytes": size, "sha256": sha.hexdigest(), "git_blob_sha1": blob.hexdigest()}


def png_dimensions(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"Invalid or incomplete PNG: {path}")
    width, height = struct.unpack(">II", header[16:24])
    if width < 1 or height < 1:
        raise ValueError(f"Invalid PNG dimensions: {path}")
    return {"format": "PNG", "width": width, "height": height}


def canonical_id(value: str) -> str:
    text = Path(value).name.lower()
    for suffix in (".png", ".json", "-invocation", "-tool-rejection"):
        if text.endswith(suffix):
            text = text[:-len(suffix)]
    return text


def frozen_snapshot(design: Path) -> dict[str, str]:
    if not design.exists():
        raise ValueError(f"Design package not found: {design}")
    result = {}
    for path in sorted(design.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(design)
        if relative.parts[0] == "review-evidence" or relative.as_posix() == "REVIEW_GALLERY.md":
            continue
        result[relative.as_posix()] = fingerprints(path)["sha256"]
    return result


def collect_sources(base: Path) -> tuple[list[tuple[Path, str, Path]], list[dict[str, str]]]:
    jobs = []
    omitted = []
    generated = base / "generated"
    for path in sorted(generated.glob("*.png")):
        group = "superseded-unselected" if canonical_id(path.name) in SUPERSEDED else "iterations"
        jobs.append((path, "generated_candidate", Path("candidates") / group / path.name))
    for path in sorted((base / "prompts").rglob("*")):
        if path.is_file():
            relative = path.relative_to(base / "prompts")
            jobs.append((path, "prompt_or_error_record", Path("prompts") / relative))
    reviews = base / "reviews"
    for path in sorted(reviews.iterdir()):
        if not path.is_file():
            if path.is_dir():
                omitted.append({"path": path.relative_to(base).as_posix(), "reason": "Nested working directory excluded; only named verifier stdout/stderr are copied."})
            continue
        if path.suffix.lower() not in {".json", ".md", ".txt", ".png"}:
            omitted.append({"path": path.relative_to(base).as_posix(), "reason": "Not a curated report/crop format."})
            continue
        if re.search(r"(?:-frozen-|-input-|prefight-input)", path.name, re.IGNORECASE) or "-S07-fetch" in path.name:
            omitted.append({"path": path.relative_to(base).as_posix(), "reason": "Duplicated frozen-input/source snapshot stays in working evidence; exact invocation records and review reports are retained."})
            continue
        kind = "crop_evidence" if path.suffix.lower() == ".png" else "review_report"
        jobs.append((path, kind, Path("reviews") / path.name))
    for folder in sorted(reviews.glob("plan-independent-work*")):
        if folder.is_dir():
            for name in ("verifier.stdout.txt", "verifier.stderr.txt"):
                path = folder / name
                if path.is_file():
                    jobs.append((path, "verifier_log", Path("verifiers") / folder.name / name))
    for path, _, _ in jobs:
        if path.is_symlink():
            raise ValueError(f"Refusing evidence symlink; use a concrete source file: {path}")
        path.resolve().relative_to(base)
    return jobs, omitted


def artifact_record(base: Path, evidence: Path, job: tuple[Path, str, Path]) -> dict[str, Any]:
    source, kind, relative = job
    info = fingerprints(source)
    target = evidence / relative
    if target.exists() and fingerprints(target)["sha256"] != info["sha256"]:
        # Keep the earlier exact bytes rather than silently replacing evidence.
        relative = relative.with_name(relative.stem + "--" + info["sha256"][:16] + relative.suffix)
        target = evidence / relative
        if target.exists() and fingerprints(target)["sha256"] != info["sha256"]:
            raise ValueError(f"Content-addressed evidence path collision: {target}")
    result = {
        "source_workspace_relative_path": source.relative_to(base).as_posix(),
        "package_relative_path": (Path("review-evidence") / relative).as_posix(),
        "kind": kind,
        **info,
    }
    if source.suffix.lower() == ".png":
        result["image"] = png_dimensions(source)
    return result


def candidate_handle(node: Any, candidates: dict[str, dict[str, Any]]) -> str | None:
    if isinstance(node, str):
        value = canonical_id(node)
        return value if value in candidates else None
    if isinstance(node, dict):
        for key in ("candidate", "candidate_id", "id", "path", "candidate_path", "image_path", "image"):
            if key in node:
                result = candidate_handle(node[key], candidates)
                if result:
                    return result
    return None


def explicit_status(node: dict[str, Any]) -> str | None:
    for key in STATUS_KEYS:
        if isinstance(node.get(key), str):
            return node[key]
    return None


def expected_image_hash(node: dict[str, Any], document: dict[str, Any], candidate: dict[str, Any]) -> str | None:
    for container in (node, node.get("candidate"), node.get("image")):
        if isinstance(container, dict):
            for key in ("image_sha256", "sha256", "candidate_sha256"):
                value = container.get(key)
                if isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{64}", value):
                    return value.lower()
    for key in ("input_files", "candidate_files_sha256", "candidate_hashes"):
        mapping = document.get(key)
        if isinstance(mapping, dict):
            for path, value in mapping.items():
                if canonical_id(path) == candidate["candidate_id"] and isinstance(value, str):
                    return value.lower()
    return None


def review_observations(base: Path, reports: list[dict[str, Any]], candidates: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    observations = []
    for report in reports:
        path = base / report["source_workspace_relative_path"]
        if path.suffix.lower() != ".json":
            continue
        document = read_json(path)
        if not isinstance(document, dict):
            continue
        nodes = []
        if isinstance(document.get("candidate"), (str, dict)):
            nodes.append(document)
        for key in ("results", "candidates", "candidate_results", "review_results", "assets", "images"):
            value = document.get(key)
            if isinstance(value, list):
                nodes.extend(item for item in value if isinstance(item, dict))
        for node in nodes:
            cid = candidate_handle(node, candidates)
            status = explicit_status(node)
            if not cid or status is None:
                continue
            expected = expected_image_hash(node, document, candidates[cid])
            score = next((node[k] for k in SCORE_KEYS if isinstance(node.get(k), (int, float)) and not isinstance(node[k], bool)), None)
            if score is None and node is document:
                score = next((document[k] for k in SCORE_KEYS if isinstance(document.get(k), (int, float)) and not isinstance(document[k], bool)), None)
            observations.append({
                "candidate_id": cid,
                "explicit_status": status,
                "explicit_score": score,
                "scope": node.get("scope", document.get("scope", document.get("review_scope", "Scope not stated in this record"))),
                "reviewer": document.get("reviewer"),
                "source_report": report["source_workspace_relative_path"],
                "package_report": report["package_relative_path"],
                "report_sha256": report["sha256"],
                "reported_image_sha256": expected,
                "image_binding": "MATCH" if expected == candidates[cid]["sha256"] else ("MISMATCH_NOT_CURRENT" if expected else "EXPLICIT_ID_NO_IMAGE_HASH_REPORTED"),
                "applies_to_current_bytes": expected is not None and expected == candidates[cid]["sha256"],
                "findings": node.get("mandatory_findings", node.get("remaining", node.get("issues", node.get("findings", document.get("findings", []))))),
            })
    return observations


def invocation_records(base: Path, artifacts: list[dict[str, Any]], candidates: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    invocations, failures = [], []
    image_cache = {}
    for item in artifacts:
        if item["kind"] != "prompt_or_error_record":
            continue
        path = base / item["source_workspace_relative_path"]
        if path.suffix.lower() != ".json":
            continue
        data = read_json(path)
        if not isinstance(data, dict):
            continue
        request = data.get("request", data)
        if isinstance(request, dict) and isinstance(request.get("prompt"), str):
            raw_id = data.get("id", data.get("candidate_id", path.stem))
            cid = canonical_id(str(raw_id))
            refs = request.get("referenced_image_paths", [])
            inputs = []
            for ref in refs:
                observed = {"exact_declared_path": ref, "observation_scope": "Bytes currently at this declared path, not independently captured tool-call bytes."}
                ref_path = Path(ref)
                if ref_path.is_file() and ref_path.suffix.lower() == ".png":
                    if ref not in image_cache:
                        image_cache[ref] = {**fingerprints(ref_path), "image": png_dimensions(ref_path)}
                    observed["observed_at_assembly"] = image_cache[ref]
                else:
                    observed["observed_at_assembly"] = None
                inputs.append(observed)
            invocations.append({
                "invocation_id": raw_id,
                "canonical_candidate_id": cid,
                "record": item["package_relative_path"],
                "source_record": item["source_workspace_relative_path"],
                "record_sha256": item["sha256"],
                "prompt_text_sha256": hashlib.sha256(request["prompt"].encode("utf-8")).hexdigest(),
                "exact_request": request,
                "declared_reference_count": len(refs),
                "input_observations": inputs,
                "explicit_record_status": data.get("status"),
                "explicit_phase": data.get("phase", data.get("scope")),
                "output_file_observed": cid in candidates,
                "output_association_basis": "Exact invocation ID matches generated filename; actual output bytes are inventoried separately." if cid in candidates else "No output file with this exact ID is present; execution/failure is not inferred.",
                "observed_output": candidates[cid]["package_relative_path"] if cid in candidates else None,
            })
        if any(key in data for key in ("error", "error_type", "reported_category")):
            ids = data.get("attempts", [data.get("candidate_id", data.get("id"))])
            failures.append({
                "record": item["package_relative_path"],
                "source_record": item["source_workspace_relative_path"],
                "record_sha256": item["sha256"],
                "candidate_ids": [canonical_id(str(x)) for x in ids if x],
                "exact_record": data,
            })
    return invocations, failures


def load_overrides(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    data = read_json(path)
    if not isinstance(data, dict) or data.get("authority") != "ROOT_PUBLICATION_ASSEMBLY_OVERRIDE":
        raise ValueError("Overrides must explicitly identify ROOT_PUBLICATION_ASSEMBLY_OVERRIDE authority.")
    for key in ("owner_selected", "owner_art_selection_claimed", "native_approved", "native_approval_claimed", "whole_task_complete"):
        if data.get(key) not in (None, False):
            raise ValueError(f"This review archive cannot assert {key}.")
        for candidate in data.get("candidates", {}).values():
            if not isinstance(candidate, dict):
                raise ValueError("Each candidate override must be an object.")
            if candidate.get(key) not in (None, False):
                raise ValueError(f"A candidate override cannot assert {key}.")
    return data


def set_candidate_states(candidates: dict[str, dict[str, Any]], observations: list[dict[str, Any]], overrides: dict[str, Any]) -> list[str]:
    by_id = {canonical_id(k): v for k, v in overrides.get("candidates", {}).items()}
    unknown = set(by_id) - set(candidates)
    if unknown:
        raise ValueError(f"Root override references missing output candidates: {sorted(unknown)}")
    warnings = []
    for cid, candidate in candidates.items():
        history = [entry for entry in observations if entry["candidate_id"] == cid]
        applicable = [entry for entry in history if entry["applies_to_current_bytes"]]
        candidate["explicit_review_history"] = history
        candidate["owner_selected"] = False
        candidate["native_approved"] = False
        if cid in SUPERSEDED:
            if cid in by_id and by_id[cid].get("current_status") != "SUPERSEDED_UNSELECTED":
                raise ValueError(f"The six retained initial studies must remain superseded/unselected: {cid}")
            candidate["current_status"] = "SUPERSEDED_UNSELECTED"
            candidate["status_authority"] = "Root's explicit publication instruction preserving the six superseded initial studies."
            candidate["status_scope"] = "Historical initial study only; current owner direction requires substantial working changes."
        elif cid in by_id:
            override = by_id[cid]
            if override.get("sha256") != candidate["sha256"]:
                raise ValueError(f"Root override is not bound to the exact current PNG hash: {cid}")
            if not isinstance(override.get("current_status"), str):
                raise ValueError(f"Root override has no explicit status: {cid}")
            candidate["current_status"] = override["current_status"]
            candidate["status_authority"] = "ROOT_EXPLICIT_OVERRIDE"
            candidate["status_scope"] = override.get("scope", "Root-designated review draft; not owner/native/whole-task approval.")
            candidate["root_override"] = override
        elif applicable:
            distinct = {entry["explicit_status"] for entry in applicable}
            if len(distinct) == 1:
                current = applicable[-1]
                candidate["current_status"] = current["explicit_status"]
                candidate["status_authority"] = current["package_report"]
                candidate["status_scope"] = current["scope"]
                candidate["explicit_review_score"] = current["explicit_score"]
            else:
                candidate["current_status"] = "CONFLICTING_EXPLICIT_REVIEW_STATUSES_ROOT_OVERRIDE_REQUIRED"
                candidate["status_authority"] = [entry["package_report"] for entry in applicable]
                candidate["status_scope"] = "No conflicting report is silently promoted over another."
                warnings.append(f"Conflicting explicit review statuses for {cid}; root override needed.")
        else:
            candidate["current_status"] = "NO_APPLICABLE_EXPLICIT_REVIEW_STATUS"
            candidate["status_authority"] = None
            candidate["status_scope"] = "Output exists; review pass or selection is not inferred."
    best = [canonical_id(x) for x in overrides.get("current_best_drafts", [])]
    if len(best) != len(set(best)) or any(cid not in candidates or cid in SUPERSEDED for cid in best):
        raise ValueError("Current-best draft list contains duplicates, missing candidates or superseded studies.")
    if any(cid not in by_id for cid in best):
        raise ValueError("Every current-best display draft needs a root status override bound to its exact PNG hash.")
    if not best:
        warnings.append("Root has not designated current best drafts; gallery will state that explicitly.")
    return warnings


def cell(value: Any) -> str:
    if value is None:
        return "—"
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False)
    return value.replace("|", "\\|").replace("\n", " ")


def gallery_text(inventory: dict[str, Any], overrides: dict[str, Any]) -> str:
    candidates = {x["candidate_id"]: x for x in inventory["actual_generation_outputs"]}
    best = [canonical_id(x) for x in overrides.get("current_best_drafts", [])]
    lines = [
        "# World 1 upgrade review gallery", "",
        "This gallery preserves generated candidates, exact invocation/error records and independent review evidence. **Every image remains unselected by the owner. No whole-task, native gameplay, animation, audio, balance or device approval is claimed.** A scoped document or architecture review is not a full defense or game approval.", "",
        "Current direction: substantial changes worth purchasing, with useful production/work/defense behavior; 10 worlds with 50 levels each. The [active design entry point](README.md) and [purchase-value plan](PURCHASE_VALUE_UPGRADE_PLAN.md) explain the proposed scope and remaining gates.", "",
        "## Current best drafts designated by root", "",
    ]
    if not best:
        lines += ["No current-best draft designation was supplied for this snapshot. The complete candidate table below retains each explicit review status without selecting a winner.", ""]
    for cid in best:
        candidate = candidates[cid]
        lines += [f"### {cid}", "", f"**Current explicit status:** {cell(candidate['current_status'])}", "", f"**Scope:** {cell(candidate['status_scope'])}", "", f"![{cid} — unselected review draft]({candidate['package_relative_path']})", ""]
        if candidate.get("root_override", {}).get("note"):
            lines += [candidate["root_override"]["note"], ""]
        lines += ["Root's display designation does not constitute owner selection.", ""]
    armed = overrides.get("armed_visual", {})
    lines += ["## Armed illustration remains a separate gate", "", f"**Status:** {cell(armed.get('status', 'BLOCKED_ARMED_ILLUSTRATION_NO_OUTPUT'))}", "", armed.get("note", "The image tool rejected the armed-tower illustration and produced no image. The owner's attack-capability requirement remains open. Any unarmed protective-architecture sheet is limited evidence and does not satisfy the armed illustration."), "", "## All generated iterations", "", "| Candidate | Dimensions | Current explicit status | Explicit scoped score | Status authority |", "|---|---:|---|---:|---|"]
    for candidate in inventory["actual_generation_outputs"]:
        dims = candidate["image"]
        authority = candidate["status_authority"]
        if isinstance(authority, str) and authority.startswith("review-evidence/"):
            authority = f"[report]({authority})"
        lines.append(f"| [{candidate['candidate_id']}]({candidate['package_relative_path']}) | {dims['width']} × {dims['height']} | {cell(candidate['current_status'])} | {cell(candidate.get('explicit_review_score'))} | {cell(authority)} |")
    lines += ["", "Scores are copied only when explicitly supplied by an applicable candidate review; a missing score stays blank. Root overrides and their exact PNG hashes are recorded in the inventory. No score threshold is used to infer a pass or selection.", "", "## Six superseded initial studies", "", "The counter, cooker, original saw and W1UP-04/05/06 studies remain **SUPERSEDED_UNSELECTED**. Their PNGs, exact prompts and existing rejection evidence are retained. They do not become selected merely because later files were added.", "", "## Invocation failures and no-output records", "", "| Affected attempt | Exact recorded status/error | Evidence |", "|---|---|---|"]
    for failure in inventory["tool_error_records"]:
        record = failure["exact_record"]
        detail = str(record.get("status", "")) + "; " + str(record.get("error", record.get("error_type", "")))
        lines.append(f"| {cell(', '.join(failure['candidate_ids']))} | {cell(detail)} | [exact record]({failure['record']}) |")
    lines += ["", "The rejected eight-reference crew attempts produced no images. The current presentation retains each full-resolution front/rear gear master and generates a separate full-resolution teamwork image from that exact master plus the work object and current resource02/04 references. Each crew stage still requires the same three views across those two files; the master alone does not complete the stage. Actual invocation records preserve earlier attempts and their original scope.", "", "## Scoped review reports", "", "| Report | Scope | Explicit verdict |", "|---|---|---|"]
    for report in inventory["scoped_report_summaries"]:
        lines.append(f"| [{cell(Path(report['source']).name)}]({report['package_path']}) | {cell(report['scope'])} | {cell(report['explicit_status'])} |")
    lines += ["", "## Evidence and remaining work", "", "[Artifact inventory](review-evidence/ARTIFACT_INVENTORY.json) binds copied files to SHA256, Git blob identity, byte count, PNG dimensions, invocation associations and explicit status provenance. [Assembly receipt](review-evidence/ASSEMBLY_RECEIPT.json) records the source snapshot and preserved frozen-file hashes.", "", "Earlier r1/r2/r3 rejection reports, crop evidence, moderation/input-limit records and verifier stdout/stderr are retained. Duplicated planning-review working checkouts are excluded. Historical review scopes and findings are not rewritten.", "", "Full appearance-level registration, remaining conditional families, actual coherent final images, armed illustration, measured upgrade value, native use states, full motion/audio and physical-device evidence remain separate requirements.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base", type=Path, default=Path(__file__).resolve().parent)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Copy curated evidence and write the gallery/inventory; no remote operations.")
    mode.add_argument("--dry-run", action="store_true", help="Default. Write only a report and gallery preview outside the package.")
    parser.add_argument("--overrides", type=Path, help="Root-authored exact-hash status/display override JSON.")
    parser.add_argument("--report-prefix", type=Path, help="Outside-package report prefix; default assembly-dry-run or assembly-applied beside script.")
    args = parser.parse_args()
    base = args.base.resolve()
    design = base / DESIGN_REL
    evidence = design / "review-evidence"
    override_path = args.overrides or (base / "review_status_overrides.json")
    if not override_path.is_absolute():
        override_path = base / override_path
    if args.overrides and not override_path.is_file():
        raise ValueError(f"Explicit root override file not found: {override_path}")
    prefix = args.report_prefix or (base / ("assembly-applied" if args.apply else "assembly-dry-run"))
    if not prefix.is_absolute():
        prefix = base / prefix
    if prefix.resolve().is_relative_to(design.resolve()):
        raise ValueError("Report prefix must remain outside the design package.")
    if evidence.is_symlink():
        raise ValueError("The review-evidence destination must not be a symlink.")
    overrides = load_overrides(override_path)
    before = frozen_snapshot(design)
    jobs, omitted = collect_sources(base)
    artifacts = [artifact_record(base, evidence, job) for job in jobs]
    candidates = {}
    for item in artifacts:
        if item["kind"] == "generated_candidate":
            cid = canonical_id(item["source_workspace_relative_path"])
            if cid in candidates:
                raise ValueError(f"Duplicate generated candidate ID: {cid}")
            candidates[cid] = {"candidate_id": cid, **item}
    missing_legacy = SUPERSEDED - candidates.keys()
    if missing_legacy:
        raise ValueError(f"Required superseded studies are missing: {sorted(missing_legacy)}")
    reports = [x for x in artifacts if x["kind"] == "review_report"]
    observations = review_observations(base, reports, candidates)
    invocations, failures = invocation_records(base, artifacts, candidates)
    warnings = set_candidate_states(candidates, observations, overrides)
    for candidate in candidates.values():
        candidate["associated_invocation_records"] = [x["record"] for x in invocations if x["canonical_candidate_id"] == candidate["candidate_id"]]
    report_summaries = []
    for report in reports:
        source = base / report["source_workspace_relative_path"]
        if source.suffix.lower() == ".json":
            data = read_json(source)
            if isinstance(data, dict) and any(k in data for k in ("scope", "review_scope", "reviewer", "verdict")):
                report_summaries.append({"source": report["source_workspace_relative_path"], "package_path": report["package_relative_path"], "scope": data.get("scope", data.get("review_scope", "Not stated")), "explicit_status": explicit_status(data), "reviewer": data.get("reviewer")})
    prior_artifacts = []
    prior_inventory = evidence / "ARTIFACT_INVENTORY.json"
    if prior_inventory.exists():
        current_paths = {x["package_relative_path"] for x in artifacts}
        for old in read_json(prior_inventory).get("artifacts", []):
            if old["package_relative_path"] not in current_paths:
                existing = design / old["package_relative_path"]
                if not existing.resolve().is_relative_to(evidence.resolve()):
                    raise ValueError(f"Prior artifact escapes the review-evidence directory: {existing}")
                if not existing.is_file() or fingerprints(existing)["sha256"] != old["sha256"]:
                    raise ValueError(f"Previously assembled evidence missing or changed: {existing}")
                prior_artifacts.append({**old, "retained_from_prior_assembly": True})
    inventory = {
        "schema_version": 1,
        "scope": "Local review evidence archive, not owner-selected art or full-task/native approval.",
        **NO_APPROVAL,
        "status_policy": "Current review status requires an explicit matching image SHA256; unbound and mismatched observations remain history only. Root exact-hash overrides take precedence. Conflicts stay conflicts. Output existence, latest filename and score thresholds never imply pass/selection.",
        "artifacts": artifacts + prior_artifacts,
        "actual_generation_outputs": list(candidates.values()),
        "generation_invocation_records": invocations,
        "tool_error_records": failures,
        "explicit_review_observations": observations,
        "scoped_report_summaries": report_summaries,
        "root_overrides": overrides,
        "omitted_working_material": omitted,
        "warnings": warnings,
    }
    gallery = gallery_text(inventory, overrides)
    receipt = {
        "schema_version": 1,
        "mode": "APPLY" if args.apply else "DRY_RUN_NO_PACKAGE_WRITES",
        "observed_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "base": str(base),
        "destination": str(evidence),
        "gallery": str(design / "REVIEW_GALLERY.md"),
        "counts": {
            "source_files": len(artifacts),
            "source_bytes": sum(x["bytes"] for x in artifacts),
            "generated_pngs": len(candidates),
            "superseded_unselected_studies": len(SUPERSEDED),
            "invocation_records": len(invocations),
            "tool_error_records": len(failures),
            "review_reports": len(reports),
            "crop_pngs": sum(x["kind"] == "crop_evidence" for x in artifacts),
            "verifier_logs": sum(x["kind"] == "verifier_log" for x in artifacts),
            "retained_prior_evidence_files": len(prior_artifacts),
        },
        "frozen_design_files_before": before,
        "root_override_path": str(override_path) if overrides else None,
        "root_override_sha256": fingerprints(override_path)["sha256"] if overrides else None,
        "warnings": warnings,
        "remote_writes": False,
        **NO_APPROVAL,
    }
    if args.apply:
        for item, job in zip(artifacts, jobs):
            source = job[0]
            target = design / item["package_relative_path"]
            if not target.resolve().is_relative_to(evidence.resolve()):
                raise ValueError(f"Evidence target escapes the archive directory: {target}")
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                temporary = target.with_name(target.name + ".assembling")
                shutil.copyfile(source, temporary)
                if fingerprints(temporary)["sha256"] != item["sha256"]:
                    temporary.unlink()
                    raise ValueError(f"Source changed during assembly: {source}")
                os.replace(temporary, target)
            elif fingerprints(target)["sha256"] != item["sha256"]:
                raise ValueError(f"Refusing to overwrite different preserved bytes: {target}")
        if frozen_snapshot(design) != before:
            raise ValueError("Frozen design files changed during assembly; archive metadata not finalized.")
        receipt["copied_artifacts_verified"] = True
        receipt["frozen_design_files_unchanged"] = True
        write_json(evidence / "ARTIFACT_INVENTORY.json", inventory)
        write_json(evidence / "ASSEMBLY_RECEIPT.json", receipt)
        write_text(design / "REVIEW_GALLERY.md", gallery)
    else:
        receipt["copied_artifacts_verified"] = None
        receipt["frozen_design_files_unchanged"] = frozen_snapshot(design) == before
        if not receipt["frozen_design_files_unchanged"]:
            raise ValueError("Frozen design files changed during the dry-run snapshot.")
    report_path = prefix.with_suffix(".json")
    preview_path = prefix.with_name(prefix.name + "-REVIEW_GALLERY.preview.md")
    write_json(report_path, {"receipt": receipt, "planned_inventory": inventory})
    write_text(preview_path, gallery)
    print(json.dumps({"mode": receipt["mode"], "counts": receipt["counts"], "frozen_design_files_unchanged": receipt["frozen_design_files_unchanged"], "report": str(report_path), "gallery_preview": str(preview_path), "warnings": warnings}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"ASSEMBLY FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)
