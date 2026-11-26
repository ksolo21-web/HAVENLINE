"""Assemble the exact reviewed static-reference package; no remote mutation."""
from pathlib import Path
import importlib.util
import json

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("archive_tools", ROOT / "archive-tools.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
IMPORT_HISTORY = []


def relative(path):
    return str(Path(path).relative_to(m.PREFIX))


def exact_document(source, destination):
    source = Path(source)
    if not source.is_absolute():
        source = ROOT / source
    target = (m.OUT / destination).resolve()
    assert target.is_relative_to(m.OUT)
    payload = source.read_bytes()
    payload.decode("utf-8")
    assert not m.SECRET_PATTERN.search(payload), source
    if target.exists() and target.read_bytes() != payload:
        old_payload = target.read_bytes()
        old_m = m.metrics(old_payload)
        dest = Path(destination)
        history = m.OUT / "provenance/import-history" / dest.parent / (dest.stem + "--" + old_m["sha256"] + dest.suffix)
        history.parent.mkdir(parents=True, exist_ok=True)
        assert not history.exists() or history.read_bytes() == old_payload
        history.write_bytes(old_payload)
        IMPORT_HISTORY.append({"original_locator": str(source), "archive_path": str(history.relative_to(m.OUT)),
                               **old_m, "byte_identical": True, "role": "Earlier exact import retained during prepublication helper/metadata recovery."})
        target.write_bytes(payload)
    return m.exact_copy(source, destination)


def main():
    config = m.read(ROOT / "archive-package-config.json")
    assert config["generation_frozen"] is True
    assert config["all_selected_mandatory_visual_checks_passed"] is True
    assert config["all_cross_sheet_checks_passed"] is True
    requirements = m.read(ROOT / "requirements.json")
    requirement_sha = m.metrics((ROOT / "requirements.json").read_bytes())["sha256"]
    assert requirement_sha == config["requirements_sha256"]
    assert requirements["required_selected_sheets"] == 9
    assert requirements["required_turnaround_angles"] == 24
    freeze_path = ROOT / config["freeze"]["path"]
    assert m.metrics(freeze_path.read_bytes())["sha256"] == config["freeze"]["sha256"]
    frozen = m.read(freeze_path)
    assert frozen["generation_frozen"] is True
    for review_binding in frozen["all_attempt_reviews"]:
        assert m.metrics((ROOT / review_binding["path"]).read_bytes())["sha256"] == review_binding["sha256"]
    final_review = ROOT / config["final_visual_review"]["path"]
    assert m.metrics(final_review.read_bytes())["sha256"] == config["final_visual_review"]["sha256"]
    for row in config["frozen_index_files"]:
        assert m.metrics((ROOT / row["path"]).read_bytes())["sha256"] == row["sha256"], row["path"]

    # Register and preserve the last immutable source versions before sealing.
    existing_ledger = m.read(ROOT / "archive-image-snapshot.json")
    if not existing_ledger["generation_frozen"]:
        m.refresh()
    else:
        # Resume a bounded metadata failure without re-registering sealed art.
        # All frozen source/index/attempt/review identities are rechecked below.
        if (ROOT / "checkpoint.json").exists():
            m.snapshot_documents([ROOT / "checkpoint.json"])
        m.bind_invocations()
    snapshot = m.read(ROOT / "archive-image-snapshot.json")
    attempts = {x["id"]: x for x in snapshot["images"]}
    assert len(attempts) == config["generated_original_count"]
    assert set(attempts) == set(config["all_generated_attempt_ids"])
    bindings = m.read(ROOT / "archive-invocation-bindings.json")
    assert bindings["actual_generated_outputs_bound"] == len(attempts)
    assert not bindings["invocations_without_registered_output"], "Unreconciled invocation without output"
    selections = config["selected"]
    expected_series = {s["id"] for a in requirements["assets"] for s in a["sheets"]}
    assert len(selections) == 9 and {x["series_id"] for x in selections} == expected_series
    assert len({x["id"] for x in selections}) == 9
    selected_rows = []
    for selected in selections:
        source = attempts[selected["id"]]
        assert selected["image_sha256"] == source["sha256"]
        review_path = ROOT / selected["review_path"]
        review_sha = m.metrics(review_path.read_bytes())["sha256"]
        assert review_sha == selected["review_sha256"]
        review = m.read(review_path)
        assert review["requirements_sha256"] == requirement_sha
        assert review["image_sha256"] == source["sha256"]
        assert review["full_image_inspected"] is True
        assert review["status"].startswith("PASS")
        assert review["score"] >= 9.5 and review["score"] > 9.0
        assert review["score"] == selected["score"]
        assert review["checks"] and all(x == "PASS" for x in review["checks"].values())
        assert not review["required_repairs"]
        alias = "selected/" + selected["series_id"] + ".png"
        saved = m.exact_copy(m.REPO / source["archive_path"], alias)
        assert saved["git_blob_sha"] == source["git_blob_sha"]
        selected_rows.append({"id": source["id"], "series_id": selected["series_id"],
            "path": alias, "original": relative(source["archive_path"]),
            "sha256": source["sha256"], "git_blob_sha": source["git_blob_sha"],
            "bytes": source["bytes"], "dimensions": source["dimensions"],
            "score": review["score"], "status": review["status"],
            "review": selected["review_path"], "review_sha256": review_sha,
            "all_mandatory_static_checks_passed": True})

    snapshot["generation_frozen"] = True
    m.write(ROOT / "archive-image-snapshot.json", snapshot)
    checkpoint = m.read(ROOT / "archive-checkpoint.json")
    checkpoint.update(stage="ASSEMBLED_FROZEN_CONTENT_PENDING_PACKAGE_AND_REMOTE_GATES",
                      completed_milestones=2, selected_aliases_created=9,
                      generation_frozen=True, all_selected_mandatory_visual_checks_passed=True,
                      next_action="Independently review this exact staged candidate and obtain root verification; then create the isolated branch and publish using an expected-head lease. Delivery receipts are one additive child after remote readback.")
    checkpoint["milestones"][1]["status"] = "PASS"
    m.write(ROOT / "archive-checkpoint.json", checkpoint)

    # Original source files retain their original bytes and locators. Canonical
    # navigation aliases are additive to the already-preserved raw snapshots.
    imports = {
        "requirements.json": "requirements.json",
        "root-input-verification.json": "root-input-verification.json",
        "root-visual-review.json": "root-visual-review.json",
        "checkpoint.json": "checkpoint.json",
        config["freeze"]["path"]: "final-freeze.json",
        "input-index.json": "inputs/input-index.json",
        "generation-index.json": "provenance/root/generation-index.json",
        "invocation-index.json": "provenance/root/invocation-index.json",
        "archive-requirements.json": "archive-requirements.json",
        "archive-checkpoint.json": "archive-checkpoint.json",
        "archive-scope-note.json": "scope-boundary.json",
        "archive-package-config.json": "provenance/archive/package-config.json",
        "archive-image-snapshot.json": "provenance/archive/generated-image-snapshot.json",
        "archive-input-snapshot.json": "provenance/archive/source-input-snapshot.json",
        "archive-evidence-snapshot.json": "provenance/archive/qa-evidence-snapshot.json",
        "archive-document-snapshots.json": "provenance/archive/raw-document-snapshot-index.json",
        "archive-binary-blob-receipts.json": "provenance/archive/binary-blob-receipts.json",
        "archive-baseline-tree.json": "evidence/baseline-tree.json",
        "archive-prior-art-tree.json": "evidence/prior-art-tree.json",
        "archive-baseline-summary.json": "evidence/baseline-summary.json",
        "archive-baseline-verification.json": "evidence/baseline-verification.json",
        "archive-source-context.json": "evidence/live-source-context.json",
        "archive-baseline-image-attributes.json": "evidence/baseline-image-attributes.json",
        "archive-invocation-bindings.json": "reference-links.json",
        "archive-source-evidence-index.json": "source-evidence-index.json",
    }
    if (ROOT / "root-checkpoint.json").exists():
        imports["root-checkpoint.json"] = "root-checkpoint.json"
    captured_root_sources = {x["task_relative_path"] for x in m.read(ROOT / "archive-document-snapshots.json")["documents"] if "/" not in x["task_relative_path"]}
    for path in sorted(ROOT.glob("*.json")):
        if path.name.startswith("archive-") or path.name in imports:
            continue
        if path.name not in captured_root_sources:
            continue
        assert not any(term in path.name for term in ("package", "remote", "delivery")), "Post-content proof belongs in delivery receipts"
        imports[path.name] = "provenance/root/" + path.name
    for path in sorted((ROOT / "counter-builder").glob("*.json")):
        imports[str(path.relative_to(ROOT))] = "provenance/counter-builder/" + path.name
    for path in sorted((ROOT / "counter-builder/source-recovery").glob("*.json")):
        imports[str(path.relative_to(ROOT))] = "sources/" + path.name
    for path in sorted((ROOT / "reviews").glob("*.json")):
        assert "package" not in path.name and "remote" not in path.name, "Post-content proof belongs in the single delivery child"
        imports[str(path.relative_to(ROOT))] = "reviews/" + path.name
    for path in sorted(ROOT.glob("*.py")):
        imports[path.name] = "provenance/tools/" + path.name
    documents = []
    prior_provenance = m.OUT / "document-provenance.json"
    if prior_provenance.exists():
        for row in m.read(prior_provenance)["documents"]:
            p = m.OUT / row["archive_path"]
            if p.is_file() and m.metrics(p.read_bytes())["sha256"] == row["sha256"]:
                documents.append(row)
    for source, destination in sorted(imports.items()):
        saved = exact_document(source, destination)
        documents.append({"original_locator": str(ROOT / source), "archive_path": relative(saved["path"]),
                          **{k: saved[k] for k in ["sha256", "git_blob_sha", "bytes"]}, "byte_identical": True})
    raw_documents = m.read(ROOT / "archive-document-snapshots.json")["documents"]
    for row in raw_documents:
        documents.append({"original_locator": row["original_locator"], "archive_path": relative(row["archive_path"]),
                          **{k: row[k] for k in ["sha256", "git_blob_sha", "bytes"]}, "byte_identical": True})
    documents += IMPORT_HISTORY
    documents = list({row["archive_path"]: row for row in documents}.values())
    m.write(m.OUT / "document-provenance.json", {"schema_version": 1, "documents": documents,
        "policy": "Original prompts, invoked input indexes, raw reviews and their prior versions preserve exact original bytes; delivery status is separate."})

    selected_by_id = {x["id"]: x for x in selected_rows}
    reviews_by_image = {}
    for path in sorted((ROOT / "reviews").glob("*.json")):
        report = m.read(path)
        if report.get("image_sha256"):
            reviews_by_image.setdefault(report["image_sha256"], []).append({
                "path": "reviews/" + path.name, "sha256": m.metrics(path.read_bytes())["sha256"],
                "status": report.get("status"), "score": report.get("score"),
                "required_repairs": report.get("required_repairs", [])})
    public_images = []
    for row in snapshot["images"]:
        public_images.append({**{k: row[k] for k in ["id", "sha256", "git_blob_sha", "bytes", "dimensions", "prompt_sha256", "prompt_git_blob_sha", "prompt_bytes"]},
            "path": relative(row["archive_path"]), "prompt": relative(row["prompt_archive_path"]),
            "selected": row["id"] in selected_by_id,
            "selected_alias": selected_by_id.get(row["id"], {}).get("path"),
            "review_entries": reviews_by_image.get(row["sha256"], [])})
    qa = m.read(ROOT / "archive-evidence-snapshot.json")
    m.write(m.OUT / "image-index.json", {"schema_version": 1, "generated_originals": len(attempts),
        "selected_same_blob_aliases": 9, "generated_original_bytes": sum(x["bytes"] for x in attempts.values()),
        "unique_generated_blobs": len({x["git_blob_sha"] for x in attempts.values()}),
        "qa_image_files_not_generated_artwork": qa["qa_image_files"],
        "actual_native_dimensions": sorted({tuple(x["dimensions"]) for x in attempts.values()}),
        "images": public_images})
    m.write(m.OUT / "selected-status.json", {"schema_version": 1, "requirements_sha256": requirement_sha,
        "assets": 3, "selected_sheets": 9, "horizontal_rotation_angles": 24,
        "all_mandatory_static_visual_checks_passed": True, "native_mesh_rig_animation_runtime_approval": False,
        "final_visual_review": config["final_visual_review"], "selections": selected_rows})
    m.write(m.OUT / "review-evidence/index.json", {"schema_version": 1,
        "qa_image_files": qa["qa_image_files"], "qa_provenance_files": qa["qa_provenance_files"],
        "generated_artwork_count": 0, "files": [{**x, "archive_path": relative(x["archive_path"])} for x in qa["files"]]})

    hash_resolver, locator_resolver = {}, {}
    def resolve_record(sha, archive_path, locator=None):
        hash_resolver.setdefault(sha, []).append(archive_path)
        if locator:
            locator_resolver.setdefault(locator, []).append(archive_path)
            p = Path(locator)
            if p.is_relative_to(ROOT):
                task_relative = str(p.relative_to(ROOT))
                locator_resolver.setdefault(task_relative, []).append(archive_path)
                locator_resolver.setdefault(ROOT.name + "/" + task_relative, []).append(archive_path)
    for row in documents:
        resolve_record(row["sha256"], row["archive_path"], row["original_locator"])
    for row in snapshot["images"]:
        resolve_record(row["sha256"], relative(row["archive_path"]), row["local_path"])
        resolve_record(row["prompt_sha256"], relative(row["prompt_archive_path"]), row["local_prompt_path"])
    for index_record in config["frozen_index_files"]:
        index_path = ROOT / index_record["path"]
        if index_path.name != "generation-index.json":
            continue
        index = m.read(index_path)
        for row in index.get("images", index.get("generations", [])):
            ident = row.get("id") or row.get("generation_id") or row.get("invocation_id")
            if ident not in attempts:
                continue
            attempt = attempts[ident]
            for key in ("native_original_path", "source_file", "path", "local_path"):
                if row.get(key):
                    locator = Path(row[key])
                    locator = locator if locator.is_absolute() else index_path.parent / locator
                    resolve_record(attempt["sha256"], relative(attempt["archive_path"]), str(locator))
    for row in selected_rows:
        resolve_record(row["sha256"], row["path"])
    for row in qa["files"]:
        resolve_record(row["sha256"], relative(row["archive_path"]), row["original_locator"])
    for row in m.read(ROOT / "archive-input-snapshot.json")["images"]:
        for locator in [row["source"]] + row.get("actual_input_locators", []):
            resolve_record(row["sha256"], relative(row["path"]), locator)
    external = {}
    for row in m.read(ROOT / "archive-source-evidence-index.json")["images"]:
        for path in row.get("archive_paths", []):
            resolve_record(row["sha256"], relative(path), row["source_locator"])
        if row.get("url"):
            external[row["sha256"]] = [row["url"]]
    for row in bindings["generation_inputs"]:
        for source in row["actual_inputs_in_order"]:
            for path in source.get("archive_paths", []):
                resolve_record(source["sha256"], relative(path), source["original_locator"])
            if source.get("url"):
                external[source["sha256"]] = [source["url"]]
    for sha, paths in hash_resolver.items():
        for path in set(paths):
            assert m.metrics((m.OUT / path).read_bytes())["sha256"] == sha, "Resolver identity mismatch"
    m.write(m.OUT / "review-input-resolver.json", {"schema_version": 1,
        "sha256_to_archive_paths": {k: sorted(set(v)) for k, v in hash_resolver.items()},
        "original_locator_to_archive_paths": {k: sorted(set(v)) for k, v in locator_resolver.items()},
        "sha256_to_immutable_existing_repository_urls": external,
        "source_video_note": "The original source-video hashes remain recorded in sources/inspected-source-manifest.json and the preserved repository reference lock. Every inspected still used in this static review resolves to exact archive bytes or an immutable existing repository image."})

    # A compact three-by-three gallery, as requested by the root/user scope.
    gallery = ["# Havenline structure reference gallery", "", "Nine selected static studio sheets. Click a preview to open its original image.", "",
               "| Structure | Cardinal views | Oblique views | Details / states |", "| --- | --- | --- | --- |"]
    labels = {"fence": "Fence", "gates": "Gates", "customer-counter": "Customer counter"}
    dimensions_rows = []
    for asset in requirements["assets"]:
        cells = []
        for sheet in asset["sheets"]:
            path = "selected/" + sheet["id"] + ".png"
            cells.append("[![" + sheet["id"] + "](" + path + ")](" + path + ")")
        gallery.append("| " + labels[asset["id"]] + " | " + " | ".join(cells) + " |")
        dims = sorted({tuple(x["dimensions"]) for x in selected_rows if x["series_id"] in {s["id"] for s in asset["sheets"]}})
        dimensions_rows.append("| " + labels[asset["id"]] + " | " + ", ".join(str(w) + " × " + str(h) for w, h in dims) + " |")
    gallery += ["", "These are actual returned native images, preserved without upscaling. The [image index](image-index.json) records each original's dimensions and hashes. See [scope and source decisions](README.md) and [exact selection/review bindings](selected-status.json).", ""]
    (m.OUT / "GALLERY.md").write_text("\n".join(gallery))
    scores = [x["score"] for x in selected_rows]
    readme = """# Havenline — fence, gates and customer counters

**Three sourced structures, nine selected static studio reference sheets:** eight horizontal rotation angles per structure, plus construction details, gate states and repeated counter placement. [Open the three-by-three gallery](GALLERY.md).

The supplied fence and gate originals control construction identity; the accepted service counter source controls the customer counter. The latest supplied style reference controls the polished stylized finish and light-gray studio presentation. Exact source images and provenance are retained.

## Selected renders and actual native sizes

| Structure | Native selected image sizes (pixels) |
| --- | --- |
""" + "\n".join(dimensions_rows) + """

The outputs are preserved at their returned native sizes, without an upscale or 4K output claim. The original 3840 × 2160 fence reference is a source input, not a newly generated deliverable.

## Construction and review decisions

The fence is an eight-log representative module of the original continuous fence, with thick rounded timber, two rails, crossed cream lashings and pointed snow crowns. The paired timber gate retains its framed planks, bracing and stout bound posts. Hidden joints, hinges and latch details are reference clarifications, not measured engineering drawings.

Gameplay references show repeated instances of the same timber/register customer counter. The blue-and-metal processing bench remains a separate internal production asset and is documented only as source context.

The nine selected sheets passed separate image and cross-sheet visual review. Scores and exact image/review bindings are in [selected status](selected-status.json) and the [final independent visual acceptance](reviews/critic-final-visual-acceptance.json). All original attempts, including rejected revisions, remain available.

## Exact archive and evidence

""" + f"This package preserves **{len(attempts)} generated PNG originals**, their exact invoked prompts, nine aliases using the same approved image blobs, {qa['qa_image_files']} QA images and {qa['qa_provenance_files']} QA provenance/observation records. Source inputs and QA images are catalogued separately from generated artwork.\n\n" + """- [All original attempts and native hashes](image-index.json), [original PNGs](attempts/) and [exact prompts](prompts/)
- [Ordered actual generation inputs](reference-links.json), [source evidence](source-evidence-index.json) and [source recovery records](sources/)
- [Independent reviews and repair retests](reviews/) and [QA image/provenance index](review-evidence/index.json)
- [Frozen requirements](requirements.json), [frozen selection](final-freeze.json) and [scope boundary](scope-boundary.json)
- [Exact document provenance](document-provenance.json) and [hash/locator resolver](review-input-resolver.json)

## Approval and preservation boundary

These are static raster references. They do not prove native mesh geometry, rigging, animation, navigation, physics or collision behavior. The prior requirement for at least two distinct usable bidirectional camp openings remains a subsequent camp layout/runtime requirement; the gate reference states do not test or fulfill it.

The package adds only `Docs/Design/StructureReferences/2026-11-25` on the isolated `art/structures-2026-11-25` branch, based on consolidated main `b80c61f13ba31bb0940792dd47976a8e2878dbf5`. All 4,144 baseline files and their modes, including 879 PNG paths, are preserved. Main, active gameplay branches, existing plans/references and operational workflows are unchanged by this package.

Original progress snapshots deliberately retain their historical pending/failure states. After the immutable content commit passes fresh remote readback, one additive `delivery-status/summary.json` records delivery completion without rewriting the artwork or original review evidence.
"""
    (m.OUT / "README.md").write_text(readme)
    manifest = m.inventory()
    print(json.dumps({**manifest, "generated_originals": len(attempts), "selected_aliases": 9,
                      "qa_images": qa["qa_image_files"], "qa_provenance": qa["qa_provenance_files"],
                      "minimum_selected_score": min(scores), "maximum_selected_score": max(scores),
                      "remote_ref_changed": False}))


if __name__ == "__main__":
    main()
