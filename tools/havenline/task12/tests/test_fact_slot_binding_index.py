#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
TOOL_PATH = ROOT / "tools/havenline/task12/validate_fact_slot_binding_index.py"
INDEX_PATH = ROOT / "Docs/Production/T12/FACT_SLOT_BINDING_INDEX_TEMPLATE.json"
CATALOG_PATH = ROOT / "Docs/Production/T12/BINDING_SLOT_CATALOG.json"

spec = importlib.util.spec_from_file_location("t12_fact_slot_index", TOOL_PATH)
validator = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(validator)

class T12FactSlotBindingIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = json.loads(INDEX_PATH.read_text())
        cls.catalog = json.loads(CATALOG_PATH.read_text())

    def validate(self, data=None, catalog=None):
        return validator.validate(
            copy.deepcopy(data if data is not None else self.index),
            copy.deepcopy(catalog if catalog is not None else self.catalog),
        )

    def test_binding_index_template_passes(self):
        result = self.validate()
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["entry_count"], 99)
        self.assertEqual(result["unresolved_entry_count"], 99)

    def resolved_index(self):
        data = copy.deepcopy(self.index)
        data["status"] = "RESOLVED_FACT_SLOT_BINDING_INDEX"
        data["shipping_path_forbidden"] = False
        for row in data["entries"]:
            fact_kind = (
                "camp_state_completed"
                if row["level"] == 6 and "camp_state_completed" in row["allowed_fact_kinds"]
                else next(
                    kind for kind in row["allowed_fact_kinds"]
                    if kind not in validator.INTERNAL_ONLY_FACT_KINDS
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
            evidence = (
                f"artifact://binding-resolution/{row['slot_id']}.json"
                if source_task in {"T10", "T11"}
                else f"artifact://binding/{row['slot_id']}.json"
            )
            row["resolved_binding"] = {
                "slot_id": row["slot_id"],
                "fact_kind": fact_kind,
                "source_task": source_task,
                "source_id": f"source.{row['level']:03d}",
                "resolution_state": "RESOLVED",
                "evidence_ref": evidence,
                "idempotency_domain": f"t12.test.{row['level']:03d}",
            }
        return data

    def test_resolved_index_passes(self):
        result = validator.validate(self.resolved_index(), self.catalog, require_resolved=True)
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["resolved_entry_count"], 99)
        self.assertEqual(result["deferred_entry_count"], 0)

    def test_shipping_binding_document_passes(self):
        data = self.resolved_index()
        shipping = {
            "schema_version": 1,
            "task_id": "T12",
            "bindings": [copy.deepcopy(row["resolved_binding"]) for row in data["entries"]],
        }
        result = validator.validate_shipping(shipping, self.catalog)
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["entry_count"], 99)

    def test_opening_activation_slot_cannot_be_deferred(self):
        data = self.resolved_index()
        row = next(item for item in data["entries"] if item["level"] == 3)
        row["resolved_binding"] = {
            "slot_id": row["slot_id"],
            "fact_kind": "world_transform_completed",
            "source_task": row["content_owner_task"],
            "source_id": "",
            "resolution_state": "DEFERRED_LATER_OWNER",
            "evidence_ref": "contract://later-owner-registration",
            "idempotency_domain": "",
        }
        result = validator.validate(data, self.catalog, require_resolved=True)
        self.assertFalse(result["passed"])
        self.assertTrue(any("opening activation binding may not be deferred" in error for error in result["errors"]))

    def test_opening_activation_requires_t11_coverage(self):
        data = self.resolved_index()
        for row in data["entries"]:
            if row["level"] == 6:
                row["resolved_binding"] = {
                    "slot_id": row["slot_id"],
                    "fact_kind": "world_transform_completed",
                    "source_task": "T10",
                    "source_id": "transform.only",
                    "resolution_state": "RESOLVED",
                    "evidence_ref": "artifact://binding-resolution/t10-only.json",
                    "idempotency_domain": "t10.transform",
                }
        result = validator.validate(data, self.catalog, require_resolved=True)
        self.assertFalse(result["passed"])
        self.assertTrue(any("consume both T10 and T11" in error for error in result["errors"]))

    def test_valid_deferred_later_owner_passes(self):
        data = self.resolved_index()
        row = data["entries"][3]  # Level 5 content-owner capability slot.
        row["resolved_binding"] = {
            "slot_id": row["slot_id"],
            "fact_kind": "capability_condition_completed",
            "source_task": row["content_owner_task"],
            "source_id": "",
            "resolution_state": "DEFERRED_LATER_OWNER",
            "evidence_ref": "contract://later-owner-registration",
            "idempotency_domain": "",
        }
        result = validator.validate(data, self.catalog, require_resolved=True)
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["deferred_entry_count"], 1)

    def test_deferred_wrong_owner_fails(self):
        data = self.resolved_index()
        row = data["entries"][3]
        row["resolved_binding"] = {
            "slot_id": row["slot_id"],
            "fact_kind": "capability_condition_completed",
            "source_task": "T99",
            "source_id": "",
            "resolution_state": "DEFERRED_LATER_OWNER",
            "evidence_ref": "contract://later-owner-registration",
            "idempotency_domain": "",
        }
        result = validator.validate(data, self.catalog, require_resolved=True)
        self.assertFalse(result["passed"])
        self.assertTrue(any("deferred source_task" in error for error in result["errors"]))

    def test_t11_resolved_binding_requires_binding_resolution_evidence(self):
        data = self.resolved_index()
        row = data["entries"][1]  # Level 3 allows camp_state_completed.
        row["resolved_binding"] = {
            "slot_id": row["slot_id"],
            "fact_kind": "camp_state_completed",
            "source_task": "T11",
            "source_id": "camp.accepted.state",
            "resolution_state": "RESOLVED",
            "evidence_ref": "artifact://camp-state.json",
            "idempotency_domain": "t11.camp",
        }
        result = validator.validate(data, self.catalog, require_resolved=True)
        self.assertFalse(result["passed"])
        self.assertTrue(any("binding-resolution proof" in error for error in result["errors"]))

    def test_duplicate_level_fails(self):
        data = copy.deepcopy(self.index)
        data["entries"][10]["level"] = data["entries"][9]["level"]
        result = self.validate(data=data)
        self.assertFalse(result["passed"])
        self.assertTrue(any("duplicate binding-index level" in error for error in result["errors"]))

    def test_slot_id_drift_fails(self):
        data = copy.deepcopy(self.index)
        data["entries"][40]["slot_id"] = "t12.fact.slot.999"
        result = self.validate(data=data)
        self.assertFalse(result["passed"])
        self.assertTrue(any("slot_id" in error for error in result["errors"]))

    def test_preactivation_resolution_is_forbidden(self):
        data = copy.deepcopy(self.index)
        data["entries"][0]["resolved_binding"] = {
            "slot_id": "t12.fact.slot.002",
            "fact_kind": "context_action_completed",
            "source_task": "T07",
            "source_id": "made-up",
            "resolution_state": "RESOLVED",
            "evidence_ref": "fake",
            "idempotency_domain": "fake",
        }
        result = self.validate(data=data)
        self.assertFalse(result["passed"])
        self.assertTrue(any("preparation template resolved_binding must remain null" in error for error in result["errors"]))

    def test_t11_public_id_invention_fails(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["authority_classes"]["T11_CAMP"]["current_public_ids"] = ["camp.future"]
        result = self.validate(catalog=catalog)
        self.assertFalse(result["passed"])
        self.assertTrue(any("T11 public IDs" in error for error in result["errors"]))

    def test_spend_blind_rule_removal_fails(self):
        data = copy.deepcopy(self.index)
        data["rules"] = [rule.replace("premium_spend", "spend") for rule in data["rules"]]
        result = self.validate(data=data)
        self.assertFalse(result["passed"])
        self.assertTrue(any("premium_spend" in error for error in result["errors"]))

if __name__ == "__main__":
    unittest.main()
