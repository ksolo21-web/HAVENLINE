#!/usr/bin/env python3
"""Static source and contract checks for the isolated T06 Character 1 work."""
from __future__ import annotations

import hashlib
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GLB = ROOT / "HavenlineGodot/assets/characters/Character1.glb"
MOTION = ROOT / "HavenlineGodot/scripts/character1_motion.gd"
EXPECTED_SHA = "95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099"
EXPECTED_ANIMATIONS = {
    "preset:biped:idle": 15.333333,
    "preset:biped:walk": 2.333333,
    "preset:biped:run": 1.25,
}
REQUIRED_BONES = {
    "Hip", "Waist", "Spine01", "Spine02",
    "L_Upperarm", "R_Upperarm", "L_Forearm", "R_Forearm",
    "L_Hand", "R_Hand", "L_Thigh", "R_Thigh",
    "L_Calf", "R_Calf", "L_Foot", "R_Foot", "L_ToeBase", "R_ToeBase",
}
REQUIRED_RUNTIME_CLIPS = {
    "idle", "walk", "run", "start_walk", "start_run", "stop_walk", "stop_run",
    "walk_to_run", "run_to_walk",
    "turn_left_030", "turn_right_030", "turn_left_090", "turn_right_090",
    "turn_left_180", "turn_right_180", "chop", "mine", "dismantle",
    "deposit", "build", "repair", "rescue", "service", "attack_contact",
}


def parse_glb(path: Path) -> dict:
    payload = path.read_bytes()
    magic, version, declared_length = struct.unpack_from("<4sII", payload, 0)
    assert magic == b"glTF" and version == 2 and declared_length == len(payload)
    cursor = 12
    while cursor < len(payload):
        length, kind = struct.unpack_from("<II", payload, cursor)
        cursor += 8
        chunk = payload[cursor:cursor + length]
        cursor += length
        if kind == 0x4E4F534A:
            return json.loads(chunk.decode("utf-8").rstrip("\x00 "))
    raise AssertionError("GLB JSON chunk missing")


def accessor_max(document: dict, accessor_index: int) -> float:
    accessor = document["accessors"][accessor_index]
    values = accessor.get("max")
    assert isinstance(values, list) and values
    return float(max(values))


def animation_duration(document: dict, animation: dict) -> float:
    return max(accessor_max(document, sampler["input"]) for sampler in animation["samplers"])


def main() -> None:
    checks: list[dict] = []

    def check(name: str, passed: bool, detail: object = None) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})
        assert passed, f"{name}: {detail}"

    raw = GLB.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    check("immutable Character1 SHA-256", digest == EXPECTED_SHA, digest)
    document = parse_glb(GLB)
    check("exact node count", len(document.get("nodes", [])) == 68, len(document.get("nodes", [])))
    check("one supplied skin", len(document.get("skins", [])) == 1, len(document.get("skins", [])))
    check("one supplied mesh", len(document.get("meshes", [])) == 1, len(document.get("meshes", [])))
    check("one supplied material", len(document.get("materials", [])) == 1, len(document.get("materials", [])))
    names = {node.get("name", "") for node in document["nodes"]}
    check("required articulated bones exist", REQUIRED_BONES <= names, sorted(REQUIRED_BONES - names))
    animations = {animation["name"]: animation for animation in document.get("animations", [])}
    check("exact three source animations", set(animations) == set(EXPECTED_ANIMATIONS), sorted(animations))
    for name, expected in EXPECTED_ANIMATIONS.items():
        observed = animation_duration(document, animations[name])
        check(f"{name} duration", abs(observed - expected) < 0.002, observed)

    source = MOTION.read_text()
    check("runtime pins immutable source", EXPECTED_SHA in source)
    check("both Character1 roles declared", all(role in source for role in ("player_lead", "core_human_companion")))
    check("simulation authority explicit", '"simulation_authoritative": true' in source)
    check("root facing remains simulation-owned", '"root_facing_authority": "simulation_external"' in source)
    check("duplicate impacts forbidden", '"duplicate_gameplay_impacts_allowed": false' in source)
    check("finished tools and weapons excluded", '"finished_tool_or_weapon_assets_included": false' in source)
    runtime_clips = set(re.findall(r'"([a-z0-9_]+)"', source))
    check("required motion vocabulary present", REQUIRED_RUNTIME_CLIPS <= runtime_clips, sorted(REQUIRED_RUNTIME_CLIPS - runtime_clips))
    check("feet and toes explicitly tuned", 'for side in ["L", "R"]' in source and 'side + "_Foot"' in source and 'side + "_ToeBase"' in source)
    check("knees receive bounded phase-aware correction", "Phase-aware hip/calf shaping" in source and 'side + "_Thigh"' in source and 'side + "_Calf"' in source)
    check("source double cycle is reduced to one readable gait", "_extract_gait_cycle" in source and "phase * 0.5" in source)
    check("every source loop receives 120 Hz seam closure", "_close_loop(idle)" in source and "_close_loop(clip)" in source and "1.0 / 120.0" in source)
    check("turns use planted support and free-foot pivot", "_turn_transition" in source and "free_side" in source and "facing_delta_for_turn" in source)
    check("walk and run transitions are distinct", all(name in source for name in ("stop_walk", "stop_run", "walk_to_run", "run_to_walk")))
    check("all contact markers declared", all(marker in source for marker in (
        "C1RightHandContact", "C1LeftHandContact", "C1TwoHandContact",
        "C1CarryContact", "C1RescueContact", "C1ForwardImpact",
    )))
    check("source file is not written", not re.search(r"FileAccess\.open\([^\n]*Character1\.glb", source))
    print(json.dumps({
        "suite": "task06_character1_static", "passed": True,
        "check_count": len(checks), "checks": checks,
        "source_sha256": digest, "source_animations": sorted(animations),
    }, indent=2))


if __name__ == "__main__":
    main()
