#!/usr/bin/env python3
"""Fail-closed visual/material evidence gate for the Havenline cooker.

PREPARE creates a private reviewer package from exact owner PNG, the *actual*
candidate GLB and Godot PNG bytes. VALIDATE checks a separately obtained
reviewer's scored raw decision. It never generates its own visual score.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import pathlib
import re
import shutil
import struct
import sys
import zipfile

from PIL import Image, ImageDraw, ImageStat

ROOT = pathlib.Path(__file__).resolve().parents[3]
POLICY = ROOT / "Docs/Production/T05/COOKER_REFERENCE_RENDER_MATERIAL_CRITIC_POLICY.json"
SHA = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
MAX_ZIP_BYTES = 130 * 1024 * 1024
MAX_FRAME_BYTES = 30 * 1024 * 1024


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def filehash(path: pathlib.Path) -> str:
    return digest(path.read_bytes())


def load_policy() -> dict:
    p = json.loads(POLICY.read_text())
    if p["reference"]["sha256"] != "729393f7980d8bd70906a7e4de04c3c6b21de5dfe4deb3d98ca7005b54d61635":
        raise ValueError("Canonical owner reference hash drift")
    if p["scores_required"]["reference_fidelity"] != 10 or p["scores_required"]["visual_language"] != 10:
        raise ValueError("Exact reference-style score requirement weakened")
    if min(p["scores_required"].values()) < 9.5:
        raise ValueError("Mandatory 9.5 visual floor weakened")
    return p


def exact_png(raw: bytes, dimensions: tuple[int, int], label: str) -> Image.Image:
    if len(raw) < 100 or len(raw) > MAX_FRAME_BYTES:
        raise ValueError(label + " image byte size invalid")
    with Image.open(io.BytesIO(raw)) as im:
        if im.format != "PNG" or im.size != dimensions or im.mode not in ("RGB", "RGBA"):
            raise ValueError(label + " must be original-size RGB(A) PNG")
        im.load()
        return im.convert("RGB")


def glb_inventory(raw: bytes, names: list[str]) -> dict:
    if len(raw) < 28 or raw[:4] != b"glTF" or struct.unpack_from("<I", raw, 4)[0] != 2:
        raise ValueError("Invalid candidate GLB header")
    if struct.unpack_from("<I", raw, 8)[0] != len(raw):
        raise ValueError("GLB length mismatch")
    size, typ = struct.unpack_from("<I4s", raw, 12)
    if typ != b"JSON" or size < 5 or 20 + size + 8 > len(raw):
        raise ValueError("Missing GLB JSON chunk")
    doc = json.loads(raw[20:20 + size])
    start = 20 + size
    binary_size, binary_type = struct.unpack_from("<I4s", raw, start)
    if binary_type != bytes((66, 73, 78, 0)) or start + 8 + binary_size > len(raw):
        raise ValueError("Missing embedded GLB binary chunk")
    binary = raw[start + 8:start + 8 + binary_size]
    materials = doc.get("materials") or []
    if len(materials) != len(names) or {m.get("name") for m in materials} != set(names):
        raise ValueError("Nine authored material identities not preserved")
    primitives = [p for mesh in doc.get("meshes", []) for p in mesh.get("primitives", [])]
    if {p.get("material") for p in primitives} != set(range(len(materials))):
        raise ValueError("Not all nine materials used on actual GLB geometry")
    inventory = []
    for index, mat in enumerate(materials):
        pbr = mat.get("pbrMetallicRoughness") or {}
        if not isinstance(pbr.get("metallicFactor", 1), (int, float)):
            raise ValueError("Material has invalid metallic factor")
        if not isinstance(pbr.get("roughnessFactor", 1), (int, float)):
            raise ValueError("Material has invalid roughness factor")
        row = {"name": mat["name"], "material_index": index,
               "roughness": pbr.get("roughnessFactor", 1),
               "metallic": pbr.get("metallicFactor", 1),
               "base_color_texture": None}
        texture = pbr.get("baseColorTexture")
        if texture is not None:
            if texture.get("texCoord", 0) != 0:
                raise ValueError("Source base color UV0 remapped for " + mat["name"])
            tex = doc["textures"][texture["index"]]
            embedded = doc["images"][tex["source"]]
            view = doc["bufferViews"][embedded["bufferView"]]
            begin = view.get("byteOffset", 0)
            end = begin + view["byteLength"]
            if view.get("buffer", 0) != 0 or begin < 0 or end > len(binary):
                raise ValueError("Embedded image buffer out of bounds")
            raw_image = binary[begin:end]
            with Image.open(io.BytesIO(raw_image)) as img:
                img.load()
                if not img.size[0] or not img.size[1]:
                    raise ValueError("Empty base color texture")
                image_type = img.format
                wh = list(img.size)
            row["base_color_texture"] = {
                "sha256": digest(raw_image), "format": image_type,
                "pixels": wh, "uv_channel": 0
            }
        inventory.append(row)
    must_have = {"HL_red", "HL_snow", "HL_wood", "HL_wood_light", "HL_blue", "HL_metal"}
    if any(x["base_color_texture"] is None for x in inventory if x["name"] in must_have):
        raise ValueError("Source-critical materials lack real exported base color textures")
    return {"material_count": len(materials), "primitive_count": len(primitives),
            "materials": inventory}


def make_board(reference: Image.Image, frames: list[tuple[str, Image.Image]], out: pathlib.Path) -> None:
    # Comparisons are explicitly *not* camera-calibrated. Never imply that
    # side-by-side compositing itself proves source fidelity.
    w, h = 720, 480
    board = Image.new("RGB", (3 * w, 2 * h + 55), (21, 31, 42))
    draw = ImageDraw.Draw(board)
    draw.text((18, 14), "T05 PRIVATE CRITIC INPUT: ORIGINAL OWNER ART / REAL GODOT 4K / UNALIGNED CAMERAS", fill="white")
    def paste(cell: int, name: str, source: Image.Image) -> None:
        x, y = (cell % 3) * w, (cell // 3) * h + 55
        copy = source.copy()
        copy.thumbnail((w - 20, h - 42), Image.Resampling.LANCZOS)
        board.paste(copy, (x + (w - copy.width) // 2, y + 32 + (h - 42 - copy.height) // 2))
        draw.text((x + 13, y + 9), name, fill="white")
    paste(0, "VERIFIED OWNER REFERENCE 18567.png (NOT A GAME FRAME)", reference)
    for idx, (view, frame) in enumerate(frames, start=1):
        paste(idx, "REAL GODOT 3840x2160: " + view, frame)
    board.save(out, format="PNG", optimize=True)


def prepare(a: argparse.Namespace) -> dict:
    policy = load_policy()
    reference_path = pathlib.Path(a.reference)
    glb_path = pathlib.Path(a.glb)
    zip_path = pathlib.Path(a.godot_zip)
    out = pathlib.Path(a.out)
    if not COMMIT.fullmatch(a.builder_commit) or not a.godot_run.isdigit():
        raise ValueError("Exact 40-char builder commit and numeric Godot run required")
    if not reference_path.is_file() or not glb_path.is_file() or not zip_path.is_file():
        raise ValueError("All three source files required")
    if zip_path.stat().st_size > MAX_ZIP_BYTES:
        raise ValueError("Godot capture archive excessively large")
    reference_bytes = reference_path.read_bytes()
    if digest(reference_bytes) != policy["reference"]["sha256"]:
        raise ValueError("Wrong authoritative owner image")
    reference = exact_png(reference_bytes, tuple(policy["reference"]["pixels"]), "owner")
    glb_bytes = glb_path.read_bytes()
    materials = glb_inventory(glb_bytes, policy["required_material_names"])
    frames = []
    hashes = {}
    raw_frames = {}
    with zipfile.ZipFile(zip_path) as z:
        # Read only fixed known paths; never bulk-extract an arbitrary archive.
        if len(z.namelist()) > 30 or len(set(z.namelist())) != len(z.namelist()):
            raise ValueError("Unexpected/duplicate capture archive entries")
        for entry in z.infolist():
            p = pathlib.PurePosixPath(entry.filename)
            if entry.is_dir():
                continue
            if p.is_absolute() or ".." in p.parts or entry.file_size > MAX_FRAME_BYTES:
                raise ValueError("Unsafe or oversized archive member")
        native = json.loads(z.read("native-4k-byte-audit.json"))
        engine = json.loads(z.read("screenshots/isolated-godot-report.json"))
        if native.get("candidate_glb_sha256") != digest(glb_bytes):
            raise ValueError("Godot evidence not tied to exact candidate GLB")
        if native.get("source_reference_sha256") != digest(reference_bytes):
            raise ValueError("Godot evidence not bound to exact owner reference")
        if native.get("resolution") != policy["required_godot_pixels"]:
            raise ValueError("Wrong Godot output size")
        if engine.get("godot_mesh_count") != 9 or engine.get("shipping_main_loaded") is not False:
            raise ValueError("Invalid isolated native Godot proof")
        if engine.get("status") != "ISOLATED_GODOT_IMPORT_ONLY_NOT_SHIPPING_QA":
            raise ValueError("Expected actual isolated Godot provenance")
        capture_map = {c.get("view"): c.get("file") for c in engine.get("captures", [])}
        native_map = {c.get("view"): c.get("sha256") for c in native.get("frames", [])}
        if set(capture_map) != set(policy["required_godot_views"]) or set(native_map) != set(capture_map):
            raise ValueError("Five distinct mandatory cameras missing")
        for view in policy["required_godot_views"]:
            filename = "screenshots/isolated-godot-" + view + ".png"
            if capture_map[view] != pathlib.PurePosixPath(filename).name:
                raise ValueError("Capture filename does not match declared view")
            raw = z.read(filename)
            if digest(raw) != native_map[view]:
                raise ValueError("Godot frame SHA-256 mismatch: " + view)
            im = exact_png(raw, tuple(policy["required_godot_pixels"]), view)
            if max(ImageStat.Stat(im.resize((160, 90))).stddev) < 3.0:
                raise ValueError("Blank or trivial Godot render " + view)
            frames.append((view, im))
            hashes[view] = native_map[view]
            raw_frames[view] = raw
    if len(set(hashes.values())) != 5:
        raise ValueError("Repeated supposedly independent camera image")
    if out.exists() and any(out.iterdir()):
        raise ValueError("Refuse overwriting a preexisting evidence package")
    out.mkdir(parents=True, exist_ok=True)
    (out / "reference.png").write_bytes(reference_bytes)
    shutil.copyfile(glb_path, out / "candidate.glb")
    for name, im in frames:
        # Preserve byte-for-byte original native evidence, not a new PIL PNG.
        (out / ("godot-" + name + ".png")).write_bytes(raw_frames[name])
    make_board(reference, frames, out / "review-board.png")
    evidence = {
        "status": "PRIVATE_SOURCE_BOUND_CRITIC_EVIDENCE_NOT_REVIEWED",
        "schema_version": 1, "critic_id": policy["critic_id"],
        "owner_source_sha256": digest(reference_bytes),
        "candidate_glb_sha256": digest(glb_bytes),
        "source_builder_commit": a.builder_commit,
        "source_godot_run_id": a.godot_run,
        "capture_archive_sha256": filehash(zip_path),
        "image_shas": {name: filehash(out / ("godot-" + name + ".png")) for name in hashes},
        "raw_godot_shas_verified_without_recompression": True,
        "private_reference_sha256": filehash(out / "reference.png"),
        "review_board_sha256": filehash(out / "review-board.png"),
        "material_inventory": materials,
        "godot_renderer": engine.get("renderer"),
        "godot_resolution": policy["required_godot_pixels"],
        "reference_view_camera_calibrated": False,
        "source_camera_alignment_required": True,
        "independent_critic_executed": False,
        "critic_score": None,
        "owner_approved": False, "actual_shipping_scene_tested": False,
        "physical_android_tested": False,
        "review_policy": str(POLICY.relative_to(ROOT))
    }
    (out / "evidence-manifest.json").write_text(json.dumps(evidence, indent=2) + "\n")
    review = {
        "critic_id": policy["critic_id"],
        "evidence_manifest_sha256": filehash(out / "evidence-manifest.json"),
        "candidate_glb_sha256": digest(glb_bytes),
        "reference_sha256": digest(reference_bytes),
        "reviewer": {"id": None, "provider": None, "model": None,
                     "separate_independent_run_id": None, "builder_independent": False,
                     "raw_output_file": None, "raw_output_sha256": None},
        "source_camera_alignment": {"verified": False, "evidence": None},
        "coverage": {"full_resolution_inspected": False, "five_godot_views_inspected": [],
                     "reference_regions_inspected": [], "material_names_inspected": []},
        "scores": {name: None for name in policy["scores_required"]},
        "defects": [], "observations": [], "confidence": None,
        "claim": "UNREVIEWED_TEMPLATE_NOT_A_CRITIC_VERDICT"
    }
    (out / "UNREVIEWED-review-template.json").write_text(json.dumps(review, indent=2) + "\n")
    print(json.dumps({"package": str(out), "status": evidence["status"],
                      "verified_materials": materials["material_count"], "views": list(hashes)}, indent=2))
    return evidence


def validate(a: argparse.Namespace) -> dict:
    p = load_policy()
    root = pathlib.Path(a.package)
    evidence_path = root / "evidence-manifest.json"
    evidence = json.loads(evidence_path.read_text())
    review = json.loads(pathlib.Path(a.review).read_text())
    errors: list[str] = []
    def test(ok, msg):
        if not ok:
            errors.append(msg)
    test(evidence.get("critic_id") == p["critic_id"], "wrong critic evidence")
    test(evidence.get("owner_source_sha256") == p["reference"]["sha256"], "wrong owner reference")
    test((root / "reference.png").is_file() and filehash(root / "reference.png") == p["reference"]["sha256"], "actual owner PNG does not match canonical source")
    test(evidence.get("raw_godot_shas_verified_without_recompression") is True, "native PNG provenance incomplete")
    test(evidence.get("godot_resolution") == p["required_godot_pixels"], "wrong native frame resolution")
    test(set(evidence.get("image_shas", {})) == set(p["required_godot_views"]), "five views not proven")
    for name, expected in [("reference.png", evidence.get("private_reference_sha256")),
                           ("candidate.glb", evidence.get("candidate_glb_sha256")),
                           ("review-board.png", evidence.get("review_board_sha256"))]:
        test((root / name).is_file() and filehash(root / name) == expected, name + " hash changed")
    for view, expected in evidence.get("image_shas", {}).items():
        path = root / ("godot-" + view + ".png")
        test(path.is_file() and filehash(path) == expected, "frame mutated " + view)
    test(review.get("critic_id") == p["critic_id"], "different critic")
    test(review.get("evidence_manifest_sha256") == filehash(evidence_path), "review evidence manifest hash mismatch")
    test(review.get("candidate_glb_sha256") == evidence.get("candidate_glb_sha256"), "reviewed GLB differs")
    test(review.get("reference_sha256") == p["reference"]["sha256"], "reviewed original image differs")
    critic = review.get("reviewer") or {}
    test(isinstance(critic.get("id"), str) and len(critic.get("id", "")) >= 3, "independent critic identity missing")
    test(critic.get("builder_independent") is True, "builder cannot self-review")
    test(isinstance(critic.get("provider"), str) and len(critic.get("provider", "")) >= 3,
         "reviewer runtime/provider missing")
    job = str(critic.get("separate_independent_run_id") or "")
    test(bool(job) and job != evidence.get("source_godot_run_id") and job != evidence.get("source_builder_commit"),
         "separate independent review run not documented")
    raw = critic.get("raw_output_file")
    raw_sha = critic.get("raw_output_sha256")
    if isinstance(raw, str) and pathlib.PurePosixPath(raw).name == raw and raw != pathlib.Path(a.review).name:
        raw_path = root / raw
        test(raw_path.is_file() and filehash(raw_path) == raw_sha, "raw independent critic response missing or changed")
        if raw_path.is_file() and filehash(raw_path) == raw_sha:
            try:
                raw_response = json.loads(raw_path.read_text())
                for field in ("scores", "defects", "observations", "confidence"):
                    test(raw_response.get(field) == review.get(field), "raw critic response differs: " + field)
            except (ValueError, UnicodeDecodeError) as ex:
                errors.append("raw critic output is not parseable JSON: " + str(ex))
    else:
        errors.append("raw independent critic response not bound")
    alignment = review.get("source_camera_alignment") or {}
    test(alignment.get("verified") is True and isinstance(alignment.get("evidence"), str)
         and len(alignment["evidence"]) > 20, "source-to-Godot camera calibration unverified")
    coverage = review.get("coverage") or {}
    test(coverage.get("full_resolution_inspected") is True, "full-resolution materials not inspected")
    test(set(coverage.get("five_godot_views_inspected", [])) == set(p["required_godot_views"]),
         "missing side/corner Godot visual inspection")
    test(set(coverage.get("reference_regions_inspected", [])) == set(p["required_reference_regions"]),
         "not all visible original reference regions examined")
    test(set(coverage.get("material_names_inspected", [])) == set(p["required_material_names"]),
         "not all nine actual material outputs examined")
    scores = review.get("scores") or {}
    test(set(scores) == set(p["scores_required"]), "all mandatory score dimensions required")
    for dimension, threshold in p["scores_required"].items():
        number = scores.get(dimension)
        if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number):
            errors.append(dimension + ": numeric reviewer score not supplied")
        elif number < threshold or number > 10:
            errors.append(dimension + ": below mandatory " + str(threshold) + "/10 (or invalid)")
    test(review.get("defects") == [], "unresolved reviewer defects")
    test(isinstance(review.get("observations"), list) and len(review.get("observations")) >= 5,
         "insufficient independent visual observations")
    test(review.get("confidence") == "high", "independent reviewer confidence must be high")
    passed = not errors
    status = "CRITIC_THRESHOLD_PASS_NOT_OWNER_OR_SHIPPING_APPROVAL" if passed else "CRITIC_BLOCKED"
    result = {"status": status, "passed": passed, "errors": errors,
              "critic_id": p["critic_id"], "scores": scores, "score_target_9_5": True,
              "style_exact_10": True, "no_averages": True, "owner_approved": False,
              "physical_android_certified": False, "shipping_scene_certified": False}
    if a.result:
        pathlib.Path(a.result).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    for k in ("reference", "glb", "godot-zip", "out", "builder-commit", "godot-run"):
        prep.add_argument("--" + k, required=True)
    verdict = sub.add_parser("validate")
    verdict.add_argument("--package", required=True)
    verdict.add_argument("--review", required=True)
    verdict.add_argument("--result")
    a = ap.parse_args()
    if a.command == "prepare":
        prepare(a)
    else:
        out = validate(a)
        raise SystemExit(0 if out["passed"] else 2)


if __name__ == "__main__":
    main()
