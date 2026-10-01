#!/usr/bin/env python3
"""Collect bounded, source-hashed diagnostics from downloaded workflow artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re

ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
SIGNAL_RE = re.compile(
    r"(?i)(assert|error|fail|fatal|traceback|timeout|exception|runtime error|script error|"
    r"parse error|mismatch|missing|invalid|blocked|score|defect)"
)
TEXT_SUFFIXES = {".json", ".jsonl", ".log", ".txt", ".md", ".out"}
MAX_FILE_BYTES = 1_000_000
MAX_LINES_PER_FILE = 24
MAX_LINE_BYTES = 1200
MAX_FILES = 40


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_failures(value, pointer="$"):
    rows = []
    if isinstance(value, dict):
        has_disposition = isinstance(value.get("passed"), bool)
        if value.get("passed") is False:
            keep = {key: value.get(key) for key in ("name", "detail", "passed") if key in value}
            rows.append((pointer, json.dumps(keep, sort_keys=True, separators=(",", ":"))))
        if has_disposition and pointer != "$":
            for key in ("errors", "failures", "fatal_error"):
                item = value.get(key)
                if value.get("passed") is False and item not in (None, [], ""):
                    rows.append((f"{pointer}.{key}", json.dumps(item, sort_keys=True, separators=(",", ":"))))
            return rows
        for key, item in value.items():
            child = f"{pointer}.{key}"
            if key in {"errors", "failures", "fatal_error"} and item not in (None, [], ""):
                rows.append((child, json.dumps(item, sort_keys=True, separators=(",", ":"))))
            rows.extend(json_failures(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            rows.extend(json_failures(item, f"{pointer}[{index}]"))
    return rows


def collect(root: pathlib.Path) -> dict:
    rows = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        raw = path.read_bytes()
        if len(raw) > MAX_FILE_BYTES:
            text = raw[:MAX_FILE_BYTES].decode("utf-8", errors="replace")
            file_truncated = True
        else:
            text = raw.decode("utf-8", errors="replace")
            file_truncated = False
        retained = []
        for number, source in enumerate(text.splitlines(), 1):
            line = ANSI_RE.sub("", source).strip()
            if not line or not SIGNAL_RE.search(line):
                continue
            if line.startswith(("{", "[")):
                try:
                    parsed = json.loads(line)
                except Exception:
                    parsed = None
                if parsed is not None:
                    projected_failures = json_failures(parsed)
                    for index, (pointer, projected) in enumerate(projected_failures, 1):
                        retained.append({"line": f"{number}.{index}", "json_pointer": pointer, "text": projected})
                        if len(retained) == MAX_LINES_PER_FILE:
                            break
                    if retained and len(retained) == MAX_LINES_PER_FILE:
                        break
                    if projected_failures:
                        continue
            encoded = line.encode("utf-8", errors="replace")
            if len(encoded) > MAX_LINE_BYTES:
                line = encoded[:MAX_LINE_BYTES].decode("utf-8", errors="ignore")
            retained.append({"line": number, "text": line})
            if len(retained) == MAX_LINES_PER_FILE:
                break
        if retained:
            rows.append({
                "path": str(path.relative_to(root)),
                "bytes": len(raw),
                "sha256": sha256(raw),
                "file_truncated_for_scan": file_truncated,
                "retained_lines": retained,
                "retained_line_count": len(retained),
            })
    rows.sort(key=lambda row: (-sum(bool(re.search(r"(?i)(assert|error|fail|fatal|traceback|runtime error)", x["text"])) for x in row["retained_lines"]), row["path"]))
    omitted = rows[MAX_FILES:]
    kept = rows[:MAX_FILES]
    return {
        "schema_version": 1,
        "artifact_root": str(root),
        "records": kept,
        "record_count": len(kept),
        "omitted_record_count": len(omitted),
        "omitted_records_sha256": sha256(json.dumps(omitted, sort_keys=True, separators=(",", ":")).encode()),
        "bounded_semantic_excerpts_only": True,
        "passed": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = pathlib.Path(args.root).resolve()
    if not root.is_dir():
        raise SystemExit("artifact root is not a directory")
    output = pathlib.Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(collect(root), indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
