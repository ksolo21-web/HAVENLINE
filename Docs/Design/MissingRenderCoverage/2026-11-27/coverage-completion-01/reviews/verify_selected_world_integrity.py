"""Read-only integrity retest of the 35 already pixel-reviewed world sheets.

This does not inspect images or award visual approval; it binds independent
manual reviews, native outputs, exact inputs and native evidence to selection.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SELECTION_SHA256 = "816d93ba1a1a86a20c14b5dcc6ed2a510ba1c3481b3978a3e619a83147b61e3e"


def identity(path):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT.parent / path if path.parts[0] == ROOT.name else ROOT / path
    body = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}


def read(path):
    return json.loads(Path(path).read_text())


checks, resolved_history, bound_files, native_crops = [], [], {}, {}


def check(name, truth, detail=None):
    checks.append({"id": name, "passed": bool(truth), "detail": detail})
    assert truth, (name, detail)


snapshot_lookup = {}
for folder in ["archive-input-snapshots", "archive-review-snapshots", "drafts/catalog-inputs"]:
    for path in (ROOT / folder).glob("*"):
        if path.is_file():
            rec = identity(path)
            snapshot_lookup.setdefault(rec["sha256"], rec)


def bind(rec, label):
    """Resolve historical mutable aliases by retained exact immutable bytes."""
    actual = identity(rec["path"])
    if actual["sha256"] != rec["sha256"]:
        actual = snapshot_lookup.get(rec["sha256"])
        check(label + ":immutable-historical-snapshot", actual is not None, rec)
        resolved_history.append({"original": rec, "resolved": actual})
    check(label + ":sha256", actual["sha256"] == rec["sha256"])
    if "bytes" in rec:
        check(label + ":bytes", actual["bytes"] == rec["bytes"])
    bound_files[actual["path"]] = actual
    return Path(actual["path"])


def bind_nested(value, label):
    if isinstance(value, dict):
        if isinstance(value.get("path"), str) and "sha256" in value:
            bind(value, label)
        for key, item in value.items():
            bind_nested(item, label + "/" + key)
    elif isinstance(value, list):
        for n, item in enumerate(value):
            bind_nested(item, label + f"/{n}")


def verify_crop(source, output, box, resize, label):
    source_path = bind(source, label + ":source")
    output_path = bind(output, label + ":crop")
    check(label + ":native-size", resize is False)
    with Image.open(source_path) as original, Image.open(output_path) as crop:
        expected = original.crop(tuple(box)).convert("RGBA")
        observed = crop.convert("RGBA")
        check(label + ":exact-source-pixels", expected.size == observed.size and expected.tobytes() == observed.tobytes())
    native_crops[str(output_path)] = {"source": source, "crop": output, "bbox_xyxy": box, "exact_native_pixels": True}


def crop_provenance(path):
    data = read(path)
    for entry in data if isinstance(data, list) else [data]:
        if "crops" in entry or "native_crops" in entry:
            raw_source = entry.get("source_path", entry.get("source"))
            source = raw_source if isinstance(raw_source, dict) else {"path": raw_source, "sha256": entry["source_sha256"]}
            if "source_bytes" in entry:
                source["bytes"] = entry["source_bytes"]
            for item in entry.get("crops", entry.get("native_crops")):
                output = {key: item[key] for key in ["path", "sha256", "bytes"] if key in item}
                verify_crop(source, output, item.get("bbox_xyxy", item.get("box")), item.get("resize", False), str(path) + ":" + Path(output["path"]).name)
        else:
            source = entry.get("source")
            if not isinstance(source, dict):
                source = {"path": entry["source_path"], "sha256": entry["source_sha256"]}
            output = entry.get("output")
            if not isinstance(output, dict):
                output = {"path": entry["output_path"], "sha256": entry.get("output_sha256", entry.get("sha256"))}
            verify_crop(source, output, entry.get("crop_box_xyxy", entry.get("bbox")), entry.get("resized", entry.get("resize", False)), str(path) + ":" + Path(output["path"]).name)


selection_path = ROOT / "selection-working.json"
selection_identity = identity(selection_path)
check("selection-exact-root-announced-bytes", selection_identity["sha256"] == EXPECTED_SELECTION_SHA256)
selection = read(selection_path)
catalog = read(ROOT / "world-render-catalog.json")
matrix = read(ROOT / "audit/world/world-gap-matrix.json")
requirements = read(ROOT / "requirements.json")
catalog_ids = {sheet["id"] for sheet in catalog["sheets"]}
required = catalog_ids | {"defense-platform-turnaround", "defense-platform-details"}
rows = [row for row in selection["selected"] if row["deliverable_id"] in required]
check("complete-selection-81-of-81", selection["selected_count"] == 81 and selection["pending_count"] == 0)
check("exact-35-required-world-sheets", len(rows) == 35 and {row["deliverable_id"] for row in rows} == required)
check("catalog-has-33-sheets", len(catalog["sheets"]) == 33 and len(catalog_ids) == 33)
check("auxiliary-study-not-selected", all(not row["render_id"].startswith("world-bridges-rear-study") for row in selection["selected"]))
forms = {(sheet["family_id"], i) for sheet in catalog["sheets"] for i in sheet["source_form_indexes_zero_based"]}
expected_forms = {(family["id"], i) for family in matrix["family_gap_matrix"] if family["id"] != "defense_platform" for i in range(family["variant_count"])}
check("all-64-non-defense-forms-exactly-covered", forms == expected_forms and len(forms) == 64)
check("30-families-65-forms-with-defense", len({family for family, _ in forms}) + 1 == 30 and len(forms) + 1 == 65)
check("162-catalog-panels", sum(len(sheet["required_views"]) for sheet in catalog["sheets"]) == 162)
check("scope-agrees-with-current-requirements", requirements["planned_selected_sheet_breakdown"]["world"] == 35 and requirements["confirmed_scope_counts"]["world_families"] == 30 and requirements["confirmed_scope_counts"]["world_depicted_forms"] == 65)

verified_rows = []
for row in rows:
    rid = row["render_id"]
    report_path = bind({"path": row["review_path"], "sha256": row["review_sha256"]}, rid + ":report")
    report = read(report_path)
    check(rid + ":independent-manual-visual-pass", report["reviewer"] == "/root/missing_world_audit" and report["independent"] and report["all_mandatory_visual_checks_passed"] and report["actual_full_png_inspected"] and not report["mandatory_defects_remaining"] and not report["native_mesh_rig_animation_runtime_approval"])
    check(rid + ":all-mandatory-scores-strictly-over-nine", row["score"] == report["score"] == min(area["score"] for area in report["areas"]) and all(area["status"] == "PASS" and area["score"] > 9 for area in report["areas"]))
    alias = bind({"path": row["local_path"], "sha256": row["sha256"], "bytes": row["bytes"]}, rid + ":selected-alias")
    inv = read(ROOT / "invocations" / (rid + ".json"))
    output = inv["output"]
    native = Path(output["native_returned_locator"])
    check(rid + ":exact-native-custody", alias.read_bytes() == native.read_bytes() and identity(alias)["sha256"] == output["sha256"] and alias.stat().st_size == output["bytes"])
    with Image.open(alias) as im:
        check(rid + ":native-PNG-dimensions", im.format == "PNG" and list(im.size) == output["dimensions"])
    reviewed = report["reviewed_image"]
    reviewed_hash = reviewed.get("sha256", reviewed.get("source_sha256"))
    check(rid + ":review-binds-selected-output", reviewed_hash == row["sha256"])
    bind_nested(report, rid + ":report-bindings")
    prompt_path = Path(inv["exact_actual_prompt_file"]["local_path"])
    check(rid + ":exact-invoked-prompt", prompt_path.read_text() == inv["arguments"]["prompt"])
    check(rid + ":reference-order", [ref["local_path"] for ref in inv["ordered_reference_inputs"]] == inv["arguments"]["referenced_image_paths"])
    for n, ref in enumerate(inv["ordered_reference_inputs"]):
        bind({"path": ref["local_path"], "sha256": ref["sha256"], "bytes": ref["bytes"]}, rid + f":reference-{n + 1}")
    check(rid + ":generation-requirements-snapshot", identity(inv["requirements_snapshot_path"])["sha256"] == report["requirements_at_generation"]["sha256"])
    provenance = report["crop_provenance"]
    for prov in provenance if isinstance(provenance, list) else [provenance]:
        crop_provenance(Path(prov["path"]))
    observed_crops = report["actual_native_crops_inspected"]
    check(rid + ":native-evidence-present", bool(observed_crops))
    for crop in observed_crops:
        cp = str(ROOT / "reviews/evidence" / crop) if isinstance(crop, str) else crop["path"]
        check(rid + ":inspected-crop-exactly-resolved:" + Path(cp).name, cp in native_crops)
    verified_rows.append({**row, "invocation": identity(ROOT / "invocations" / (rid + ".json")), "native_original": identity(native), "native_crop_count": len(observed_crops), "integrity_passed": True})

open_gate = next(row for row in rows if row["deliverable_id"] == "world-fortress-gates-open")
closed_gate = next(row for row in rows if row["deliverable_id"] == "world-fortress-gates-closed")
open_report = read(Path(open_gate["review_path"]))
check("gate-open-final-binds-accepted-closed-r2", closed_gate["render_id"] == "world-fortress-gates-closed-r2" and any(item["path"] == closed_gate["local_path"] and item["sha256"] == closed_gate["sha256"] for item in open_report["cross_sheet_bindings"]))
history = []
for rp in sorted((ROOT / "reviews").glob("critic-*.json")):
    report = read(rp)
    if not report.get("reviewed_image") or report.get("all_mandatory_visual_checks_passed", True):
        continue
    rid = rp.name[len("critic-"):-len(".json")]
    if not rid.startswith(("world-", "defense-platform-")):
        continue
    invp = ROOT / "invocations" / (rid + ".json")
    inv = read(invp)
    output = inv["output"]
    observed = identity(output["local_path"])
    check(rid + ":rejected-original-retained", observed["sha256"] == output["sha256"] and Path(output["local_path"]).read_bytes() == Path(output["native_returned_locator"]).read_bytes())
    check(rid + ":rejected-not-selected", all(row["render_id"] != rid for row in rows))
    history.append({"render_id": rid, "output": observed, "review": identity(rp), "status": report["status"]})

check("selection-unchanged-during-read-only-check", identity(selection_path) == selection_identity)
result = {
    "schema_version": 1,
    "reviewer": "/root/missing_world_audit",
    "independent_of_image_builder": True,
    "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS — LOCAL SELECTED WORLD EVIDENCE INTEGRITY ONLY",
    "evidence_integrity_score": 10,
    "score_basis": "All exact-byte, coverage and native-crop integrity checks passed. Visual scores remain the separately recorded minimum mandatory scores; they are not averaged or raised by this report.",
    "selection": selection_identity,
    "catalog": identity(ROOT / "world-render-catalog.json"),
    "requirements": identity(ROOT / "requirements.json"),
    "world_source_census": identity(ROOT / "audit/world/world-gap-matrix.json"),
    "counts": {"selected_world_sheets": 35, "catalog_sheets": 33, "defense_sheets": 2, "world_families": 30, "depicted_forms": 65, "catalog_panels": 162, "exact_native_crops_verified": len(native_crops), "unique_bound_files": len(bound_files), "retained_rejected_world_originals": len(history), "checks": len(checks)},
    "minimum_selected_visual_score": min(row["score"] for row in rows),
    "maximum_selected_visual_score": max(row["score"] for row in rows),
    "selected_world_sheets": verified_rows,
    "historical_aliases_resolved_without_mutation": resolved_history,
    "native_crop_checks": list(native_crops.values()),
    "bound_files": list(bound_files.values()),
    "retained_rejected_world_originals": history,
    "checks": checks,
    "checker_preparation_note": "Initial invocation stopped before reporting because an early defense provenance record used a workspace-relative path. The parser was corrected to resolve that legitimate path without changing any source, render or review; this is not an art failure.",
    "boundaries": ["No new visual judgments were inferred by this script; manual actual-image reviews are authoritative.", "All approval remains static concept/reference art. No native model, rig, animation, collision, engineered load capacity or runtime was tested.", "Source-hidden surfaces, authored guides and future Atlas forms retain their interpretation status.", "GitHub publication and fresh immutable remote complete-body readback remain separate pending gates."]
}
dest = ROOT / "reviews/critic-selected-world-evidence-integrity.json"
dest.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
print(json.dumps({"report": str(dest), "status": result["status"], "counts": result["counts"], "minimum_visual_score": result["minimum_selected_visual_score"]}, indent=2))
