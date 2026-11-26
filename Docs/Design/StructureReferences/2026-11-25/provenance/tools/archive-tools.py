"""Bounded static-reference archive helpers. Never mutate remote GitHub refs.

This session helper preserves exact original image and prompt bytes, computes
Git object identities without cloning unrelated assets, and audits additive
candidate trees against the freshly observed consolidated baseline.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
from PIL import Image

ROOT = Path(__file__).resolve().parent
REPO = ROOT / "archive-repo"
PREFIX = "Docs/Design/StructureReferences/2026-11-25"
OUT = REPO / PREFIX
BASE = "b80c61f13ba31bb0940792dd47976a8e2878dbf5"
BASE_TREE = "598ca77bd0635e418e7eced4db6384658f9687d4"
BRANCH = "art/structures-2026-11-25"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
SECRET_PATTERN = re.compile(rb"ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|[?&](?:sig|signature|X-Amz-Signature|token)=")


def metrics(data: bytes) -> dict:
    return {"sha256": hashlib.sha256(data).hexdigest(),
            "git_blob_sha": hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest(),
            "bytes": len(data)}


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def exact_copy(source: Path, relative: str) -> dict:
    source = source.resolve()
    target = (OUT / relative).resolve()
    assert target.is_relative_to(OUT), "Escaped archive destination"
    payload = source.read_bytes()
    if source.suffix.lower() in {".json", ".md", ".txt", ".py", ".js"}:
        payload.decode("utf-8")
        assert not SECRET_PATTERN.search(payload), source
    assert not target.exists() or target.read_bytes() == payload, "Refusing to overwrite preserved bytes: " + str(target)
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    return {"source": str(source), "path": str(target.relative_to(REPO)), **metrics(payload)}


def git_tree_identity(entries: list[dict]) -> str:
    """Compute ordinary Git tree bytes from exact flat leaf identities/modes."""
    root: dict = {}
    for row in entries:
        if row["type"] == "tree":
            continue
        parts = row["path"].split("/")
        node = root
        for part in parts[:-1]:
            child = node.setdefault(part, {})
            assert isinstance(child, dict), "File/directory collision"
            node = child
        assert parts[-1] not in node, "Duplicate leaf: " + row["path"]
        node[parts[-1]] = (row["mode"].lstrip("0"), row["sha"])

    def subtree(node: dict) -> str:
        content = bytearray()
        for name, value in sorted(node.items(), key=lambda kv: (kv[0] + ("/" if isinstance(kv[1], dict) else "")).encode("utf-8")):
            mode, sha = ("40000", subtree(value)) if isinstance(value, dict) else value
            content.extend(mode.encode() + b" " + name.encode("utf-8") + b"\0" + bytes.fromhex(sha))
        return hashlib.sha1(b"tree " + str(len(content)).encode() + b"\0" + content).hexdigest()
    return subtree(root)


def baseline_check() -> dict:
    baseline = read(ROOT / "archive-baseline-tree.json")
    assert baseline["truncated"] is False
    assert baseline["sha"] == BASE_TREE
    leaves = [x for x in baseline["tree"] if x["type"] != "tree"]
    assert len(leaves) == 4144
    assert not any(x["path"].startswith(PREFIX + "/") for x in leaves)
    assert not any(x["path"] == ".github" or x["path"].startswith(".github/") for x in leaves)
    computed = git_tree_identity(leaves)
    assert computed == BASE_TREE, (computed, BASE_TREE)
    report = {"status": "PASS", "base_commit": BASE, "base_tree": BASE_TREE,
              "tree_reconstructed_from_all_leaf_identities": computed,
              "prior_files_to_preserve": len(leaves),
              "prior_png_paths_to_preserve": sum(x["path"].lower().endswith(".png") for x in leaves),
              "recursive_tree_truncated": False, "operational_github_absent": True,
              "allowed_preexisting_changes": [], "destination": PREFIX, "branch": BRANCH}
    write(ROOT / "archive-baseline-verification.json", report)
    return report


def register(index_path: Path) -> dict:
    original = read(index_path)
    images = (original.get("images", original.get("generations")) if isinstance(original, dict) else original)
    assert isinstance(images, list), "Missing images/generations list"
    invocations = {}
    invocation_path = index_path.parent / "invocation-index.json"
    if invocation_path.exists():
        for invocation in read(invocation_path).get("invocations", []):
            invocations[invocation.get("id", invocation.get("invocation_id"))] = invocation

    def resolve(locator: str) -> Path:
        path = Path(locator)
        return (path if path.is_absolute() else index_path.parent / path).resolve()
    snapshot_path = ROOT / "archive-image-snapshot.json"
    ledger = read(snapshot_path) if snapshot_path.exists() else {
        "schema_version": 1, "generation_frozen": False, "base_commit": BASE,
        "repository": "ksolo21-web/HAVENLINE", "destination": PREFIX, "images": []}
    assert ledger["generation_frozen"] is False, "Generation already frozen"
    prior = {x["id"]: x for x in ledger["images"]}
    prepared = []
    for row in images:
        ident = row.get("id") or row.get("invocation_id") or row.get("generation_id")
        assert re.fullmatch(r"[a-z0-9][a-z0-9_-]*", ident), ident
        image_locator = row.get("local_path") or row.get("image_path") or row.get("path") or row.get("output_path")
        prompt_locator = row.get("local_prompt_path") or row.get("prompt_path") or invocations.get(ident, {}).get("prompt_path")
        if prompt_locator is None and isinstance(row.get("prompt"), str) and "\n" not in row["prompt"]:
            prompt_locator = row["prompt"]
        assert image_locator and prompt_locator, "Missing exact image/prompt locator for " + ident
        image = resolve(image_locator)
        prompt = resolve(prompt_locator)
        assert image.is_file() and prompt.is_file(), ident
        payload = image.read_bytes()
        assert image.suffix.lower() == ".png" and payload.startswith(PNG_MAGIC), image
        m = metrics(payload)
        native_locator = row.get("native_original_path") or row.get("source_file")
        if native_locator and Path(native_locator).is_file():
            assert metrics(Path(native_locator).read_bytes()) == m, "Native image output differs from registered copy: " + ident
        for key in ("sha256", "git_blob_sha", "bytes"):
            if key in row:
                assert row[key] == m[key], (ident, key)
        with Image.open(image) as opened:
            assert opened.format == "PNG"
            dimensions = list(opened.size)
            opened.verify()
        prompt_payload = prompt.read_bytes()
        prompt_payload.decode("utf-8")
        assert not SECRET_PATTERN.search(prompt_payload), prompt
        pm = metrics(prompt_payload)
        if row.get("prompt_sha256"):
            assert row["prompt_sha256"] == pm["sha256"], "Prompt identity mismatch: " + ident
        if invocations.get(ident, {}).get("prompt_sha256"):
            assert invocations[ident]["prompt_sha256"] == pm["sha256"], "Invocation prompt identity mismatch: " + ident
        if invocations.get(ident, {}).get("prompt"):
            assert invocations[ident]["prompt"] == prompt_payload.decode("utf-8"), "Recorded literal prompt differs from exact prompt file: " + ident
        record = {"id": ident, "local_path": str(image), "local_prompt_path": str(prompt),
                  "archive_path": PREFIX + "/attempts/" + ident + ".png",
                  "prompt_archive_path": PREFIX + "/prompts/" + ident + ".txt",
                  **m, "dimensions": dimensions,
                  "prompt_sha256": pm["sha256"], "prompt_git_blob_sha": pm["git_blob_sha"],
                  "prompt_bytes": pm["bytes"], "source_index": str(index_path.resolve())}
        if ident in prior:
            assert all(prior[ident][k] == record[k] for k in ("sha256", "git_blob_sha", "bytes", "prompt_sha256", "prompt_git_blob_sha", "prompt_bytes")), "Registered original mutated: " + ident
        prepared.append((record, image, prompt))
    added = []
    for record, image, prompt in prepared:
        exact_copy(image, "attempts/" + record["id"] + ".png")
        exact_copy(prompt, "prompts/" + record["id"] + ".txt")
        if record["id"] not in prior:
            ledger["images"].append(record)
            prior[record["id"]] = record
            added.append(record["id"])
    ledger["registered_generated_originals"] = len(ledger["images"])
    ledger["distinct_generated_blobs"] = len({x["git_blob_sha"] for x in ledger["images"]})
    ledger["generated_original_bytes"] = sum(x["bytes"] for x in ledger["images"])
    write(snapshot_path, ledger)
    checkpoint = read(ROOT / "archive-checkpoint.json")
    checkpoint.update(stage="REGISTERING_ORIGINALS_AWAITING_CREATIVE_FREEZE", registered_generated_originals=len(ledger["images"]))
    write(ROOT / "archive-checkpoint.json", checkpoint)
    return {"registered_generated_originals": len(ledger["images"]), "added": added, "remote_ref_changed": False}


def inventory() -> dict:
    baseline_check()
    baseline = read(ROOT / "archive-baseline-tree.json")
    baseline_leaves = [x for x in baseline["tree"] if x["type"] != "tree"]
    baseline_paths = {x["path"] for x in baseline_leaves}
    rows = []
    for path in sorted(REPO.rglob("*")):
        if not path.is_file():
            continue
        relative = str(path.relative_to(REPO))
        assert relative.startswith(PREFIX + "/"), "Path outside owned prefix: " + relative
        assert relative not in baseline_paths, "Preexisting file changed: " + relative
        payload = path.read_bytes()
        if path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
            assert not payload.startswith(b"version https://git-lfs.github.com/spec/"), relative
            with Image.open(path) as opened:
                opened.verify()
        else:
            payload.decode("utf-8")
            assert not SECRET_PATTERN.search(payload), relative
        rows.append({"path": relative, "mode": "100644", "type": "blob", **metrics(payload)})
    leaves = baseline_leaves + [{"path": x["path"], "mode": x["mode"], "type": x["type"], "sha": x["git_blob_sha"]} for x in rows]
    candidate = git_tree_identity(leaves)
    manifest = {"base_commit": BASE, "base_tree": BASE_TREE, "prefix": PREFIX,
                "candidate_tree": candidate, "allowed_preexisting_changes": [],
                "baseline_files_unchanged": len(baseline_leaves), "files": rows}
    write(ROOT / "archive-expected-paths.json", manifest)
    return {"package_paths": len(rows), "candidate_tree": candidate, "prior_files_unchanged": len(baseline_leaves)}


def snapshot_documents(paths: list[Path]) -> dict:
    ledger_path = ROOT / "archive-document-snapshots.json"
    ledger = read(ledger_path) if ledger_path.exists() else {"schema_version": 1, "documents": []}
    existing = {(x["task_relative_path"], x["sha256"]) for x in ledger["documents"]}
    added = []
    for path in sorted(set(x.resolve() for x in paths)):
        assert path.is_relative_to(ROOT) and not path.is_relative_to(REPO), path
        assert not path.name.startswith("archive-"), "Archive's derived records cannot recursively snapshot themselves"
        assert path.suffix.lower() in {".json", ".md", ".txt", ".py"}, path
        payload = path.read_bytes()
        payload.decode("utf-8")
        assert not SECRET_PATTERN.search(payload), path
        if path.suffix.lower() == ".json":
            json.loads(payload)
        m = metrics(payload)
        relative = path.relative_to(ROOT)
        key = (str(relative), m["sha256"])
        if key in existing:
            continue
        archive_relative = "provenance/raw/" + str(relative.parent / (relative.stem + "--" + m["sha256"] + relative.suffix))
        saved = exact_copy(path, archive_relative)
        row = {"original_locator": str(path), "task_relative_path": str(relative),
               "archive_path": saved["path"], **m, "byte_identical": True}
        ledger["documents"].append(row)
        existing.add(key)
        added.append(str(relative))
    write(ledger_path, ledger)
    return {"exact_document_snapshots": len(ledger["documents"]), "added": added}


def upload_plan() -> dict:
    baseline = {x["sha"] for x in read(ROOT / "archive-baseline-tree.json")["tree"] if x["type"] == "blob"}
    receipts = {}
    for name in ("archive-input-blob-receipts.json", "archive-binary-blob-receipts.json"):
        path = ROOT / name
        if path.exists():
            for row in read(path)["receipts"]:
                receipts[row["git_blob_sha"]] = row
    pending = {}
    files = []
    for path in sorted(OUT.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            continue
        row = {"local_path": str(path), "path": str(path.relative_to(REPO)), **metrics(path.read_bytes())}
        sha = row["git_blob_sha"]
        if sha in baseline:
            row["transfer"] = "baseline_same_blob"
            receipts[sha] = row
        elif sha not in receipts:
            row["transfer"] = "needs_upload"
            pending[sha] = row
        else:
            row["transfer"] = "already_uploaded"
        files.append(row)
    return {"files": files, "pending": list(pending.values()), "receipts": list(receipts.values())}


def stage_evidence() -> dict:
    ledger_path = ROOT / "archive-evidence-snapshot.json"
    ledger = read(ledger_path) if ledger_path.exists() else {"schema_version": 1, "files": []}
    known = {(x["task_relative_path"], x["sha256"]) for x in ledger["files"]}
    sources = [ROOT / "reviews/evidence", ROOT / "inspection", ROOT / "counter-builder/inspection"]
    added = []
    for directory in sources:
        for path in sorted(directory.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".json"}:
                continue
            relative = path.relative_to(ROOT)
            payload = path.read_bytes()
            m = metrics(payload)
            key = (str(relative), m["sha256"])
            if key in known:
                continue
            if path.suffix.lower() == ".json":
                json.loads(payload)
                assert not SECRET_PATTERN.search(payload), path
                kind, dimensions = "qa_provenance", None
            else:
                with Image.open(path) as opened:
                    dimensions = list(opened.size)
                    opened.verify()
                kind = "qa_image"
            destination = "review-evidence/" + str(relative.parent / (relative.stem + "--" + m["sha256"] + relative.suffix))
            saved = exact_copy(path, destination)
            ledger["files"].append({"original_locator": str(path), "task_relative_path": str(relative),
                "archive_path": saved["path"], **m, "kind": kind, "dimensions": dimensions,
                "generated_artwork_count": 0, "byte_identical": True})
            known.add(key)
            added.append(str(relative))
    ledger["qa_image_files"] = sum(x["kind"] == "qa_image" for x in ledger["files"])
    ledger["qa_provenance_files"] = sum(x["kind"] == "qa_provenance" for x in ledger["files"])
    ledger["generated_artwork_count"] = 0
    write(ledger_path, ledger)
    return {"qa_image_files": ledger["qa_image_files"], "qa_provenance_files": ledger["qa_provenance_files"], "added": added}


def bind_invocations() -> dict:
    images = read(ROOT / "archive-image-snapshot.json")["images"]
    invocations = {}
    index_paths = [ROOT / "invocation-index.json", ROOT / "counter-builder/invocation-index.json"]
    snapshot_documents([x for x in index_paths if x.exists()])
    raw_documents = read(ROOT / "archive-document-snapshots.json")["documents"]
    image_resolver = {}
    for row in images:
        image_resolver.setdefault(row["sha256"], []).append(row["archive_path"])
    for filename, key in [("archive-input-snapshot.json", "images"), ("archive-evidence-snapshot.json", "files")]:
        source = ROOT / filename
        if source.exists():
            for row in read(source)[key]:
                image_resolver.setdefault(row["sha256"], []).append(row.get("archive_path", row.get("path")))
    evidence_path = ROOT / "archive-source-evidence-index.json"
    if evidence_path.exists():
        for row in read(evidence_path)["images"]:
            if row.get("archive_paths"):
                image_resolver.setdefault(row["sha256"], []).extend(row["archive_paths"])
    by_blob = {}
    for row in read(ROOT / "archive-baseline-tree.json")["tree"]:
        if row["type"] == "blob":
            by_blob.setdefault(row["sha"], []).append(row["path"])
    for index_path in index_paths:
        if not index_path.exists():
            continue
        index_sha = metrics(index_path.read_bytes())["sha256"]
        bound_snapshots = [x["archive_path"] for x in raw_documents if x["original_locator"] == str(index_path) and x["sha256"] == index_sha]
        assert bound_snapshots, "Missing exact invocation index snapshot"
        for invocation in read(index_path)["invocations"]:
            ident = invocation.get("id") or invocation.get("invocation_id")
            assert ident not in invocations, "Invocation identity collision: " + ident
            invocations[ident] = (invocation, index_path, index_sha, bound_snapshots)
    results = []
    for row in images:
        ident = row["id"]
        assert ident in invocations, "Generated output has no exact invocation: " + ident
        invocation, index_path, index_sha, bound_snapshots = invocations[ident]
        prompt = Path(invocation["prompt_path"])
        prompt_m = metrics(prompt.read_bytes())
        assert prompt_m["sha256"] == row["prompt_sha256"] == invocation["prompt_sha256"]
        if invocation.get("output_sha256"):
            assert invocation["output_sha256"] == row["sha256"], "Output binding differs: " + ident
        nested_output = invocation.get("output")
        if isinstance(nested_output, dict):
            if nested_output.get("sha256"):
                assert nested_output["sha256"] == row["sha256"], "Nested output identity differs: " + ident
            if nested_output.get("bytes"):
                assert nested_output["bytes"] == row["bytes"], "Nested output size differs: " + ident
            if nested_output.get("dimensions"):
                assert nested_output["dimensions"] == row["dimensions"], "Nested output dimensions differ: " + ident
        references = invocation.get("ordered_reference_inputs")
        if references is None:
            paths = invocation["referenced_image_paths"]
            hashes = invocation["reference_sha256"]
            assert len(paths) == len(hashes)
            references = [{"order": i + 1, "local_path": path, "sha256": hashes[i]} for i, path in enumerate(paths)]
        ordered = []
        for i, reference in enumerate(references):
            path = Path(reference.get("local_path", reference.get("path")))
            m = metrics(path.read_bytes())
            assert m["sha256"] == reference["sha256"], (ident, i, "Reference bytes changed")
            if reference.get("bytes"):
                assert m["bytes"] == reference["bytes"]
            assert reference.get("order", i + 1) == i + 1, "Reference order inconsistent"
            bound = {"order": i + 1, "original_locator": str(path), **m}
            if m["sha256"] in image_resolver:
                bound["archive_paths"] = sorted(set(image_resolver[m["sha256"]]))
            elif m["git_blob_sha"] in by_blob:
                source_path = sorted(by_blob[m["git_blob_sha"]], key=lambda x: ("/selected/" not in x, len(x), x))[0]
                bound.update(source_commit=BASE, repository_path=source_path,
                             url="https://github.com/ksolo21-web/HAVENLINE/blob/" + BASE + "/" + source_path)
            else:
                raise AssertionError("Unpreserved actual generation input: " + str(path))
            ordered.append(bound)
        results.append({"id": ident, "output_sha256": row["sha256"], "prompt_sha256": prompt_m["sha256"],
                        "exact_invocation_index_sha256": index_sha, "exact_invocation_index_snapshots": bound_snapshots,
                        "tool": invocation["tool"], "transparent_background": invocation.get("transparent_background"),
                        "actual_inputs_in_order": ordered})
    generated_ids = {x["id"] for x in images}
    unmatched = [{"id": key, "recorded_status": value[0].get("status"), "prompt_path": value[0].get("prompt_path")}
                 for key, value in invocations.items() if key not in generated_ids]
    report = {"schema_version": 1, "actual_generated_outputs_bound": len(results),
              "all_registered_outputs_have_exact_prompt_and_ordered_input_binding": True,
              "generation_inputs": results, "invocations_without_registered_output": unmatched}
    write(ROOT / "archive-invocation-bindings.json", report)
    return {"exact_generated_invocations_bound": len(results), "invocations_without_registered_output": unmatched}


def refresh() -> dict:
    registrations = []
    for path in [ROOT / "generation-index.json", ROOT / "counter-builder/generation-index.json"]:
        if path.exists():
            registrations.append(register(path))
    documents = []
    for pattern in ("*.json", "*.md", "*.py"):
        documents += [p for p in ROOT.glob(pattern) if not p.name.startswith("archive-")]
    documents += list((ROOT / "reviews").glob("*.json"))
    documents += list((ROOT / "counter-builder").glob("*.json"))
    documents += list((ROOT / "counter-builder/source-recovery").glob("*.json"))
    raw = snapshot_documents(documents)
    evidence = stage_evidence()
    bindings = bind_invocations() if (ROOT / "archive-image-snapshot.json").exists() else {}
    checkpoint = read(ROOT / "archive-checkpoint.json")
    checkpoint.update(stage="REGISTERING_ORIGINALS_AND_REVIEW_HISTORY_AWAITING_FINAL_FREEZE",
                      registered_generated_originals=bindings.get("exact_generated_invocations_bound", 0),
                      exact_document_snapshots=raw["exact_document_snapshots"],
                      qa_image_files=evidence["qa_image_files"],
                      qa_provenance_files=evidence["qa_provenance_files"],
                      pending_output_invocations=bindings.get("invocations_without_registered_output", []),
                      selected_aliases_created=0,
                      updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                      next_action="Continue immutable registration and review-history capture; await nine-sheet final visual freeze, then assemble and independently review the exact additive package before any branch/ref creation.")
    write(ROOT / "archive-checkpoint.json", checkpoint)
    return {"registrations": registrations, "documents": raw, "evidence": evidence, "bindings": bindings}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["baseline", "register", "inventory", "snapshot", "upload-plan", "stage-evidence", "bind-invocations", "refresh"])
    parser.add_argument("--index", type=Path)
    parser.add_argument("--source", type=Path, action="append", default=[])
    args = parser.parse_args()
    if args.command == "baseline":
        result = baseline_check()
    elif args.command == "register":
        assert args.index is not None, "--index is required"
        result = register(args.index)
    elif args.command == "inventory":
        result = inventory()
    elif args.command == "snapshot":
        result = snapshot_documents(args.source)
    elif args.command == "upload-plan":
        result = upload_plan()
    elif args.command == "stage-evidence":
        result = stage_evidence()
    elif args.command == "bind-invocations":
        result = bind_invocations()
    else:
        result = refresh()
    print(json.dumps(result))


if __name__ == "__main__":
    main()
