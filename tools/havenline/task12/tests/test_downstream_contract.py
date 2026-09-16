#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
VALIDATOR_PATH = ROOT / "tools/havenline/task12/validate_downstream_contract.py"
CONTRACT_PATH = ROOT / "Docs/Production/T12/DOWNSTREAM_CONSUMER_CONTRACT.json"

spec = importlib.util.spec_from_file_location("t12_downstream_validator", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validator)


class T12DownstreamContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT_PATH.read_text())

    def validate(self, mutator=None):
        candidate = copy.deepcopy(self.contract)
        if mutator:
            mutator(candidate)
        return validator.validate_contract(candidate)

    def test_prepared_downstream_contract_passes(self):
        result = self.validate()
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["consumer_count"], 13)

    def test_rejects_missing_t13_consumer(self):
        result = self.validate(lambda c: c["consumers"].pop("T13"))
        self.assertFalse(result["passed"])
        self.assertTrue(any("T13" in error for error in result["errors"]))

    def test_rejects_region_owner_band_drift(self):
        def mutate(contract):
            contract["consumers"]["T48"]["owned_band"] = "band_swamp"
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("T48" in error and "band_volcanic" in error for error in result["errors"]))

    def test_rejects_region_level_range_drift(self):
        def mutate(contract):
            contract["consumers"]["T50"]["owned_levels"] = [70,80]
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("T50" in error and "[71, 80]" in error for error in result["errors"]))

    def test_rejects_t13_purchase_boundary_removal(self):
        def mutate(contract):
            contract["consumers"]["T13"]["must_not_require_from_T12"] = ["difficulty score"]
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("T13" in error and "purchase" in error for error in result["errors"]))

    def test_rejects_t14_migration_boundary_removal(self):
        def mutate(contract):
            contract["consumers"]["T14"]["must_not_require_from_T12"] = ["global save version"]
            contract["consumers"]["T14"]["boundary"] = "T14 owns persistence."
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("T14" in error and "migration" in error for error in result["errors"]))

    def test_rejects_missing_progression_snapshot_output(self):
        def mutate(contract):
            contract["shared_outputs"].pop("progression_snapshot")
        result = self.validate(mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(any("progression_snapshot" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
