"""Bind a critic's manual pixel findings to exact, verified output bytes.

This helper does not inspect or score imagery. Its caller must supply findings
after independently viewing the full image, useful native crops, and sources.
"""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def identity(path):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    data = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def write_review(render_id, *, areas, inspected_crops, source_evidence,
                 defects=None, fixes=None, notes=None, cross_sheet=None):
    inv_path = ROOT / "invocations" / f"{render_id}.json"
    inv = json.loads(inv_path.read_text())
    out = inv["output"]
    actual = identity(out["local_path"])
    assert actual["sha256"] == out["sha256"]
    assert actual["bytes"] == out["bytes"]
    native = identity(out["native_returned_locator"])
    assert native["sha256"] == actual["sha256"]
    with Image.open(actual["path"]) as im:
        dims = list(im.size)
        assert dims == out["dimensions"] and im.format == "PNG"
    prompt = identity(inv["exact_actual_prompt_file"]["local_path"])
    assert Path(prompt["path"]).read_text() == inv["arguments"]["prompt"]
    for ref in inv["ordered_reference_inputs"]:
        assert identity(ref["local_path"])["sha256"] == ref["sha256"]
    defects = defects or []
    passed = not defects and all(a["status"] == "PASS" and a["score"] > 9.0 for a in areas)
    evidence = [identity("reviews/evidence/" + f) for f in inspected_crops]
    source_evidence = [identity(f) for f in source_evidence]
    provenance = []
    for f in (ROOT / "reviews/evidence").glob(f"{render_id}*provenance.json"):
        provenance.append(identity(f))
    report = {
        "schema_version": 2,
        "reviewer": "/root/missing_world_audit",
        "independent": True,
        "reviewed_at_utc": datetime.now(timezone.utc).isoformat(),
        "review_id": f"{render_id}-independent-world",
        "status": "PASS — STATIC REFERENCE ONLY" if passed else "REPAIR REQUIRED — NOT APPROVED",
        "score_method": "Minimum mandatory visual-area score; no averaging away a failed requirement.",
        "score": min(a["score"] for a in areas),
        "actual_full_png_inspected": True,
        "reviewed_image": {**actual, "native_original": native, "dimensions": dims, "actual_format": "PNG"},
        "invocation": identity(inv_path),
        "prompt": prompt,
        "requirements_at_generation": identity(inv["requirements_snapshot_path"]),
        "current_requirements_at_review": identity("requirements.json"),
        "catalog_at_review": identity("world-render-catalog.json"),
        "actual_native_crops_inspected": evidence,
        "crop_provenance": provenance,
        "source_images_or_native_excerpts_inspected": source_evidence,
        "areas": areas,
        "all_mandatory_visual_checks_passed": passed,
        "mandatory_defects_remaining": defects,
        "minimum_repairs": fixes or [],
        "notes": notes or [],
        "cross_sheet_bindings": [identity(f) for f in cross_sheet or []],
        "native_mesh_rig_animation_runtime_approval": False,
        "pending_separate_evidence": [
            "Additive GitHub archive and complete-content remote readback",
            "Other family coverage; this report reviews only the exact PNG identified above"
        ],
    }
    dest = ROOT / "reviews" / f"critic-{render_id}.json"
    dest.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return {"report": str(dest), "status": report["status"], "score": report["score"], "sha256": actual["sha256"]}
