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

    def completed_state(self):
        graph, registry, ownership, gates, checklist = self.state()
        for i in range(1,11): graph['tasks'][f'T{i:02d}']['status']='APPROVED'
        registry['workstreams'][0]['status']='APPROVED'
        registry['workstreams'][0]['candidate_commit']='b'*40
        owner=ownership['active_owners'].pop()
        owner.update(status='APPROVED',accepted_source='b'*40,integrated_source='c'*40)
        ownership['completed_production_owners']=[owner]
        for field in list(gates):
            if field.startswith('active_'):gates[field]=None
        gates['approved_tasks']=[f'T{i:02d}' for i in range(1,11)]
        gates['completed_task_records']={'T10':dict(status='APPROVED',accepted_source='b'*40,integrated_source='c'*40,record='Docs/Production/T10/verified-completion.json')}
        gates['next_post_t03_wave'][0]['state']='APPROVED'
        return graph, registry, ownership, gates, checklist

    def test_complete_terminal_state(self):
        self.assertEqual([],self.errors(self.completed_state()))

    def test_terminal_registry_candidate_failures(self):
        for value in (None,'bad','d'*40):
            state=self.completed_state()
            if value is None:state[1]['workstreams'][0].pop('candidate_commit')
            else:state[1]['workstreams'][0]['candidate_commit']=value
            with self.subTest(value=value):self.assertTrue(self.errors(state))

    def test_terminal_owner_failures(self):
        for change in ('missing','duplicate','active','source','status','branch'):
            state=self.completed_state();owners=state[2]
            if change=='missing':owners['completed_production_owners']=[]
            elif change=='duplicate':owners['completed_production_owners']*=2
            elif change=='active':owners['active_owners']=[dict(task_id='T10')]
            else:owners['completed_production_owners'][0][{'source':'integrated_source'}.get(change,change)]='wrong'
            with self.subTest(change=change):self.assertTrue(self.errors(state))

    def test_terminal_gate_failures(self):
        for change in ('pointer','missing_pointer','source','record','status','prefix_missing','prefix_extra','future'):
            state=self.completed_state();gates=state[3]
            if change=='pointer':gates['active_task']='T10'
            elif change=='missing_pointer':del gates['active_evidence']
            elif change=='prefix_missing':gates['approved_tasks'].pop()
            elif change=='prefix_extra':gates['approved_tasks'].append('T11')
            elif change=='future':state[0]['tasks']['T11']['status']='ASSIGNED'
            else:gates['completed_task_records']['T10'][{'source':'accepted_source'}.get(change,change)]='wrong'
            with self.subTest(change=change):self.assertTrue(self.errors(state))


class T10WorkflowActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        workflow = (PRODUCTION.parents[2] / ".github/workflows/havenline-production-governance.yml").read_text()
        start = workflow.index("          cat > /tmp/t10_activation_check.py <<'PY'\n")
        body = workflow[start:].split("\n", 1)[1].split("          PY\n", 1)[0]
        code = "\n".join(line[10:] for line in body.splitlines())
        namespace = {"__name__": "workflow_fixture"}
        exec(compile(code, "workflow_activation_helper", "exec"), namespace)
        cls.check = staticmethod(namespace["validate_t10_activation"])
        cls.active_states = namespace["ACTIVE_RUNTIME_STATES"]

    def fixture(self, status="ASSIGNED"):
        graph, registry, ownership, _, _ = T10ActivationValidationTests().state()
        graph["tasks"]["T10"]["status"] = status
        registry["workstreams"][0]["status"] = status
        snapshot = {"task_id": "T10", "lifecycle_status": status,
                    "task_branch": registry["workstreams"][0]["branch"],
                    "owned_paths": ownership["aliases"]["@reservation:T10"],
                    "validation": {"passed": True}, "snapshot_is_derived_not_authority": True,
                    "blockers": []}
        return [graph, registry, ownership, snapshot, "Active packet"]

    def test_all_canonical_active_states(self):
        for status in self.active_states:
            with self.subTest(status=status):
                self.assertEqual(self.check(*self.fixture(status)), status)

    def test_completed_is_not_runtime_activation(self):
        data = self.fixture("APPROVED")
        data[-1] = "DO NOT start runtime implementation"
        self.assertEqual(self.check(*data), "APPROVED")

    def test_inactive_states_reject(self):
        for status in ("LOCKED", "PREPARED", "BLOCKED"):
            with self.subTest(status=status), self.assertRaises(AssertionError):
                self.check(*self.fixture(status))

    def test_mismatch_or_missing_ownership_rejects(self):
        for field, value in (("status", "BUILDING_ISOLATED"), ("branch", ""), ("owned_paths", [])):
            data = self.fixture()
            data[1]["workstreams"][0][field] = value
            with self.subTest(field=field), self.assertRaises(AssertionError):
                self.check(*data)

    def test_invalid_stale_unowned_snapshot_rejects(self):
        for field, value in (("validation", {"passed": False}), ("snapshot_is_derived_not_authority", False),
                             ("lifecycle_status", "LOCKED"), ("task_branch", "wrong"), ("owned_paths", []),
                             ("blockers", ["ownership_not_assigned"]), ("blockers", ["lifecycle_status_LOCKED"])):
            data = self.fixture()
            data[3][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(AssertionError):
                self.check(*data)

    def test_stop_warned_active_packet_rejects(self):
        data = self.fixture()
        data[-1] = "DO NOT start runtime implementation"
        with self.assertRaises(AssertionError):
            self.check(*data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
