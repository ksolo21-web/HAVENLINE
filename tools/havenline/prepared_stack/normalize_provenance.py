#!/usr/bin/env python3
"""Normalize preparation provenance for Havenline tasks T13-T70 only.

This tool never edits runtime, task state, dependency status, contract blob hashes,
or any task before T13. It canonicalizes FROZEN_SCOPE provenance headers and the
existing JSON provenance keys prepared_branch, prepared_from_branch, and
prepared_from_commit while preserving all other packet content.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "Docs" / "Production"
TASK_IDS = [f"T{i:02d}" for i in range(13, 71)]
BASELINE_BRANCH = "havenline/QA-integration"
BASELINE_SHA = "ac54e55fcf034673b97a1fcb02aba833a3ad2989"
CANONICAL = f"**Forward preparation baseline:** `{BASELINE_BRANCH}` @ `{BASELINE_SHA}`"
LEGACY_PREFIX = "**Prepared from:**"
CANONICAL_PREFIX = "**Forward preparation baseline:**"
BRANCH_KEYS = {"prepared_branch", "prepared_from_branch"}
COMMIT_KEYS = {"prepared_from_commit"}
CORE_FILENAMES = ("FROZEN_SCOPE.md", "ACTIVATION_CHECKLIST.json", "PREBUILD_CONTRACT.json")
LEGACY_BRANCH_RE = re.compile(r"havenline/governance-[A-Za-z0-9._/-]*prep")


def scope_paths(root: pathlib.Path = DOCS) -> list[pathlib.Path]:
    return [root / task_id / "FROZEN_SCOPE.md" for task_id in TASK_IDS]


def checklist_paths(root: pathlib.Path = DOCS) -> list[pathlib.Path]:
    return [root / task_id / "ACTIVATION_CHECKLIST.json" for task_id in TASK_IDS]


def prebuild_paths(root: pathlib.Path = DOCS) -> list[pathlib.Path]:
    return [root / task_id / "PREBUILD_CONTRACT.json" for task_id in TASK_IDS]


def core_paths(root: pathlib.Path = DOCS) -> list[pathlib.Path]:
    return scope_paths(root) + checklist_paths(root) + prebuild_paths(root)


def task_text_paths(root: pathlib.Path = DOCS) -> list[pathlib.Path]:
    paths: list[pathlib.Path] = []
    for task_id in TASK_IDS:
        task_dir = root / task_id
        if not task_dir.is_dir():
            continue
        for path in task_dir.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".json", ".md", ".txt", ".yml", ".yaml"}:
                paths.append(path)
    return sorted(paths)


def normalize_scope_text(text: str) -> tuple[str, bool]:
    lines = text.splitlines(keepends=True)
    legacy = [i for i, line in enumerate(lines) if line.strip().startswith(LEGACY_PREFIX)]
    canonical = [i for i, line in enumerate(lines) if line.strip().startswith(CANONICAL_PREFIX)]
    if len(legacy) > 1:
        raise ValueError("multiple legacy provenance headers")
    if len(canonical) > 1:
        raise ValueError("multiple forward preparation baseline headers")
    if legacy and canonical:
        raise ValueError("both legacy and canonical provenance headers are present")

    replacement = CANONICAL + "  \n"
    changed = False
    if legacy:
        idx = legacy[0]
        if lines[idx] != replacement:
            lines[idx] = replacement
            changed = True
    elif canonical:
        idx = canonical[0]
        if lines[idx].strip() != CANONICAL:
            lines[idx] = replacement
            changed = True
    else:
        anchor = next(
            (i for i, line in enumerate(lines) if line.strip().startswith("**Authoritative runtime status:**")),
            None,
        )
        if anchor is None:
            raise ValueError("missing authoritative runtime status anchor")
        lines.insert(anchor + 1, replacement)
        changed = True

    normalized = "".join(lines)
    if LEGACY_PREFIX in normalized:
        raise ValueError("legacy provenance header survived normalization")
    if normalized.count(CANONICAL) != 1:
        raise ValueError("canonical provenance header count is not exactly one")
    return normalized, changed


def replace_json_string_value(text: str, key: str, value: str) -> tuple[str, bool]:
    pattern = re.compile(rf'("{re.escape(key)}"\s*:\s*)"(?:\\.|[^"\\])*"')
    matches = list(pattern.finditer(text))
    if len(matches) > 1:
        raise ValueError(f"duplicate JSON key refused: {key}")
    if not matches:
        return text, False
    match = matches[0]
    replacement = match.group(1) + json.dumps(value)
    if match.group(0) == replacement:
        return text, False
    return text[: match.start()] + replacement + text[match.end() :], True


def provenance_failures(obj: Any, prefix: str = "$") -> list[str]:
    failures: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            location = f"{prefix}.{key}"
            if key in BRANCH_KEYS and value != BASELINE_BRANCH:
                failures.append(f"{location}={value!r}, expected {BASELINE_BRANCH!r}")
            elif key in COMMIT_KEYS and value != BASELINE_SHA:
                failures.append(f"{location}={value!r}, expected {BASELINE_SHA!r}")
            failures.extend(provenance_failures(value, location))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            failures.extend(provenance_failures(value, f"{prefix}[{index}]"))
    return failures


def normalize_json_metadata_text(text: str) -> tuple[str, bool]:
    # Parse before editing so malformed packet JSON fails closed.
    json.loads(text)
    changed = False
    normalized = text
    for key in sorted(BRANCH_KEYS):
        normalized, did_change = replace_json_string_value(normalized, key, BASELINE_BRANCH)
        changed = changed or did_change
    for key in sorted(COMMIT_KEYS):
        normalized, did_change = replace_json_string_value(normalized, key, BASELINE_SHA)
        changed = changed or did_change
    parsed = json.loads(normalized)
    failures = provenance_failures(parsed)
    if failures:
        raise ValueError("; ".join(failures))
    return normalized, changed


def validate_core_target_set(paths: list[pathlib.Path]) -> None:
    expected = set(core_paths())
    actual = set(paths)
    if len(expected) != 174:
        raise ValueError(f"internal expected core count must be 174, got {len(expected)}")
    if actual != expected:
        missing = sorted(str(p.relative_to(ROOT)) for p in expected - actual)
        extra = sorted(str(p.relative_to(ROOT)) for p in actual - expected)
        raise ValueError(f"core artifact set mismatch; missing={missing}; extra={extra}")
    for path in paths:
        match = re.fullmatch(r"T(\d{2})", path.parent.name)
        if not match or not (13 <= int(match.group(1)) <= 70):
            raise ValueError(f"out-of-range target refused: {path}")
        if path.name not in CORE_FILENAMES:
            raise ValueError(f"unexpected core artifact refused: {path}")


def audit_task_tree(root: pathlib.Path = DOCS) -> list[str]:
    failures: list[str] = []
    for path in task_text_paths(root):
        rel = path.relative_to(ROOT)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            failures.append(f"{rel}: UTF-8 read failed: {exc}")
            continue
        legacy_refs = sorted(set(LEGACY_BRANCH_RE.findall(text)))
        if legacy_refs:
            failures.append(f"{rel}: legacy prep branch references remain: {legacy_refs}")
        if path.name == "FROZEN_SCOPE.md":
            if LEGACY_PREFIX in text:
                failures.append(f"{rel}: legacy Prepared from header remains")
            if text.count(CANONICAL) != 1:
                failures.append(f"{rel}: canonical baseline header count is {text.count(CANONICAL)}, expected 1")
        if path.suffix.lower() == ".json":
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as exc:
                failures.append(f"{rel}: malformed JSON: {exc}")
                continue
            for failure in provenance_failures(parsed):
                failures.append(f"{rel}: {failure}")
    return failures


def run(apply: bool) -> int:
    paths = core_paths()
    validate_core_target_set(paths)
    missing = [str(path.relative_to(ROOT)) for path in paths if not path.exists()]
    if missing:
        print({"scope": "T13-T70 provenance", "passed": False, "missing": missing})
        return 1

    pending: list[str] = []
    normalized_map: dict[pathlib.Path, str] = {}
    failures: list[str] = []
    for path in paths:
        try:
            original = path.read_text(encoding="utf-8")
            if path.name == "FROZEN_SCOPE.md":
                normalized, changed = normalize_scope_text(original)
            else:
                normalized, changed = normalize_json_metadata_text(original)
            normalized_map[path] = normalized
            if changed:
                pending.append(str(path.relative_to(ROOT)))
        except Exception as exc:  # fail closed with exact path
            failures.append(f"{path.relative_to(ROOT)}: {exc}")

    if failures:
        print({"scope": "T13-T70 provenance", "passed": False, "failures": failures})
        return 1

    if apply:
        pending_set = set(pending)
        for path in paths:
            if str(path.relative_to(ROOT)) in pending_set:
                path.write_text(normalized_map[path], encoding="utf-8")
        persisted_failures = audit_task_tree()
        passed = not persisted_failures
        print(
            {
                "scope": "T13-T70 provenance normalization",
                "core_artifact_count": len(paths),
                "changed_count": len(pending),
                "changed_files": pending,
                "persisted_failures": persisted_failures,
                "passed": passed,
            }
        )
        return 0 if passed else 1

    audit_failures = audit_task_tree()
    passed = not pending and not audit_failures
    print(
        {
            "scope": "T13-T70 provenance check",
            "task_count": len(TASK_IDS),
            "core_artifact_count": len(paths),
            "noncanonical_count": len(pending),
            "noncanonical_files": pending,
            "audit_failures": audit_failures,
            "passed": passed,
        }
    )
    return 0 if passed else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    return run(apply=args.apply)


if __name__ == "__main__":
    sys.exit(main())
