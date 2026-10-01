#!/usr/bin/env python3
"""Pure non-shipping reference state machine for future T12 progression runtime."""
from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
from collections import defaultdict
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[3]
TASK = ROOT / "tools" / "havenline" / "task12"
BINDING_FIELDS = {
    "slot_id", "fact_kind", "source_task", "source_id",
    "resolution_state", "evidence_ref", "idempotency_domain",
}
STATE_FIELDS = {
    "completed_level_ids",
    "satisfied_fact_slot_ids",
    "fact_slot_source_keys",
    "consumed_fact_keys",
    "emitted_completion_event_ids",
    "emitted_milestone_ids",
}
RESOLUTION_STATES = {"RESOLVED", "DEFERRED_LATER_OWNER"}

def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, TASK / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

progression_validator = _load_module("t12_progression_validator_reference_engine", "validate_progression_contract.py")

def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())

def _unique_strings(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or any(not _nonempty(x) for x in value):
        raise ValueError(f"{label} must be a list of non-empty strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{label} contains duplicates")
    return list(value)

def empty_state() -> dict[str, Any]:
    return {
        "completed_level_ids": [],
        "satisfied_fact_slot_ids": [],
        "fact_slot_source_keys": {},
        "consumed_fact_keys": [],
        "emitted_completion_event_ids": [],
        "emitted_milestone_ids": [],
    }

class ReferenceProgressionEngine:
    def __init__(
        self,
        levels_doc: dict[str, Any],
        milestones_doc: dict[str, Any],
        bindings: list[dict[str, Any]],
        snapshot: dict[str, Any] | None = None,
    ):
        self.levels_doc = copy.deepcopy(levels_doc)
        self.milestones_doc = copy.deepcopy(milestones_doc)
        combined = {
            "schema_version": self.levels_doc.get("schema_version"),
            "task_id": self.levels_doc.get("task_id"),
            "levels": self.levels_doc.get("levels"),
            "milestones": self.milestones_doc.get("milestones"),
        }
        result = progression_validator.validate_manifest(combined)
        if not result["passed"]:
            raise ValueError("progression contract invalid: " + json.dumps(result["errors"]))

        self.levels = sorted(combined["levels"], key=lambda row: int(row["level"]))
        self.milestones = list(combined["milestones"])
        self.level_by_id = {row["level_id"]: row for row in self.levels}
        self.number_by_id = {row["level_id"]: int(row["level"]) for row in self.levels}
        self.milestone_by_id = {row["milestone_id"]: row for row in self.milestones}
        self.reverse_dependencies: dict[str, list[str]] = defaultdict(list)
        for row in self.levels:
            for prereq in row["prerequisite_level_ids"]:
                self.reverse_dependencies[prereq].append(row["level_id"])
        for key in self.reverse_dependencies:
            self.reverse_dependencies[key].sort(key=lambda level_id: self.number_by_id[level_id])

        self.required_slots = {
            slot
            for row in self.levels
            for slot in row["required_fact_ids"]
        }
        self.bindings = self._validate_bindings(bindings)
        self.bindings_by_source: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in self.bindings:
            if row["resolution_state"] == "RESOLVED":
                key = (row["source_task"], row["fact_kind"], row["source_id"])
                self.bindings_by_source[key].append(row)
        for key in self.bindings_by_source:
            self.bindings_by_source[key].sort(key=lambda row: row["slot_id"])

        self.metrics = {
            "observations": 0,
            "mutating_observations": 0,
            "duplicate_observations": 0,
            "invalid_observations": 0,
            "settlement_passes": 0,
            "completed_levels": 0,
            "emitted_intents": 0,
        }

        self.state = self._restore_state(snapshot if snapshot is not None else empty_state())
        self.initialization_intents = self._settle()
        self._validate_state(self.state)

    def _validate_bindings(self, rows: Any) -> list[dict[str, Any]]:
        if not isinstance(rows, list):
            raise ValueError("bindings must be a list")
        by_slot: dict[str, dict[str, Any]] = {}
        normalized: list[dict[str, Any]] = []
        for index, row in enumerate(rows):
            if not isinstance(row, dict) or set(row) != BINDING_FIELDS:
                raise ValueError(f"bindings[{index}] fields mismatch")
            slot = row.get("slot_id")
            if slot not in self.required_slots:
                raise ValueError(f"bindings[{index}] unknown/unneeded slot_id {slot!r}")
            if slot in by_slot:
                raise ValueError(f"duplicate binding for slot {slot}")
            state = row.get("resolution_state")
            if state not in RESOLUTION_STATES:
                raise ValueError(f"binding {slot} invalid resolution_state {state!r}")
            if not _nonempty(row.get("source_task")):
                raise ValueError(f"binding {slot} source_task must be non-empty")
            if not _nonempty(row.get("evidence_ref")):
                raise ValueError(f"binding {slot} evidence_ref must be non-empty")
            if state == "RESOLVED":
                for field in ("fact_kind", "source_id", "idempotency_domain"):
                    if not _nonempty(row.get(field)):
                        raise ValueError(f"resolved binding {slot} {field} must be non-empty")
            else:
                if row.get("source_id") not in ("", None):
                    raise ValueError(f"deferred binding {slot} may not carry a source_id")
                if row.get("idempotency_domain") not in ("", None):
                    raise ValueError(f"deferred binding {slot} may not carry an idempotency_domain")
                if not _nonempty(row.get("fact_kind")):
                    raise ValueError(f"deferred binding {slot} fact_kind must retain the intended semantic kind")
            copy_row = copy.deepcopy(row)
            normalized.append(copy_row)
            by_slot[slot] = copy_row
        if set(by_slot) != self.required_slots:
            missing = sorted(self.required_slots - set(by_slot))
            raise ValueError(f"binding index does not cover every required fact slot: {missing}")
        return sorted(normalized, key=lambda row: row["slot_id"])

    def _restore_state(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(snapshot, dict) or set(snapshot) != STATE_FIELDS:
            raise ValueError("snapshot fields mismatch")
        state = {
            "completed_level_ids": _unique_strings(snapshot["completed_level_ids"], "completed_level_ids"),
            "satisfied_fact_slot_ids": _unique_strings(snapshot["satisfied_fact_slot_ids"], "satisfied_fact_slot_ids"),
            "fact_slot_source_keys": dict(snapshot["fact_slot_source_keys"]) if isinstance(snapshot["fact_slot_source_keys"], dict) else None,
            "consumed_fact_keys": _unique_strings(snapshot["consumed_fact_keys"], "consumed_fact_keys"),
            "emitted_completion_event_ids": _unique_strings(snapshot["emitted_completion_event_ids"], "emitted_completion_event_ids"),
            "emitted_milestone_ids": _unique_strings(snapshot["emitted_milestone_ids"], "emitted_milestone_ids"),
        }
        if state["fact_slot_source_keys"] is None:
            raise ValueError("fact_slot_source_keys must be an object")
        self._validate_state(state)
        return state

    def _validate_state(self, state: dict[str, Any]) -> None:
        completed = set(state["completed_level_ids"])
        satisfied = set(state["satisfied_fact_slot_ids"])
        source_map = state["fact_slot_source_keys"]
        consumed_list = state["consumed_fact_keys"]
        if len(consumed_list) != len(set(consumed_list)):
            raise ValueError("consumed_fact_keys contains duplicates")
        consumed = set(consumed_list)
        emitted = set(state["emitted_completion_event_ids"])
        emitted_milestones = set(state["emitted_milestone_ids"])

        unknown_levels = completed - set(self.level_by_id)
        if unknown_levels:
            raise ValueError(f"snapshot contains unknown completed levels: {sorted(unknown_levels)}")
        unknown_slots = satisfied - self.required_slots
        if unknown_slots:
            raise ValueError(f"snapshot contains unknown satisfied fact slots: {sorted(unknown_slots)}")
        if set(source_map) != satisfied:
            raise ValueError("fact_slot_source_keys must have exactly one key for every satisfied fact slot")
        if any(not _nonempty(value) for value in source_map.values()):
            raise ValueError("fact_slot_source_keys values must be non-empty")
        if any(value not in consumed for value in source_map.values()):
            raise ValueError("every fact-slot source key must exist in consumed_fact_keys")
        justified_consumed = set(source_map.values())
        if consumed != justified_consumed:
            raise ValueError("consumed_fact_keys must be exactly justified by satisfied fact-slot source keys")

        known_events = {
            event
            for row in self.levels
            for event in row["one_time_event_ids"]
        }
        if not emitted.issubset(known_events):
            raise ValueError("snapshot contains unknown emitted completion event IDs")
        if not emitted_milestones.issubset(set(self.milestone_by_id)):
            raise ValueError("snapshot contains unknown emitted milestone IDs")

        for level_id in completed:
            row = self.level_by_id[level_id]
            if not set(row["prerequisite_level_ids"]).issubset(completed):
                raise ValueError(f"completed level {level_id} has incomplete prerequisite")
            if not set(row["required_fact_ids"]).issubset(satisfied):
                raise ValueError(f"completed level {level_id} is missing satisfied fact slot")
            canonical_event = f"t12.event.level.{int(row['level']):03d}.completed"
            if canonical_event not in emitted:
                raise ValueError(f"completed level {level_id} is missing emitted completion event")
            for milestone_id in row["milestone_ids"]:
                if milestone_id not in emitted_milestones:
                    raise ValueError(f"completed milestone level {level_id} is missing emitted milestone {milestone_id}")

        justified_events = {
            f"t12.event.level.{int(self.level_by_id[level_id]['level']):03d}.completed"
            for level_id in completed
        }
        if emitted != justified_events:
            raise ValueError("emitted completion event state is not exactly justified by completed levels")

        justified_milestones = {
            milestone_id
            for level_id in completed
            for milestone_id in self.level_by_id[level_id]["milestone_ids"]
        }
        if emitted_milestones != justified_milestones:
            raise ValueError("emitted milestone state is not exactly justified by completed levels")

    def snapshot(self) -> dict[str, Any]:
        return {
            "completed_level_ids": sorted(self.state["completed_level_ids"], key=lambda x: self.number_by_id[x]),
            "satisfied_fact_slot_ids": sorted(self.state["satisfied_fact_slot_ids"]),
            "fact_slot_source_keys": {
                key: self.state["fact_slot_source_keys"][key]
                for key in sorted(self.state["fact_slot_source_keys"])
            },
            "consumed_fact_keys": sorted(self.state["consumed_fact_keys"]),
            "emitted_completion_event_ids": sorted(self.state["emitted_completion_event_ids"]),
            "emitted_milestone_ids": sorted(self.state["emitted_milestone_ids"]),
        }

    def _intent_for(self, row: dict[str, Any]) -> dict[str, Any]:
        level = int(row["level"])
        level_id = row["level_id"]
        event_id = f"t12.event.level.{level:03d}.completed"
        unlocked = [
            dependent
            for dependent in self.reverse_dependencies.get(level_id, [])
            if set(self.level_by_id[dependent]["prerequisite_level_ids"]).issubset(set(self.state["completed_level_ids"]))
            and dependent not in self.state["completed_level_ids"]
        ]
        source_keys = [
            self.state["fact_slot_source_keys"][slot]
            for slot in row["required_fact_ids"]
        ]
        return {
            "intent_id": f"t12.intent.level.{level:03d}.completed",
            "level_id": level_id,
            "completion_event_id": event_id,
            "unlocked_level_ids": unlocked,
            "milestone_ids": list(row["milestone_ids"]),
            "source_fact_keys": source_keys,
        }

    def _settle(self) -> list[dict[str, Any]]:
        intents: list[dict[str, Any]] = []
        while True:
            self.metrics["settlement_passes"] += 1
            changed = False
            completed = set(self.state["completed_level_ids"])
            satisfied = set(self.state["satisfied_fact_slot_ids"])
            for row in self.levels:
                level_id = row["level_id"]
                if level_id in completed:
                    continue
                if not set(row["prerequisite_level_ids"]).issubset(completed):
                    continue
                if not set(row["required_fact_ids"]).issubset(satisfied):
                    continue

                self.state["completed_level_ids"].append(level_id)
                completed.add(level_id)
                event_id = f"t12.event.level.{int(row['level']):03d}.completed"
                if event_id in self.state["emitted_completion_event_ids"]:
                    raise ValueError(f"uncompleted level {level_id} already had emitted completion event")
                self.state["emitted_completion_event_ids"].append(event_id)
                for milestone_id in row["milestone_ids"]:
                    if milestone_id in self.state["emitted_milestone_ids"]:
                        raise ValueError(f"uncompleted level {level_id} already had emitted milestone {milestone_id}")
                    self.state["emitted_milestone_ids"].append(milestone_id)
                intent = self._intent_for(row)
                intents.append(intent)
                self.metrics["completed_levels"] += 1
                self.metrics["emitted_intents"] += 1
                changed = True
            if not changed:
                break
        return intents

    def get_level_state(self, level_id: str) -> dict[str, Any]:
        if level_id not in self.level_by_id:
            raise ValueError(f"unknown level_id {level_id}")
        row = self.level_by_id[level_id]
        completed = set(self.state["completed_level_ids"])
        satisfied = set(self.state["satisfied_fact_slot_ids"])
        if level_id in completed:
            return {"level_id": level_id, "state": "complete", "missing_prerequisite_level_ids": [], "missing_fact_slot_ids": []}
        missing_prereqs = sorted(set(row["prerequisite_level_ids"]) - completed, key=lambda x: self.number_by_id[x])
        missing_facts = sorted(set(row["required_fact_ids"]) - satisfied)
        return {
            "level_id": level_id,
            "state": "ready" if not missing_prereqs and not missing_facts else "locked",
            "missing_prerequisite_level_ids": missing_prereqs,
            "missing_fact_slot_ids": missing_facts,
        }

    def get_unlockable_levels(self) -> list[str]:
        return [
            row["level_id"]
            for row in self.levels
            if self.get_level_state(row["level_id"])["state"] == "ready"
        ]

    def observe_authoritative_fact(
        self,
        source_task: str,
        fact_kind: str,
        source_id: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        self.metrics["observations"] += 1
        if not all(_nonempty(value) for value in (source_task, fact_kind, source_id, idempotency_key)):
            self.metrics["invalid_observations"] += 1
            return {"passed": False, "mutated": False, "replayed": False, "intents": [], "errors": ["invalid_fact_identity"]}

        rows = self.bindings_by_source.get((source_task, fact_kind, source_id), [])
        if not rows:
            self.metrics["invalid_observations"] += 1
            return {"passed": False, "mutated": False, "replayed": False, "intents": [], "errors": ["unresolved_or_unknown_fact"]}

        unsatisfied = [row for row in rows if row["slot_id"] not in self.state["satisfied_fact_slot_ids"]]
        if not unsatisfied:
            self.metrics["duplicate_observations"] += 1
            return {"passed": True, "mutated": False, "replayed": True, "intents": [], "errors": []}

        new_fact_keys: list[str] = []
        pending_unique_keys: set[str] = set()
        consumed_keys = set(self.state["consumed_fact_keys"])
        for row in unsatisfied:
            fact_key = f"{row['idempotency_domain']}|{idempotency_key}"
            if fact_key in consumed_keys:
                self.metrics["invalid_observations"] += 1
                return {"passed": False, "mutated": False, "replayed": False, "intents": [], "errors": ["fact_key_collision_without_satisfied_slot"]}
            new_fact_keys.append(fact_key)
            pending_unique_keys.add(fact_key)

        for row, fact_key in zip(unsatisfied, new_fact_keys):
            self.state["satisfied_fact_slot_ids"].append(row["slot_id"])
            self.state["fact_slot_source_keys"][row["slot_id"]] = fact_key
        self.state["consumed_fact_keys"].extend(sorted(pending_unique_keys))

        self.metrics["mutating_observations"] += 1
        intents = self._settle()
        self._validate_state(self.state)
        return {"passed": True, "mutated": True, "replayed": False, "intents": intents, "errors": []}

    def get_metrics(self) -> dict[str, int]:
        return dict(self.metrics)
