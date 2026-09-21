#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
TOOL_PATH = ROOT / "tools/havenline/task12/prepare_activation.py"

spec = importlib.util.spec_from_file_location("t12_prepare_activation", TOOL_PATH)
activation = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(activation)


class T12PrepareActivationTests(unittest.TestCase):
    t10 = "a" * 40
    t11 = "b" * 40
    head = "c" * 40

    def state(self):
        checklist = {"dependencies": ["T07", "T08", "T10", "T11"]}
        graph = {
            "tasks": {
                task: {"status": "APPROVED"}
                for task in checklist["dependencies"]
            }
        }
        registry = {
            "legacy_approvals": {},
            "workstreams": [
                {"task_id": task, "status": "APPROVED"}
                for task in checklist["dependencies"]
            ],
        }
        ownership = {
            "active_owners": [],
            "completed_production_owners": [
                {
                    "task_id": "T10",
                    "status": "APPROVED",
                    "integrated_source": self.t10,
                },
                {
                    "task_id": "T11",
                    "status": "APPROVED",
                    "integrated_source": self.t11,
                },
            ],
        }
        gates = {
            "approved_tasks": list(checklist["dependencies"]),
            "completed_task_records": {
                "T10": {
                    "status": "APPROVED",
                    "integrated_source": self.t10,
                },
                "T11": {
                    "status": "APPROVED",
                    "integrated_source": self.t11,
                },
            },
        }
        return checklist, graph, registry, ownership, gates

    def validate(self, state=None, ancestry_check=lambda source, head: True):
        checklist, graph, registry, ownership, gates = state or self.state()
        return activation.validate_dependency_closeout(
            checklist,
            graph,
            registry,
            ownership,
            gates,
            self.head,
            ancestry_check=ancestry_check,
        )

    def test_clean_dependency_closeout_passes(self):
        errors, sources = self.validate()
        self.assertEqual(errors, [])
        self.assertEqual(sources, {"T10": self.t10, "T11": self.t11})

    def test_unapproved_dependency_fails(self):
        state = self.state()
        state[1]["tasks"]["T11"]["status"] = "ASSIGNED"
        state[2]["workstreams"][-1]["status"] = "ASSIGNED"
        state[4]["approved_tasks"].remove("T11")
        errors, _ = self.validate(state)
        self.assertTrue(any("T11 graph status" in e for e in errors))
        self.assertTrue(any("T11 registry status" in e for e in errors))
        self.assertTrue(any("T11 missing from task-gates" in e for e in errors))

    def test_missing_completed_task_record_fails(self):
        state = self.state()
        del state[4]["completed_task_records"]["T11"]
        errors, _ = self.validate(state)
        self.assertTrue(any("T11 has no completed_task_records" in e for e in errors))

    def test_completed_owner_source_mismatch_fails(self):
        state = self.state()
        state[3]["completed_production_owners"][0]["integrated_source"] = "d" * 40
        errors, _ = self.validate(state)
        self.assertTrue(any("does not match task-gates source" in e for e in errors))

    def test_nonancestor_accepted_source_fails(self):
        errors, _ = self.validate(
            ancestry_check=lambda source, head: source != self.t11
        )
        self.assertTrue(any("T11 accepted/integrated source" in e and "not an ancestor" in e for e in errors))

    def test_stale_dependency_owner_fails(self):
        state = self.state()
        state[3]["active_owners"] = [{
            "task_id": "T11",
            "status": "APPROVED",
            "paths_alias": "@reservation:T11",
        }]
        errors, _ = self.validate(state)
        self.assertTrue(any("still listed as an active owner" in e for e in errors))

    def test_path_safety_rejects_escape_and_absolute(self):
        self.assertTrue(activation.safe_repo_pattern("HavenlineGodot/data/example.json"))
        self.assertFalse(activation.safe_repo_pattern("../outside.json"))
        self.assertFalse(activation.safe_repo_pattern("/absolute/path"))

    def test_overlap_detects_exact_and_prefix_collisions(self):
        self.assertTrue(
            activation.may_overlap(
                "HavenlineGodot/data/**",
                "HavenlineGodot/data/progression_levels_v1.json",
            )
        )
        self.assertFalse(
            activation.may_overlap(
                "HavenlineGodot/data/progression_levels_v1.json",
                "HavenlineGodot/scripts/world_transform.gd",
            )
        )


if __name__ == "__main__":
    unittest.main()
