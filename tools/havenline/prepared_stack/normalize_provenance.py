#!/usr/bin/env python3
"""Normalize provenance headers for prepared Havenline tasks T13-T70 only.

This tool never edits runtime, task state, dependency status, or any task before T13.
It canonicalizes the preparation-baseline header in each T13-T70 FROZEN_SCOPE.md.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "Docs" / "Production"
TASK_IDS = [f"T{i:02d}" for i in range(13, 71)]
BASELINE_SHA = "ac54e55fcf034673b97a1fcb02aba833a3ad2989"
CANONICAL = (
    "**Forward preparation baseline:** `havenline/QA-integration` @ "
    f"`{BASELINE_SHA}`"
)
LEGACY_PREFIX = "**Prepared from:**"
CANONICAL_PREFIX = "**Forward preparation baseline:**"


def scope_paths(root: pathlib.Path = DOCS) -> list[pathlib.Path]:
    return [root / task_id / "FROZEN_SCOPE.md" for task_id in TASK_IDS]


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


def validate_target_set(paths: list[pathlib.Path]) -> None:
    if len(paths) != 58:
        raise ValueError(f"expected 58 T13-T70 scopes, found {len(paths)}")
    expected = set(scope_paths())
    actual = set(paths)
    if actual != expected:
        missing = sorted(str(p.relative_to(ROOT)) for p in expected - actual)
        extra = sorted(str(p.relative_to(ROOT)) for p in actual - expected)
        raise ValueError(f"scope set mismatch; missing={missing}; extra={extra}")
    for path in paths:
        match = re.fullmatch(r"T(\d{2})", path.parent.name)
        if not match or not (13 <= int(match.group(1)) <= 70):
            raise ValueError(f"out-of-range target refused: {path}")


def run(apply: bool) -> int:
    paths = scope_paths()
    validate_target_set(paths)
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
            normalized, changed = normalize_scope_text(original)
            normalized_map[path] = normalized
            if changed:
                pending.append(str(path.relative_to(ROOT)))
        except Exception as exc:  # fail closed with exact path
            failures.append(f"{path.relative_to(ROOT)}: {exc}")

    if failures:
        print({"scope": "T13-T70 provenance", "passed": False, "failures": failures})
        return 1

    if apply:
        for path in paths:
            if str(path.relative_to(ROOT)) in pending:
                path.write_text(normalized_map[path], encoding="utf-8")
        # Re-read and verify the exact persisted result.
        persisted_failures = []
        for path in paths:
            text = path.read_text(encoding="utf-8")
            if LEGACY_PREFIX in text or text.count(CANONICAL) != 1:
                persisted_failures.append(str(path.relative_to(ROOT)))
        passed = not persisted_failures
        print(
            {
                "scope": "T13-T70 provenance normalization",
                "changed_count": len(pending),
                "changed_files": pending,
                "persisted_failures": persisted_failures,
                "passed": passed,
            }
        )
        return 0 if passed else 1

    passed = not pending
    print(
        {
            "scope": "T13-T70 provenance check",
            "task_count": len(paths),
            "noncanonical_count": len(pending),
            "noncanonical_files": pending,
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
