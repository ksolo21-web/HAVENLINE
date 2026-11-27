"""Forward review acceptance; historical receipt checks never grant approval.

Raw reviewer scores remain unchanged. Thresholds are applied per required
unrounded dimension after review, without using averages or rounded values.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable

from lib import ROOT, DOCS

POLICY_PATH = DOCS / "REFERENCE_ACCEPTANCE_POLICY.json"
VISUAL_CRITICS = frozenset({"C1", "C2", "C3", "C4", "C5", "C11"})
KNOWN_CRITICS = frozenset(f"C{i}" for i in range(1, 12))
PHASES = frozenset({"final", "interim"})


def strict_json_loads(body: str | bytes) -> Any:
    """Reject ambiguous duplicate keys and non-JSON numeric constants at intake."""
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result
    def invalid_constant(value):
        raise ValueError("non-finite JSON constant: " + value)
    return json.loads(body, object_pairs_hook=unique_object, parse_constant=invalid_constant)


def load_json_strict(path: Path) -> Any:
    return strict_json_loads(path.read_bytes())


def declared_reference_dimensions(manifest: Any, critic_id: str,
                                  expected_dimensions: Iterable[str]) -> list[str]:
    """Resolve a source manifest's immutable declaration, never a reviewer waiver.

    A specialist manifest uses a list; a shared evidence index may use a map
    keyed by critic. Policy-wide reference dimensions remain additive.
    """
    if not isinstance(manifest, dict):
        raise ValueError("input manifest must be an object")
    if "reference_sensitive_dimensions" not in manifest:
        raise ValueError("input manifest must explicitly declare reference_sensitive_dimensions (empty only when none)")
    value = manifest.get("reference_sensitive_dimensions", [])
    if isinstance(value, dict):
        value = value.get(critic_id, [])
    if not isinstance(value, list) or any(not isinstance(x, str) or not x for x in value):
        raise ValueError("manifest reference_sensitive_dimensions must be a list of canonical dimensions")
    if len(set(value)) != len(value) or set(value) - set(expected_dimensions):
        raise ValueError("manifest reference dimensions are duplicate or outside the mandatory dimension set")
    return list(value)


def nonapproving_scope_errors(record: Any) -> list[str]:
    if not isinstance(record, dict):
        return ["review record must be an object"]
    errors = []
    scope = str(record.get("review_scope", "")).lower()
    kind = str(record.get("validation_kind", "")).upper()
    if "historical" in scope or "HISTORICAL" in kind or record.get("historical_only") is True:
        errors.append("historical-only validation cannot authorize current final approval")
    binding = record.get('reference_acceptance')
    if "interim" in scope or (isinstance(binding, dict) and binding.get('phase') != 'final'):
        errors.append('interim or non-final review scope cannot authorize current final approval')
    if 'status' in record and record['status'] != 'PASS':
        errors.append('explicit non-PASS status cannot authorize current final approval')
    if 'passed' in record and record['passed'] is not True:
        errors.append('explicit passed disposition must be boolean true for final approval')
    if 'approval_allowed' in record and record['approval_allowed'] is not True:
        errors.append("record explicitly disallows approval")
    return errors


def playback_errors(review: Any, required_media: Iterable[dict], *, root: Path = ROOT) -> list[str]:
    """Validate retained playback coverage; static frames cannot satisfy this gate.

    The caller must first bind ``review`` to the independent original session
    artifact. This validates that its reviewed ranges cover the actual decoded
    candidate clips and the mandatory cycle, transition and contact checks.
    """
    from shipping_visual_gate import _video_metadata
    errors = []
    ranges = review.get("reviewed_ranges") if isinstance(review, dict) else None
    if not isinstance(ranges, list) or not ranges:
        return ["independent full-cycle/transition playback ranges are missing"]
    media = list(required_media)
    if not media or any(not isinstance(item, dict) for item in media):
        return ["required source-bound motion clips are missing"]
    categories = {item.get("category") for item in media if isinstance(item.get("category"), str)}
    if not {"motion_cycle", "motion_transition"} <= categories:
        errors.append("motion input must include complete cycles and transitions")
    cameras = {item.get("camera") for item in media if isinstance(item.get("camera"), str) and item["camera"].strip()}
    if len(cameras) < 2:
        errors.append("motion playback requires at least two distinct meaningful camera views")
    seen = set(); checks = set(); identities = set()
    mandatory = {"full_cycle", "foot_contact", "lower_body_mechanics", "upper_body_mechanics",
                 "weight_transfer", "transitions", "clipping", "secondary_motion_contact"}
    for item in media:
        rel = item.get("path"); digest = item.get("sha256")
        if not isinstance(rel, str) or not rel or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            errors.append("motion clip path/hash invalid"); continue
        identity = (rel, digest); identities.add(identity)
        if digest in seen: errors.append("duplicate motion bytes do not add playback coverage")
        seen.add(digest)
        path = root / rel
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
            errors.append("motion clip missing or outside source root: " + rel); continue
        body = path.read_bytes()
        if hashlib.sha256(body).hexdigest() != digest:
            errors.append("motion clip hash mismatch: " + rel); continue
        try:
            metadata = _video_metadata(body)
            duration = metadata["duration"]; fps = metadata["fps"]
            if not _number(duration) or duration <= 0 or not _number(fps) or fps <= 0:
                raise ValueError("invalid decoded duration or FPS")
            # ffprobe metadata alone is insufficient: decode every video frame.
            subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", "pipe:0", "-map", "0:v:0",
                            "-f", "null", "-"], input=body, stdout=subprocess.DEVNULL,
                           stderr=subprocess.PIPE, check=True, timeout=60)
        except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
            errors.append("motion clip cannot be fully decoded: " + rel + ": " + str(exc)); continue
        spans = []
        for row in ranges:
            if not isinstance(row, dict): errors.append("playback range must be an object"); continue
            if (row.get("path"), row.get("sha256")) != identity: continue
            start = row.get("start_seconds"); end = row.get("end_seconds")
            required_checks = row.get("checks")
            if not _number(start) or not _number(end) or not 0 <= start < end <= duration + 0.5 / fps:
                errors.append("playback range outside actual clip: " + rel); continue
            if not isinstance(required_checks, list) or any(not isinstance(x, str) for x in required_checks):
                errors.append("playback range mandatory checks missing: " + rel); continue
            checks.update(required_checks); spans.append((start, end))
        cursor = 0.0
        for start, end in sorted(spans):
            if start > cursor + 0.5 / fps:
                errors.append("unreviewed playback gap: " + rel)
            cursor = max(cursor, end)
        if cursor < duration - 0.5 / fps:
            errors.append("full decoded motion clip was not reviewed: " + rel)
    if any(not isinstance(row, dict) or (row.get("path"), row.get("sha256")) not in identities for row in ranges):
        errors.append("playback receipt names motion outside the frozen input manifest")
    if not mandatory <= checks:
        errors.append("playback receipt lacks mandatory C5 checks: " + ",".join(sorted(mandatory - checks)))
    return errors


def _number(value: Any) -> bool:
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except (OverflowError, TypeError):
        return False


def _policy(policy: dict | None = None) -> tuple[dict, str, list[str]]:
    try:
        if policy is None:
            body = POLICY_PATH.read_bytes()
            value = strict_json_loads(body)
        else:
            value = policy
            body = json.dumps(policy, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        errors = policy_errors(value)
        return value, hashlib.sha256(body).hexdigest(), errors
    except (OSError, ValueError, TypeError) as exc:
        return {}, "", ["reference acceptance policy missing or invalid: " + str(exc)]


def policy_errors(policy: Any) -> list[str]:
    if not isinstance(policy, dict):
        return ["reference acceptance policy must be an object"]
    errors = []
    if policy.get("schema_version") != 1 or not isinstance(policy.get("policy_id"), str) or not policy.get("policy_id"):
        errors.append("reference acceptance policy identity is invalid")
    final = policy.get("final_acceptance", {})
    interim = policy.get("interim_review", {})
    if not isinstance(final, dict) or not isinstance(interim, dict):
        return errors + ["final/interim acceptance policy is missing"]
    for field, floor in (("minimum_dimension_score", 9.5), ("reference_minimum_dimension_score", 9.9)):
        value = final.get(field)
        if not _number(value) or not floor <= value <= 10:
            errors.append(f"final {field} must preserve the {floor} floor and 10 maximum")
    if type(final.get("exact_score")) not in (int, float) or final.get("exact_score") != 10:
        errors.append("existing exact visual score must remain 10")
    for field in ("reference_sensitive_critic_ids", "exact_score_critic_ids"):
        ids = final.get(field)
        if not isinstance(ids, list) or any(not isinstance(x, str) for x in ids) or not VISUAL_CRITICS <= set(ids):
            errors.append("final " + field + " must preserve every existing visual critic")
    dimensions = final.get("reference_sensitive_dimensions", [])
    if not isinstance(dimensions, list) or any(not isinstance(x, str) or not x for x in dimensions):
        errors.append("reference_sensitive_dimensions must be a list of named dimensions")
    if final.get("forbid_averaging") is not True or final.get("require_unrounded") is not True:
        errors.append("final acceptance must forbid averaging and require unrounded scores")
    if not _number(interim.get("minimum_dimension_score")) or not 9.5 <= interim["minimum_dimension_score"] <= 10:
        errors.append("interim score floor must be at least 9.5 and at most 10")
    if interim.get("approval_allowed") is not False:
        errors.append("interim review may never authorize approval")
    return errors


def acceptance_binding(phase: str = "final", policy: dict | None = None) -> dict:
    cfg, digest, errors = _policy(policy)
    if phase not in PHASES:
        errors.append("unknown review phase")
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "policy_id": cfg["policy_id"],
        "policy_sha256": digest,
        "phase": phase,
        "scores_unrounded": True,
        "score_averaging_used": False,
    }


def binding_errors(record: Any, *, phase: str = "final", policy: dict | None = None) -> list[str]:
    if not isinstance(record, dict):
        return ["review record must be an object"]
    try:
        expected = acceptance_binding(phase, policy)
    except ValueError as exc:
        return [str(exc)]
    binding = record.get("reference_acceptance")
    if not isinstance(binding, dict):
        return ["current reference_acceptance binding is missing"]
    errors = nonapproving_scope_errors(record) if phase == "final" else []
    for name, value in expected.items():
        # Numeric equality is deliberately not enough for the boolean assertions.
        if type(value) is bool:
            good = binding.get(name) is value
        else:
            good = binding.get(name) == value
        if not good:
            errors.append("reference_acceptance " + name + " mismatch")
    if record.get("score_averaging_used") not in (None, False):
        errors.append("score averaging is forbidden")
    if record.get("scores_rounded") is True or record.get("score_rounding_used") is True:
        errors.append("rounded scores cannot authorize approval")
    return errors


def score_errors(scores: Any, expected_dimensions: Iterable[str], critic_id: str, *,
                 phase: str = "final", policy: dict | None = None,
                 reference_dimensions: Iterable[str] = ()) -> list[str]:
    cfg, _, errors = _policy(policy)
    if errors:
        return errors
    if phase not in PHASES:
        return ["unknown review phase"]
    if critic_id not in KNOWN_CRITICS:
        errors.append("unknown critic id")
    if isinstance(expected_dimensions, str):
        return errors + ["mandatory dimensions must be an explicit collection"]
    try:
        expected = list(expected_dimensions)
    except TypeError:
        return errors + ["mandatory dimensions are missing"]
    if not expected or any(not isinstance(x, str) or not x for x in expected) or len(set(expected)) != len(expected):
        return errors + ["mandatory dimensions are empty, invalid or duplicated"]
    if not isinstance(scores, dict) or not scores:
        return errors + ["score map is empty or invalid"]
    if set(scores) != set(expected):
        errors.append("mandatory dimension coverage mismatch")
    if isinstance(reference_dimensions, str):
        return errors + ["reference dimensions must be an explicit collection"]
    try:
        declared = list(reference_dimensions)
    except TypeError:
        return errors + ["reference dimensions are invalid"]
    if any(not isinstance(x, str) or x not in expected for x in declared):
        errors.append("declared reference dimensions must be mandatory dimensions")
    final = cfg["final_acceptance"]
    reference = set(final.get("reference_sensitive_dimensions", [])) | set(x for x in declared if isinstance(x, str))
    for name, value in scores.items():
        if not _number(value):
            errors.append(f"{name}: score must be a finite number, not a boolean")
            continue
        if not 0 <= value <= 10:
            errors.append(f"{name}: score must be within 0..10")
            continue
        if phase == "interim":
            minimum = cfg["interim_review"]["minimum_dimension_score"]
            exact = None
        else:
            minimum = final["minimum_dimension_score"]
            if critic_id in final["reference_sensitive_critic_ids"] or name in reference:
                minimum = max(minimum, final["reference_minimum_dimension_score"])
            exact = final["exact_score"] if critic_id in final["exact_score_critic_ids"] else None
        if exact is not None and value != exact:
            errors.append(f"{name}: must equal {exact} exactly for final {critic_id} visual acceptance")
        elif value < minimum:
            errors.append(f"{name}: unrounded score {value} is below {minimum}")
    return errors


def record_errors(record: Any, expected_dimensions: Iterable[str], critic_id: str, *,
                  phase: str = "final", require_binding: bool = True,
                  policy: dict | None = None,
                  reference_dimensions: Iterable[str] | None = None) -> list[str]:
    if not isinstance(record, dict):
        return ["review record must be an object"]
    declared = record.get("reference_sensitive_dimensions", [])
    errors = []
    if reference_dimensions is not None:
        frozen = list(reference_dimensions)
        if declared != frozen:
            errors.append("review reference dimensions differ from the frozen input manifest")
        # The source declaration is authoritative even when a reviewer omits it.
        declared = frozen
    errors += score_errors(record.get("scores"), expected_dimensions, critic_id, phase=phase,
                           policy=policy, reference_dimensions=declared)
    if require_binding:
        errors += binding_errors(record, phase=phase, policy=policy)
    if record.get("coverage_complete") is not True:
        errors.append("mandatory evidence coverage is missing or incomplete")
    if record.get("defects") != []:
        errors.append("mandatory defects must be an explicit empty list")
    if 'passed' in record and record['passed'] is not True:
        errors.append("reviewer marked the record failed")
    if phase == "final":
        errors += nonapproving_scope_errors(record)
        if require_binding and (record.get('status')!='PASS' or record.get('passed') is not True):
            errors.append('bound final record requires explicit PASS and boolean passed=true')
    return errors


def final_rule(policy: dict | None = None) -> str:
    cfg, _, errors = _policy(policy)
    if errors:
        raise ValueError("; ".join(errors))
    f = cfg["final_acceptance"]
    return (f"Every mandatory dimension >= {f['minimum_dimension_score']} unrounded; "
            f"reference-sensitive dimensions >= {f['reference_minimum_dimension_score']}; "
            f"{','.join(f['exact_score_critic_ids'])} every mandatory dimension exactly {f['exact_score']}; "
            "no averaging or rounding; complete evidence; zero mandatory defects")


def required_final_critics(task_id: str, base_critics: Iterable[str], *,
                           style_required: bool = False, policy: dict | None = None) -> list[str]:
    """Add mandatory forward critics without rewriting historical task records."""
    cfg, _, errors = _policy(policy)
    if not isinstance(task_id, str) or not re.fullmatch(r"T(?:0[1-9]|[1-6][0-9]|70)", task_id):
        errors.append("final acceptance requires an authentic T01-T70 task id")
    if isinstance(base_critics, str):
        errors.append("base critic set must be an explicit collection")
        result = []
    else:
        try:
            result = list(base_critics)
        except TypeError:
            errors.append("base critic set is missing")
            result = []
    if any(not isinstance(x, str) or x not in KNOWN_CRITICS for x in result):
        errors.append("unknown mandatory critic")
    motion = cfg.get("required_motion_critics", {})
    tasks = motion.get("always_add_C5_to_tasks", []) if isinstance(motion, dict) else []
    if not isinstance(tasks, list) or any(not isinstance(x, str) for x in tasks) or not {"T09", "T16", "T19", "T21", "T23"} <= set(tasks):
        errors.append("mandatory forward motion task coverage is missing")
    if errors:
        raise ValueError("; ".join(errors))
    if task_id in tasks:
        result.append("C5")
    if style_required:
        result.append("C1")
    return list(dict.fromkeys(result))


def validate_historical_receipt(task_id: str, candidate: str, receipt_path: str,
                                policy: dict | None = None) -> dict:
    cfg, _, errors = _policy(policy)
    if not isinstance(candidate, str) or not re.fullmatch(r"[0-9a-f]{40}", candidate):
        errors.append("historical candidate must be exact 40-hex")
    entries = cfg.get("historical_preservation", {}).get("receipts", [])
    matches = [x for x in entries if isinstance(x, dict) and
               (x.get("task_id"), x.get("candidate_sha"), x.get("path")) == (task_id, candidate, receipt_path)]
    if len(matches) != 1:
        errors.append("historical receipt is not uniquely pinned by task, candidate and path")
    else:
        raw = ROOT / receipt_path
        resolved = raw.resolve()
        if raw.is_symlink() or not resolved.is_relative_to(ROOT.resolve()):
            errors.append("historical receipt path escapes repository or is a symlink")
        elif not resolved.is_file():
            errors.append("historical receipt bytes are missing")
        elif hashlib.sha256(resolved.read_bytes()).hexdigest() != matches[0].get("sha256"):
            errors.append("historical receipt bytes differ from immutable pinned receipt")
    return {"passed": not errors, "validation_kind": "HISTORICAL_RECEIPT_ONLY",
            "approval_allowed": False, "task_id": task_id, "candidate": candidate,
            "receipt_path": receipt_path, "errors": errors}
