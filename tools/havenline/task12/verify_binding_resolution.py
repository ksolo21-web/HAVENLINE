#!/usr/bin/env python3
"""Verify T12 reconciliation of accepted T10/T11 public identifiers.

Default mode is a pre-activation guard: the resolution template must remain
unresolved/blank until activation reconciliation. --require-resolved switches to
a future activation-time proof that verifies exact accepted dependency commits,
completion records and repository-backed JSON-pointer identity evidence.

This tool never edits upstream files and never promotes shipping data.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[3]
EXPECTED_TASKS = ("T10", "T11")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
FORBIDDEN_ID_MARKERS = ("provisional", "prepared", "example", "debug", "fixture", "test_only", "test-only")
EXPECTED_COMPLETION_PATHS = {
    "T10": "Docs/Production/T10/verified-completion.json",
    "T11": "Docs/Production/T11/verified-completion.json",
}
ALLOWED_ID_KINDS = {
    "T10": {"transform_state", "transform_recipe"},
    "T11": {"camp_state", "camp_recipe_binding"},
}
FACT_KIND_COMPATIBILITY = {
    "world_transform_completed": {
        "source_task": "T10",
        "accepted_id_kinds": {"transform_state", "transform_recipe"},
    },
    "camp_state_completed": {
        "source_task": "T11",
        "accepted_id_kinds": {"camp_state", "camp_recipe_binding"},
    },
}
ALLOWED_SOURCE_PREFIXES = {
    "T10": (
        "HavenlineGodot/data/world_transform_recipes.json",
        "HavenlineGodot/assets/world_transform_v1/",
    ),
    "T11": (
        "HavenlineGodot/data/camp_construction_recipes.json",
        "HavenlineGodot/assets/camp_construction_v1/",
    ),
}


def decode_pointer_token(token: str) -> str:
    return token.replace("~1", "/").replace("~0", "~")


def resolve_json_pointer(document: Any, pointer: str) -> Any:
    if pointer == "":
        return document
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ValueError("json_pointer must be empty or begin with /")
    current = document
    for raw in pointer.split("/")[1:]:
        token = decode_pointer_token(raw)
        if isinstance(current, list):
            if not token.isdigit():
                raise KeyError(token)
            index = int(token)
            current = current[index]
        elif isinstance(current, dict):
            current = current[token]
        else:
            raise KeyError(token)
    return current


def safe_repo_relative(path: str) -> bool:
    pure = pathlib.PurePosixPath(path)
    return bool(path) and not pure.is_absolute() and ".." not in pure.parts


def source_path_allowed(task: str, source_path: str) -> bool:
    return any(
        source_path == prefix or (prefix.endswith("/") and source_path.startswith(prefix))
        for prefix in ALLOWED_SOURCE_PREFIXES[task]
    )


def git_head(root: pathlib.Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def git_is_ancestor(root: pathlib.Path, ancestor: str, head: str) -> bool:
    proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, head],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return proc.returncode == 0


def git_file_bytes(root: pathlib.Path, commit: str, source_path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{source_path}"], cwd=root)


def completion_source(record: dict[str, Any]) -> str | None:
    for key in ("integrated_source", "accepted_source", "accepted_integrated_source", "candidate_source"):
        value = record.get(key)
        if isinstance(value, str) and HEX40.fullmatch(value):
            return value
    return None


def completion_passes(record: dict[str, Any]) -> bool:
    status = str(record.get("status", "")).upper()
    return status in {"PASS", "APPROVED"}


def validate_resolution(
    resolution: dict[str, Any],
    *,
    require_resolved: bool,
    root: pathlib.Path = ROOT,
    activation_head: str | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    verified_ids = 0
    globally_seen_ids: dict[str, str] = {}

    if resolution.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if resolution.get("task_id") != "T12":
        errors.append("task_id must be T12")
    allowed_kinds = resolution.get("allowed_id_kinds_by_task")
    expected_allowed_kinds = {
        task: sorted(ALLOWED_ID_KINDS[task])
        for task in EXPECTED_TASKS
    }
    normalized_allowed_kinds = {
        task: sorted(value) if isinstance(value, list) else value
        for task, value in (allowed_kinds.items() if isinstance(allowed_kinds, dict) else [])
    }
    if normalized_allowed_kinds != expected_allowed_kinds:
        errors.append("allowed_id_kinds_by_task drifted from frozen T10/T11 ID-kind contract")

    compatibility = resolution.get("fact_kind_compatibility")
    expected_compatibility = {
        fact_kind: {
            "source_task": row["source_task"],
            "accepted_id_kinds": sorted(row["accepted_id_kinds"]),
        }
        for fact_kind, row in FACT_KIND_COMPATIBILITY.items()
    }
    normalized_compatibility = {}
    if isinstance(compatibility, dict):
        for fact_kind, row in compatibility.items():
            if isinstance(row, dict):
                normalized_compatibility[fact_kind] = {
                    "source_task": row.get("source_task"),
                    "accepted_id_kinds": sorted(row.get("accepted_id_kinds", []))
                    if isinstance(row.get("accepted_id_kinds"), list)
                    else row.get("accepted_id_kinds"),
                }
    if normalized_compatibility != expected_compatibility:
        errors.append("fact_kind_compatibility drifted from frozen T10/T11 semantic binding contract")

    dependencies = resolution.get("dependencies")
    if not isinstance(dependencies, dict):
        return {"passed": False, "verified_ids": 0, "errors": ["dependencies must be an object"]}
    if set(dependencies) != set(EXPECTED_TASKS):
        errors.append(f"dependencies must contain exactly {list(EXPECTED_TASKS)}")

    resolved_head = activation_head
    if require_resolved and resolved_head is None:
        try:
            resolved_head = git_head(root)
        except Exception as exc:
            errors.append(f"cannot determine activation HEAD: {exc}")

    for task in EXPECTED_TASKS:
        entry = dependencies.get(task)
        if not isinstance(entry, dict):
            errors.append(f"missing dependency resolution entry: {task}")
            continue
        source = entry.get("accepted_integrated_source")
        ids = entry.get("resolved_public_ids")
        completion_path = entry.get("verified_completion_path")

        if not isinstance(ids, list):
            errors.append(f"{task}.resolved_public_ids must be a list")
            ids = []

        if not require_resolved:
            if source not in ("", None):
                errors.append(f"{task} accepted_integrated_source must remain blank before activation reconciliation")
            if ids:
                errors.append(f"{task} resolved_public_ids must remain empty before activation reconciliation")
            continue

        source_valid = isinstance(source, str) and HEX40.fullmatch(source) is not None
        if not source_valid:
            errors.append(f"{task} accepted_integrated_source must be an exact 40-hex commit")
        elif not isinstance(resolved_head, str) or HEX40.fullmatch(resolved_head) is None:
            errors.append(f"{task} activation head is not an exact 40-hex commit")
        else:
            try:
                if not git_is_ancestor(root, source, resolved_head):
                    errors.append(f"{task} accepted integrated source is not an ancestor of activation head")
            except Exception as exc:
                errors.append(f"{task} accepted source ancestry proof failed: {exc}")

        expected_completion = EXPECTED_COMPLETION_PATHS[task]
        if completion_path != expected_completion:
            errors.append(f"{task} verified_completion_path must be {expected_completion}")
            continue
        if not safe_repo_relative(completion_path):
            errors.append(f"{task} verified_completion_path is not repository-relative safe")
            continue
        completion_file = root / completion_path
        if not completion_file.is_file():
            errors.append(f"{task} completion record missing: {completion_path}")
            continue
        try:
            completion = json.loads(completion_file.read_text())
        except Exception as exc:
            errors.append(f"{task} completion record unreadable: {exc}")
            continue
        if not isinstance(completion, dict) or not completion_passes(completion):
            errors.append(f"{task} completion record is not PASS/APPROVED")
        accepted = completion_source(completion) if isinstance(completion, dict) else None
        if accepted is None:
            errors.append(f"{task} completion record has no recognized accepted/integrated commit field")
        elif source != accepted:
            errors.append(f"{task} resolution source {source!r} does not match completion source {accepted!r}")

        if not ids:
            errors.append(f"{task} must resolve at least one public ID before activation")
            continue

        seen: set[str] = set()
        for index, item in enumerate(ids):
            prefix = f"{task}.resolved_public_ids[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} must be an object")
                continue
            public_id = item.get("id")
            kind = item.get("kind")
            source_path = item.get("source_path")
            pointer = item.get("json_pointer")
            if not isinstance(public_id, str) or not public_id.strip():
                errors.append(f"{prefix}.id must be non-empty")
                continue
            normalized = public_id.lower()
            if any(marker in normalized for marker in FORBIDDEN_ID_MARKERS):
                errors.append(f"{prefix}.id looks provisional/test-only: {public_id}")
            if public_id in seen:
                errors.append(f"{task} duplicate resolved ID: {public_id}")
            seen.add(public_id)
            if public_id in globally_seen_ids:
                errors.append(
                    f"resolved public ID {public_id} is ambiguous across {globally_seen_ids[public_id]} and {task}"
                )
            else:
                globally_seen_ids[public_id] = task
            if not isinstance(kind, str) or not kind.strip():
                errors.append(f"{prefix}.kind must be non-empty")
            elif kind not in ALLOWED_ID_KINDS[task]:
                errors.append(
                    f"{prefix}.kind {kind!r} is not allowed for {task}; "
                    f"allowed={sorted(ALLOWED_ID_KINDS[task])}"
                )
            if not isinstance(source_path, str) or not source_path:
                errors.append(f"{prefix}.source_path must be non-empty")
                continue
            if not safe_repo_relative(source_path):
                errors.append(f"{prefix}.source_path is not repository-relative safe")
                continue
            if not source_path_allowed(task, source_path):
                errors.append(f"{prefix}.source_path is outside {task} accepted ownership: {source_path}")
                continue
            evidence_file = root / source_path
            if not evidence_file.is_file():
                errors.append(f"{prefix} source file missing: {source_path}")
                continue
            if evidence_file.suffix.lower() != ".json":
                errors.append(f"{prefix} source_path must point to JSON for exact pointer proof")
                continue
            if source_valid:
                try:
                    accepted_bytes = git_file_bytes(root, source, source_path)
                    if evidence_file.read_bytes() != accepted_bytes:
                        errors.append(
                            f"{prefix} source file drifted from accepted integrated source {source}"
                        )
                        continue
                except Exception as exc:
                    errors.append(f"{prefix} accepted-source blob proof failed: {exc}")
                    continue
            try:
                document = json.loads(evidence_file.read_text())
                resolved = resolve_json_pointer(document, pointer)
            except Exception as exc:
                errors.append(f"{prefix} pointer proof failed: {exc}")
                continue
            if resolved != public_id:
                errors.append(f"{prefix} pointer resolves to {resolved!r}, expected {public_id!r}")
                continue
            verified_ids += 1

    expected_status = "RESOLVED_FOR_ACTIVATION" if require_resolved else "PREPARATION_TEMPLATE_UNRESOLVED"
    if resolution.get("status") != expected_status:
        errors.append(f"status must be {expected_status} in this mode")
    expected_promotion = True if require_resolved else False
    if resolution.get("promotion_allowed") is not expected_promotion:
        errors.append(f"promotion_allowed must be {expected_promotion} in this mode")

    return {
        "passed": not errors,
        "mode": "require_resolved" if require_resolved else "preactivation_blank",
        "activation_head": resolved_head if require_resolved else None,
        "verified_ids": verified_ids,
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resolution", default="Docs/Production/T12/BINDING_RESOLUTION_TEMPLATE.json")
    parser.add_argument("--require-resolved", action="store_true")
    parser.add_argument("--activation-head", help="Exact activation HEAD; defaults to checked-out HEAD in resolved mode")
    args = parser.parse_args()
    resolution = json.loads(pathlib.Path(args.resolution).read_text())
    result = validate_resolution(
        resolution,
        require_resolved=args.require_resolved,
        activation_head=args.activation_head,
    )
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
