#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
BINDINGS_PATH = ROOT / "Docs" / "Production" / "T11" / "T05_REUSE_BINDINGS.json"
CATALOG_PATH = ROOT / "HavenlineGodot" / "assets" / "stations_v2" / "catalog.json"


def load(path: pathlib.Path):
    return json.loads(path.read_text())


class T11T05BindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bindings = load(BINDINGS_PATH)
        cls.catalog = load(CATALOG_PATH)
        cls.entries = {row["id"]: row for row in cls.catalog["entries"]}

    def assert_binding_matches_catalog(self, binding: dict):
        asset_id = binding["id"]
        self.assertIn(asset_id, self.entries, asset_id)
        source = self.entries[asset_id]
        self.assertEqual(binding["asset"], source["asset"], asset_id)
        self.assertEqual(binding["sha256"], source["sha256"], asset_id)
        if "footprint" in binding:
            self.assertEqual(binding["footprint"], source["footprint"], asset_id)
        if "clearance" in binding:
            self.assertEqual(binding["clearance"], source["clearance"], asset_id)
        if "triangles" in binding:
            self.assertEqual(binding["triangles"], source["triangles"], asset_id)
        if "sockets" in binding:
            self.assertEqual(binding["sockets"], source["sockets"], asset_id)
        if "visual_variant" in binding:
            self.assertEqual(binding["visual_variant"], source["visual_variant"], asset_id)

    def test_catalog_authority_is_exact(self):
        authority = self.bindings["t05_authority"]
        self.assertEqual(self.catalog["authority_id"], authority["authority_id"])
        self.assertFalse(authority["mutation_allowed_from_t11"])
        self.assertEqual(authority["accepted_t05_source"], "fa6fa70f154f3757d22303522ca3f6de2c3d391f")

    def test_direct_t11_bindings_match_catalog_and_are_owned_for_t11(self):
        direct = self.bindings["direct_t11_bindings"]
        self.assertEqual({x["id"] for x in direct}, {"hearth_vessel", "pad_build", "pad_upgrade"})
        for binding in direct:
            self.assert_binding_matches_catalog(binding)
            self.assertEqual(self.entries[binding["id"]]["later_task"], "T11", binding["id"])
            self.assertEqual(binding["t05_later_task"], "T11", binding["id"])

    def test_passive_bindings_match_catalog_but_do_not_grant_behavior(self):
        passive = self.bindings["passive_composition_bindings"]
        self.assertEqual({x["id"] for x in passive}, {"service_counter", "processing_counter", "pad_stock"})
        for binding in passive:
            self.assert_binding_matches_catalog(binding)
            self.assertFalse(binding["t11_behavior_allowed"], binding["id"])
            self.assertNotEqual(binding["behavior_owner"], "T11", binding["id"])
            self.assertEqual(binding["t05_later_task"], self.entries[binding["id"]]["later_task"], binding["id"])

    def test_resource_visual_bindings_match_catalog_and_preserve_t08_authority(self):
        resources = self.bindings["resource_visuals_external_to_t11_state"]
        self.assertEqual({x["id"] for x in resources}, {"wood_stack", "stone_stack", "metal_stack"})
        for binding in resources:
            self.assert_binding_matches_catalog(binding)
            self.assertEqual(binding["state_owner"], "T08", binding["id"])
            self.assertIn("must not spawn a fake quantity", binding["rule"])

    def test_t11_does_not_claim_later_behavior_families(self):
        excluded = "\n".join(self.bindings["explicitly_excluded_from_t11_behavior"])
        for token in ("T17", "T16", "T22", "T08", "T10"):
            self.assertIn(token, excluded)


if __name__ == "__main__":
    unittest.main()
