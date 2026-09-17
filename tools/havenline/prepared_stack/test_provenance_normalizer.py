#!/usr/bin/env python3
"""Focused regression tests for T13-T70 provenance normalization."""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from normalize_provenance import CANONICAL, normalize_scope_text  # noqa: E402


def main() -> int:
    failures: list[str] = []

    stale = (
        "# T13\n\n"
        "**Preparation status:** PREPARED_GOVERNANCE_ONLY  \n"
        "**Authoritative runtime status:** LOCKED  \n"
        "**Prepared from:** `havenline/governance-t12-prep` @ `oldsha`\n\n"
        "Dependencies: T12\n"
    )
    normalized, changed = normalize_scope_text(stale)
    if not changed or CANONICAL not in normalized or "**Prepared from:**" in normalized:
        failures.append("stale historical header was not replaced")
    if "Dependencies: T12" not in normalized:
        failures.append("legitimate T12 dependency text was altered")

    missing = (
        "# T70\n\n"
        "**Preparation status:** PREPARED_GOVERNANCE_ONLY  \n"
        "**Authoritative runtime status:** LOCKED\n\n"
        "## Required outcome\n"
    )
    normalized, changed = normalize_scope_text(missing)
    if not changed or normalized.count(CANONICAL) != 1:
        failures.append("missing canonical header was not inserted exactly once")

    already = (
        "# T44\n\n"
        "**Preparation status:** PREPARED_GOVERNANCE_ONLY  \n"
        "**Authoritative runtime status:** LOCKED  \n"
        f"{CANONICAL}  \n\n"
    )
    normalized, changed = normalize_scope_text(already)
    if changed or normalized != already:
        failures.append("canonical scope was not idempotent")

    ambiguous = (
        "# T13\n"
        "**Authoritative runtime status:** LOCKED\n"
        "**Prepared from:** `one` @ `a`\n"
        "**Prepared from:** `two` @ `b`\n"
    )
    try:
        normalize_scope_text(ambiguous)
        failures.append("multiple legacy headers did not fail closed")
    except ValueError:
        pass

    print({"scope": "T13-T70 provenance normalizer regression tests", "passed": not failures, "failures": failures})
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
