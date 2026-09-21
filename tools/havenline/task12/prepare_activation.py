#!/usr/bin/env python3
"""Validate T12 parallel preparation and activation readiness after T11 approval.

Default mode validates governance preparation only. `--activate --base <sha>`
is read-only and proves that T12 may be activated from the exact integration
head. This tool never creates the builder branch, mutates governance files, or
edits gameplay/runtime.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "Docs" / "Production"
T12_DOCS = DOCS / "T12"
CHECKLIST_PATH = T12_DOCS / "ACTIVATION_CHECKLIST.json"
GRAPH_PATH = DOCS / "DEPENDENCY_GRAPH.json"
REGISTRY_PATH = DOCS / "WORKSTREAM_REGISTRY.json"
OWNERSHIP_PATH = DOCS / "PATH_OWNERSHIP.json"
CRITICS_PATH = DOCS / "CRITIC_MATRIX.json"
GATES_PATH = DOCS / "task-gates.json"
MATRIX_PATH = T12_DOCS / "LEVEL_1_100_MATRIX.json"
RESOLUTION_TEMPLATE_PATH = T12_DOCS / "BINDING_RESOLUTION_TEMPLATE.json"
RESOLUTION_PATH = T12_DOCS / "BINDING_RESOLUTION.json"
RUNTIME_CONTRACT_PATH = T12_DOCS / "RUNTIME_INTERFACE_CONTRACT.json"
TRACEABILITY_PATH = T12_DOCS / "ACCEPTANCE_TRACEABILITY.json"
DOWNSTREAM_CONTRACT_PATH = T12_DOCS / "DOWNSTREAM_CONSUMER_CONTRACT.json"
DATA_SCHEMA_PATH = T12_DOCS / "PROGRESSION_DATA_SCHEMA.json"
ENGINE_VECTORS_PATH = T12_DOCS / "ENGINE_TEST_VECTORS.json"
CANDIDATE_EVIDENCE_TEMPLATE_PATH = T12_DOCS / "CANDIDATE_EVIDENCE_TEMPLATE.json"
CRITIC_REVIEW_TEMPLATE_PATH = T12_DOCS / "CRITIC_REVIEW_RECORD_TEMPLATE.json"
EVIDENCE_INDEX_TEMPLATE_PATH = T12_DOCS / "EVIDENCE_INDEX_TEMPLATE.json"
MATRIX_VALIDATOR = ROOT / "tools" / "havenline" / "task12" / "validate_level_matrix.py"
BINDING_VERIFIER = ROOT / "tools" / "havenline" / "task12" / "verify_binding_resolution.py"
RUNTIME_VALIDATOR = ROOT / "tools" / "havenline" / "task12" / "validate_runtime_interface.py"
TRACEABILITY_VALIDATOR = ROOT / "tools" / "havenline" / "task12" / "validate_traceability.py"
DOWNSTREAM_VALIDATOR = ROOT / "tools" / "havenline" / "task12" / "validate_downstream_contract.py"
DATA_SCHEMA_VALIDATOR = ROOT / "tools" / "havenline" / "task12" / "validate_data_schema.py"
REFERENCE_ORACLE = ROOT / "tools" / "havenline" / "task12" / "reference_progression_oracle.py"
CANDIDATE_EVIDENCE_VALIDATOR = ROOT / "tools" / "havenline" / "task12" / "validate_candidate_evidence.py"
CRITIC_REVIEW_VALIDATOR = ROOT / "tools" / "havenline" / "task12" / "validate_critic_review_records.py"
EVIDENCE_INDEX_VALIDATOR = ROOT / "tools" / "havenline" / "task12" / "validate_evidence_index.py"
FUZZ_GATE = ROOT / "tools" / "havenline" / "task12" / "fuzz_progression_contract.py"
PREBUILD_BENCHMARK = ROOT / "tools" / "havenline" / "task12" / "benchmark_prebuild_validators.py"
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def load(path: pathlib.Path):
    return json.loads(path.read_text())


def has_glob(segment: str) -> bool:
    return any(token in segment for token in ("*", "?", "["))


def literal_prefix(segment: str) -> str:
    cut = len(segment)
    for token in ("*", "?", "["):
        pos = segment.find(token)
        if pos >= 0:
            cut = min(cut, pos)
    return segment[:cut]


def literal_suffix(segment: str) -> str:
    last = -1
    for token in ("*", "?", "]"):
        pos = segment.rfind(token)
        if pos > last:
            last = pos
    return segment[last + 1:] if last >= 0 else segment


def segment_patterns_overlap(a: str, b: str) -> bool:
    if a == b:
        return True
    if not has_glob(a):
        return fnmatch.fnmatchcase(a, b)
    if not has_glob(b):
        return fnmatch.fnmatchcase(b, a)

    pa, pb = literal_prefix(a), literal_prefix(b)
    if pa and pb and not (pa.startswith(pb) or pb.startswith(pa)):
        return False
    sa, sb = literal_suffix(a), literal_suffix(b)
    if sa and sb and not (sa.endswith(sb) or sb.endswith(sa)):
        return False
    # The remaining wildcard languages are treated conservatively as possibly
    # intersecting. This avoids false negatives while still proving common
    # task-number patterns such as task12-* vs task03-* are disjoint.
    return True


def may_overlap(a: str, b: str) -> bool:
    """Return whether two repository glob patterns can match a common path."""
    a_parts = tuple(part for part in a.strip("/").split("/") if part)
    b_parts = tuple(part for part in b.strip("/").split("/") if part)
    memo: dict[tuple[int, int], bool] = {}

    def visit(i: int, j: int) -> bool:
        key = (i, j)
        if key in memo:
            return memo[key]
        if i == len(a_parts) and j == len(b_parts):
            memo[key] = True
            return True
        if i == len(a_parts):
            result = all(part == "**" for part in b_parts[j:])
            memo[key] = result
            return result
        if j == len(b_parts):
            result = all(part == "**" for part in a_parts[i:])
            memo[key] = result
            return result

        left, right = a_parts[i], b_parts[j]
        if left == "**" and right == "**":
            result = visit(i + 1, j) or visit(i, j + 1)
        elif left == "**":
            result = visit(i + 1, j) or visit(i, j + 1)
        elif right == "**":
            result = visit(i, j + 1) or visit(i + 1, j)
        elif segment_patterns_overlap(left, right):
            result = visit(i + 1, j + 1)
        else:
            result = False
        memo[key] = result
        return result

    return visit(0, 0)


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def git_is_ancestor(ancestor: str, head: str) -> bool:
    proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, head],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return proc.returncode == 0


def safe_repo_pattern(pattern: str) -> bool:
    pure = pathlib.PurePosixPath(pattern)
    return bool(pattern) and not pure.is_absolute() and ".." not in pure.parts


def completion_source(record) -> str | None:
    if not isinstance(record, dict):
        return None
    for key in ("integrated_source", "accepted_source", "accepted_integrated_source", "candidate_source"):
        value = record.get(key)
        if isinstance(value, str) and HEX40.fullmatch(value):
            return value
    return None


def registry_status(registry, task_id: str):
    if task_id in registry.get("legacy_approvals", {}):
        return "APPROVED"
    row = next((x for x in registry.get("workstreams", []) if x.get("task_id") == task_id), None)
    return (row or {}).get("status")


def run_read_only_tool(args: list[str]) -> tuple[bool, str]:
    proc = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return proc.returncode == 0, proc.stdout.strip()


def validate_dependency_closeout(
    checklist,
    graph,
    registry,
    ownership,
    gates,
    head: str,
    *,
    ancestry_check=git_is_ancestor,
) -> tuple[list[str], dict[str, str]]:
    errors: list[str] = []
    dependency_sources: dict[str, str] = {}
    dependencies = checklist.get("dependencies", [])

    for dep in dependencies:
        graph_status = graph.get("tasks", {}).get(dep, {}).get("status")
        reg_status = registry_status(registry, dep)
        if graph_status != "APPROVED":
            errors.append(f"dependency {dep} graph status is {graph_status}, not APPROVED")
        if reg_status != "APPROVED":
            errors.append(f"dependency {dep} registry status is {reg_status}, not APPROVED")
        if dep not in gates.get("approved_tasks", []):
            errors.append(f"dependency {dep} missing from task-gates approved_tasks")

    completed = gates.get("completed_task_records", {})
    for dep in ("T10", "T11"):
        record = completed.get(dep)
        if not isinstance(record, dict):
            errors.append(f"{dep} has no completed_task_records entry in task-gates")
            continue
        if str(record.get("status", "")).upper() != "APPROVED":
            errors.append(f"{dep} completed_task_records status is not APPROVED")
        source = completion_source(record)
        if source is None:
            errors.append(f"{dep} completed_task_records has no exact accepted/integrated source")
            continue
        dependency_sources[dep] = source
        if not ancestry_check(source, head):
            errors.append(f"{dep} accepted/integrated source {source} is not an ancestor of activation head {head}")

        owner_row = next(
            (x for x in ownership.get("completed_production_owners", []) if x.get("task_id") == dep),
            None,
        )
        if not isinstance(owner_row, dict) or owner_row.get("status") != "APPROVED":
            errors.append(f"{dep} is missing an APPROVED completed production owner record")
        else:
            owner_source = owner_row.get("integrated_source") or owner_row.get("accepted_source")
            if owner_source != source:
                errors.append(
                    f"{dep} completed production owner source {owner_source!r} does not match task-gates source {source!r}"
                )

    stale_owners = [
        x for x in ownership.get("active_owners", [])
        if x.get("task_id") in set(dependencies)
    ]
    if stale_owners:
        errors.append("a T12 dependency is still listed as an active owner; finish closeout before T12 activation")

    return errors, dependency_sources


def validate_preparation():
    checklist = load(CHECKLIST_PATH)
    graph = load(GRAPH_PATH)
    registry = load(REGISTRY_PATH)
    ownership = load(OWNERSHIP_PATH)
    critics = load(CRITICS_PATH)
    errors: list[str] = []

    t12 = graph.get("tasks", {}).get("T12")
    if not t12:
        errors.append("T12 is missing from DEPENDENCY_GRAPH.json")
        t12 = {}

    expected_deps = checklist["dependencies"]
    if t12.get("dependencies") != expected_deps:
        errors.append(f"T12 dependency mismatch: graph={t12.get('dependencies')} checklist={expected_deps}")

    expected_critics = checklist["required_critics"]
    if t12.get("critics") != expected_critics:
        errors.append(f"T12 critic mismatch in dependency graph: {t12.get('critics')}")
    if critics.get("task_applicability", {}).get("T12") != expected_critics:
        errors.append(f"T12 critic mismatch in CRITIC_MATRIX.json: {critics.get('task_applicability', {}).get('T12')}")

    if checklist.get("runtime_build_allowed_before_activation") is not False:
        errors.append("runtime_build_allowed_before_activation must remain false")

    planned = checklist["planned_owned_paths"]
    if not isinstance(planned, list) or not planned:
        errors.append("planned_owned_paths must be a non-empty list")
        planned = []
    if len(planned) != len(set(planned)):
        errors.append("planned T12 reservation contains duplicate paths")
    unsafe_planned = [path for path in planned if not isinstance(path, str) or not safe_repo_pattern(path)]
    if unsafe_planned:
        errors.append("planned T12 reservation contains unsafe repository paths: " + json.dumps(unsafe_planned))

    planned_alias = checklist.get("planned_owned_alias")
    if planned_alias != "@reservation:T12":
        errors.append("planned_owned_alias must remain @reservation:T12")
    if planned_alias in ownership.get("aliases", {}):
        errors.append("@reservation:T12 already exists before activation")

    protected = ownership.get("aliases", {}).get("@integration-only", [])
    collisions = []
    for candidate in planned:
        for path in protected:
            if may_overlap(candidate, path):
                collisions.append({"candidate": candidate, "protected": path})

    active_collisions = []
    for active in ownership.get("active_owners", []):
        alias = active.get("paths_alias")
        foreign = ownership.get("aliases", {}).get(alias, [])
        for candidate in planned:
            for path in foreign:
                if may_overlap(candidate, path):
                    active_collisions.append({
                        "task": active.get("task_id"),
                        "candidate": candidate,
                        "foreign": path,
                    })

    foreign_owner_collisions = []
    for alias, foreign_paths in ownership.get("aliases", {}).items():
        if alias in ("@integration-only", planned_alias) or alias.startswith("@protected:"):
            continue
        if not (alias.startswith("@reservation:") or alias.startswith("@ownership:")):
            continue
        if not isinstance(foreign_paths, list):
            continue
        for candidate in planned:
            for path in foreign_paths:
                if may_overlap(candidate, path):
                    foreign_owner_collisions.append({
                        "alias": alias,
                        "candidate": candidate,
                        "foreign": path,
                    })

    t11_checklist = DOCS / "T11" / "ACTIVATION_CHECKLIST.json"
    t11_collisions = []
    if t11_checklist.exists():
        t11_paths = load(t11_checklist).get("planned_owned_paths", [])
        for candidate in planned:
            for path in t11_paths:
                if may_overlap(candidate, path):
                    t11_collisions.append({"candidate": candidate, "t11": path})

    if collisions:
        errors.append("planned T12 reservation collides with integration-only paths: " + json.dumps(collisions))
    if active_collisions:
        errors.append("planned T12 reservation collides with active ownership: " + json.dumps(active_collisions))
    if foreign_owner_collisions:
        errors.append("planned T12 reservation collides with existing task ownership: " + json.dumps(foreign_owner_collisions))
    if t11_collisions:
        errors.append("planned T12 reservation collides with T11: " + json.dumps(t11_collisions))

    support = checklist.get("prepared_support_artifacts")
    if not isinstance(support, list) or not support:
        errors.append("prepared_support_artifacts must be a non-empty list")
        support = []
    if len(support) != len(set(support)):
        errors.append("prepared_support_artifacts contains duplicate paths")
    unsafe_support = [path for path in support if not isinstance(path, str) or not safe_repo_pattern(path)]
    if unsafe_support:
        errors.append("prepared_support_artifacts contains unsafe repository paths: " + json.dumps(unsafe_support))

    try:
        tracked_output = subprocess.check_output(
            [
                "git",
                "ls-files",
                "Docs/Production/T12",
                "tools/havenline/task12",
                ".github/workflows/havenline-task12-prep.yml",
            ],
            cwd=ROOT,
            text=True,
        )
        tracked_t12 = {line.strip() for line in tracked_output.splitlines() if line.strip()}
        manifested_t12 = set(support) | {str(CHECKLIST_PATH.relative_to(ROOT))}
        missing_manifest_entries = sorted(tracked_t12 - manifested_t12)
        stale_manifest_entries = sorted(manifested_t12 - tracked_t12)
        if missing_manifest_entries:
            errors.append("tracked T12 preparation files missing from support manifest: " + json.dumps(missing_manifest_entries))
        if stale_manifest_entries:
            errors.append("support manifest references untracked T12 files: " + json.dumps(stale_manifest_entries))
    except Exception as exc:
        errors.append(f"could not prove T12 support-manifest completeness: {exc}")

    required = [ROOT / path for path in support if isinstance(path, str) and safe_repo_pattern(path)] + [CHECKLIST_PATH]
    for path in required:
        try:
            relative = path.relative_to(ROOT)
        except ValueError:
            errors.append(f"required preparation artifact escapes repository root: {path}")
            continue
        if not path.exists() or not path.is_file() or not path.read_text().strip():
            errors.append(f"missing/empty preparation artifact: {relative}")

    matrix_passed = False
    resolution_blank_passed = False
    runtime_contract_passed = False
    traceability_passed = False
    downstream_contract_passed = False
    data_schema_passed = False
    engine_parity_passed = False
    candidate_evidence_template_passed = False
    critic_review_template_passed = False
    evidence_index_template_passed = False

    if MATRIX_VALIDATOR.exists() and MATRIX_PATH.exists():
        matrix_passed, output = run_read_only_tool([str(MATRIX_VALIDATOR), "--input", str(MATRIX_PATH)])
        if not matrix_passed:
            errors.append("non-shipping Level 1-100 matrix validation failed: " + output)
    if BINDING_VERIFIER.exists() and RESOLUTION_TEMPLATE_PATH.exists():
        resolution_blank_passed, output = run_read_only_tool([
            str(BINDING_VERIFIER),
            "--resolution",
            str(RESOLUTION_TEMPLATE_PATH),
        ])
        if not resolution_blank_passed:
            errors.append("pre-activation T10/T11 binding template guard failed: " + output)
    if RUNTIME_VALIDATOR.exists() and RUNTIME_CONTRACT_PATH.exists():
        runtime_contract_passed, output = run_read_only_tool([
            str(RUNTIME_VALIDATOR),
            "--input",
            str(RUNTIME_CONTRACT_PATH),
        ])
        if not runtime_contract_passed:
            errors.append("prepared T12 runtime-interface authority validation failed: " + output)
    if TRACEABILITY_VALIDATOR.exists() and TRACEABILITY_PATH.exists():
        traceability_passed, output = run_read_only_tool([
            str(TRACEABILITY_VALIDATOR),
            "--input",
            str(TRACEABILITY_PATH),
        ])
        if not traceability_passed:
            errors.append("T12 R01-R16 acceptance traceability validation failed: " + output)
    if DOWNSTREAM_VALIDATOR.exists() and DOWNSTREAM_CONTRACT_PATH.exists():
        downstream_contract_passed, output = run_read_only_tool([
            str(DOWNSTREAM_VALIDATOR),
            "--input",
            str(DOWNSTREAM_CONTRACT_PATH),
        ])
        if not downstream_contract_passed:
            errors.append("T12 downstream consumer boundary validation failed: " + output)
    if DATA_SCHEMA_VALIDATOR.exists() and DATA_SCHEMA_PATH.exists():
        data_schema_passed, output = run_read_only_tool([
            str(DATA_SCHEMA_VALIDATOR),
            "--input",
            str(DATA_SCHEMA_PATH),
        ])
        if not data_schema_passed:
            errors.append("T12 future shipping-data schema validation failed: " + output)
    if REFERENCE_ORACLE.exists() and ENGINE_VECTORS_PATH.exists():
        engine_parity_passed, output = run_read_only_tool([
            str(REFERENCE_ORACLE),
            "--input",
            str(ENGINE_VECTORS_PATH),
        ])
        if not engine_parity_passed:
            errors.append("T12 non-shipping engine parity vector validation failed: " + output)
    if CANDIDATE_EVIDENCE_VALIDATOR.exists() and CANDIDATE_EVIDENCE_TEMPLATE_PATH.exists():
        candidate_evidence_template_passed, output = run_read_only_tool([
            str(CANDIDATE_EVIDENCE_VALIDATOR),
            "--input",
            str(CANDIDATE_EVIDENCE_TEMPLATE_PATH),
        ])
        if not candidate_evidence_template_passed:
            errors.append("T12 candidate-evidence template validation failed: " + output)
    if CRITIC_REVIEW_VALIDATOR.exists() and CRITIC_REVIEW_TEMPLATE_PATH.exists():
        critic_review_template_passed, output = run_read_only_tool([
            str(CRITIC_REVIEW_VALIDATOR),
            "--input",
            str(CRITIC_REVIEW_TEMPLATE_PATH),
        ])
        if not critic_review_template_passed:
            errors.append("T12 per-dimension critic-review template validation failed: " + output)
    if EVIDENCE_INDEX_VALIDATOR.exists() and EVIDENCE_INDEX_TEMPLATE_PATH.exists():
        evidence_index_template_passed, output = run_read_only_tool([
            str(EVIDENCE_INDEX_VALIDATOR),
            "--input",
            str(EVIDENCE_INDEX_TEMPLATE_PATH),
        ])
        if not evidence_index_template_passed:
            errors.append("T12 complete evidence-index template validation failed: " + output)

    shipping_paths = [
        ROOT / "HavenlineGodot" / "scripts" / "progression_architecture.gd",
        ROOT / "HavenlineGodot" / "data" / "progression_levels_v1.json",
        ROOT / "HavenlineGodot" / "data" / "progression_milestones_v1.json",
    ]
    for path in shipping_paths:
        if path.exists():
            errors.append(f"shipping T12 path exists before activation: {path.relative_to(ROOT)}")

    row = next((x for x in registry.get("workstreams", []) if x.get("task_id") == "T12"), None)
    if row and row.get("status") not in ("LOCKED", "PREPARED"):
        errors.append(f"pre-activation registry T12 status must be LOCKED/PREPARED, got {row.get('status')}")
    if any(x.get("task_id") == "T12" for x in ownership.get("active_owners", [])):
        errors.append("T12 must not be an active path owner before activation")
    if any(x.get("task_id") == "T12" for x in ownership.get("completed_production_owners", [])):
        errors.append("T12 must not appear as a completed production owner before activation")
    if ownership.get("integration_branch") != registry.get("integration_branch"):
        errors.append("PATH_OWNERSHIP integration_branch must match WORKSTREAM_REGISTRY integration_branch")

    return {
        "task_id": "T12",
        "mode": "preparation",
        "integration_branch": registry.get("integration_branch", "codex/havenline-sequential-task-01"),
        "prepared_from_branch": checklist.get("prepared_from_branch"),
        "prepared_from_commit": checklist.get("prepared_from_commit"),
        "t10_current_graph_status": graph.get("tasks", {}).get("T10", {}).get("status"),
        "t11_current_graph_status": graph.get("tasks", {}).get("T11", {}).get("status"),
        "planned_owned_path_count": len(planned),
        "required_support_artifact_count": len(support),
        "integration_only_collision_count": len(collisions),
        "active_ownership_collision_count": len(active_collisions),
        "foreign_owner_collision_count": len(foreign_owner_collisions),
        "t11_collision_count": len(t11_collisions),
        "level_matrix_validation_passed": matrix_passed,
        "blank_binding_resolution_guard_passed": resolution_blank_passed,
        "runtime_interface_validation_passed": runtime_contract_passed,
        "acceptance_traceability_validation_passed": traceability_passed,
        "downstream_consumer_validation_passed": downstream_contract_passed,
        "data_schema_validation_passed": data_schema_passed,
        "engine_parity_validation_passed": engine_parity_passed,
        "candidate_evidence_template_validation_passed": candidate_evidence_template_passed,
        "critic_review_template_validation_passed": critic_review_template_passed,
        "evidence_index_template_validation_passed": evidence_index_template_passed,
        "required_critics": expected_critics,
        "runtime_build_allowed": False,
        "passed": not errors,
        "errors": errors,
    }


def validate_activation(base: str):
    prep = validate_preparation()
    if not prep["passed"]:
        return {**prep, "mode": "activation-preflight", "base": base, "passed": False}

    checklist = load(CHECKLIST_PATH)
    graph = load(GRAPH_PATH)
    registry = load(REGISTRY_PATH)
    ownership = load(OWNERSHIP_PATH)
    gates = load(GATES_PATH)
    errors: list[str] = []

    head = git_head()
    if head != base:
        errors.append(f"activation base must equal checked-out HEAD: head={head} base={base}")

    closeout_errors, dependency_sources = validate_dependency_closeout(
        checklist,
        graph,
        registry,
        ownership,
        gates,
        head,
    )
    errors.extend(closeout_errors)

    if graph.get("tasks", {}).get("T12", {}).get("status") not in ("LOCKED", "PREPARED"):
        errors.append(f"unexpected pre-activation T12 graph state: {graph.get('tasks', {}).get('T12', {}).get('status')}")

    binding_resolution_passed = False
    if not RESOLUTION_PATH.exists():
        errors.append("T10/T11 exact binding reconciliation is missing: Docs/Production/T12/BINDING_RESOLUTION.json")
    else:
        binding_resolution_passed, output = run_read_only_tool([
            str(BINDING_VERIFIER),
            "--resolution",
            str(RESOLUTION_PATH),
            "--require-resolved",
            "--activation-head",
            base,
        ])
        if not binding_resolution_passed:
            errors.append("T10/T11 exact binding reconciliation failed: " + output)

    matrix_passed, matrix_output = run_read_only_tool([str(MATRIX_VALIDATOR), "--input", str(MATRIX_PATH)])
    if not matrix_passed:
        errors.append("activation-time Level 1-100 matrix revalidation failed: " + matrix_output)

    runtime_passed, runtime_output = run_read_only_tool([str(RUNTIME_VALIDATOR), "--input", str(RUNTIME_CONTRACT_PATH)])
    if not runtime_passed:
        errors.append("activation-time runtime authority/interface revalidation failed: " + runtime_output)

    traceability_passed, traceability_output = run_read_only_tool([str(TRACEABILITY_VALIDATOR), "--input", str(TRACEABILITY_PATH)])
    if not traceability_passed:
        errors.append("activation-time R01-R16 traceability revalidation failed: " + traceability_output)

    downstream_passed, downstream_output = run_read_only_tool([
        str(DOWNSTREAM_VALIDATOR),
        "--input",
        str(DOWNSTREAM_CONTRACT_PATH),
    ])
    if not downstream_passed:
        errors.append("activation-time downstream consumer boundary revalidation failed: " + downstream_output)

    schema_passed, schema_output = run_read_only_tool([
        str(DATA_SCHEMA_VALIDATOR),
        "--input",
        str(DATA_SCHEMA_PATH),
    ])
    if not schema_passed:
        errors.append("activation-time future shipping-data schema revalidation failed: " + schema_output)

    engine_parity_passed, oracle_output = run_read_only_tool([
        str(REFERENCE_ORACLE),
        "--input",
        str(ENGINE_VECTORS_PATH),
    ])
    if not engine_parity_passed:
        errors.append("activation-time engine parity oracle failed: " + oracle_output)

    fuzz_passed, fuzz_output = run_read_only_tool([str(FUZZ_GATE)])
    if not fuzz_passed:
        errors.append("activation-time deterministic progression fuzz gate failed: " + fuzz_output)

    prebuild_benchmark_passed, benchmark_output = run_read_only_tool([str(PREBUILD_BENCHMARK)])
    if not prebuild_benchmark_passed:
        errors.append("activation-time prebuild validation benchmark failed: " + benchmark_output)

    return {
        "task_id": "T12",
        "mode": "activation-preflight",
        "base": base,
        "head": head,
        "dependencies": checklist["dependencies"],
        "future_branch": checklist["future_builder_branch"],
        "owner": checklist["future_owner"],
        "owned_alias": checklist["planned_owned_alias"],
        "level_matrix_validation_passed": matrix_passed,
        "runtime_interface_validation_passed": runtime_passed,
        "acceptance_traceability_validation_passed": traceability_passed,
        "downstream_consumer_validation_passed": downstream_passed,
        "data_schema_validation_passed": schema_passed,
        "engine_parity_validation_passed": engine_parity_passed,
        "fuzz_gate_passed": fuzz_passed,
        "prebuild_benchmark_passed": prebuild_benchmark_passed,
        "shipping_c6_satisfied_by_prebuild_benchmark": False,
        "binding_resolution_passed": binding_resolution_passed,
        "dependency_accepted_sources": dependency_sources,
        "reservation_patch": {
            "alias": checklist["planned_owned_alias"],
            "paths": checklist["planned_owned_paths"]
        },
        "claim_command": checklist["claim_template"].replace("<POST_T11_INTEGRATION_SHA>", base),
        "passed": not errors,
        "errors": errors,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--activate", action="store_true", help="Require all T12 dependencies approved and exact base/head match")
    ap.add_argument("--base", help="Exact post-T11 integration head used for T12 activation")
    args = ap.parse_args()

    if args.activate and not args.base:
        raise SystemExit("--activate requires --base <exact integration head>")

    result = validate_activation(args.base) if args.activate else validate_preparation()
    print(json.dumps(result, indent=2))
    if not result.get("passed"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
