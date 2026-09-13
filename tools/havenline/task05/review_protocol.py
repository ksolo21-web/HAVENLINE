#!/usr/bin/env python3
"""Pure T05 visual-review slice planning and scope contracts."""
from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path


VIEWS = ["front", "rear", "left", "right", "three-quarter", "detail"]
PROTOCOL = "family-matched-local-scope-v3"
ROLE_DIMENSIONS = {
    "C1": ["reference_fidelity", "visual_language", "cross_view_consistency"],
    "C2": ["geometry_contact", "clipping_seams", "intentional_gap_integrity", "cross_view_integrity"],
}

NOTES = {
    "core-families": "Inspect every angle of the heated vessel, counters and six distinct pads. Pads may share a family language, but their silhouettes/trim/icon sockets must remain distinguishable without HUD text.",
    "loop-families": "Inspect fishing, processing and defense fixtures from all six required angles. T05 supplies static visual foundations and sockets only; later fishing, conveyor, processing and firing behavior is explicitly outside this task.",
    "resources-and-details": "Inspect all reusable resource props, close details, camp/lakeshore arrangements and night/blizzard conditions. Judge authored finish, grounding, legibility and cross-view consistency, not future moving-stack behavior.",
    "shipping-device-and-tracking": "Inspect the exact integrated shipping call site across landscape phone/tablet/foldable and tracking/target states. Grade T05 station visibility, scale, contact and obstruction only; T04 camera behavior is already approved.",
    "shipping-contexts-and-native": "Inspect normal camp/lakeshore/gate use, day/night/blizzard and all three 3840x2160 scale-1 frames. Preserve T01-T04; report only defects caused by T05 assets or placement.",
}


def family_files(*families: str) -> list[str]:
    return [f"families/family-{family}-{view}.png" for family in families for view in VIEWS]


FILES = {
    "core-families": family_files("hearth", "counters", "pads"),
    "loop-families": family_files("fishing", "processing", "defense"),
    "resources-and-details": family_files("resources") + [
        "component/close-hearth-front.png",
        "component/close-counter-reverse.png",
        "component/close-fishing-side.png",
        "component/close-processing-front.png",
        "component/close-defense-reverse.png",
        "component/camp-day-front.png",
        "component/camp-day-reverse.png",
        "component/lakeshore-day-front.png",
        "component/lakeshore-day-reverse.png",
        "component/camp-night-front.png",
        "component/camp-blizzard-side.png",
        "component/lakeshore-night-front.png",
    ],
    "shipping-device-and-tracking": [
        "gameplay/aspect-phone-16-9.png",
        "gameplay/aspect-phone-20-9.png",
        "gameplay/aspect-tablet-16-10.png",
        "gameplay/aspect-tablet-4-3.png",
        "gameplay/aspect-foldable-outer.png",
        "gameplay/aspect-foldable-inner.png",
        "gameplay/direction-north.png",
        "gameplay/direction-east.png",
        "gameplay/direction-south.png",
        "gameplay/direction-west.png",
        "gameplay/target-inclusion-storage.png",
        "gameplay/target-release-damped.png",
        "gameplay/resize-fold-inner-safe.png",
        "gameplay/resize-fold-inner-settled.png",
    ],
    "shipping-contexts-and-native": [
        "gameplay/gameplay-camp.png",
        "gameplay/gameplay-lakeshore.png",
        "gameplay/gameplay-west-gate.png",
        "gameplay/condition-day.png",
        "gameplay/condition-night.png",
        "gameplay/condition-blizzard.png",
        "native4k/native-gameplay-camp.png",
        "native4k/native-gameplay-lakeshore.png",
        "native4k/native-gameplay-east-river-gate.png",
    ],
}

GROUP_FAMILIES = {
    "core-families": ("hearth", "counters", "pads"),
    "loop-families": ("fishing", "processing", "defense"),
    "resources-and-details": ("resources", "hearth", "counters", "fishing", "processing", "defense"),
    "shipping-device-and-tracking": ("hearth", "counters", "pads", "fishing", "processing", "defense", "resources"),
    "shipping-contexts-and-native": ("hearth", "counters", "pads", "fishing", "processing", "defense", "resources"),
}

EXPLICIT_REFERENCE_FAMILY = {
    "component/close-hearth-front.png": "hearth",
    "component/close-counter-reverse.png": "counters",
    "component/close-fishing-side.png": "fishing",
    "component/close-processing-front.png": "processing",
    "component/close-defense-reverse.png": "defense",
    "component/camp-day-front.png": "hearth",
    "component/camp-day-reverse.png": "counters",
    "component/lakeshore-day-front.png": "fishing",
    "component/lakeshore-day-reverse.png": "processing",
    "component/camp-night-front.png": "hearth",
    "component/camp-blizzard-side.png": "defense",
    "component/lakeshore-night-front.png": "fishing",
    "gameplay/aspect-phone-16-9.png": "hearth",
    "gameplay/aspect-phone-20-9.png": "counters",
    "gameplay/aspect-tablet-16-10.png": "pads",
    "gameplay/aspect-tablet-4-3.png": "fishing",
    "gameplay/aspect-foldable-outer.png": "processing",
    "gameplay/aspect-foldable-inner.png": "defense",
    "gameplay/direction-north.png": "resources",
    "gameplay/direction-east.png": "hearth",
    "gameplay/direction-south.png": "counters",
    "gameplay/direction-west.png": "pads",
    "gameplay/target-inclusion-storage.png": "resources",
    "gameplay/target-release-damped.png": "resources",
    "gameplay/resize-fold-inner-safe.png": "counters",
    "gameplay/resize-fold-inner-settled.png": "counters",
    "gameplay/gameplay-camp.png": "hearth",
    "gameplay/gameplay-lakeshore.png": "fishing",
    "gameplay/gameplay-west-gate.png": "defense",
    "gameplay/condition-day.png": "counters",
    "gameplay/condition-night.png": "pads",
    "gameplay/condition-blizzard.png": "resources",
    "native4k/native-gameplay-camp.png": "processing",
    "native4k/native-gameplay-lakeshore.png": "fishing",
    "native4k/native-gameplay-east-river-gate.png": "defense",
}


def reference_family_for(path: str) -> str:
    if path.startswith("families/family-"):
        stem = path.removeprefix("families/family-").removesuffix(".png")
        for view in sorted(VIEWS, key=len, reverse=True):
            suffix = "-" + view
            if stem.endswith(suffix):
                return stem.removesuffix(suffix)
        raise ValueError("unknown family view: " + path)
    return EXPLICIT_REFERENCE_FAMILY[path]


def build_slice_plan(group: str, reference_paths: dict[str, list[str]]) -> list[dict]:
    """Pair every candidate exactly once with a declared, family-matched authority."""
    assert group in FILES
    buckets: dict[str, list[str]] = defaultdict(list)
    for candidate in FILES[group]:
        family = reference_family_for(candidate)
        assert family in GROUP_FAMILIES[group]
        buckets[family].append(candidate)

    slices = []
    for family in GROUP_FAMILIES[group]:
        candidates = buckets[family]
        assert candidates, f"{group} has no candidate coverage for {family}"
        refs = reference_paths.get(family, [])
        assert refs, f"{group} lacks authoritative reference pixels for {family}"
        for offset in range(0, len(candidates), 2):
            candidate_paths = candidates[offset:offset + 2]
            direct = all(path.startswith("families/") or path.startswith("component/close-") for path in candidate_paths)
            slices.append({
                "reference_family": family,
                "reference_path": refs[(offset // 2) % len(refs)],
                "candidate_paths": candidate_paths,
                "comparison_mode": "direct_family_reference" if direct else "style_feature_authority_not_scene_identity",
                "unseen_assets_out_of_scope": True,
            })

    flattened = [path for item in slices for path in item["candidate_paths"]]
    assert flattened == [path for family in GROUP_FAMILIES[group] for path in buckets[family]]
    assert len(flattened) == len(set(flattened)) == len(FILES[group])
    assert set(flattened) == set(FILES[group])
    assert {item["reference_family"] for item in slices} == set(GROUP_FAMILIES[group])
    return slices


def build_slice_contract(source: str, role: str, attempt: str, group: str, index: int, total: int, scope: dict) -> dict:
    assert role in ROLE_DIMENSIONS and group in FILES and 1 <= index <= total
    return {
        "task": "T05", "source": source, "critic_id": role, "attempt": attempt,
        "group": group, "protocol": PROTOCOL,
        "slice_scope": {
            "group": group,
            "slice": f"{index}/{total}",
            "reviewed_candidate_paths": scope["reviewed_candidate_paths"],
            "reference_family": scope["reference_family"],
            "reference_path_used": scope["reference_path"],
            "comparison_mode": scope["comparison_mode"],
            "unseen_assets_out_of_scope": True,
            "coverage_complete_definition": "all and only reviewed_candidate_paths were inspected for reference_family",
        },
    }


def build_review_prompt(source: str, role: str, contract: dict) -> str:
    role_prompt = {
        "C1": "Judge reference fidelity, bright polished sculpted Havenline visual language, normal-scale readability and consistency across all supplied views.",
        "C2": "Judge grounding/contact, clipping, seams, sockets/bounds implied by visible construction, deliberate openings versus defects and cross-view technical integrity.",
    }[role]
    base = f"""You are an independent visual critic reviewing only Havenline Task T05 at exact integrated source {source}. Each board shows one checksum-bound authoritative user-video reference on the LEFT and one or two labelled exact source-bound candidates on the RIGHT. The full T05 inventory is distributed across many slices; one slice is NEVER required to show assets assigned to another slice. Judge only the exact candidate paths and reference family declared in CURRENT SLICE SCOPE. An absent unlisted asset is out of scope and MUST NOT be reported as a defect or reduce any score. coverage_complete means every declared candidate on this slice was inspected for this slice's declared reference family; it does not mean the entire T05 inventory appears here. The reference is visual/style/feature authority, not a demand for scene-content identity in integrated context frames. T05 is a static authored visual/socket foundation. Fishing, conveyor motion, customer service, payments, combat, upgrades, actors and animations are later tasks and MUST NOT be scored as missing behavior. Context actors are scale markers, not T05 defects. Preserve approved T01-T04 environment and camera. Primitive-looking unfinished art, default/debug materials, visible penetrations, floating contact, broken silhouettes, indistinguishable pad variants or inconsistent cross-views remain defects when visible in a declared candidate. {role_prompt} Inspect every labelled candidate. Use 2-4 concise observations and no more than 4 concise defects; defects must be [] when clean and never contain words such as 'none'. Every mandatory score is 0-10. PASS requires each score strictly above 9.0 unrounded, zero defects, slice-local complete coverage and medium/high confidence. Do not average, round, excuse a visible defect, or penalize unlisted assets. Return JSON only."""
    return base + "\nCURRENT SLICE SCOPE (binding JSON): " + json.dumps(contract["slice_scope"], sort_keys=True) + "\n" + NOTES[contract["group"]]


def build_review_schema(role: str, candidate_paths: list[str], reference_path: str) -> dict:
    score_properties = {name: {"type": "number", "minimum": 0, "maximum": 10} for name in ROLE_DIMENSIONS[role]}
    return {
        "type": "object",
        "properties": {
            "observations": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 4},
            "defects": {"type": "array", "items": {"type": "string"}, "maxItems": 4},
            "coverage_complete": {"type": "boolean"},
            "reviewed_candidate_paths": {"type": "array", "items": {"type": "string", "enum": candidate_paths}, "minItems": 1, "maxItems": 2},
            "reference_path_used": {"type": "string", "enum": [reference_path]},
            "unseen_assets_out_of_scope_acknowledged": {"type": "boolean"},
            "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
            "scores": {"type": "object", "properties": score_properties, "required": ROLE_DIMENSIONS[role], "additionalProperties": False},
        },
        "required": ["observations", "defects", "coverage_complete", "reviewed_candidate_paths", "reference_path_used", "unseen_assets_out_of_scope_acknowledged", "confidence", "scores"],
        "additionalProperties": False,
    }


def expected_request_settings(role: str, attempt: str, seed: int) -> dict:
    return {
        "model": f"T05-{role}-{attempt}", "max_tokens": 1150,
        "temperature": 0.2, "top_p": 0.9, "seed": seed,
        "repeat_penalty": 1.12, "chat_template_kwargs": {"enable_thinking": False},
        "response_format_type": "json_object", "cache_prompt": False,
    }


def persist_model_response(raw_bytes: bytes, raw_path: Path, answer_path: Path, name: str) -> dict:
    """Preserve exact response bytes before any completion or JSON validation."""
    raw_path.write_bytes(raw_bytes)
    raw = json.loads(raw_bytes)
    choice = raw["choices"][0]
    if choice.get("finish_reason") != "stop":
        raise RuntimeError("truncated " + name)
    parsed = json.loads(choice["message"]["content"])
    answer_path.write_text(json.dumps(parsed, indent=2))
    return parsed


def write_incomplete_group_bundle(
    path: Path, *, source: str, role: str, attempt: str, seed: int,
    group: str, slices: list[dict], failed_slice: dict | None,
) -> dict:
    payload = {
        "schema_version": 3, "task": "T05", "source": source, "critic_id": role,
        "attempt": attempt, "seed": seed, "group": group,
        "aggregation": "incomplete; no score produced",
        "execution_complete": False, "slices": slices,
        "failed_slice": failed_slice, "aggregate_review": None,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return payload


def review_exit_code(execution_complete: bool) -> int:
    return 0 if execution_complete else 1
