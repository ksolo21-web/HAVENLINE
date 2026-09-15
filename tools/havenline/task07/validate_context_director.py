#!/usr/bin/env python3
"""Fail-closed static contract gate for the isolated T07 context director."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "HavenlineGodot/scripts/context_director.gd"
TEST = ROOT / "HavenlineGodot/tests/test_task07_context_director.gd"
ACTORS = ROOT / "Docs/Production/ACTOR_CAPABILITY_MATRIX.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(candidate: str) -> dict:
    checks: list[dict] = []
    failures: list[str] = []

    def check(name: str, passed: bool, detail: object = None) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})
        if not passed:
            failures.append(name)

    source = SOURCE.read_text()
    tests = TEST.read_text()
    matrix = json.loads(ACTORS.read_text())
    required_roles = matrix["required_actor_keys_by_task"]["T07"]

    check("exact T07 class", "class_name HavenlineContextDirector" in source)
    check("one joystick and no action strip", '"one_primary_movement_joystick": true' in source and '"permanent_action_buttons": 0' in source)
    check("simulation authority is explicit", '"simulation_authoritative": true' in source and '"emits_gameplay_events": false' in source)
    check("context is ephemeral", '"saved_fields": []' in source and "FileAccess" not in source)
    check("input and eligible caps are explicit", "MAX_INPUT_CANDIDATES := 128" in source and "MAX_ELIGIBLE_CANDIDATES := 96" in source)
    check("acquire hold release and switch controls exist", all(token in source for token in ("ACQUIRE_DWELL_SECONDS", "MINIMUM_HOLD_SECONDS", "RELEASE_MARGIN", "SWITCH_MARGIN")))
    check("every nonzero movement blocks and resets acquire dwell", "MOVEMENT_CANCEL_THRESHOLD := 0.0" in source and "movement_owns_locomotion" in source and re.search(r"if moving:\s+focus_elapsed = 0\.0", source) is not None)
    check("stable identity is final comparator", 'return String(left.identity) < String(right.identity)' in source)
    check("ranking comparator is strict", "if a != b:" in source and "is_equal_approx(a, b)" not in source)
    ordered = '["priority_band", "declared_priority", "distance_score", "target_relevance", "facing_score"]'
    check("ranking order is frozen", ordered in source)
    check("urgent actions are explicit", 'const URGENT_KINDS := ["enemy", "rescue", "npc_rescue"]' in source)
    check("spend metadata has no ranking field", not re.search(r"candidate\.(purchase|spend|vip|personalization)|candidate\.get\(\"(purchase|spend|vip|personalization)", source, re.I))
    check("director never mutates simulation", re.search(r"sim\.[A-Za-z_][A-Za-z0-9_]*\s*(?:=|\+=|-=)", source) is None)
    check("director defines no gameplay impact function", not re.search(r"func\s+(perform_action|damage|reward|grant|deposit|harvest)\b", source))
    check("director creates no controls", not re.search(r"\b(Button|TouchScreenButton|TextureButton|InputMap)\b", source))
    check("all required actor roles are represented", all(role in source for role in required_roles), required_roles)
    for role in required_roles:
        capabilities = matrix["actors"][role]["capabilities"]
        match = re.search(rf'"{re.escape(role)}": \[(.*?)\]', source)
        observed = re.findall(r'"([^"]+)"', match.group(1)) if match else []
        check(f"{role} capabilities match registry", observed == capabilities, {"expected": capabilities, "observed": observed})
    check("test covers malformed and duplicate input", "malformed candidates fail closed" in tests and "duplicate stable identities are rejected" in tests)
    check("test covers acquire versus release-only radius", "preview cannot acquire inside release-only margin" in tests)
    check("release-only rows cannot consume acquire cap", "release-only rows cannot evict an acquirable context" in tests)
    check("test covers all ranking dimensions", all(phrase in tests for phrase in ("declared priority", "distance precedes", "target relevance", "facing resolves", "stable identity")))
    check("test covers hysteresis hold and urgent preemption", "minimum hold timing" in tests and "prevents nearby target thrash" in tests and "urgent interrupt bypasses" in tests)
    check("same-band priority cannot bypass anti-thrash", "tiny same-band priority oscillation cannot bypass switch margin" in tests)
    check("test covers movement cancel and reacquire", "movement does not secretly accrue" in tests and "deterministically reacquires" in tests)
    check("test covers no duplicate impact contract", "descriptor declares no emitted impact" in tests)
    check("test covers T06 compatibility", "compatible with T06 selector" in tests)
    check("test covers visible population context and fail-closed actors", "visible survivor rescue is a canonical context" in tests and "unpresented survivor cannot become an invisible context" in tests)
    check("test covers persistence reconstruction", "context reconstructs deterministically after reload" in tests)
    check("test covers deterministic caps and overflow", all(phrase in tests for phrase in ("cap is independent of producer order", "urgent candidate after eligible cap", "duplicate across full input cap", "input overflow fails closed")))
    check("test covers invalid recovery and strict movement", "valid recovery after invalid input must reacquire" in tests and "every finite nonzero movement input blocks action" in tests)
    check("test covers visible blocked and cancellation feedback", "actor readiness failure is exposed in presentation" in tests and "movement cancellation is explicit and readable" in tests)
    check("test covers population cap performance", "worst-population selection remains bounded" in tests)
    check("test covers complete isolated C6 metrics", all(phrase in tests for phrase in ("worst-population p95", "retains no engine objects", "process RSS growth", "steady jitter does not thrash")))

    return {
        "task": "T07",
        "candidate_commit": candidate,
        "source": str(SOURCE.relative_to(ROOT)),
        "source_sha256": digest(SOURCE),
        "test_sha256": digest(TEST),
        "actor_matrix_sha256": digest(ACTORS),
        "checks": checks,
        "check_count": len(checks),
        "passed": not failures,
        "failures": failures,
        "future_scope_implemented": [],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", default="local-working-tree")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(args.candidate)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(rendered, end="")
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
