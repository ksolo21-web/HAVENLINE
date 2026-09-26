#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
ENGINE_PATH = ROOT / "tools/havenline/task12/reference_progression_engine.py"
MATERIALIZER_PATH = ROOT / "tools/havenline/task12/materialize_progression_data.py"
BLUEPRINT_PATH = ROOT / "Docs/Production/T12/AUTHORING_BLUEPRINT.json"

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

engine_mod = load_module("t12_reference_engine_test", ENGINE_PATH)
materializer = load_module("t12_materializer_engine_test", MATERIALIZER_PATH)

class T12ReferenceProgressionEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        blueprint = json.loads(BLUEPRINT_PATH.read_text())
        cls.levels_doc, cls.milestones_doc, _ = materializer.materialize(blueprint)

    def bindings(self):
        rows = []
        for level in range(2, 101):
            rows.append({
                "slot_id": f"t12.fact.slot.{level:03d}",
                "fact_kind": "synthetic_fact_completed",
                "source_task": "TSYN",
                "source_id": f"synthetic.source.{level:03d}",
                "resolution_state": "RESOLVED",
                "evidence_ref": f"fixture://binding/{level:03d}",
                "idempotency_domain": f"t12.synthetic.{level:03d}",
            })
        return rows

    def engine(self, bindings=None, snapshot=None):
        return engine_mod.ReferenceProgressionEngine(
            copy.deepcopy(self.levels_doc),
            copy.deepcopy(self.milestones_doc),
            copy.deepcopy(bindings if bindings is not None else self.bindings()),
            copy.deepcopy(snapshot) if snapshot is not None else None,
        )

    def observe(self, engine, level, key=None):
        return engine.observe_authoritative_fact(
            "TSYN",
            "synthetic_fact_completed",
            f"synthetic.source.{level:03d}",
            key or f"producer-key-{level:03d}",
        )

    def test_fresh_initialization_completes_level_one_once(self):
        engine = self.engine()
        self.assertEqual(
            [intent["level_id"] for intent in engine.initialization_intents],
            ["t12.level.001"],
        )
        self.assertEqual(engine.snapshot()["completed_level_ids"], ["t12.level.001"])
        self.assertEqual(
            engine.initialization_intents[0]["unlocked_level_ids"],
            ["t12.level.002"],
        )
        self.assertEqual(engine.initialization_intents[0]["source_fact_keys"], [])

    def test_out_of_order_fact_is_retained_without_skipping_prerequisite(self):
        engine = self.engine()
        first = self.observe(engine, 3, "fact-three")
        self.assertTrue(first["passed"])
        self.assertTrue(first["mutated"])
        self.assertEqual(first["intents"], [])
        self.assertIn("t12.fact.slot.003", engine.snapshot()["satisfied_fact_slot_ids"])
        level3 = engine.get_level_state("t12.level.003")
        self.assertEqual(level3["state"], "locked")
        self.assertEqual(level3["missing_prerequisite_level_ids"], ["t12.level.002"])

        second = self.observe(engine, 2, "fact-two")
        self.assertTrue(second["passed"])
        self.assertEqual(
            [intent["level_id"] for intent in second["intents"]],
            ["t12.level.002", "t12.level.003"],
        )
        self.assertEqual(
            engine.snapshot()["completed_level_ids"],
            ["t12.level.001", "t12.level.002", "t12.level.003"],
        )
        level3_intent = second["intents"][1]
        self.assertEqual(
            level3_intent["source_fact_keys"],
            ["t12.synthetic.003|fact-three"],
        )

    def test_duplicate_fact_after_slot_satisfied_is_bounded_noop(self):
        engine = self.engine()
        first = self.observe(engine, 2, "same")
        before = engine.snapshot()
        second = self.observe(engine, 2, "different-key-same-semantic-fact")
        self.assertTrue(first["mutated"])
        self.assertTrue(second["passed"])
        self.assertTrue(second["replayed"])
        self.assertFalse(second["mutated"])
        self.assertEqual(second["intents"], [])
        self.assertEqual(engine.snapshot(), before)

    def test_one_authoritative_fact_can_satisfy_multiple_slots_without_duplicate_fact_keys(self):
        bindings = self.bindings()
        for index in (0, 1):
            bindings[index]["source_id"] = "synthetic.shared.002-003"
            bindings[index]["idempotency_domain"] = "t12.synthetic.shared"
        engine = self.engine(bindings=bindings)
        result = engine.observe_authoritative_fact(
            "TSYN",
            "synthetic_fact_completed",
            "synthetic.shared.002-003",
            "shared-key",
        )
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(
            [intent["level_id"] for intent in result["intents"]],
            ["t12.level.002", "t12.level.003"],
        )
        snapshot = engine.snapshot()
        self.assertEqual(
            snapshot["consumed_fact_keys"],
            ["t12.synthetic.shared|shared-key"],
        )
        self.assertEqual(
            snapshot["fact_slot_source_keys"]["t12.fact.slot.002"],
            "t12.synthetic.shared|shared-key",
        )
        self.assertEqual(
            snapshot["fact_slot_source_keys"]["t12.fact.slot.003"],
            "t12.synthetic.shared|shared-key",
        )
        restored = self.engine(bindings=bindings, snapshot=snapshot)
        self.assertEqual(restored.initialization_intents, [])
        self.assertEqual(restored.snapshot(), snapshot)

    def test_milestone_emits_exactly_once(self):
        engine = self.engine()
        last = None
        for level in range(2, 11):
            last = self.observe(engine, level)
        self.assertIsNotNone(last)
        self.assertEqual(last["intents"][-1]["level_id"], "t12.level.010")
        self.assertEqual(last["intents"][-1]["milestone_ids"], ["t12.milestone.010"])
        snapshot = engine.snapshot()
        self.assertEqual(snapshot["emitted_milestone_ids"], ["t12.milestone.010"])
        replay = self.observe(engine, 10, "another-key")
        self.assertTrue(replay["replayed"])
        self.assertEqual(replay["intents"], [])
        self.assertEqual(engine.snapshot()["emitted_milestone_ids"], ["t12.milestone.010"])

    def test_restore_does_not_reemit_completed_levels(self):
        engine = self.engine()
        self.observe(engine, 2)
        self.observe(engine, 3)
        snapshot = engine.snapshot()
        restored = self.engine(snapshot=snapshot)
        self.assertEqual(restored.initialization_intents, [])
        self.assertEqual(restored.snapshot(), snapshot)

    def test_restore_settles_retained_out_of_order_slot_when_prerequisite_is_complete(self):
        engine = self.engine()
        self.observe(engine, 3, "stored-three")
        snapshot = engine.snapshot()

        # Simulate a valid interrupted transition after L2 completion was durably
        # recorded by constructing the exact consistent completion/event state.
        snapshot["completed_level_ids"].append("t12.level.002")
        snapshot["satisfied_fact_slot_ids"].append("t12.fact.slot.002")
        snapshot["fact_slot_source_keys"]["t12.fact.slot.002"] = "t12.synthetic.002|stored-two"
        snapshot["consumed_fact_keys"].append("t12.synthetic.002|stored-two")
        snapshot["emitted_completion_event_ids"].append("t12.event.level.002.completed")

        restored = self.engine(snapshot=snapshot)
        self.assertEqual(
            [intent["level_id"] for intent in restored.initialization_intents],
            ["t12.level.003"],
        )
        self.assertIn("t12.level.003", restored.snapshot()["completed_level_ids"])

    def test_deferred_binding_cannot_satisfy_slot(self):
        bindings = self.bindings()
        row = bindings[2]  # Level 4.
        row["resolution_state"] = "DEFERRED_LATER_OWNER"
        row["source_id"] = ""
        row["idempotency_domain"] = ""
        engine = self.engine(bindings=bindings)
        result = self.observe(engine, 4)
        self.assertFalse(result["passed"])
        self.assertFalse(result["mutated"])
        self.assertEqual(result["errors"], ["unresolved_or_unknown_fact"])

    def test_invalid_snapshot_missing_fact_slot_for_completed_level_fails(self):
        engine = self.engine()
        self.observe(engine, 2)
        snapshot = engine.snapshot()
        snapshot["satisfied_fact_slot_ids"].remove("t12.fact.slot.002")
        snapshot["fact_slot_source_keys"].pop("t12.fact.slot.002")
        with self.assertRaises(ValueError):
            self.engine(snapshot=snapshot)

    def test_snapshot_with_orphan_consumed_fact_key_fails(self):
        engine = self.engine()
        self.observe(engine, 2)
        snapshot = engine.snapshot()
        snapshot["consumed_fact_keys"].append("orphan.domain|key")
        with self.assertRaisesRegex(ValueError, "exactly justified"):
            self.engine(snapshot=snapshot)

    def test_snapshot_with_unjustified_completion_event_fails(self):
        engine = self.engine()
        snapshot = engine.snapshot()
        snapshot["emitted_completion_event_ids"].append("t12.event.level.002.completed")
        with self.assertRaisesRegex(ValueError, "completion event state is not exactly justified"):
            self.engine(snapshot=snapshot)

    def test_invalid_observation_does_not_mutate(self):
        engine = self.engine()
        before = engine.snapshot()
        result = engine.observe_authoritative_fact("TUNKNOWN", "bad", "bad", "bad")
        self.assertFalse(result["passed"])
        self.assertFalse(result["mutated"])
        self.assertEqual(engine.snapshot(), before)

if __name__ == "__main__":
    unittest.main()
