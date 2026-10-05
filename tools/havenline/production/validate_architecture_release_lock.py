#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[3]
LOCK_PATH = ROOT / "Docs/Production/ARCHITECTURE_RELEASE_LOCK.json"
ACCEPTED_SOURCE = "673d7a7477cc94aef2b7bb8f3d788b1b3c47f902"
ARCHITECTURE_VERSION = "3.1"
NEXT_ARCHITECTURE_VERSION = "3.2"
EXPECTED_MANIFEST_SHA256 = "4858759f46b3c34d942082cb9fa9ea11a14eb0f871c131eb1f6eeeb26fb54c9d"
REQUIRED_CODEOWNER_LINES = (
    "/.github/CODEOWNERS @ksolo21-web",
    "/Docs/Production/ARCHITECTURE_RELEASE_LOCK.json @ksolo21-web",
    "/Docs/Production/PRODUCTION_ARCHITECTURE_V3.md @ksolo21-web",
    "/Docs/Production/PRODUCTION_ARCHITECTURE_V31_STANDARD.md @ksolo21-web",
    "/Docs/Production/CI_TOOLCHAIN_LOCK.json @ksolo21-web",
    "/Docs/Production/FORWARD_GATE_RUNNERS.json @ksolo21-web",
    "/tools/havenline/production/** @ksolo21-web",
    "/.github/workflows/havenline-*.yml @ksolo21-web",
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=check)


def load_lock() -> dict:
    return json.loads(LOCK_PATH.read_text())


def validate_manifest(cfg: dict) -> list[str]:
    errors: list[str] = []
    if cfg.get("schema_version") != 1:
        errors.append("release lock schema_version must be 1")
    if cfg.get("architecture_version") != ARCHITECTURE_VERSION:
        errors.append(f"architecture_version must remain {ARCHITECTURE_VERSION}")
    if cfg.get("accepted_source") != ACCEPTED_SOURCE:
        errors.append("accepted V3.1 source changed; open an explicit V3.2 architecture release instead")
    if cfg.get("upgrade_requires_version") != NEXT_ARCHITECTURE_VERSION:
        errors.append(f"upgrade_requires_version must be {NEXT_ARCHITECTURE_VERSION}")
    locked = cfg.get("locked_files")
    if not isinstance(locked, list) or not locked:
        errors.append("locked_files must be a non-empty list")
        locked = []
    if len(locked) != len(set(locked)):
        errors.append("locked_files contains duplicate paths")
    for path in locked:
        if not isinstance(path, str) or not path or path.startswith("/") or ".." in Path(path).parts:
            errors.append(f"unsafe locked path: {path!r}")
    policy = cfg.get("policy", {})
    required_true = (
        "accepted_source_is_byte_authority",
        "direct_modification_of_locked_files_forbidden",
        "locked_file_change_requires_explicit_v32_scope",
        "ordinary_task_repairs_may_not_reopen_v31",
        "data_ledgers_remain_dynamic",
        "codeowners_required",
        "governance_wiring_required",
        "branch_protection_is_external_admin_control",
        "authorized_direct_push_can_only_be_prevented_by_external_github_ruleset",
    )
    for key in required_true:
        if policy.get(key) is not True:
            errors.append(f"release-lock policy must keep {key}=true")
    if cfg.get("audit_path") != "Docs/Production/Archive/PRODUCTION_ARCHITECTURE_V31_AUDIT_20260917.md":
        errors.append("V3.1 acceptance audit path changed")
    if cfg.get("validator_path") != "tools/havenline/production/validate_architecture_release_lock.py":
        errors.append("release-lock validator path changed")
    return errors


def compare_locked_material(
    cfg: dict,
    current_loader: Callable[[str], bytes],
    accepted_loader: Callable[[str], bytes],
) -> tuple[list[str], list[dict]]:
    errors: list[str] = []
    records: list[dict] = []
    for rel in cfg.get("locked_files", []):
        try:
            accepted = accepted_loader(rel)
        except Exception as exc:
            errors.append(f"accepted source missing locked file {rel}: {exc}")
            continue
        try:
            current = current_loader(rel)
        except Exception as exc:
            errors.append(f"current source missing locked file {rel}: {exc}")
            continue
        accepted_hash = _sha256(accepted)
        current_hash = _sha256(current)
        records.append({"path": rel, "accepted_sha256": accepted_hash, "current_sha256": current_hash, "match": accepted_hash == current_hash})
        if accepted != current:
            errors.append(f"V3.1 locked file changed: {rel}")
    return errors, records


def validate_codeowners_text(text: str) -> list[str]:
    lines = {line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")}
    return [f"CODEOWNERS missing required architecture owner rule: {line}" for line in REQUIRED_CODEOWNER_LINES if line not in lines]


def validate_governance_text(text: str) -> list[str]:
    errors: list[str] = []
    for token in (
        "validate_architecture_release_lock.py",
        ACCEPTED_SOURCE,
        EXPECTED_MANIFEST_SHA256,
        ".github/CODEOWNERS",
    ):
        if token not in text:
            errors.append(f"production governance is not wired to the V3.1 release lock: missing {token}")
    return errors


def validate() -> dict:
    errors: list[str] = []
    manifest_bytes = LOCK_PATH.read_bytes() if LOCK_PATH.is_file() else b""
    manifest_sha = _sha256(manifest_bytes) if manifest_bytes else None
    if manifest_sha != EXPECTED_MANIFEST_SHA256:
        errors.append("ARCHITECTURE_RELEASE_LOCK.json digest changed; V3.1 is frozen")
    try:
        cfg = json.loads(manifest_bytes.decode())
    except Exception as exc:
        return {"passed": False, "architecture_version": ARCHITECTURE_VERSION, "accepted_source": ACCEPTED_SOURCE, "errors": errors + [f"unable to parse release lock: {exc}"]}
    errors += validate_manifest(cfg)

    source_check = _git("cat-file", "-e", f"{ACCEPTED_SOURCE}^{{commit}}", check=False)
    if source_check.returncode != 0:
        errors.append("accepted V3.1 source is not available in git history")
    ancestor = _git("merge-base", "--is-ancestor", ACCEPTED_SOURCE, "HEAD", check=False)
    if ancestor.returncode != 0:
        errors.append("current HEAD does not descend from the accepted V3.1 source")

    def current_loader(rel: str) -> bytes:
        return (ROOT / rel).read_bytes()

    def accepted_loader(rel: str) -> bytes:
        proc = _git("show", f"{ACCEPTED_SOURCE}:{rel}", check=False)
        if proc.returncode != 0:
            raise FileNotFoundError(proc.stderr.decode(errors="replace").strip() or rel)
        return proc.stdout

    locked_errors, records = compare_locked_material(cfg, current_loader, accepted_loader)
    errors += locked_errors

    audit_path = ROOT / cfg["audit_path"]
    if not audit_path.is_file():
        errors.append("V3.1 acceptance audit is missing")
    else:
        audit = audit_path.read_text(errors="replace")
        if ACCEPTED_SOURCE not in audit or "V3.1 architecture acceptance: PASS" not in audit:
            errors.append("V3.1 acceptance audit no longer proves the locked source/pass disposition")

    codeowners = ROOT / ".github/CODEOWNERS"
    if not codeowners.is_file():
        errors.append(".github/CODEOWNERS is missing")
    else:
        errors += validate_codeowners_text(codeowners.read_text())

    governance = ROOT / ".github/workflows/havenline-production-governance.yml"
    if not governance.is_file():
        errors.append("production governance workflow is missing")
    else:
        errors += validate_governance_text(governance.read_text())

    return {
        "passed": not errors,
        "schema_version": 1,
        "architecture_version": ARCHITECTURE_VERSION,
        "accepted_source": ACCEPTED_SOURCE,
        "upgrade_requires_version": NEXT_ARCHITECTURE_VERSION,
        "manifest_sha256": manifest_sha,
        "locked_file_count": len(cfg.get("locked_files", [])),
        "locked_files_matching": sum(1 for row in records if row["match"]),
        "external_branch_protection_required_for_admin_tamper_resistance": True,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail closed if accepted Havenline V3.1 architecture drifts without an explicit V3.2 release")
    parser.add_argument("--output")
    args = parser.parse_args()
    result = validate()
    text = json.dumps(result, indent=2) + "\n"
    print(text, end="")
    if args.output:
        path = Path(args.output)
        if not path.is_absolute():
            path = ROOT / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
