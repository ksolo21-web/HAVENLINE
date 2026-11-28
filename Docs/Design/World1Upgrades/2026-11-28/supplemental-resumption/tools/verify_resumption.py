#!/usr/bin/env python3
"""Read-only integrity checks for the additive World 1 resumption evidence."""

import argparse
import hashlib
import json
from pathlib import Path


SUPPLEMENT = Path(__file__).resolve().parents[1]
REPOSITORY = SUPPLEMENT.parents[4]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def fingerprint(path):
    data = path.read_bytes()
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "git_blob_sha1": hashlib.sha1(
            b"blob " + str(len(data)).encode() + b"\0" + data
        ).hexdigest(),
        "bytes": len(data),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-finalized", action="store_true",
        help="Also require the final assembled inventory/receipt/gallery and root additions.",
    )
    args = parser.parse_args()
    manifest = read_json(SUPPLEMENT / "RESUMPTION_MANIFEST.json")
    source_manifest = read_json(SUPPLEMENT / "SOURCE_PRESERVATION_MANIFEST.json")
    audit = read_json(SUPPLEMENT / "PUBLICATION_AUDIT.json")
    failures = []
    checks = 0

    def require(ok, label):
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(label)

    for relative, expected in manifest["files"].items():
        path = (SUPPLEMENT / relative).resolve()
        valid = path.is_relative_to(SUPPLEMENT) and path.is_file()
        require(valid and fingerprint(path) == expected, "Supplemental file: " + relative)

    staged = [r for r in source_manifest["records"] if r.get("snapshot_repository_path")]
    pinned = [r for r in source_manifest["records"] if r.get("base_commit_contains_exact_bytes")]
    require(len(staged) == 20 and len(pinned) == 32, "Source preservation counts")
    require(sum(r["bytes"] for r in staged) == 4564444, "Staged payload bytes")
    for record in staged:
        path = (REPOSITORY / record["snapshot_repository_path"]).resolve()
        expected = {k: record[k] for k in ("sha256", "git_blob_sha1", "bytes")}
        require(
            path.is_relative_to(SUPPLEMENT / "staged-sources")
            and path.is_file() and fingerprint(path) == expected
            and record["runtime_integration_claimed"] is False,
            "Staged source: " + record["original_repository_path"],
        )
    for record in pinned:
        require(
            len(record.get("commit", "")) == 40
            and record.get("url", "").endswith("/" + record["original_repository_path"])
            and record["base_commit_contains_exact_bytes"] is True,
            "Pinned source metadata: " + record["original_repository_path"],
        )
    for relative, expected_sha in audit["prior_package_file_bindings"].items():
        path = (REPOSITORY / relative).resolve()
        require(
            path.is_relative_to(REPOSITORY) and path.is_file()
            and fingerprint(path)["sha256"] == expected_sha,
            "Preserved prior package file: " + relative,
        )

    final_paths = [
        SUPPLEMENT.parent / "REVIEW_GALLERY.md",
        SUPPLEMENT.parent / "review-evidence/ARTIFACT_INVENTORY.json",
        SUPPLEMENT.parent / "review-evidence/ASSEMBLY_RECEIPT.json",
    ] + [REPOSITORY / item["repository_path"] for item in manifest["required_final_root_additions"]]
    pending = [str(p.relative_to(REPOSITORY)) for p in final_paths if not p.is_file()]
    if args.require_finalized:
        require(not pending, "All final assembly and root checkpoint files exist")
        if not pending:
            receipt = read_json(SUPPLEMENT.parent / "review-evidence/ASSEMBLY_RECEIPT.json")
            override = SUPPLEMENT / "final/root-review-status-overrides.json"
            require(
                receipt.get("root_override_sha256") == fingerprint(override)["sha256"],
                "Exact final raw override matches assembly receipt",
            )
            require(receipt.get("mode") == "APPLY", "Final receipt records actual APPLY")

    print(json.dumps({
        "scope": "Supplemental source/code/package preservation only",
        "checks_passed": checks - len(failures),
        "checks_required": checks,
        "failures": failures,
        "pending_finalization_files": pending,
        "require_finalized": args.require_finalized,
        "files_written": 0,
        "art_selection_claimed": False,
        "runtime_approval_claimed": False,
        "publication_or_whole_task_approval_claimed": False,
    }, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
