#!/usr/bin/env python3
"""Regression guards for the clean T13+ preparation stack."""
from __future__ import annotations
import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "Docs" / "Production"
FINAL_TASKS = [f"T{i:02d}" for i in range(62, 71)]
FORBIDDEN_EVIDENCE_ROOT = "Docs/Production/Evidence/"


def load_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    errors: list[str] = []
    wave = load_module("t62_wave", ROOT / "tools/havenline/t62_t70/prepare_activation.py")
    stack = load_module("stack_audit", ROOT / "tools/havenline/prepared_stack/audit_t13_t70.py")

    # Regression for the false T03 collision that contaminated earlier prep history.
    for label, overlap in (("T62 wave", wave.overlap), ("stack audit", stack.overlap)):
        if overlap("tools/havenline/task13/**", "tools/havenline/*task03*"):
            errors.append(f"{label}: task13 falsely overlaps legacy *task03* pattern")
        if not overlap("foo/**", "foo/bar/**"):
            errors.append(f"{label}: real nested ownership overlap was missed")

    ownership = load_json(DOCS / "PATH_OWNERSHIP.json")
    active = ownership.get("active_owners", [])
    aliases = ownership.get("aliases", {})

    for tid in FINAL_TASKS:
        task_dir = DOCS / tid
        checklist = load_json(task_dir / "ACTIVATION_CHECKLIST.json")
        prebuild = load_json(task_dir / "PREBUILD_CONTRACT.json")
        packet = (task_dir / "TASK_PACKET.md").read_text(encoding="utf-8")
        c_paths = checklist.get("planned_owned_paths", [])
        p_paths = prebuild.get("planned_owned_paths", [])
        required_local = f"Docs/Production/{tid}/Evidence/**"

        if c_paths != p_paths:
            errors.append(f"{tid}: checklist/prebuild planned_owned_paths differ")
        if required_local not in c_paths:
            errors.append(f"{tid}: missing task-local evidence reservation {required_local}")
        if any(path.startswith(FORBIDDEN_EVIDENCE_ROOT) for path in c_paths):
            errors.append(f"{tid}: claims QA-GOV global evidence namespace")
        if FORBIDDEN_EVIDENCE_ROOT in packet:
            errors.append(f"{tid}: task packet references QA-GOV global evidence namespace")

        for candidate in c_paths:
            for owner in active:
                for foreign in aliases.get(owner.get("paths_alias"), []):
                    if wave.overlap(candidate, foreign):
                        errors.append(f"{tid}: active ownership collision with {owner.get('task_id')}: {candidate} vs {foreign}")

    result = {"scope":"forward path guards","tasks":FINAL_TASKS,"passed":not errors,"errors":errors}
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
