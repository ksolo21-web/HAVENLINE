#!/usr/bin/env python3
"""Deterministic digest for the frozen T12 pre-activation acceptance bundle."""
from __future__ import annotations

import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
CHECKLIST_RELATIVE = "Docs/Production/T12/ACTIVATION_CHECKLIST.json"
CANONICAL_CANDIDATE_GUARD = "tools/havenline/production/workstream.py"


def bundle_files(root: pathlib.Path = ROOT) -> tuple[str, ...]:
    checklist_path = root / CHECKLIST_RELATIVE
    if not checklist_path.is_file():
        raise FileNotFoundError(f"validator bundle checklist missing: {CHECKLIST_RELATIVE}")
    checklist = json.loads(checklist_path.read_text())
    support = checklist.get("prepared_support_artifacts")
    if not isinstance(support, list) or not support:
        raise ValueError("ACTIVATION_CHECKLIST prepared_support_artifacts must be a non-empty list")
    if len(support) != len(set(support)):
        raise ValueError("ACTIVATION_CHECKLIST prepared_support_artifacts contains duplicates")
    files = set(support)
    files.add(CHECKLIST_RELATIVE)
    files.add(CANONICAL_CANDIDATE_GUARD)
    return tuple(sorted(files))


def bundle_digest(root: pathlib.Path = ROOT) -> str:
    digest = hashlib.sha256()
    for relative in bundle_files(root):
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(f"validator bundle file missing: {relative}")
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def main() -> None:
    print(bundle_digest())


if __name__ == "__main__":
    main()
