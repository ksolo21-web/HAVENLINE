from __future__ import annotations

import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve()
PRODUCTION = HERE.parents[1]
sys.path.insert(0, str(PRODUCTION))

from proof_invalidation import diff_contract_sets


PERSISTENCE = {
    "owner": "T14",
    "version": 1,
    "compatibility": "migration_required",
    "consumers": [],
    "consumer_ranges": [["T15", "T70"]],
    "watch_paths": [],
    "description": "fixture",
}


class ProofInvalidationDiffTests(unittest.TestCase):
    def test_no_contract_change_does_not_invalidate(self):
        r = diff_contract_sets({"persistence_schema": PERSISTENCE}, {"persistence_schema": dict(PERSISTENCE)})
        self.assertTrue(r["passed"])
        self.assertFalse(r["contract_change_detected"])
        self.assertFalse(r["proof_reuse_blocked"])
        self.assertEqual(r["invalidated_tasks"], [])

    def test_changed_persistence_contract_invalidates_transitively(self):
        changed = dict(PERSISTENCE); changed["version"] = 2
        r = diff_contract_sets({"persistence_schema": PERSISTENCE}, {"persistence_schema": changed})
        self.assertTrue(r["contract_change_detected"])
        self.assertTrue(r["proof_reuse_blocked"])
        self.assertFalse(r["automatic_approval_revocation"])
        self.assertTrue(r["integration_owner_disposition_required"])
        self.assertIn("T14", r["invalidated_tasks"])
        self.assertIn("T15", r["invalidated_tasks"])
        self.assertIn("T70", r["invalidated_tasks"])
        self.assertIn("save_matrix", r["invalidated_gates"])

    def test_removed_contract_uses_base_consumers_for_invalidation(self):
        r = diff_contract_sets({"persistence_schema": PERSISTENCE}, {})
        self.assertEqual(r["changed_contracts"], ["persistence_schema"])
        self.assertIn("T70", r["invalidated_tasks"])
        self.assertTrue(r["proof_reuse_blocked"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
