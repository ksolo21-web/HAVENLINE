import copy
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve()
PROD = HERE.parents[1]
sys.path.insert(0, str(PROD))

from lib import DOCS, load_json
from validate_integration_scope import evaluate


class IntegrationScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_json(DOCS / "WORKSTREAM_REGISTRY.json")
        cls.ownership = load_json(DOCS / "PATH_OWNERSHIP.json")

    def registry_with(self, task_id, status):
        registry = copy.deepcopy(self.registry)
        row = next(w for w in registry["workstreams"] if w["task_id"] == task_id)
        row["status"] = status
        return registry

    def test_governance_only_change_passes(self):
        report = evaluate(["Docs/Production/WORKSTREAM_REGISTRY.json"], self.registry, self.ownership)
        self.assertTrue(report["passed"])
        self.assertEqual(report["classification"], "GOVERNANCE_ONLY")
        self.assertIsNone(report["task_id"])

    def test_assigned_t04_runtime_cannot_integrate_early(self):
        registry = self.registry_with("T04", "ASSIGNED")
        report = evaluate(["HavenlineGodot/scripts/camera_composition.gd"], registry, self.ownership)
        self.assertFalse(report["passed"])
        self.assertTrue(any("T04 runtime path changed while task state is ASSIGNED" in x for x in report["errors"]))

    def test_t04_runtime_passes_when_integration_ready(self):
        registry = self.registry_with("T04", "INTEGRATION_READY")
        report = evaluate(["HavenlineGodot/scripts/camera_composition.gd"], registry, self.ownership)
        self.assertTrue(report["passed"])
        self.assertEqual(report["task_id"], "T04")

    def test_locked_t05_runtime_is_rejected(self):
        report = evaluate(["HavenlineGodot/scripts/station_kit.gd"], self.registry, self.ownership)
        self.assertFalse(report["passed"])
        self.assertTrue(any("T05 runtime path changed while task state is LOCKED" in x for x in report["errors"]))

    def test_unowned_runtime_is_rejected(self):
        report = evaluate(["HavenlineGodot/scripts/unregistered_future_runtime.gd"], self.registry, self.ownership)
        self.assertFalse(report["passed"])
        self.assertTrue(any("exactly one registered task owner" in x for x in report["errors"]))

    def test_integration_only_wiring_requires_authorization(self):
        registry = self.registry_with("T04", "INTEGRATING")
        files = ["HavenlineGodot/scripts/camera_composition.gd", "HavenlineGodot/scripts/main.gd"]
        denied = evaluate(files, registry, self.ownership)
        self.assertFalse(denied["passed"])
        self.assertTrue(any("lacks authorized change request for T04" in x for x in denied["errors"]))
        allowed = evaluate(files, registry, self.ownership, {"T04": {"HavenlineGodot/scripts/main.gd"}})
        self.assertTrue(allowed["passed"])

    def test_sequential_commit_cannot_span_multiple_tasks(self):
        registry = self.registry_with("T04", "INTEGRATING")
        registry = copy.deepcopy(registry)
        next(w for w in registry["workstreams"] if w["task_id"] == "T05")["status"] = "INTEGRATING"
        files = ["HavenlineGodot/scripts/camera_composition.gd", "HavenlineGodot/scripts/station_kit.gd"]
        report = evaluate(files, registry, self.ownership)
        self.assertFalse(report["passed"])
        self.assertTrue(any("spans multiple task owners" in x for x in report["errors"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
