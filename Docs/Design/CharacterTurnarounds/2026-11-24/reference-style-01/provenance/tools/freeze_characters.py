"""Bind all generated originals and the independently reviewed v2 selection.

This script verifies recorded evidence; it does not perform or grant visual approval.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
from PIL import Image

ROOT = Path(__file__).resolve().parent
INDEXES = [ROOT / "generation-index.json", ROOT / "builder-characters-2-4/generation-index.json"]


def metrics(path):
    data = path.read_bytes()
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "git_blob_sha": hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest(),
        "bytes": len(data),
    }


req_path = ROOT / "requirements-v2.json"
req = json.loads(req_path.read_text())
prefix = req["archive_prefix"]
status_path = ROOT / "reviews/latest-independent-status.json"
status = json.loads(status_path.read_text())
assert status["requirements_sha256"] == metrics(req_path)["sha256"]
assert status["independent"] is True
assert status["complete_visual_set"] is True, "Independent visual review is incomplete"
assert status["approved_sheet_count"] == status["required_sheet_count"] == req["required_sheet_count"] == 12
assert len(status["slots"]) == 12

attempts, sources, references, reference_records = {}, [], {}, []
for index_path in INDEXES:
    index = json.loads(index_path.read_text())
    registered_paths = set()
    for record in index["images"]:
        image_id = record["id"]
        assert image_id not in attempts, image_id
        path = Path(record["path"])
        registered_paths.add(path.resolve())
        actual = metrics(path)
        assert actual == {k: record[k] for k in actual}, image_id
        assert metrics(Path(record["source_file"])) == actual, image_id
        assert path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        with Image.open(path) as im:
            assert list(im.size) == record["dimensions"]
            im.verify()
        prompt = index_path.parent / record["prompt"]
        prompt_hash = metrics(prompt)["sha256"]
        assert prompt.stat().st_size > 0
        if record.get("prompt_sha256"):
            assert record["prompt_sha256"] == prompt_hash
        attempts[image_id] = {
            "id": image_id,
            "local_path": str(path),
            "archive_path": prefix + "/attempts/" + image_id + ".png",
            **actual,
            "dimensions": record["dimensions"],
            "prompt_local_path": str(prompt),
            "prompt_archive_path": prefix + "/prompts/" + image_id + ".txt",
            "prompt_sha256": prompt_hash,
            "source_index": str(index_path),
        }
    actual_paths = {p.resolve() for p in (index_path.parent / "renders").glob("*.png")}
    assert actual_paths == registered_paths, f"Unregistered or missing render: {index_path.parent}"
    sources.append({"path": str(index_path), **metrics(index_path), "registered_outputs": len(index["images"])})
    ref_path = index_path.parent / "reference-inputs.json"
    outputs = json.loads(ref_path.read_text())["outputs"]
    if isinstance(outputs, list):
        outputs = {r["id"]: r["actual_referenced_image_paths"] for r in outputs}
    assert not (set(references) & set(outputs)), "Duplicate reference record"
    references.update(outputs)
    reference_records.append({"path": str(ref_path), **metrics(ref_path)})

assert set(references) == set(attempts), "Every actual generation must have its actual inputs recorded"
for output_id, input_images in references.items():
    assert input_images, output_id
    for ref in input_images:
        path = Path(ref.get("local_path", ref.get("path")))
        assert metrics(path)["sha256"] == ref["sha256"], (output_id, str(path))

execution_path = ROOT / "builder-characters-2-4/execution-log.json"
execution = json.loads(execution_path.read_text())
prepared_not_invoked = []
completed_builder_ids = set()
for entry in execution["entries"]:
    prompt = execution_path.parent / entry["prompt"]
    assert metrics(prompt)["sha256"] == entry["prompt_sha256"]
    if entry["execution_status"] == "PREPARED_NOT_INVOKED":
        assert entry["id"] not in attempts and entry["output"] is None
        prepared_not_invoked.append({
            "id": entry["id"],
            "execution_status": "PREPARED_NOT_INVOKED",
            "local_path": str(prompt),
            "archive_path": prefix + "/provenance/prepared-not-invoked/" + prompt.name,
            **metrics(prompt),
            "generated_image_count": 0,
        })
    else:
        assert entry["execution_status"] == "COMPLETED", "Builder invocation still incomplete"
        attempt = attempts[entry["id"]]
        assert entry["output"]["sha256"] == attempt["sha256"]
        assert entry["prompt_sha256"] == attempt["prompt_sha256"]
        completed_builder_ids.add(entry["id"])
assert completed_builder_ids == {a["id"] for a in attempts.values() if "builder-characters-2-4" in a["source_index"]}

by_path = {Path(a["local_path"]).resolve(): a for a in attempts.values()}
selected, seen = [], set()
for slot in status["slots"]:
    assert slot["id"] not in seen
    seen.add(slot["id"])
    assert slot["status"].startswith("PASS")
    assert slot["score"] >= 9.5 and slot["mandatory_checks_passed"] is True
    attempt = by_path[Path(slot["selected_path"]).resolve()]
    assert attempt["sha256"] == slot["sha256"]
    review_path = Path(slot["raw_review_path"])
    review_metrics = metrics(review_path)
    assert review_metrics["sha256"] == slot["raw_review_sha256"]
    review = json.loads(review_path.read_text())
    assert review["independent"] is True
    assert review["requirements_sha256"] == metrics(req_path)["sha256"]
    matches = [r for r in review["entries"] if r["slot_id"] == slot["id"] and r["sha256"] == slot["sha256"]]
    assert len(matches) == 1
    reviewed = matches[0]
    assert reviewed["status"].startswith("PASS")
    assert reviewed["mandatory_visual_checks_passed"] is True
    assert reviewed["score"] == slot["score"]
    assert reviewed["actual_full_sheet_inspected"] is True
    selected.append({
        **attempt,
        "archive_path": prefix + "/selected/" + slot["id"] + ".png",
        "series_id": slot["id"],
        "subject_id": slot["subject_id"],
        "sheet_type": slot["sheet_type"],
        "status": slot["status"],
        "score": slot["score"],
        "all_mandatory_checks_passed": True,
        "raw_review_path": str(review_path),
        "raw_review_sha256": review_metrics["sha256"],
    })

expected = {s["id"] + "-" + kind for s in req["subjects"] for kind in ["cardinal", "diagonal", "hands"]}
assert seen == expected
assert len({s["subject_id"] for s in selected}) == 4
assert status.get("all_cross_sheet_consistency_passed") is True, "Cross-sheet consistency evidence is required"
set_audit_path = ROOT / "reviews/final-character-set-visual-audit.json"
set_audit = json.loads(set_audit_path.read_text())
assert set_audit["independent"] is True
assert set_audit["requirements_sha256"] == metrics(req_path)["sha256"]
assert set_audit["approved_sheet_count"] == 12
assert set_audit["all_cross_sheet_consistency_passed"] is True
assert {r["slot_id"]: r["sha256"] for r in set_audit["selected"]} == {r["series_id"]: r["sha256"] for r in selected}
for subject_id, cross in set_audit["cross_sheet_reviews"].items():
    assert cross["status"] == "PASS" and cross["score"] >= 9.5
    assert set(cross["image_hashes"]) == {r["sha256"] for r in selected if r["subject_id"] == subject_id}
    assert metrics(Path(cross["raw_review_path"]))["sha256"] == cross["raw_review_sha256"]
comparison = set_audit["set_comparison_evidence"]
assert comparison["actual_pixels_inspected"] is True
assert metrics(Path(comparison["path"]))["sha256"] == comparison["sha256"]
assert metrics(Path(comparison["provenance_path"]))["sha256"] == comparison["provenance_sha256"]
freeze = {
    "schema_version": 2,
    "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
    "generation_frozen": True,
    "repository": req["repository"],
    "branch": req["branch"],
    "parent_commit": req["parent_commit"],
    "destination": prefix,
    "scope": req["scope"],
    "required_subject_count": 4,
    "required_sheet_count": 12,
    "required_body_view_count": 32,
    "required_hand_view_count": 16,
    "generated_png_count": len(attempts),
    "generated_original_bytes": sum(a["bytes"] for a in attempts.values()),
    "declared_output_indexes": sources,
    "exact_reference_input_records": reference_records,
    "builder_execution_record": {"path": str(execution_path), **metrics(execution_path)},
    "prepared_not_invoked_prompts": prepared_not_invoked,
    "all_generated_attempts": list(attempts.values()),
    "selected": selected,
    "supplementary": [],
    "independent_status": {"path": str(status_path), **metrics(status_path)},
    "final_visual_set_audit": {"path": str(set_audit_path), **metrics(set_audit_path)},
    "requirements": {"path": str(req_path), **metrics(req_path)},
    "historical_requirements": {"path": str(ROOT / "requirements.json"), **metrics(ROOT / "requirements.json")},
    "all_selected_mandatory_checks_passed": True,
    "all_cross_sheet_consistency_passed": True,
    "minimum_selected_score": min(s["score"] for s in selected),
    "remote_delivery_verified": False,
    "native_mesh_rig_animation_runtime_approval": False,
    "next_action": "Assemble the additive archive, independently verify it, publish, then verify the remote tree and original bytes.",
}
target = ROOT / "final-freeze.json"
assert not target.exists(), "Freeze already exists; do not silently replace it"
target.write_text(json.dumps(freeze, indent=2, ensure_ascii=False) + "\n")
print(json.dumps({"freeze": str(target), **metrics(target), "selected": len(selected), "originals": len(attempts), "minimum_score": freeze["minimum_selected_score"]}))
