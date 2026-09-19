#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from lib import DOCS, ROOT, any_match, git

# Historical migration-safe paths that predate the QA-GOV ownership alias.
# Keep this deliberately narrow. Runtime production paths are not admitted by
# ownership; only the two explicit QA capture harnesses remain exceptions.
STATIC_MIGRATION_PATTERNS = [
    "Docs/Production/**",
    "tools/havenline/production/**",
    "AGENTS.md",
    ".github/workflows/havenline-production-governance.yml",
    ".github/workflows/havenline-candidate-guard.yml",
    ".github/workflows/havenline-apply-governance-v2.yml",
    ".github/workflows/havenline-task09-harvesting.yml",
    "HavenlineGodot/tests/production_capture_harness.gd",
    "HavenlineGodot/tests/production_motion_capture.gd",
]


def _base_ownership(base: str) -> dict:
    raw = git("show", f"{base}:Docs/Production/PATH_OWNERSHIP.json")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"base PATH_OWNERSHIP.json is invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("base PATH_OWNERSHIP.json must be an object")
    return value


def governance_patterns_from_base(ownership: dict) -> list[str]:
    aliases = ownership.get("aliases", {})
    patterns = aliases.get("@ownership:QA-GOV")
    if not isinstance(patterns, list) or not patterns:
        raise ValueError("base ownership is missing @ownership:QA-GOV")

    safe: list[str] = []
    for pattern in patterns:
        if not isinstance(pattern, str) or not pattern:
            raise ValueError("base QA-GOV ownership contains an invalid pattern")
        # Never let governance ownership authorize production runtime. The only
        # HavenlineGodot paths accepted by migration are the two static QA
        # harnesses above.
        if pattern.startswith("HavenlineGodot/"):
            continue
        safe.append(pattern)
    return safe


def classify_changed_files(changed: list[str], base_ownership: dict) -> dict:
    qa_patterns = governance_patterns_from_base(base_ownership)
    allowed_patterns = list(dict.fromkeys(STATIC_MIGRATION_PATTERNS + qa_patterns))
    allowed: list[str] = []
    rejected: list[str] = []
    for path in changed:
        if any_match(path, allowed_patterns):
            allowed.append(path)
        else:
            rejected.append(path)
    return {
        "passed": not rejected,
        "changed_files": changed,
        "allowed_files": allowed,
        "rejected_files": rejected,
        "base_qa_governance_pattern_count": len(qa_patterns),
        "runtime_ownership_filtered": True,
        "candidate_cannot_self_authorize": True,
    }


def validate_scope(base: str, head: str = "HEAD") -> dict:
    if not base:
        raise ValueError("--base is required")
    # Resolve refs once so the report binds the decision to immutable commits.
    base_sha = git("rev-parse", f"{base}^{{commit}}")
    head_sha = git("rev-parse", f"{head}^{{commit}}")
    ownership = _base_ownership(base_sha)
    changed = [line for line in git("diff", "--name-only", f"{base_sha}..{head_sha}").splitlines() if line]
    result = classify_changed_files(changed, ownership)
    result.update({
        "schema_version": 1,
        "base": base_sha,
        "head": head_sha,
        "ownership_source": f"{base_sha}:Docs/Production/PATH_OWNERSHIP.json",
    })
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Havenline governance migration change scope against pre-change ownership")
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        report = validate_scope(args.base, args.head)
    except Exception as exc:
        report = {"schema_version": 1, "passed": False, "errors": [str(exc)]}
    text = json.dumps(report, indent=2) + "\n"
    print(text, end="")
    if args.output:
        path = (ROOT / args.output).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return 0 if report.get("passed") else 2


if __name__ == "__main__":
    raise SystemExit(main())
