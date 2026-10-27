#!/usr/bin/env python3
"""Havenline permanent, fail-closed reference-versus-native-material review gate.

This tool checks actual file bytes, visual-review coverage, provenance, and
independently authored reviewer scores. It does NOT perform an independent
visual review, infer quality from image hashes, or create artificial scores.
Use a *private* evidence workspace for owner-supplied reference imagery.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import re
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[3]
POLICY = ROOT / "Docs/Production/GLOBAL_RENDERED_MATERIAL_CRITIC_POLICY.json"
HEX40 = re.compile(r"^[a-f0-9]{40}$")
HEX64 = re.compile(r"^[a-f0-9]{64}$")
ID = re.compile(r"^[A-Za-z0-9_.:-]{1,100}$")
MAX_FILE_BYTES = 150_000_000


def load_policy(path: pathlib.Path = POLICY) -> dict:
    p = json.loads(path.read_text())
    assert p["status"] == "PERMANENT_GAMEWIDE_REQUIREMENT_STAGED_FOR_INTEGRATION"
    assert p["threshold"]["reference_fidelity"] == p["threshold"]["visual_language"] == 10
    assert p["threshold"]["minimum_other_applicable_dimensions"] >= 9.5
    assert p["scope"]["all_new_or_modified_game_art"] and p["scope"]["all_existing_shipped_art_at_T70"]
    assert p["threshold"]["no_average_waiver"] and p["evidence"]["both_separately_executed_C1_and_C2_reviews"]
    return p


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rooted(root: pathlib.Path, rel: str) -> pathlib.Path:
    if not isinstance(rel, str) or not rel or pathlib.PurePosixPath(rel).is_absolute():
        raise ValueError("Missing/absolute proof path")
    path = pathlib.PurePosixPath(rel)
    if path.as_posix() != rel or any(part in ("", ".", "..") for part in path.parts):
        raise ValueError("Invalid source proof path " + rel)
    full = (root / rel).resolve()
    if not full.is_relative_to(root.resolve()):
        raise ValueError("Escaping evidence root " + rel)
    return full


def verified_file(root: pathlib.Path, obj: dict, label: str, errors: list[str]) -> pathlib.Path | None:
    try:
        if not isinstance(obj, dict) or not HEX64.fullmatch(str(obj.get("sha256") or "")):
            raise ValueError("required file hash missing")
        full = rooted(root, obj.get("path"))
        if not full.is_file() or not 0 < full.stat().st_size <= MAX_FILE_BYTES:
            raise ValueError("missing, empty or oversized file")
        if sha256(full) != obj["sha256"]:
            raise ValueError("actual bytes do not match declared SHA-256")
        return full
    except (ValueError, OSError, TypeError) as e:
        errors.append(label + ": " + str(e))
        return None


def image_check(path: pathlib.Path, min_resolution: list[int] | None, label: str,
                errors: list[str], godot: bool) -> None:
    try:
        from PIL import Image
        with Image.open(path) as im:
            # Reference images may really be JPEG-encoded despite a .png name.
            if im.format not in (("PNG",) if godot else ("PNG", "JPEG", "WEBP")):
                raise ValueError("actual image byte format not accepted")
            if im.width <= 0 or im.height <= 0:
                raise ValueError("empty image")
            if min_resolution and (im.width < min_resolution[0] or im.height < min_resolution[1]):
                raise ValueError("actual Godot image below required resolution")
            im.verify()
    except (OSError, ValueError, ImportError) as e:
        errors.append(label + ": " + str(e))


def _scores(review: dict, policy: dict, label: str, errors: list[str]) -> None:
    required = set(policy["required_dimensions"])
    scores = review.get("scores") or {}
    if not isinstance(scores, dict) or set(scores) != required:
        errors.append(label + ": missing or extra mandatory score dimensions")
        return
    for key in policy["required_dimensions"]:
        score = scores[key]
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score):
            errors.append(label + ": invalid numeric score " + key)
            continue
        minimum = policy["threshold"].get(key, policy["threshold"]["minimum_other_applicable_dimensions"])
        if score < minimum or score > 10:
            errors.append(label + ": " + key + " below " + str(minimum) + "/10 or out of range")


def validate(manifest: dict, evidence_root: pathlib.Path, mode: str = "review",
             expected_paths: list[str] | None = None, policy: dict | None = None) -> dict:
    """Modes: evidence verifies immutable inputs; review additionally requires C1+C2;
    release also requires real shipping-scene captures and a complete T70 census.
    """
    p = policy or load_policy()
    root = evidence_root.resolve()
    errors: list[str] = []
    if mode not in ("evidence", "review", "release"):
        raise ValueError("Unknown mode")
    if manifest.get("schema_version") != 1:
        errors.append("schema version must be 1")
    task_id = manifest.get("task_id")
    candidate = manifest.get("candidate_commit")
    builder_run = manifest.get("builder_run_id")
    if not isinstance(task_id, str) or not re.fullmatch(r"T[0-9]{2}", task_id):
        errors.append("task id invalid")
    if not isinstance(candidate, str) or not HEX40.fullmatch(candidate):
        errors.append("candidate exact 40-hex commit required")
    if type(builder_run) is not int or builder_run <= 0:
        errors.append("builder run id required")
    assets = manifest.get("assets")
    if not isinstance(assets, list) or not assets:
        errors.append("all asset material coverage requires non-empty assets array")
        assets = []
    if len(assets) > 5000:
        errors.append("asset inventory unreasonably large")
    asset_ids = []
    covered_paths = []
    for asset in assets[:5000]:
        if not isinstance(asset, dict):
            errors.append("invalid asset row")
            continue
        aid = asset.get("asset_id")
        if not isinstance(aid, str) or not ID.fullmatch(aid):
            errors.append("invalid asset id")
            continue
        asset_ids.append(aid)
        label = "asset " + aid
        profile = asset.get("profile")
        specification = p["evidence_profiles"].get(profile)
        if not specification:
            errors.append(label + ": unsupported material/asset profile")
            continue
        source = asset.get("asset_source")
        source_path = verified_file(root, source, label + " source", errors)
        if source_path and isinstance(source, dict):
            target = source.get("shipping_path")
            if not isinstance(target, str) or not target.startswith("HavenlineGodot/") or ".." in pathlib.PurePosixPath(target).parts:
                errors.append(label + ": no precise tracked shipping path")
            else:
                covered_paths.append(target)
        references = asset.get("references")
        if not isinstance(references, list) or not references:
            errors.append(label + ": no authoritative reference pixels")
            references = []
        ref_sha: set[str] = set()
        for i, item in enumerate(references):
            fp = verified_file(root, item, label + " ref" + str(i), errors)
            if fp:
                ref_sha.add(item["sha256"])
                image_check(fp, None, label + " reference" + str(i), errors, False)
            if not isinstance(item, dict) or item.get("authority") not in ("owner_original", "locked_reference_frame"):
                errors.append(label + ": reference is not owner/locked authority")
        if len(ref_sha) != len(references):
            errors.append(label + ": reference source identity missing/duplicate")
        captures = asset.get("captures")
        if not isinstance(captures, list):
            errors.append(label + ": camera evidence must be a list")
            captures = []
        wanted = set(specification["views"])
        got = [x.get("view") for x in captures if isinstance(x, dict)]
        if set(got) != wanted or len(got) != len(wanted):
            errors.append(label + ": missing, duplicate or unexpected actual Godot views")
        captured_files = {}
        for shot in captures:
            if not isinstance(shot, dict):
                continue
            view = shot.get("view")
            path = verified_file(root, shot, label + " screenshot " + str(view), errors)
            if path:
                image_check(path, specification["minimum_resolution"],
                            label + " 4K screenshot " + str(view), errors, True)
                captured_files[view] = shot["sha256"]
            if shot.get("engine") != "Godot" or shot.get("candidate_commit") != candidate:
                errors.append(label + ": screenshot engine/commit not source-bound")
            if type(shot.get("render_run_id")) is not int or shot["render_run_id"] <= 0:
                errors.append(label + ": Godot native render run id missing")
            if mode == "release" and shot.get("shipping_scene_loaded") is not True:
                errors.append(label + ": isolated Godot view cannot establish shipping visual approval")
        if len(set(captured_files.values())) != len(wanted):
            errors.append(label + ": distinct actual screenshot hashes required")
        if specification["motion_required"]:
            motion = asset.get("motion")
            verified_file(root, motion, label + " mandatory motion footage", errors)
            if not isinstance(motion, dict) or motion.get("from_native_Godot") is not True:
                errors.append(label + ": actual native Godot motion provenance missing")
        materials = asset.get("materials")
        if not isinstance(materials, list) or not materials:
            errors.append(label + ": zero actual material slots/variants")
            materials = []
        mids = []
        for surface in materials:
            if not isinstance(surface, dict):
                errors.append(label + ": invalid surface row")
                continue
            mid = surface.get("material_id")
            if not isinstance(mid, str) or not ID.fullmatch(mid):
                errors.append(label + ": invalid material ID")
                continue
            mids.append(mid)
            views = surface.get("visible_in_views")
            if not isinstance(views, list) or not views or not set(views).issubset(wanted):
                errors.append(label + ": material slot not visually inspected in actual renderer: " + mid)
            if "in_game_use" in wanted and "in_game_use" not in views and mode == "release":
                errors.append(label + ": material lacks gameplay-frame coverage: " + mid)
            if surface.get("reference_shas") != sorted(ref_sha):
                errors.append(label + ": material " + mid + " not bound to all authoritative reference bytes")
        if len(mids) != len(set(mids)):
            errors.append(label + ": repeated material IDs")
        alignment = asset.get("reference_camera")
        if not isinstance(alignment, dict) or alignment.get("reference_visible_geometry_calibrated") is not True:
            errors.append(label + ": original reference camera/perspective not calibrated")
        elif not isinstance(alignment.get("justification"), str) or len(alignment["justification"].strip()) < 40:
            errors.append(label + ": insufficient source-camera alignment justification")
        if asset.get("known_visible_reference_mismatches") != []:
            errors.append(label + ": unresolved visible reference mismatch or missing explicit empty list")
    if len(asset_ids) != len(set(asset_ids)):
        errors.append("duplicate asset identifiers")
    if len(covered_paths) != len(set(covered_paths)):
        errors.append("duplicate tracked source path; split variants explicitly with unique source inventory")
    expected_paths = expected_paths if expected_paths is not None else manifest.get("changed_visual_paths")
    if not isinstance(expected_paths, list) or sorted(covered_paths) != sorted(expected_paths):
        errors.append("material source path coverage differs from exact changed/release visual census")
    if task_id == "T70" or mode == "release":
        if manifest.get("full_shipped_material_census") is not True:
            errors.append("T70/release requires actual full shipped material census")
        if not manifest.get("shipping_scenes_inspected"):
            errors.append("release requires actual shipping scene material usage inspection")
    if mode in ("review", "release"):
        reviews = manifest.get("reviews")
        if not isinstance(reviews, list):
            reviews = []
        ids = [r.get("critic_id") for r in reviews if isinstance(r, dict)]
        if sorted(ids) != ["C1", "C2"] or len(reviews) != 2:
            errors.append("real separate C1 and C2 reviewer records both required")
        runids = []
        for rec in reviews:
            if not isinstance(rec, dict):
                continue
            critic = rec.get("critic_id")
            label = "critic " + str(critic)
            if rec.get("independent_of_builder") is not True:
                errors.append(label + ": self-review is forbidden")
            runid = rec.get("independent_run_id")
            if type(runid) is not int or runid <= 0 or runid == builder_run:
                errors.append(label + ": separate independent run required")
            else:
                runids.append(runid)
            if not all(isinstance(rec.get(k), str) and len(rec[k]) >= 3
                       for k in ("provider", "model", "reviewer_id")):
                errors.append(label + ": reviewer model/provider/identity incomplete")
            raw = verified_file(root, rec.get("raw_output"), label + " raw score output", errors)
            if not raw:
                continue
            try:
                payload = json.loads(raw.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, ValueError) as e:
                errors.append(label + ": unreadable raw critic JSON: " + str(e))
                continue
            if (payload.get("critic_id") != critic or payload.get("candidate_commit") != candidate
                    or payload.get("task_id") != task_id):
                errors.append(label + ": raw reviewer source identity mismatch")
            entries = payload.get("assets")
            if not isinstance(entries, list) or len(entries) != len(asset_ids):
                errors.append(label + ": incomplete per-asset review census")
                continue
            seen = []
            for item in entries:
                if not isinstance(item, dict):
                    errors.append(label + ": invalid per-asset reviewer row")
                    continue
                aid = item.get("asset_id")
                seen.append(aid)
                asset = next((z for z in assets if isinstance(z, dict) and z.get("asset_id") == aid), None)
                if not asset:
                    errors.append(label + ": unknown reviewed asset " + str(aid))
                    continue
                l = label + " asset " + aid
                _scores(item, p, l, errors)
                if item.get("defects") != []:
                    errors.append(l + ": unresolved reviewer defect")
                observations = item.get("observations")
                if not isinstance(observations, list) or len(observations) < 3 or any(
                        not isinstance(x, str) or len(x.strip()) < 20 for x in observations):
                    errors.append(l + ": missing substantive visual observations")
                if item.get("confidence") != "high":
                    errors.append(l + ": confidence is not high")
                coverage = item.get("coverage") or {}
                if set(coverage.get("material_ids", [])) != {
                        m["material_id"] for m in asset.get("materials", []) if isinstance(m, dict)}:
                    errors.append(l + ": not all authored material slots actually judged")
                if set(coverage.get("views", [])) != set(p["evidence_profiles"][asset["profile"]]["views"]):
                    errors.append(l + ": critic did not inspect all actual Godot views")
                if sorted(coverage.get("reference_shas", [])) != sorted(
                        r["sha256"] for r in asset.get("references", []) if isinstance(r, dict)):
                    errors.append(l + ": critic never actually saw all source reference bytes")
            if len(seen) != len(set(seen)) or set(seen) != set(asset_ids):
                errors.append(label + ": duplicate/missing/unknown reviewed asset IDs")
        if len(runids) != 2 or len(set(runids)) != 2:
            errors.append("C1 and C2 must execute as separate independent runs")
    passed = not errors
    return {
        "schema_version": 1,
        "status": "SOURCE_BOUND_MATERIAL_CRITIC_PASS_NOT_USER_APPROVAL" if passed and mode != "evidence"
                  else "SOURCE_BOUND_PRIVATE_EVIDENCE_COMPLETE_NOT_YET_REVIEWED" if passed
                  else "RENDERED_MATERIAL_CRITIC_BLOCKED",
        "passed": passed, "mode": mode, "task_id": task_id, "candidate_commit": candidate,
        "asset_ids": asset_ids, "material_count": sum(len(a.get("materials", [])) for a in assets if isinstance(a, dict)),
        "source_paths_covered": covered_paths,
        "critic_ids_verified": ["C1", "C2"] if passed and mode != "evidence" else [],
        "real_visual_review_completed": passed and mode != "evidence",
        "reference_fidelity_10_required": True, "other_dimensions_minimum_9_5": True,
        "user_approved": False, "physical_android_verified": False,
        "errors": errors
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--root", required=True, help="Private evidence root, not public repository")
    parser.add_argument("--mode", choices=["evidence", "review", "release"], default="review")
    parser.add_argument("--expected-visual-paths-json")
    parser.add_argument("--report")
    a = parser.parse_args()
    expected = json.loads(pathlib.Path(a.expected_visual_paths_json).read_text()) if a.expected_visual_paths_json else None
    report = validate(json.loads(pathlib.Path(a.manifest).read_text()), pathlib.Path(a.root), a.mode, expected)
    if a.report:
        pathlib.Path(a.report).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 2)


if __name__ == "__main__":
    main()
