#!/usr/bin/env python3
"""Validate that the isolated T10 candidate has complete critic-input evidence.

This is deliberately NOT a critic and does not assign C1/C2/C3/C4/C6/C7 scores.
It proves that the evidence each required critic needs has been captured and bound
to the isolated candidate, while preserving the post-T09 integration boundary.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/havenline/production"))
from critic_profile import resolve_critic

REQUIRED_CRITICS = ["C1", "C2", "C3", "C4", "C6", "C7"]
REQUIRED_STATES = ["ready", "blocked", "preview", "committing", "complete", "replay"]
REQUIRED_ANGLES = ["front", "side", "three-quarter", "overhead", "gameplay", "detail"]


def load(path: Path):
    if not path.exists():
        raise AssertionError(f"missing evidence: {path}")
    return json.loads(path.read_text())


def check_names(report: dict) -> set[str]:
    return {str(row.get("name")) for row in report.get("checks", []) if row.get("passed") is True}


def authority_errors(domain: dict, integration: dict, lifecycle: dict, native4k: dict, candidate: str) -> list[str]:
    errors = []
    for name, report in (("domain", domain), ("integration", integration), ("lifecycle", lifecycle), ("native4k", native4k)):
        if report.get("candidate") != candidate:
            errors.append(name + " exact candidate mismatch")
    if integration.get("fixture_simulation_only") is not False or integration.get("real_t09_adapter_bound") is not True:
        errors.append("real simulation integration proof required")
    for name, report in (("lifecycle", lifecycle), ("native4k", native4k)):
        if report.get("real_t09_adapter_bound") is not True or report.get("exact_debit_verified") is not True or report.get("fixture_only") is not False:
            errors.append(name + " requires real authority and exact debit proof")
    return errors


def package_errors(root, candidate):
    from build_critic_evidence import benchmark_errors, prompt_errors, compact_progression, digest, SCOPE_SYNOPSIS
    errors=[]
    try:
        index=load(root/'evidence-index.json')
        assert index['candidate']==candidate
        for rel,expected in index['files'].items():
            assert (root/rel).is_file() and digest(root/rel)==expected, 'indexed raw digest mismatch '+rel
        assert (root/'scope-brief.txt').read_text()==SCOPE_SYNOPSIS
        proof=compact_progression(load(root/'progression.json'))
        assert (root/'progression-brief.txt').read_text()==proof+'\nRaw critic-input/progression.json SHA256 '+digest(root/'progression.json')+'\n'
        errors.extend(benchmark_errors(load(root/'benchmark/manifest.json'),candidate))
        required={'FROZEN_SCOPE.md','recipes.json','progression.json','domain-tests.json','integration-tests.json','review-summary.json','motion-timeline.json','save-matrix/save-matrix.json','benchmark/manifest.json','performance.json'}
        for cid in ('C3','C4','C6','C7'):
            manifest=load(root/(cid+'-manifest.json'))
            assert manifest['candidate_commit']==candidate and manifest['critic_id']==cid
            entries=manifest['preserved_sources']
            assert {i['path'].removeprefix('critic-input/') for i in entries}==required
            for item in entries+[i for g in manifest['groups'] for i in g['items']]:
                assert item['path'].startswith('critic-input/'), 'canonical package path required'
                rel=item['path'].removeprefix('critic-input/')
                assert rel in index['files'] and index['files'][rel]==item['sha256'], 'manifest/index mismatch '+rel
            if cid!='C6':
                # Rebase only filesystem paths for transported package validation.
                transported=json.loads(json.dumps(manifest))
                for group in transported['groups']:
                    for item in group['items']:item['path']=item['path'].removeprefix('critic-input/')
                errors.extend(prompt_errors(transported,root,path_mode='transported'))
                categories={i['category'] for g in manifest['groups'] for i in g['items']}
                spec,_=resolve_critic('T10',cid,load(ROOT/'Docs/Production/CRITIC_EXECUTION.json'),load(ROOT/'Docs/Production/CRITIC_MATRIX.json'))
                assert set(spec['required_categories'])<=categories
                if cid in ('C3','C4'):
                    paths=[i['path'].removeprefix('critic-input/') for g in manifest['groups'] for i in g['items'] if i['kind'] in ('image','motion_frame')]
                    expected={'native4k/'+s+'-front.png' for s in REQUIRED_STATES}
                    expected|={str(p.relative_to(root)) for p in (root/'capture').glob('motion-*.png')}
                    expected|={str(p.relative_to(root)) for s in ('blocked','complete') for p in (root/'device-layout').glob('*/'+s+'-front.png')}
                    assert len(paths)==len(expected) and set(paths)==expected, 'visual coverage incomplete'
    except (KeyError,AssertionError,OSError,ValueError,TypeError) as exc: errors.append('critic package: '+str(exc))
    return errors


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence-root", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    root = Path(args.evidence_root)
    domain = load(root / "domain-tests.json")
    integration = load(root / "integration-tests.json")
    source = load(root / "source-contract.json")
    lifecycle = load(root / "capture" / "manifest.json")
    devices = load(root / "device-layout-evidence.json")
    native4k = load(root / "native4k" / "manifest.json")
    native4k_index = load(root / "native4k-evidence.json")

    errors: list[str] = []
    candidate = args.candidate
    errors.extend(package_errors(ROOT / "critic-input", candidate))
    errors.extend(authority_errors(domain, integration, lifecycle, native4k, candidate))
    execution = load(ROOT / "Docs/Production/CRITIC_EXECUTION.json")
    matrix = load(ROOT / "Docs/Production/CRITIC_MATRIX.json")
    c7_spec, _ = resolve_critic("T10", "C7", execution, matrix)
    if c7_spec.get("scope_profile") != "T10_transaction_state_integrity_v1" or matrix["task_applicability"]["T10"] != REQUIRED_CRITICS:
        errors.append("T10 critic contract mismatch")

    if source.get("candidate") != candidate:
        errors.append(f"source contract candidate mismatch: {source.get('candidate')} != {candidate}")
    if lifecycle.get("candidate") != candidate:
        errors.append(f"lifecycle candidate mismatch: {lifecycle.get('candidate')} != {candidate}")
    if native4k.get("candidate") != candidate:
        errors.append(f"native4k candidate mismatch: {native4k.get('candidate')} != {candidate}")
    if native4k_index.get("candidate") != candidate:
        errors.append(f"native4k index candidate mismatch: {native4k_index.get('candidate')} != {candidate}")

    if not domain.get("passed") or domain.get("failures"):
        errors.append("domain suite is not clean")
    if int(domain.get("check_count", 0)) < 154:
        errors.append("domain suite has fewer than 154 hardened checks")
    if domain.get("stress_targets") != 512 or domain.get("stress_transactions") != 1024:
        errors.append("domain stress cardinality mismatch")
    if domain.get("stress_retained_receipts") != 512:
        errors.append("bounded receipt history proof missing")
    if domain.get("preview_stress_iterations") != 5000 or domain.get("reject_stress_iterations") != 5000:
        errors.append("preview/reject stress proof missing")
    if domain.get("catalog_stress_recipes") != 258:
        errors.append("large recipe catalog proof missing")

    if not integration.get("passed") or integration.get("failures"):
        errors.append("fixture integration suite is not clean")
    if int(integration.get("check_count", 0)) < 75:
        errors.append("fixture integration suite has fewer than 75 R06/R11-hardened checks")
    if integration.get("simulation_models_carried_vs_stored_delivery") is not True:
        errors.append("R06 carried-vs-stored delivery model proof missing")
    if integration.get("simulation_debits_stored_only") is not True:
        errors.append("R06 stored-only debit proof missing")
    if integration.get("simulation_bounded_receipt_history_by_target") is not True:
        errors.append("R06 bounded simulation receipt history proof missing")
    if integration.get("r11_world_response_tested") is not True:
        errors.append("R11 world-response proof missing")
    if integration.get("visual_node_budget") != 4 or integration.get("visual_build_count") != 1 or integration.get("visual_node_count") != 4:
        errors.append("bounded presentation proof missing")

    if not source.get("passed"):
        errors.append("source contract is not clean")
    if lifecycle.get("passed") is not True or lifecycle.get("record_count") != 12:
        errors.append("baseline lifecycle evidence is incomplete")
    if lifecycle.get("states") != REQUIRED_STATES or lifecycle.get("angles") != ["front", "three-quarter"]:
        errors.append("baseline lifecycle state/angle contract mismatch")

    if devices.get("passed") is not True or devices.get("device_count") != 6 or devices.get("capture_count") != 36:
        errors.append("device-layout matrix evidence is incomplete")

    if native4k.get("passed") is not True or native4k.get("native_scale_1") is not True:
        errors.append("native 4K scale-1 manifest is not clean")
    if native4k.get("capture_resolution") != [3840, 2160] or native4k.get("record_count") != 36:
        errors.append("native 4K capture cardinality/resolution mismatch")
    if native4k.get("states") != REQUIRED_STATES or native4k.get("angles") != REQUIRED_ANGLES:
        errors.append("native 4K state/angle coverage mismatch")
    if native4k_index.get("passed") is not True or native4k_index.get("unique_capture_count") != 36:
        errors.append("native 4K uniqueness/index proof missing")

    if not lifecycle.get("exact_replay_verified") or lifecycle.get("motion_frames_per_state") != 30 or not (root / "capture/lifecycle.mp4").is_file():
        errors.append("continuous lifecycle and exact replay evidence required")

    saves = load(root / "save-matrix" / "save-matrix.json")
    if saves.get("candidate_commit") != candidate or saves.get("passed") is not True or len(saves.get("cases", [])) != 7 or any(x.get("passed") is not True for x in saves.get("cases", [])):
        errors.append("exact-source seven-case save matrix required")
    c6 = load(root / "C6.json")
    if c6.get("candidate") != candidate or c6.get("passed") is not True:
        errors.append("quantitative C6 required")

    domain_names = check_names(domain)
    integration_names = check_names(integration)

    required_domain_markers = {
        "preview purity is explicit",
        "one in-flight transaction per target is explicit",
        "completed receipt history is bounded per target",
        "recipe graph is monotonic except explicit inverse pairs",
        "reversible pairs require reciprocal inverse metadata",
        "duplicate recipe IDs are rejected",
        "undeclared two-state progression cycle is rejected",
        "undeclared multi-state progression cycle is rejected",
        "explicit reciprocal reversible pair configures",
        "explicit inverse returns to source without skipping revision",
        "failed cyclic reconfiguration preserves prior catalog",
        "5000 repeated previews all succeed",
        "5000 rejected commits all fail closed",
        "256 bulk recipe previews remain deterministic",
        "512-target two-stage stress completes without semantic failure",
        "stress snapshot round-trips exactly",
    }
    missing_domain = sorted(required_domain_markers - domain_names)
    if missing_domain:
        errors.append("missing domain critic markers: " + ", ".join(missing_domain))

    required_integration_markers = {
        "second transaction against same target is blocked before debit",
        "carried resources alone cannot satisfy T10 affordability",
        "R06 preview does not mutate carried or stored resources",
        "deposit moves wood from carried inventory to delivered stored",
        "deposit moves stone from carried inventory to delivered stored",
        "same transform becomes eligible only after deposit",
        "authoritative transform debit consumes stored only",
        "delivered-resource receipt advances T10 exactly once",
        "unsolicited but well-formed simulation receipt is rejected",
        "simulation can reject stale delivered resource availability",
        "pending state restores after crash",
        "simulation bounded receipt state restores after crash",
        "restored simulation replays prior debit without second mutation",
        "different targets can prepare concurrently",
        "simulation receipt history remains bounded one latest row per target",
        "higher target revision replaces bounded simulation receipt",
        "stale lower revision with old key fails closed after newer receipt",
        "blocked world response preserves exact reasons and shortfalls",
        "committing target pulse changes shape without rebuilding nodes",
        "repeated lifecycle calls create zero visual node growth",
        "view remains presentation-only after full lifecycle",
    }
    missing_integration = sorted(required_integration_markers - integration_names)
    if missing_integration:
        errors.append("missing integration critic markers: " + ", ".join(missing_integration))

    coverage = {
        "C1": {
            "focus": "reference/world-response fidelity",
            "isolated_inputs": ["36-frame native-4K multi-angle lifecycle set", "gameplay/overhead/side/three-quarter/detail coverage", "neutral T11-safe fixture"],
            "input_ready": not errors,
            "production_review_blocked_by": ["real post-T09 integrated candidate", "final integration provenance"],
        },
        "C2": {
            "focus": "technical and visual integrity",
            "isolated_inputs": ["native-4K multi-angle set", "12-frame baseline set", "4-node/1-build presentation bound", "cross-state deterministic manifest"],
            "input_ready": not errors,
            "production_review_blocked_by": ["post-T09 recapture if integration changes affected visuals"],
        },
        "C3": {
            "focus": "Havenline gameplay identity",
            "isolated_inputs": ["presentation-only authority checks", "fixture simulation exact-once flow", "carried inventory versus delivered stored-resource separation", "stored-only transform debit", "no T09/T08 mutation boundary"],
            "input_ready": not errors,
            "production_review_blocked_by": ["fresh integrated-source gameplay regression"],
        },
        "C4": {
            "focus": "gameplay UX and readability",
            "isolated_inputs": ["blocked/ready/preview/committing/complete states", "exact blocked reasons/shortfalls", "6-device/36-frame layout matrix", "native-4K gameplay/detail views"],
            "input_ready": not errors,
            "production_review_blocked_by": ["post-T09 integrated gameplay capture"],
        },
        "C6": {
            "focus": "performance and bounded growth",
            "isolated_inputs": ["512 targets/1024 transforms", "5000 previews", "5000 rejected commits", "258 recipes", "bounded T10 receipt history", "bounded simulation authority receipt history by target", "zero visual-node growth"],
            "input_ready": not errors,
            "production_review_blocked_by": ["post-integration performance regression", "physical-device certification remains T68/T69"],
        },
        "C7": {
            "focus": "progression/state integrity",
            "isolated_inputs": ["branching recipe coverage", "prerequisite enforcement", "stale/out-of-order rejection", "exact snapshot/recovery", "malformed/duplicate recipe rejection", "undeclared cycle rejection", "reciprocal reversible/inverse execution", "stale lower-revision authority rejection"],
            "input_ready": not errors,
            "production_review_blocked_by": ["source-bound C7 transactional progression proof"],
        },
    }

    report = {
        "task": "T10",
        "candidate": candidate,
        "required_critics": REQUIRED_CRITICS,
        "c7_dimensions": c7_spec["dimensions"],
        "isolated_critic_input_ready": not errors,
        "production_critic_execution_allowed": not errors,
        "integration_allowed": False,
        "task_approved": False,
        "real_t09_adapter_bound": integration.get("real_t09_adapter_bound") is True,
        "coverage": coverage,
        "remaining_integration_blockers": [
            "integration-owner acceptance and fresh integrated-source regression/evidence",
            "execute required C1/C2/C3/C4/C6/C7 production reviews with every mandatory dimension >9.0 unrounded",
        ],
        "errors": errors,
        "passed": not errors,
    }
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
