from __future__ import annotations

import copy
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve()
PRODUCTION = HERE.parents[1]
sys.path.insert(0, str(PRODUCTION))

from validate_migration import t10_activation_errors


class T10ActivationValidationTests(unittest.TestCase):
    BASE = "a" * 40

    def state(self):
        dependencies = ["T05", "T08", "T09"]
        critics = ["C1", "C2", "C3", "C4", "C6", "C7"]
        paths = ["HavenlineGodot/scripts/world_transform.gd", "Docs/Production/T10/**"]
        tasks = {f"T{i:02d}": {"status": "LOCKED", "dependencies": [], "critics": []} for i in range(1, 71)}
        for task in dependencies:
            tasks[task]["status"] = "APPROVED"
        tasks["T10"] = {"status": "ASSIGNED", "dependencies": dependencies, "critics": critics}
        registry = {"workstreams": [{
            "task_id": "T10", "workstream_id": "T10-world-transformation-builder", "status": "ASSIGNED",
            "owner": "world-transformation-builder", "branch": "havenline/T10-world-transformation",
            "base_commit": self.BASE, "owned_paths": ["@reservation:T10"], "dependencies": dependencies,
            "critic_requirements": critics, "evidence_path": "Docs/Production/Evidence/T10/",
        }]}
        ownership = {
            "aliases": {"@reservation:T10": paths},
            "active_owners": [{
                "task_id": "T10", "workstream": "T10-world-transformation-builder", "status": "ASSIGNED",
                "owner": "world-transformation-builder", "branch": "havenline/T10-world-transformation",
                "base_commit": self.BASE, "paths_alias": "@reservation:T10",
            }],
        }
        gates = {
            "active_task": "T10", "active_status": "ASSIGNED", "active_base_integration_commit": self.BASE,
            "active_frozen_scope": "Docs/Production/T10/FROZEN_SCOPE.md",
            "active_task_packet": "Docs/Production/T10/TASK_PACKET.md",
            "active_evidence": "Docs/Production/Evidence/T10/",
            "active_critic_state": "PENDING_BUILD_AND_INDEPENDENT_REVIEW",
            "next_post_t03_wave": [{
                "task": "T10", "state": "ASSIGNED", "owner": "world-transformation-builder",
                "branch": "havenline/T10-world-transformation", "base_commit": self.BASE,
            }],
        }
        checklist = {"dependencies": dependencies, "required_critics": critics, "planned_owned_paths": paths}
        return {"tasks": tasks}, registry, ownership, gates, checklist

    def errors(self, state):
        return t10_activation_errors(*state)

    def test_exact_activated_state_passes(self):
        self.assertEqual(self.errors(self.state()), [])

    def test_locked_state_with_cleared_pointers_passes(self):
        graph, registry, ownership, gates, checklist = self.state()
        graph["tasks"]["T10"]["status"] = "LOCKED"
        ownership["active_owners"] = []
        for field in ("active_task", "active_status", "active_base_integration_commit", "active_frozen_scope", "active_task_packet", "active_evidence", "active_critic_state"):
            gates[field] = None
        self.assertEqual(self.errors((graph, registry, ownership, gates, checklist)), [])

    def test_missing_registry_fails(self):
        state = list(self.state())
        state[1]["workstreams"] = []
        self.assertTrue(self.errors(tuple(state)))

    def test_each_activation_identity_mismatch_fails(self):
        mutations = (
            (1, "workstreams", 0, "branch"),
            (1, "workstreams", 0, "base_commit"),
            (2, "active_owners", 0, "owner"),
            (2, "active_owners", 0, "paths_alias"),
            (3, None, None, "active_status"),
        )
        for container_index, collection, row_index, field in mutations:
            with self.subTest(field=field):
                state = list(copy.deepcopy(self.state()))
                target = state[container_index] if collection is None else state[container_index][collection][row_index]
                target[field] = "mismatch"
                self.assertTrue(self.errors(tuple(state)))

    def test_future_unlock_or_owner_fails(self):
        state = list(self.state())
        state[0]["tasks"]["T11"]["status"] = "ASSIGNED"
        state[2]["active_owners"].append({"task_id": "T11"})
        errors = self.errors(tuple(state))
        self.assertTrue(any("T11+ must remain LOCKED" in error for error in errors))
        self.assertTrue(any("T11+ active ownership" in error for error in errors))

    def test_unapproved_dependency_fails(self):
        state = list(self.state())
        state[0]["tasks"]["T09"]["status"] = "UNDER_REVIEW"
        self.assertTrue(any("dependencies are not all APPROVED" in error for error in self.errors(tuple(state))))


if __name__ == "__main__":
    unittest.main(verbosity=2)
