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
PREBUILD_CONTRACT_PATH = T12_DOCS / "PREBUILD_CONTRACT.json"
UPSTREAM_BINDINGS_PATH = T12_DOCS / "UPSTREAM_BINDINGS.json"
DEFECT_LEDGER_PATH = T12_DOCS / "defect-ledger.json"
PERFORMANCE_BUDGET_PATH = T12_DOCS / "PREBUILD_PERFORMANCE_BUDGET.json"
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
ACTIVATION_DYNAMIC_ARTIFACTS = {
    "Docs/Production/T12/BINDING_RESOLUTION.json",
}
EXPECTED_BUILDER_PATHS = [
    "HavenlineGodot/scripts/progression_architecture.gd",
    "HavenlineGodot/data/progression_levels_v1.json",
    "HavenlineGodot/data/progression_milestones_v1.json",
    "HavenlineGodot/data/progression_bindings_v1.json",
    "HavenlineGodot/tests/test_task12_progression_architecture.gd",
    "HavenlineGodot/tests/test_task12_integration.gd",
    "HavenlineGodot/tests/capture_task12_progression.gd",
]


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


def validate_cross_contracts(checklist, prebuild=None, schema=None) -> list[str]:
    errors: list[str] = []
    if checklist.get("schema_version") != 1 or checklist.get("task_id") != "T12":
        errors.append("ACTIVATION_CHECKLIST identity must remain schema_version=1 task_id=T12")
    if checklist.get("preparation_status") != "PREPARED_GOVERNANCE_ONLY":
        errors.append("ACTIVATION_CHECKLIST preparation_status drifted")
    if checklist.get("prepared_branch") != "havenline/governance-t12-prep":
        errors.append("ACTIVATION_CHECKLIST prepared_branch drifted")
    if checklist.get("prepared_from_branch") != "havenline/governance-t11-prep" or checklist.get("prepared_from_commit") != "b383e450594d60b172d43ed2d60bda535ca9f225":
        errors.append("ACTIVATION_CHECKLIST preparation provenance drifted")
    if checklist.get("future_builder_branch") != "havenline/T12-progression-architecture":
        errors.append("ACTIVATION_CHECKLIST future_builder_branch drifted")
    if checklist.get("future_owner") != "progression-architecture-builder":
        errors.append("ACTIVATION_CHECKLIST future_owner drifted")
    if checklist.get("planned_owned_paths") != EXPECTED_BUILDER_PATHS:
        errors.append("ACTIVATION_CHECKLIST planned_owned_paths must remain the seven frozen shipping/runtime test paths")
    if checklist.get("activation_requires_all_dependencies_approved") is not True:
        errors.append("ACTIVATION_CHECKLIST must require all dependencies approved")
    acceptance = checklist.get("acceptance", {})
    if (
        acceptance.get("operator") != ">"
        or acceptance.get("threshold") != 9
        or acceptance.get("unrounded") is not True
        or acceptance.get("target") != 10
        or acceptance.get("zero_unresolved_mandatory_defects") is not True
    ):
        errors.append("ACTIVATION_CHECKLIST acceptance rule drifted")
    claim_template = str(checklist.get("claim_template", ""))
    for token in ("T12", "havenline/T12-progression-architecture", "@reservation:T12", "<POST_T11_INTEGRATION_SHA>"):
        if token not in claim_template:
            errors.append(f"ACTIVATION_CHECKLIST claim_template missing {token!r}")

    prebuild = load(PREBUILD_CONTRACT_PATH) if prebuild is None else prebuild
    schema = load(DATA_SCHEMA_PATH) if schema is None else schema

    if prebuild.get("schema_version") != 1 or prebuild.get("task_id") != "T12":
        errors.append("PREBUILD_CONTRACT identity must remain schema_version=1 task_id=T12")

    dependency_gate = prebuild.get("dependency_gate", {})
    if dependency_gate.get("required_approved") != checklist.get("dependencies"):
        errors.append("PREBUILD_CONTRACT dependency gate drifted from ACTIVATION_CHECKLIST")
    if dependency_gate.get("runtime_allowed_before_gate") is not False:
        errors.append("PREBUILD_CONTRACT must forbid runtime before dependency gate")

    expected_product = {
        "level_min": 1,
        "level_max": 100,
        "exact_shipping_level_record_count": 100,
        "practical_progression_every_level": True,
        "visible_improvement_target_max_gap_levels": 3,
        "major_milestone_target_interval_levels": 10,
        "connected_world": True,
        "zero_dollar_completion_required": True,
        "energy_wall_forbidden": True,
        "purchase_or_vip_gated_level_eligibility_forbidden": True,
        "difficulty_owner": "T13",
        "persistence_owner": "T14",
        "economy_owner": "T33+",
        "authored_region_owner": "T44-T52",
    }
    if prebuild.get("product_contract") != expected_product:
        errors.append("PREBUILD_CONTRACT product contract drifted from frozen T12 product invariants")

    level_fields = prebuild.get("level_record_schema", {}).get("required_fields")
    schema_level_fields = schema.get("level_record", {}).get("required_fields")
    if level_fields != schema_level_fields:
        errors.append("PREBUILD_CONTRACT level required_fields drifted from PROGRESSION_DATA_SCHEMA")

    milestone_fields = prebuild.get("milestone_schema", {}).get("required_fields")
    schema_milestone_fields = schema.get("milestone_record", {}).get("required_fields")
    if milestone_fields != schema_milestone_fields:
        errors.append("PREBUILD_CONTRACT milestone required_fields drifted from PROGRESSION_DATA_SCHEMA")

    expected_regions = [
        ("opening-frozen", "1-10", "T32"),
        ("forest", "11-20", "T44"),
        ("desert", "21-30", "T45"),
        ("underwater", "31-40", "T46"),
        ("sky", "41-50", "T47"),
        ("volcanic", "51-60", "T48"),
        ("swamp", "61-70", "T49"),
        ("ruins", "71-80", "T50"),
        ("underground", "81-90", "T51"),
        ("alien", "91-100", "T52"),
    ]
    region_rows = prebuild.get("region_band_contract")
    actual_regions = []
    if isinstance(region_rows, list):
        actual_regions = [
            (row.get("band"), row.get("approx_levels"), row.get("content_owner"))
            for row in region_rows
            if isinstance(row, dict)
        ]
    if actual_regions != expected_regions:
        errors.append("PREBUILD_CONTRACT region-band ownership/ranges drifted")

    upstream_tasks = {
        row.get("task")
        for row in prebuild.get("upstream_bindings", [])
        if isinstance(row, dict)
    }
    if upstream_tasks != {"T07", "T08", "T10", "T11"}:
        errors.append("PREBUILD_CONTRACT upstream binding task set drifted")

    fact_slot = prebuild.get("fact_slot_contract", {})
    if not isinstance(fact_slot, dict):
        errors.append("PREBUILD_CONTRACT fact_slot_contract must be an object")
        fact_slot = {}
    if fact_slot.get("namespace") != "t12.fact.slot.NNN":
        errors.append("PREBUILD_CONTRACT fact-slot namespace drifted")
    if fact_slot.get("level_1_required_fact_ids") != []:
        errors.append("PREBUILD_CONTRACT Level 1 fact-slot rule drifted")
    if fact_slot.get("levels_2_100_rule") != "exactly one matching fact slot per level":
        errors.append("PREBUILD_CONTRACT Levels 2-100 fact-slot rule drifted")
    if fact_slot.get("external_source_ids_in_level_records_forbidden") is not True:
        errors.append("PREBUILD_CONTRACT must forbid external producer IDs in level records")
    if set(fact_slot.get("resolution_states", [])) != {"RESOLVED", "DEFERRED_LATER_OWNER"}:
        errors.append("PREBUILD_CONTRACT fact-slot resolution states drifted")
    if fact_slot.get("t10_t11_exact_binding_proof_required") is not True:
        errors.append("PREBUILD_CONTRACT must require exact T10/T11 binding proof")
    if fact_slot.get("presentation_requirements_never_resolve_fact_slots") is not True:
        errors.append("PREBUILD_CONTRACT must forbid presentation requirements from resolving fact slots")
    if fact_slot.get("shipping_dataset_path") != "HavenlineGodot/data/progression_bindings_v1.json":
        errors.append("PREBUILD_CONTRACT fact-slot shipping dataset path drifted")
    if fact_slot.get("exact_shipping_binding_count") != 99:
        errors.append("PREBUILD_CONTRACT fact-slot shipping binding count must be 99")
    if fact_slot.get("shipping_top_level_fields") != ["schema_version", "task_id", "bindings"]:
        errors.append("PREBUILD_CONTRACT fact-slot shipping top-level fields drifted")
    if fact_slot.get("opening_activation_required_levels") != [3, 4, 6, 9, 10]:
        errors.append("PREBUILD_CONTRACT opening activation levels drifted")
    if set(fact_slot.get("opening_activation_required_upstream_coverage", [])) != {"T10", "T11"}:
        errors.append("PREBUILD_CONTRACT opening activation must require T10 and T11 coverage")
    if fact_slot.get("opening_activation_deferred_forbidden") is not True:
        errors.append("PREBUILD_CONTRACT opening activation must forbid deferred bindings")
    opening_rule = str(fact_slot.get("opening_activation_rule", "")).lower()
    for token in ("3,4,6,9,10", "resolved", "t10", "t11"):
        if token not in opening_rule:
            errors.append(f"PREBUILD_CONTRACT opening activation rule missing {token!r}")

    buildout = prebuild.get("preactivation_buildout", {})
    expected_buildout = {
        "authoring_blueprint": "Docs/Production/T12/AUTHORING_BLUEPRINT.json",
        "exact_authoring_level_count": 100,
        "binding_slot_catalog": "Docs/Production/T12/BINDING_SLOT_CATALOG.json",
        "exact_fact_slot_count": 100,
        "binding_index_template": "Docs/Production/T12/FACT_SLOT_BINDING_INDEX_TEMPLATE.json",
        "exact_binding_index_entry_count": 99,
        "full_vector_corpus": "Docs/Production/T12/FULL_ENGINE_VECTOR_CORPUS.json",
        "exact_full_vector_count": 398,
        "materializer": "tools/havenline/task12/materialize_progression_data.py",
        "shipping_binding_dataset": "HavenlineGodot/data/progression_bindings_v1.json",
        "reference_runtime_semantics": "Docs/Production/T12/REFERENCE_RUNTIME_SEMANTICS.json",
        "reference_runtime_engine": "tools/havenline/task12/reference_progression_engine.py",
        "out_of_order_fact_retention_required": True,
        "reference_runtime_snapshot_restore_required": True,
        "dry_run_required_before_activation": True,
        "repository_write_allowed_before_activation": False,
        "shipping_write_requires_claimed_t12_owner": True,
        "shipping_write_requires_resolved_binding_proof": True,
        "shipping_write_requires_resolved_binding_index": True,
    }
    if buildout != expected_buildout:
        errors.append("PREBUILD_CONTRACT preactivation_buildout drifted")

    schema_fact_slot = schema.get("fact_slot_contract", {})
    if not isinstance(schema_fact_slot, dict) or schema_fact_slot.get("namespace") != fact_slot.get("namespace"):
        errors.append("PREBUILD_CONTRACT fact-slot namespace drifted from PROGRESSION_DATA_SCHEMA")

    critic = prebuild.get("critic_contract", {})
    expected_critics = checklist.get("required_critics")
    if critic.get("required") != expected_critics:
        errors.append("PREBUILD_CONTRACT critic set drifted from ACTIVATION_CHECKLIST")
    if (
        critic.get("operator") != ">"
        or critic.get("threshold") != 9.0
        or critic.get("unrounded") is not True
        or critic.get("target") != 10.0
        or critic.get("zero_unresolved_mandatory_defects") is not True
        or critic.get("builder_self_review_is_independent_critic") is not False
    ):
        errors.append("PREBUILD_CONTRACT critic threshold/provenance rules drifted")

    return errors


def validate_upstream_preparation_bindings(data=None) -> list[str]:
    errors: list[str] = []
    data = load(UPSTREAM_BINDINGS_PATH) if data is None else data
    if data.get("schema_version") != 1 or data.get("task_id") != "T12":
        errors.append("UPSTREAM_BINDINGS identity must remain schema_version=1 task_id=T12")
    bindings = data.get("bindings")
    if not isinstance(bindings, dict) or set(bindings) != {"T07", "T08", "T10", "T11"}:
        errors.append("UPSTREAM_BINDINGS must contain exactly T07,T08,T10,T11")
        return errors

    expected_approved = {
        "T07": ("94b3f6c5097356a3857ebd13a77fb1e316eb06ae", "Docs/Production/T07/verified-completion.json"),
        "T08": ("9d56ea8ae972d0a0705ff8b985e13fab31dde493", "Docs/Production/T08/verified-completion.json"),
        "T10": ("eba0107def258824549fb10d81785290d0c81d97", "Docs/Production/T10/verified-completion.json"),
    }
    for task, (source, completion) in expected_approved.items():
        row = bindings.get(task, {})
        if row.get("status") != "APPROVED":
            errors.append(f"UPSTREAM_BINDINGS {task} status must be APPROVED")
        if row.get("integrated_source") != source:
            errors.append(f"UPSTREAM_BINDINGS {task} integrated_source drifted")
        if row.get("verified_completion") != completion:
            errors.append(f"UPSTREAM_BINDINGS {task} verified_completion drifted")

    t10 = bindings.get("T10", {})
    if t10.get("reconcile_at_activation") is not True:
        errors.append("UPSTREAM_BINDINGS T10 must be reverified at activation")

    t11 = bindings.get("T11", {})
    if t11.get("status") not in {"ASSIGNED_PROVISIONAL_CONTRACT", "UNRESOLVED_PROVISIONAL_CONTRACT"}:
        errors.append("UPSTREAM_BINDINGS T11 must remain unresolved/provisional before activation")
    if t11.get("branch") != "havenline/T11-camp-construction":
        errors.append("UPSTREAM_BINDINGS T11 authoritative branch drifted")
    if t11.get("reconcile_at_activation") is not True:
        errors.append("UPSTREAM_BINDINGS T11 must require activation reconciliation")
    if t11.get("reconciliation_failure") != "BLOCK_T12_ACTIVATION_AND_RAISE_CHANGE_REQUEST":
        errors.append("UPSTREAM_BINDINGS T11 reconciliation must fail closed")

    reconciliation = data.get("activation_reconciliation", {})
    if reconciliation.get("required") != ["T10", "T11"] or reconciliation.get("fail_closed") is not True:
        errors.append("UPSTREAM_BINDINGS activation reconciliation contract drifted")
    checks = reconciliation.get("checks")
    if not isinstance(checks, list) or len(checks) < 5:
        errors.append("UPSTREAM_BINDINGS activation reconciliation checks are incomplete")

    return errors


def validate_performance_budget_contract(data=None) -> list[str]:
    errors: list[str] = []
    data = load(PERFORMANCE_BUDGET_PATH) if data is None else data
    if data.get("schema_version") != 1 or data.get("task_id") != "T12":
        errors.append("PREBUILD_PERFORMANCE_BUDGET identity drifted")
    if data.get("status") != "PREPARATION_ONLY_BUDGET":
        errors.append("PREBUILD_PERFORMANCE_BUDGET status drifted")

    static = data.get("static_validation_budget", {})
    if static.get("iterations") != 500 or static.get("memory_iterations") != 100:
        errors.append("static validation iteration budget drifted")
    expected_static_limits = {
        "check_count": 19,
        "maximum_mean_ms": 20,
        "maximum_p95_ms": 25,
        "maximum_single_ms": 75,
        "maximum_retained_growth_kib": 512,
        "maximum_mean_ms_per_check": 1.0,
        "maximum_p95_ms_per_check": 1.5,
    }
    for key, expected in expected_static_limits.items():
        if static.get(key) != expected:
            errors.append(f"static validation budget {key} drifted from frozen value {expected}")
    if "19 static preparation checks" not in str(static.get("input_shape", "")):
        errors.append("static validation input_shape must enumerate the 19-check surface")
    budget_rule = str(static.get("budget_rule", "")).lower()
    for token in ("19-check", "normalized", "unbounded"):
        if token not in budget_rule:
            errors.append(f"static validation budget_rule missing {token!r}")

    fuzz = data.get("fuzz_budget", {})
    if fuzz.get("cases") != 250 or fuzz.get("minimum_rejected_mutations") != 250:
        errors.append("fuzz budget must require 250/250 rejected malformed cases")
    mutation_classes = fuzz.get("mutation_classes")
    if not isinstance(mutation_classes, list) or len(mutation_classes) != 30 or len(set(mutation_classes)) != 30:
        errors.append("fuzz mutation_classes must contain exactly 30 unique classes")
    if fuzz.get("deterministic_seed") != 1200:
        errors.append("fuzz deterministic seed drifted")
    if not isinstance(fuzz.get("maximum_total_seconds"), (int, float)) or fuzz.get("maximum_total_seconds") <= 0:
        errors.append("fuzz maximum_total_seconds must be positive")

    shipping = data.get("shipping_c6_boundary", {})
    if shipping.get("required_after_activation") is not True or shipping.get("critics") != ["C6"]:
        errors.append("shipping C6 boundary must remain required and owned by C6")
    if "cannot approve or waive shipping C6" not in str(shipping.get("rule", "")):
        errors.append("prebuild budget must explicitly remain unable to waive shipping C6")
    return errors


def validate_defect_ledger_preparation(ledger=None) -> list[str]:
    errors: list[str] = []
    ledger = load(DEFECT_LEDGER_PATH) if ledger is None else ledger
    if ledger.get("schema_version") != 1 or ledger.get("task_id") != "T12":
        errors.append("T12 defect ledger identity drifted")
    if ledger.get("mode") != "PREPARATION":
        errors.append("T12 defect ledger must remain PREPARATION before activation")
    if ledger.get("mandatory_defects") != []:
        errors.append("T12 preparation has unresolved mandatory defects in defect-ledger.json")

    blockers = ledger.get("dependency_blockers")
    if not isinstance(blockers, list):
        errors.append("T12 dependency_blockers must be a list")
        return errors
    by_dep = {row.get("dependency"): row for row in blockers if isinstance(row, dict)}
    if set(by_dep) != {"T10", "T11"}:
        errors.append("T12 dependency blocker set must contain exactly T10 and T11")
        return errors
    t10 = by_dep["T10"]
    if t10.get("status") != "RESOLVED":
        errors.append("T10 dependency blocker must remain RESOLVED")
    evidence = t10.get("resolution_evidence", {})
    if evidence.get("integrated_source") != "eba0107def258824549fb10d81785290d0c81d97":
        errors.append("T10 defect-ledger integrated source drifted")
    t11 = by_dep["T11"]
    if t11.get("status") != "OPEN_EXPECTED":
        errors.append("T11 dependency blocker must remain OPEN_EXPECTED until authoritative closeout")
    if t11.get("branch") != "havenline/T11-camp-construction":
        errors.append("T11 defect-ledger branch drifted")

    rule = ledger.get("acceptance_rule", {})
    if (
        rule.get("operator") != ">"
        or rule.get("threshold") != 9.0
        or rule.get("unrounded") is not True
        or rule.get("target") != 10.0
        or rule.get("zero_unresolved_mandatory_defects") is not True
    ):
        errors.append("T12 defect-ledger acceptance rule drifted")
    return errors


def validate_preparation():
    checklist = load(CHECKLIST_PATH)
    graph = load(GRAPH_PATH)
    registry = load(REGISTRY_PATH)
    ownership = load(OWNERSHIP_PATH)
    critics = load(CRITICS_PATH)
    errors: list[str] = []
    errors.extend(validate_cross_contracts(checklist))
    errors.extend(validate_upstream_preparation_bindings())
    errors.extend(validate_defect_ledger_preparation())
    errors.extend(validate_performance_budget_contract())

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
        dynamic_present = {
            relative
            for relative in ACTIVATION_DYNAMIC_ARTIFACTS
            if (ROOT / relative).is_file()
        }
        manifested_t12 = set(support) | {str(CHECKLIST_PATH.relative_to(ROOT))} | dynamic_present
        missing_manifest_entries = sorted(tracked_t12 - manifested_t12)
        stale_manifest_entries = sorted((manifested_t12 - dynamic_present) - tracked_t12)
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
        ROOT / "HavenlineGodot" / "data" / "progression_bindings_v1.json",
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
