#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
TOOL_PATH = ROOT / "tools/havenline/task12/materialize_progression_data.py"
BLUEPRINT_PATH = ROOT / "Docs/Production/T12/AUTHORING_BLUEPRINT.json"
BINDING_INDEX_PATH = ROOT / "Docs/Production/T12/FACT_SLOT_BINDING_INDEX_TEMPLATE.json"
BINDING_CATALOG_PATH = ROOT / "Docs/Production/T12/BINDING_SLOT_CATALOG.json"

spec = importlib.util.spec_from_file_location("t12_materializer", TOOL_PATH)
materializer = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(materializer)

class T12MaterializerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.blueprint = json.loads(BLUEPRINT_PATH.read_text())
        cls.binding_index = json.loads(BINDING_INDEX_PATH.read_text())
        cls.binding_catalog = json.loads(BINDING_CATALOG_PATH.read_text())

    def test_dry_run_materialization_passes_real_shipping_validator(self):
        result = materializer.validate_materialized(copy.deepcopy(self.blueprint))
        self.assertTrue(result["passed"], result["progression_validation"]["errors"])
        self.assertEqual(result["level_count"], 100)
        self.assertEqual(result["milestone_count"], 10)

    def test_materialized_fact_slots_are_canonical(self):
        levels_doc, _, _ = materializer.materialize(copy.deepcopy(self.blueprint))
        self.assertEqual(levels_doc["levels"][0]["required_fact_ids"], [])
        for level in range(2, 101):
            self.assertEqual(
                levels_doc["levels"][level - 1]["required_fact_ids"],
                [f"t12.fact.slot.{level:03d}"],
            )

    def test_external_upstream_ids_do_not_leak_into_shipping_level_data(self):
        levels_doc, _, _ = materializer.materialize(copy.deepcopy(self.blueprint))
        blob = json.dumps(levels_doc)
        self.assertNotIn("framework_anchor_seed_to_foundation", blob)
        self.assertNotIn("framework_anchor_foundation_to_reinforced", blob)
        self.assertNotIn("t11_provisional", blob)

    def resolved_binding_index(self):
        data = copy.deepcopy(self.binding_index)
        data["status"] = "RESOLVED_FACT_SLOT_BINDING_INDEX"
        data["shipping_path_forbidden"] = False
        for row in data["entries"]:
            fact_kind = (
                "camp_state_completed"
                if row["level"] == 6 and "camp_state_completed" in row["allowed_fact_kinds"]
                else next(
                    kind for kind in row["allowed_fact_kinds"]
                    if kind not in materializer.binding_index_validator.INTERNAL_ONLY_FACT_KINDS
                )
            )
            if fact_kind == "context_action_completed":
                source_task = "T07"
            elif fact_kind == "resource_delivery_completed":
                source_task = "T08"
            elif fact_kind == "world_transform_completed":
                source_task = "T10"
            elif fact_kind == "camp_state_completed":
                source_task = "T11"
            else:
                source_task = row["content_owner_task"]
            row["resolved_binding"] = {
                "slot_id": row["slot_id"],
                "fact_kind": fact_kind,
                "source_task": source_task,
                "source_id": f"accepted.source.{row['level']:03d}",
                "resolution_state": "RESOLVED",
                "evidence_ref": (
                    f"artifact://binding-resolution/{row['slot_id']}.json"
                    if source_task in {"T10", "T11"}
                    else f"artifact://binding/{row['slot_id']}.json"
                ),
                "idempotency_domain": f"t12.materializer.{row['level']:03d}",
            }
        return data

    def test_resolved_binding_index_materializes_canonical_shipping_file(self):
        document = materializer.materialize_bindings(
            self.resolved_binding_index(),
            copy.deepcopy(self.binding_catalog),
        )
        self.assertEqual(set(document), {"schema_version", "task_id", "bindings"})
        self.assertEqual(document["schema_version"], 1)
        self.assertEqual(document["task_id"], "T12")
        self.assertEqual(len(document["bindings"]), 99)
        result = materializer.binding_index_validator.validate_shipping(
            document,
            self.binding_catalog,
        )
        self.assertTrue(result["passed"], result["errors"])

    def test_unresolved_binding_template_cannot_materialize_shipping_file(self):
        with self.assertRaisesRegex(ValueError, "resolved binding index invalid"):
            materializer.materialize_bindings(
                copy.deepcopy(self.binding_index),
                copy.deepcopy(self.binding_catalog),
            )

    def test_shipping_t10_binding_must_exist_in_binding_resolution(self):
        document = materializer.materialize_bindings(
            self.resolved_binding_index(),
            copy.deepcopy(self.binding_catalog),
        )
        t10_row = next(row for row in document["bindings"] if row["source_task"] == "T10")
        resolution = {
            "fact_kind_compatibility": {
                "world_transform_completed": {
                    "source_task": "T10",
                    "accepted_id_kinds": ["transform_recipe", "transform_state"],
                },
                "camp_state_completed": {
                    "source_task": "T11",
                    "accepted_id_kinds": ["camp_recipe_binding", "camp_state"],
                },
            },
            "dependencies": {
                "T10": {"resolved_public_ids": [{"id": "different-transform-id", "kind": "transform_recipe"}]},
                "T11": {
                    "resolved_public_ids": [
                        {"id": row["source_id"], "kind": "camp_state"}
                        for row in document["bindings"]
                        if row["source_task"] == "T11"
                    ]
                },
            },
        }
        errors = materializer.validate_shipping_bindings_against_resolution(document, resolution)
        self.assertTrue(any("T10 source IDs absent from BINDING_RESOLUTION" in error for error in errors))
        self.assertIn(t10_row["source_id"], errors[0])

    def test_shipping_t10_t11_binding_cross_proof_passes_when_all_ids_are_accepted(self):
        document = materializer.materialize_bindings(
            self.resolved_binding_index(),
            copy.deepcopy(self.binding_catalog),
        )
        resolution = {
            "fact_kind_compatibility": {
                "world_transform_completed": {
                    "source_task": "T10",
                    "accepted_id_kinds": ["transform_recipe", "transform_state"],
                },
                "camp_state_completed": {
                    "source_task": "T11",
                    "accepted_id_kinds": ["camp_recipe_binding", "camp_state"],
                },
            },
            "dependencies": {
                task: {
                    "resolved_public_ids": [
                        {
                            "id": row["source_id"],
                            "kind": "transform_recipe" if task == "T10" else "camp_state",
                        }
                        for row in document["bindings"]
                        if row["source_task"] == task
                    ]
                }
                for task in ("T10", "T11")
            },
        }
        self.assertEqual(
            materializer.validate_shipping_bindings_against_resolution(document, resolution),
            [],
        )

    def test_shipping_t10_binding_kind_must_match_fact_kind(self):
        document = materializer.materialize_bindings(
            self.resolved_binding_index(),
            copy.deepcopy(self.binding_catalog),
        )
        resolution = {
            "fact_kind_compatibility": {
                "world_transform_completed": {
                    "source_task": "T10",
                    "accepted_id_kinds": ["transform_recipe"],
                },
                "camp_state_completed": {
                    "source_task": "T11",
                    "accepted_id_kinds": ["camp_state"],
                },
            },
            "dependencies": {
                "T10": {
                    "resolved_public_ids": [
                        {"id": row["source_id"], "kind": "transform_state"}
                        for row in document["bindings"]
                        if row["source_task"] == "T10"
                    ]
                },
                "T11": {
                    "resolved_public_ids": [
                        {"id": row["source_id"], "kind": "camp_state"}
                        for row in document["bindings"]
                        if row["source_task"] == "T11"
                    ]
                },
            },
        }
        errors = materializer.validate_shipping_bindings_against_resolution(document, resolution)
        self.assertTrue(any("incompatible with fact_kind" in error for error in errors))

    def test_blueprint_identity_drift_fails_closed(self):
        blueprint = copy.deepcopy(self.blueprint)
        blueprint["task_id"] = "T13"
        with self.assertRaises(ValueError):
            materializer.materialize(blueprint)

    def test_actual_builder_branch_is_required_for_shipping_write(self):
        self.assertEqual(
            materializer.validate_actual_builder_branch(materializer.EXPECTED_BRANCH),
            [],
        )
        errors = materializer.validate_actual_builder_branch("havenline/wrong-branch")
        self.assertTrue(any("shipping materialization must run on" in error for error in errors))

    def test_write_authority_passes_only_for_claimed_t12(self):
        base = "a" * 40
        registry = {
            "workstreams": [{
                "task_id": "T12",
                "status": "ASSIGNED",
                "owner": materializer.EXPECTED_OWNER,
                "branch": materializer.EXPECTED_BRANCH,
                "base_commit": base,
                "owned_paths": ["@reservation:T12"],
            }]
        }
        ownership = {
            "active_owners": [{
                "task_id": "T12",
                "paths_alias": "@reservation:T12",
            }]
        }
        original = materializer.binding_verifier.validate_resolution
        materializer.binding_verifier.validate_resolution = lambda *args, **kwargs: {
            "passed": True, "activation_head": base, "errors": []
        }
        try:
            errors = materializer.validate_write_authority(base, registry, ownership, {})
        finally:
            materializer.binding_verifier.validate_resolution = original
        self.assertEqual(errors, [])

    def test_write_authority_rejects_wrong_owner_and_missing_active_ownership(self):
        base = "a" * 40
        registry = {
            "workstreams": [{
                "task_id": "T12",
                "status": "ASSIGNED",
                "owner": "wrong-owner",
                "branch": materializer.EXPECTED_BRANCH,
                "base_commit": base,
                "owned_paths": ["@reservation:T12"],
            }]
        }
        original = materializer.binding_verifier.validate_resolution
        materializer.binding_verifier.validate_resolution = lambda *args, **kwargs: {
            "passed": True, "activation_head": base, "errors": []
        }
        try:
            errors = materializer.validate_write_authority(base, registry, {"active_owners": []}, {})
        finally:
            materializer.binding_verifier.validate_resolution = original
        self.assertTrue(any("owner mismatch" in error for error in errors))
        self.assertTrue(any("exactly one active T12 owner" in error for error in errors))

    def test_write_authority_rejects_unresolved_binding_proof(self):
        base = "a" * 40
        registry = {
            "workstreams": [{
                "task_id": "T12",
                "status": "ASSIGNED",
                "owner": materializer.EXPECTED_OWNER,
                "branch": materializer.EXPECTED_BRANCH,
                "base_commit": base,
                "owned_paths": ["@reservation:T12"],
            }]
        }
        ownership = {"active_owners": [{"task_id": "T12", "paths_alias": "@reservation:T12"}]}
        original = materializer.binding_verifier.validate_resolution
        materializer.binding_verifier.validate_resolution = lambda *args, **kwargs: {
            "passed": False, "errors": ["unresolved T11"]
        }
        try:
            errors = materializer.validate_write_authority(base, registry, ownership, {})
        finally:
            materializer.binding_verifier.validate_resolution = original
        self.assertTrue(any("resolved binding proof failed" in error for error in errors))

if __name__ == "__main__":
    unittest.main()
