"""Bind the final reviewed roster to exact original bytes; never approves visuals."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parent
PREFIX = "Docs/Design/InvaderTurnarounds/2026-11-24/roster-expansion-02"
BASE = "bb54c582916b3dbc5d542309f290e5101ab9e218"
INDEXES = [
    ROOT / "generation-index.json",
    ROOT / "animal-builds/generation-index.json",
    ROOT / "aerial-siege-builds/generation-index.json",
]


def metrics(path):
    data = path.read_bytes()
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "git_blob_sha": hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest(),
        "bytes": len(data),
    }


requirements_path = ROOT / "requirements.json"
requirements = json.loads(requirements_path.read_text())
status_path = ROOT / "reviews/latest-independent-status.json"
status = json.loads(status_path.read_text())
assert status["all_required_visuals_passed"] is True, "Independent visual review is incomplete"
assert status["approved_required_count"] == status["required_count"] == 16
assert len(status["required_slots"]) == 16
assert requirements["required_sheet_count"] == 16

attempts = {}
sources = []
references = {}
reference_records = []
for index_path in INDEXES:
    index = json.loads(index_path.read_text())
    registered_paths = set()
    for image in index["images"]:
        image_id = image["id"]
        assert image_id not in attempts, f"Duplicate output ID: {image_id}"
        path = Path(image["path"])
        registered_paths.add(path.resolve())
        actual = metrics(path)
        assert actual == {k: image[k] for k in actual}, image_id
        if image.get("source_file"):
            assert metrics(Path(image["source_file"])) == actual, image_id
        assert path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"), image_id
        prompt = index_path.parent / image["prompt"]
        prompt_metrics = metrics(prompt)
        assert prompt.stat().st_size > 0
        if image.get("prompt_sha256"):
            assert prompt_metrics["sha256"] == image["prompt_sha256"]
        attempts[image_id] = {
            "id": image_id,
            "local_path": str(path),
            "archive_path": PREFIX + "/attempts/" + image_id + ".png",
            **actual,
            "dimensions": image["dimensions"],
            "prompt_local_path": str(prompt),
            "prompt_archive_path": PREFIX + "/prompts/" + image_id + ".txt",
            "prompt_sha256": prompt_metrics["sha256"],
            "source_index": str(index_path),
        }
    actual_paths = {p.resolve() for p in (index_path.parent / "renders").glob("*.png")}
    assert actual_paths == registered_paths, f"Unregistered or missing generated render in {index_path.parent}"
    sources.append({"path": str(index_path), **metrics(index_path), "registered_outputs": len(index["images"])})
    ref_path = index_path.parent / "reference-inputs.json"
    ref_data = json.loads(ref_path.read_text())
    reference_outputs = ref_data.get("outputs", ref_data.get("images", {}))
    if isinstance(reference_outputs, dict):
        references.update(reference_outputs)
    reference_records.append({"path": str(ref_path), **metrics(ref_path)})

assert set(references) == set(attempts), "Every generated attempt must declare its actual image references"
for output_id, input_images in references.items():
    assert input_images, output_id
    for input_image in input_images:
        assert metrics(Path(input_image["local_path"]))["sha256"] == input_image["sha256"], output_id

selected = []
seen_series = set()
for slot in status["required_slots"]:
    assert slot["series_id"] not in seen_series
    seen_series.add(slot["series_id"])
    assert slot["all_mandatory_checks_passed"] is True
    assert slot["status"].startswith("PASS") and slot["score"] >= 9.5
    attempt = attempts[slot["asset_id"]]
    assert slot["sha256"] == attempt["sha256"]
    assert Path(slot["path"]).resolve() == Path(attempt["local_path"]).resolve()
    review_path = Path(slot["raw_review"]["path"])
    review_metrics = metrics(review_path)
    assert review_metrics["sha256"] == slot["raw_review"]["sha256"]
    review = json.loads(review_path.read_text())
    matching = [r for r in review["results"] if r.get("asset_id", r.get("id")) == slot["asset_id"]]
    assert len(matching) == 1
    reviewed = matching[0]
    assert reviewed["sha256"] == attempt["sha256"]
    assert reviewed["score"] == slot["score"]
    assert reviewed["all_mandatory_checks_passed"] is True
    selected.append({
        **attempt,
        "archive_path": PREFIX + "/selected/" + slot["series_id"] + ".png",
        "series_id": slot["series_id"],
        "subject_id": slot["subject_id"],
        "sheet_type": slot["sheet_type"],
        "status": slot["status"],
        "score": slot["score"],
        "all_mandatory_checks_passed": True,
        "raw_review_path": str(review_path),
        "raw_review_sha256": review_metrics["sha256"],
    })

expected_series = {subject["id"] + "-" + kind for subject in requirements["subjects"] for kind in ["turnaround", "details"]}
assert seen_series == expected_series
assert len({x["subject_id"] for x in selected}) == 8
freeze = {
    "schema_version": 1,
    "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
    "generation_frozen": True,
    "repository": "ksolo21-web/HAVENLINE",
    "branch": "art/enemy-invaders-2026-11-24",
    "parent_commit": BASE,
    "destination": PREFIX,
    "scope": "Eight authored enemy proposals; sixteen static boards. No source-roster exhaustiveness or runtime approval.",
    "required_subject_count": 8,
    "required_sheet_count": 16,
    "generated_png_count": len(attempts),
    "generated_original_bytes": sum(r["bytes"] for r in attempts.values()),
    "declared_output_indexes": sources,
    "exact_reference_input_records": reference_records,
    "all_generated_attempts": list(attempts.values()),
    "selected": selected,
    "supplementary": [],
    "independent_status": {"path": str(status_path), **metrics(status_path)},
    "requirements": {"path": str(requirements_path), **metrics(requirements_path)},
    "all_selected_mandatory_checks_passed": True,
    "minimum_selected_score": min(r["score"] for r in selected),
    "remote_delivery_verified": False,
    "next_action": "Assemble the additive archive, independently check it, commit, then verify the live remote tree and original bytes.",
}
target = ROOT / "final-freeze.json"
assert not target.exists(), "Freeze already exists; do not silently overwrite it"
target.write_text(json.dumps(freeze, indent=2, ensure_ascii=False) + "\n")
print(json.dumps({"freeze": str(target), **metrics(target), "selected": len(selected), "originals": len(attempts), "minimum_score": freeze["minimum_selected_score"]}))
