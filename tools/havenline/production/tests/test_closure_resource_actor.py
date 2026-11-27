"""Current resource/actor closure component; these are not game approvals."""
from __future__ import annotations

from contextlib import ExitStack
import copy
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

PRODUCTION = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PRODUCTION))
import closure_validator as closure
import resource_actor_contract as contract


class ClosureResourceActorTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.root = pathlib.Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.resources = contract.load(contract.RESOURCE_FILE)
        self.actors = contract.load(contract.ACTOR_FILE)
        self.animations = contract.load(contract.ANIMATION_FILE)
        self.paths = {}
        for constant, data in (("RESOURCE_FILE", self.resources), ("ACTOR_FILE", self.actors),
                               ("ANIMATION_FILE", self.animations)):
            path = self.root / (constant + ".json")
            path.write_text(json.dumps(data), encoding="utf-8")
            self.paths[constant] = path
            self.stack.enter_context(patch.object(contract, constant, path))
        self.stack.enter_context(patch.object(closure, "ROOT", self.root))

    def sync_registries(self):
        for constant, data in (("RESOURCE_FILE", self.resources), ("ACTOR_FILE", self.actors),
                               ("ANIMATION_FILE", self.animations)):
            self.paths[constant].write_text(json.dumps(data), encoding="utf-8")

    def manifest(self, task):
        return {"task_id": task, "candidate_commit": "a" * 40,
                "resource_actor_contract": {
                    "applicable": True, "validation_passed": True,
                    "introduced_resource_ids": [],
                    "resource_ids_covered": ["wood", "stone", "metal", "fuel"]
                                            if task in {"T09", "T23", "T31", "T44"} else [],
                    "actor_keys_covered": list(self.actors["actors"]),
                    "animation_profiles_covered": list(self.animations["profiles"]),
                    "animation_delta": False}}

    def store_receipt(self, manifest, *, force_pass=False, change=None):
        proof = contract.evaluate_task(manifest["task_id"], manifest)
        manifest["resource_actor_contract"]["registry_hashes"] = copy.deepcopy(proof["registry_hashes"])
        if force_pass:
            # Model an older/falsely passed receipt. Even matching current input
            # hashes cannot waive a failure in the current executable checks.
            proof["passed"] = True
            proof["errors"] = []
        if change:
            change(proof)
        path = self.root / "contract-proof.json"
        body = (json.dumps(proof, sort_keys=True) + "\n").encode()
        path.write_bytes(body)
        manifest["resource_actor_contract"].update({
            "validator_output_path": path.name,
            "validator_output_sha256": hashlib.sha256(body).hexdigest()})
        return path, body

    def check(self, manifest):
        with patch.object(closure, "evaluate_resource_actor_task", wraps=contract.evaluate_task) as live:
            result = closure.validate_current_resource_actor_contract(manifest["task_id"], manifest)
            live.assert_called_once_with(manifest["task_id"], manifest)
            return result

    def test_phase_valid_T09_still_passes_this_component_with_current_receipt(self):
        manifest = self.manifest("T09")
        path, before = self.store_receipt(manifest)
        result = self.check(manifest)
        self.assertTrue(result["passed"], result["errors"])
        self.assertTrue(result["c5_required"])
        self.assertEqual(before, path.read_bytes())
        self.assertEqual("T23_FREEZE_REQUIRED", self.resources["resources"]["metal"]["survivor_animation_profile"])

    def test_passed_receipt_cannot_waive_removed_pet_attack_capability(self):
        self.actors["actors"]["fox"]["capabilities"].remove("attack")
        self.sync_registries()
        manifest = self.manifest("T26")
        path, before = self.store_receipt(manifest, force_pass=True)
        result = self.check(manifest)
        self.assertFalse(result["passed"])
        self.assertTrue(any("required pet fox lacks attack capability" in e for e in result["errors"]))
        self.assertEqual(before, path.read_bytes())

    def test_passed_receipt_cannot_waive_missing_named_pet_attack_profile(self):
        self.animations["profiles"]["alternative_owl_attack"] = self.animations["profiles"].pop("owl_attack")
        self.sync_registries()
        manifest = self.manifest("T27")
        self.store_receipt(manifest, force_pass=True)
        result = self.check(manifest)
        self.assertFalse(result["passed"])
        self.assertTrue(any("missing named attack profile owl_attack" in e for e in result["errors"]))

    def test_passed_receipt_cannot_waive_unresolved_required_survivor_profiles(self):
        for task in ("T23", "T31", "T44"):
            with self.subTest(task=task):
                manifest = self.manifest(task)
                path, before = self.store_receipt(manifest, force_pass=True)
                result = self.check(manifest)
                self.assertFalse(result["passed"])
                self.assertTrue(any("metal survivor profile remains deferred to T23" in e for e in result["errors"]))
                self.assertTrue(any("fuel survivor profile remains deferred to T23" in e for e in result["errors"]))
                self.assertEqual(before, path.read_bytes())

    def test_omitted_candidate_identity_or_schema_receipt_cannot_approve_coverage(self):
        mutations = [lambda proof: proof.pop("candidate_commit"),
                     lambda proof: proof.update(schema_only=True),
                     lambda proof: proof.update(validation_kind="REGISTRY_SCHEMA_ONLY")]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                manifest = self.manifest("T09")
                self.store_receipt(manifest, change=mutate)
                self.assertFalse(self.check(manifest)["passed"])

    def test_stale_validator_implementation_or_registry_binding_is_rejected(self):
        for field in ("validator_sha256", "registry_hashes"):
            with self.subTest(field=field):
                manifest = self.manifest("T09")
                self.store_receipt(manifest, change=lambda proof: proof.update({field: "0" * 64}))
                result = self.check(manifest)
                self.assertFalse(result["passed"])
                self.assertTrue(any("stale" in e for e in result["errors"]))

    def test_motion_critic_requirement_reaches_closure_for_every_species(self):
        for task in ("T24", "T25", "T26", "T27", "T28", "T29", "T30"):
            with self.subTest(task=task):
                manifest = self.manifest(task)
                self.store_receipt(manifest)
                result = self.check(manifest)
                self.assertTrue(result["passed"], result["errors"])
                self.assertTrue(result["c5_required"])

    def test_missing_current_evaluator_data_fails_closed(self):
        manifest = self.manifest("T09")
        self.store_receipt(manifest)
        with patch.object(closure, "evaluate_resource_actor_task", side_effect=OSError("unavailable registry")):
            result = closure.validate_current_resource_actor_contract("T09", manifest)
        self.assertFalse(result["passed"])
        self.assertTrue(any("unavailable" in e for e in result["errors"]))

    def test_unrelated_T05_scope_is_not_retroactively_expanded(self):
        result = closure.validate_current_resource_actor_contract("T05", {"candidate_commit": "a" * 40})
        self.assertFalse(result["applicable"])
        self.assertTrue(result["passed"], result["errors"])


if __name__ == "__main__":
    unittest.main()
