#!/usr/bin/env python3
"""Focused regression tests for T13-T70 provenance normalization."""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from normalize_provenance import (  # noqa: E402
    BASELINE_BRANCH,
    BASELINE_SHA,
    CANONICAL,
    normalize_json_metadata_text,
    normalize_scope_text,
    provenance_failures,
)


def main() -> int:
    failures: list[str] = []

    stale_scope = (
        "# T13\n\n"
        "**Preparation status:** PREPARED_GOVERNANCE_ONLY  \n"
        "**Authoritative runtime status:** LOCKED  \n"
        "**Prepared from:** `havenline/governance-t12-prep` @ `oldsha`\n\n"
        "Dependencies: T12\n"
    )
    normalized, changed = normalize_scope_text(stale_scope)
    if not changed or CANONICAL not in normalized or "**Prepared from:**" in normalized:
        failures.append("stale historical scope header was not replaced")
    if "Dependencies: T12" not in normalized:
        failures.append("legitimate T12 dependency text was altered")

    missing_scope = (
        "# T70\n\n"
        "**Preparation status:** PREPARED_GOVERNANCE_ONLY  \n"
        "**Authoritative runtime status:** LOCKED\n\n"
        "## Required outcome\n"
    )
    normalized, changed = normalize_scope_text(missing_scope)
    if not changed or normalized.count(CANONICAL) != 1:
        failures.append("missing canonical scope header was not inserted exactly once")

    already_scope = (
        "# T44\n\n"
        "**Preparation status:** PREPARED_GOVERNANCE_ONLY  \n"
        "**Authoritative runtime status:** LOCKED  \n"
        f"{CANONICAL}  \n\n"
    )
    normalized, changed = normalize_scope_text(already_scope)
    if changed or normalized != already_scope:
        failures.append("canonical scope was not idempotent")

    stale_json = json.dumps(
        {
            "task_id": "T13",
            "prepared_branch": "havenline/governance-t13-t20-prep",
            "prepared_from_branch": "havenline/governance-t12-prep",
            "prepared_from_commit": "66efe083a57573b35fe4e6a3e8c9ab378d680796",
            "prepared_contract_git_blob_sha": "46d8c6c265f7c17922ec9fdc8a9c52ef924b0882",
            "future_builder_branch": "havenline/T13-challenge-director",
            "dependencies": ["T12"],
        },
        separators=(",", ":"),
    )
    normalized, changed = normalize_json_metadata_text(stale_json)
    parsed = json.loads(normalized)
    if not changed:
        failures.append("stale JSON metadata was not changed")
    if parsed.get("prepared_branch") != BASELINE_BRANCH:
        failures.append("prepared_branch was not canonicalized")
    if parsed.get("prepared_from_branch") != BASELINE_BRANCH:
        failures.append("prepared_from_branch was not canonicalized")
    if parsed.get("prepared_from_commit") != BASELINE_SHA:
        failures.append("prepared_from_commit was not canonicalized")
    if parsed.get("prepared_contract_git_blob_sha") != "46d8c6c265f7c17922ec9fdc8a9c52ef924b0882":
        failures.append("consumer contract blob hash was altered")
    if parsed.get("future_builder_branch") != "havenline/T13-challenge-director":
        failures.append("future builder branch was altered")
    if parsed.get("dependencies") != ["T12"]:
        failures.append("dependency list was altered")

    partial_json = '{"task_id":"T44","prepared_from_commit":"old","future_owner":"forest-region-builder"}'
    normalized, changed = normalize_json_metadata_text(partial_json)
    parsed = json.loads(normalized)
    if not changed or parsed.get("prepared_from_commit") != BASELINE_SHA:
        failures.append("commit-only metadata was not canonicalized")
    if "prepared_branch" in parsed or "prepared_from_branch" in parsed:
        failures.append("missing branch provenance keys were invented")

    clean_json = '{"task_id":"T70","future_owner":"final-release-owner"}'
    normalized, changed = normalize_json_metadata_text(clean_json)
    if changed or normalized != clean_json:
        failures.append("JSON without provenance keys was changed")

    bad = {"prepared_from_commit": "stale"}
    if not provenance_failures(bad):
        failures.append("noncanonical provenance object did not fail audit")

    ambiguous_scope = (
        "# T13\n"
        "**Authoritative runtime status:** LOCKED\n"
        "**Prepared from:** `one` @ `a`\n"
        "**Prepared from:** `two` @ `b`\n"
    )
    try:
        normalize_scope_text(ambiguous_scope)
        failures.append("multiple legacy scope headers did not fail closed")
    except ValueError:
        pass

    duplicate_json = '{"prepared_from_commit":"a","prepared_from_commit":"b"}'
    try:
        normalize_json_metadata_text(duplicate_json)
        failures.append("duplicate provenance JSON key did not fail closed")
    except ValueError:
        pass

    print({"scope": "T13-T70 provenance normalizer regression tests", "passed": not failures, "failures": failures})
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
