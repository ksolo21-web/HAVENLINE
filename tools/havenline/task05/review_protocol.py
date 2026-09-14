#!/usr/bin/env python3
"""Pure T05 visual-review slice planning and scope contracts."""
from __future__ import annotations

from collections import defaultdict
import json
import math
from pathlib import Path


VIEWS = ["front", "rear", "left", "right", "three-quarter", "detail"]
PROTOCOL = "family-focus-local-scope-v4"
ROLE_DIMENSIONS = {
    "C1": ["reference_fidelity", "visual_language", "cross_view_consistency"],
    "C2": ["geometry_contact", "clipping_seams", "intentional_gap_integrity", "cross_view_integrity"],
}

GROUP_DISPLAY_NAMES = {
    "core-families": "station-family turntables",
    "loop-families": "fixture-family turntables",
    "resources-and-details": "resource, detail, and environment-context views",
    "shipping-device-and-tracking": "landscape device-matrix and approved camera-state views",
    "shipping-contexts-and-native": "integrated context and native-4K views",
}

FAMILY_NOTES = {
    "hearth": "Judge only the visible heated-vessel/hearth construction, authored finish, grounding, and readability.",
    "counters": "Judge only the visible service-counter construction, authored finish, work surfaces, grounding, and readability. Do not require pad variants or catalog metadata.",
    "pads": "Judge only visible pad silhouettes, trim differentiation, icon-socket presentation, grounding, and readability. Do not require unrelated stations.",
    "fishing": "Judge only visible fishing fixture/prop construction, authored finish, grounding, and readability. A close-detail view is not required to show shoreline or water.",
    "processing": "Judge only visible processing fixture construction, authored finish, openings, grounding, and readability. Motion and processing behavior are out of scope.",
    "defense": "Judge only visible defense fixture construction, authored finish, grounding, and readability. Firing, targeting, and damage behavior are out of scope.",
    "resources": "Judge only visible resource-prop construction, authored finish, grounding, differentiation, and readability. Moving-stack behavior is out of scope.",
}

REFERENCE_FOCUS_BOXES = {
    "hearth": [90, 380, 1000, 1560],
    "counters": [380, 1100, 1060, 1850],
    "pads": [150, 620, 980, 1570],
    "fishing": [250, 650, 1020, 1550],
    "processing": [80, 400, 1080, 1550],
    "defense": [140, 350, 1000, 1450],
    "resources": [50, 420, 1000, 1600],
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

REVIEW_ROLES = ("C1", "C2")


def build_primary_matrix(mode: str, recovery_targets_json: str = "[]") -> dict:
    """Build an exact, validated matrix for full or selected primary execution."""
    if mode not in {"primary", "recover", "adjudicate"}:
        raise ValueError("unknown review mode")
    all_pairs = [(role, group) for role in REVIEW_ROLES for group in FILES]
    if mode == "recover":
        targets = json.loads(recovery_targets_json)
        allowed = {f"{role}:{group}" for role, group in all_pairs}
        if not isinstance(targets, list) or not targets:
            raise ValueError("recover mode requires at least one target")
        if not all(isinstance(target, str) for target in targets):
            raise ValueError("recovery targets must be strings")
        if len(targets) != len(set(targets)) or not set(targets) <= allowed:
            raise ValueError("invalid or duplicate recovery target")
        pairs = [target.split(":", 1) for target in targets]
    else:
        pairs = all_pairs
    return {"include": [{"critic": role, "group": group} for role, group in pairs]}

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


def applicable_dimensions(role: str, candidate_paths: list[str]) -> list[str]:
    """A single candidate cannot provide cross-view evidence."""
    dimensions = list(ROLE_DIMENSIONS[role])
    if len(candidate_paths) == 1:
        dimensions = [name for name in dimensions if not name.startswith("cross_view_")]
    return dimensions


def slice_note(scope: dict) -> str:
    paths = scope["candidate_paths"]
    conditions = []
    joined = " ".join(paths)
    for condition in ("day", "night", "blizzard"):
        if condition in joined:
            conditions.append(condition)
    note = FAMILY_NOTES[scope["reference_family"]]
    if conditions:
        note += " The candidate's required scene condition is " + "/".join(conditions) + "; it must not be penalized for differing from the reference frame's condition."
    if any("direction-" in path for path in paths):
        note += " Approved camera-direction changes can reverse screen position; do not call that a layout inconsistency."
    if any("aspect-" in path or "fold-" in path or "resize-" in path for path in paths):
        note += " Aspect/fold/resize differences are approved T04 framing states; grade only T05 visibility, contact, and obstruction."
    if len(paths) == 1:
        note += " This slice has one candidate, so no cross-view dimension is applicable or requested."
    return note


def build_slice_contract(source: str, role: str, attempt: str, group: str, index: int, total: int, scope: dict) -> dict:
    assert role in ROLE_DIMENSIONS and group in FILES and 1 <= index <= total
    return {
        "task": "T05", "source": source, "critic_id": role, "attempt": attempt,
        "group": group, "protocol": PROTOCOL,
        "slice_scope": {
            "review_context": GROUP_DISPLAY_NAMES[group],
            "slice": f"{index}/{total}",
            "reviewed_candidate_paths": scope["reviewed_candidate_paths"],
            "reference_family": scope["reference_family"],
            "reference_path_used": scope["reference_path"],
            "comparison_mode": scope["comparison_mode"],
            "unseen_assets_out_of_scope": True,
            "coverage_complete_definition": "all and only reviewed_candidate_paths were inspected for reference_family",
            "applicable_dimensions": applicable_dimensions(role, scope["reviewed_candidate_paths"]),
            "slice_specific_instruction": slice_note({**scope, "candidate_paths": scope["reviewed_candidate_paths"]}),
        },
    }


def build_review_prompt(source: str, role: str, contract: dict) -> str:
    role_prompt = {
        "C1": "Judge reference fidelity, bright polished sculpted Havenline visual language, normal-scale readability and consistency across all supplied views.",
        "C2": "Judge visible grounding/contact, clipping, seams, deliberate openings versus defects, and cross-view technical integrity only when multiple views are supplied.",
    }[role]
    base = f"""You are an independent visual critic reviewing only Havenline Task T05 at exact integrated source {source}. Each board shows a checksum-bound focused crop of one authoritative user-video reference on the LEFT and one or two labelled exact source-bound candidates on the RIGHT. The full T05 inventory is distributed across many slices; one slice is NEVER required to show assets, views, contexts, or conditions assigned to another slice. Judge only the exact candidate paths, reference family, applicable dimensions, and slice-specific instruction declared in CURRENT SLICE SCOPE. An absent unlisted asset is out of scope and MUST NOT be reported as a defect or reduce any score. coverage_complete means every declared candidate on this slice was inspected for this slice's declared reference family; it does not mean the entire T05 inventory appears here. The reference is visual/style/feature authority, not a demand for scene-content identity. A close-detail candidate is not required to contain its surrounding environment. T05 is a static authored visual/socket foundation. Fishing, conveyor motion, customer service, payments, combat, upgrades, actors and animations are later tasks and MUST NOT be scored as missing behavior. Context actors are scale markers, not T05 defects. 'Shipping' means release/build use and is not an in-scene device or object. Preserve approved T01-T04 environment and camera. Do not infer missing catalog metadata, hidden sockets, bounds, controls, behavior, or HUD from pixels; deterministic audits cover those requirements. Primitive-looking unfinished art, default/debug materials, visible penetrations, floating contact, broken silhouettes, indistinguishable visible pad variants, or inconsistent supplied views remain defects only when visibly localized in a declared candidate. {role_prompt} Inspect every labelled candidate. Use 2-4 concise observations and no more than 4 concise defects. Each defect must have one matching defect_evidence entry naming a declared candidate path, applicable dimension, visible region, and precise visible description. A score at or below 9.0 must have matching localized defect evidence for that dimension. Defects and defect_evidence must both be [] when clean. Every requested score is 0-10. PASS requires each applicable score strictly above 9.0 unrounded, zero defects, slice-local complete coverage and medium/high confidence. Do not average, round, excuse a visible defect, or penalize unlisted content. Return JSON only."""
    return base + "\nCURRENT SLICE SCOPE (binding JSON): " + json.dumps(contract["slice_scope"], sort_keys=True)


def build_review_schema(role: str, candidate_paths: list[str], reference_path: str) -> dict:
    dimensions = applicable_dimensions(role, candidate_paths)
    score_properties = {name: {"type": "number", "minimum": 0, "maximum": 10} for name in dimensions}
    properties = {
            "observations": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 4},
            "defect_evidence": {"type": "array", "items": {
                "type": "object",
                "properties": {
                    "candidate_path": {"type": "string", "enum": candidate_paths},
                    "dimension": {"type": "string", "enum": dimensions},
                    "visible_region": {"type": "string", "minLength": 3},
                    "description": {"type": "string", "minLength": 8},
                },
                "required": ["candidate_path", "dimension", "visible_region", "description"],
                "additionalProperties": False,
            }, "maxItems": 4},
            "coverage_complete": {"type": "boolean"},
            "reviewed_candidate_paths": {"type": "array", "items": {"type": "string", "enum": candidate_paths}, "minItems": 1, "maxItems": 2},
            "reference_path_used": {"type": "string", "enum": [reference_path]},
            "unseen_assets_out_of_scope_acknowledged": {"type": "boolean"},
            "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
            "scores": {"type": "object", "properties": score_properties, "required": dimensions, "additionalProperties": False},
    }
    properties = {"observations": properties.pop("observations"), "defects": {"type": "array", "items": {"type": "string"}, "maxItems": 4}, **properties}
    required = ["observations", "defects", "defect_evidence", "coverage_complete", "reviewed_candidate_paths", "reference_path_used", "unseen_assets_out_of_scope_acknowledged", "confidence", "scores"]
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def review_integrity_errors(review: dict, role: str, candidate_paths: list[str]) -> list[str]:
    """Reject unsupported scores and defects before they can become a vote."""
    errors = []
    dimensions = set(applicable_dimensions(role, candidate_paths))
    scores = review.get("scores", {})
    if set(scores) != dimensions or any(
        isinstance(value, bool) or not isinstance(value, (int, float))
        or not math.isfinite(value) or not 0 <= value <= 10
        for value in scores.values()
    ):
        return ["scores do not match the slice's applicable dimensions"]
    defects = review.get("defects")
    evidence = review.get("defect_evidence")
    if not isinstance(defects, list) or not all(isinstance(value, str) and value.strip() for value in defects):
        errors.append("defects must be a list of non-empty descriptions")
        defects = []
    if not isinstance(evidence, list):
        errors.append("defect_evidence must be a list")
        evidence = []
    descriptions = []
    evidenced_dimensions = set()
    for item in evidence:
        if not isinstance(item, dict) or set(item) != {"candidate_path", "dimension", "visible_region", "description"}:
            errors.append("defect evidence has an invalid structure")
            continue
        if item["candidate_path"] not in candidate_paths or item["dimension"] not in dimensions:
            errors.append("defect evidence is outside the bound slice scope")
        if not isinstance(item["visible_region"], str) or len(item["visible_region"].strip()) < 3:
            errors.append("defect evidence lacks a visible region")
        if not isinstance(item["description"], str) or len(item["description"].strip()) < 8:
            errors.append("defect evidence lacks a precise description")
        descriptions.append(item.get("description"))
        evidenced_dimensions.add(item.get("dimension"))
    if defects != descriptions:
        errors.append("defects must exactly match ordered defect-evidence descriptions")
    for dimension, score in scores.items():
        if score <= 9.0 and dimension not in evidenced_dimensions:
            errors.append("score at or below 9.0 lacks localized defect evidence for " + dimension)
    for dimension in evidenced_dimensions:
        if scores.get(dimension, 10.0) > 9.0:
            errors.append("localized defect evidence is inconsistent with a passing score for " + str(dimension))
    return errors


def materialize_defect_summary(review: dict) -> tuple[dict, bool]:
    """Derive the redundant defect summary from authoritative localized evidence.

    The exact model answer remains preserved separately. The derived list has the
    same cardinality as defect_evidence, so it cannot hide evidence or turn a
    failing visual judgment into a passing one.
    """
    defects = review.get("defects")
    evidence = review.get("defect_evidence")
    if not isinstance(defects, list) or not isinstance(evidence, list):
        return review, False
    descriptions = [
        item.get("description") if isinstance(item, dict) else None
        for item in evidence
    ]
    if not all(isinstance(value, str) and value.strip() for value in defects):
        return review, False
    if not all(isinstance(value, str) and value.strip() for value in descriptions):
        if defects == descriptions == []:
            return review, False
        return review, False
    if not defects and not evidence:
        return review, False
    if not defects or not evidence or len(defects) != len(evidence):
        return review, False
    materialized = dict(review)
    materialized["defects"] = descriptions
    return materialized, defects != descriptions


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
    schema_version: int = 4,
) -> dict:
    payload = {
        "schema_version": schema_version, "task": "T05", "source": source, "critic_id": role,
        "attempt": attempt, "seed": seed, "group": group,
        "aggregation": "incomplete; no score produced",
        "execution_complete": False, "slices": slices,
        "failed_slice": failed_slice, "aggregate_review": None,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return payload


def review_exit_code(execution_complete: bool) -> int:
    return 0 if execution_complete else 1
