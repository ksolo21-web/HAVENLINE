#!/usr/bin/env python3
"""Synthetic positive/negative fixtures for permanent per-material native-review gate.

Fake pixel patterns and fictitious scores exist ONLY within these tests; no
fixture is a Havenline art critic's real score, pass or owner approval.
"""
from __future__ import annotations

import copy
import hashlib
import io
import json
import pathlib
import sys
import tempfile
import unittest

from PIL import Image

PROD = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROD))
from global_rendered_material_critic import validate, sha256, load_policy

SRC = "b" * 40
TASK = "T42"


def make_png(seed, w=32, h=32):
    im = Image.new("RGB", (w, h))
    im.putdata([((x * 5 + seed) % 256, (y * 9 + seed) % 256,
                 (x * 13 + y * 17 + seed) % 256)
                for y in range(h) for x in range(w)])
    f = io.BytesIO()
    im.save(f, format="PNG")
    return f.getvalue()


class PermanentMaterialCriticTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.policy = copy.deepcopy(load_policy())
        self.policy["evidence_profiles"]["static_3d"]["minimum_resolution"] = [32, 32]
        self.policy["evidence_profiles"]["ui_and_2d"]["minimum_resolution"] = [32, 32]
        self.policy["evidence_profiles"]["dynamic_vfx"]["minimum_resolution"] = [32, 32]
        self.policy["evidence_profiles"]["scene_or_terrain"]["minimum_resolution"] = [32, 32]
        self.assetpath = "HavenlineGodot/assets/test/synthetic_tree.glb"
        (self.root / "original_name_is_png_but_jpeg.jpg").write_bytes(b"synthetic unused")
        reference_image = Image.open(io.BytesIO(make_png(44)))
        jpeg = io.BytesIO()
        reference_image.save(jpeg, format="JPEG", quality=92)
        self.source = self.addfile("18567.png", jpeg.getvalue())
        self.glb = self.addfile("synthetic_mesh.glb", b"not an actual glTF file; fixture checks source hash binding only")
        profile = self.policy["evidence_profiles"]["static_3d"]
        captures = []
        for i, view in enumerate(profile["views"]):
            p = self.addfile("godot_" + view + ".png", make_png(i * 24 + 10))
            captures.append({
                "view": view, **p, "engine": "Godot",
                "render_run_id": 8004, "candidate_commit": SRC,
                "shipping_scene_loaded": False})
        self.material_names = ["HL_snow", "HL_wood", "HL_metal"]
        self.asset = {
            "asset_id": "test_tree",
            "profile": "static_3d",
            "asset_source": {**self.glb, "shipping_path": self.assetpath},
            "references": [{**self.source, "authority": "owner_original"}],
            "captures": captures,
            "materials": [{"material_id": m,
                           "reference_shas": [self.source["sha256"]],
                           "visible_in_views": list(profile["views"])}
                          for m in self.material_names],
            "reference_camera": {
                "reference_visible_geometry_calibrated": True,
                "justification": "Controlled synthetic camera perspective identical to generated comparison test geometry"},
            "known_visible_reference_mismatches": [],
            "owner_visual_rejection_active": False
        }
        self.manifest = {
            "schema_version": 1, "task_id": TASK, "candidate_commit": SRC,
            "builder_run_id": 8003, "changed_visual_paths": [self.assetpath],
            "assets": [self.asset],
            "reviews": []
        }
        self.make_reviews()

    def addfile(self, name, data):
        path = self.root / name
        path.write_bytes(data)
        return {"path": name, "sha256": sha256(path)}

    def make_reviews(self):
        self.manifest["reviews"] = []
        for index, critic in enumerate(("C1", "C2")):
            payload = {
                "critic_id": critic, "candidate_commit": SRC, "task_id": TASK,
                "assets": [{
                    "asset_id": "test_tree",
                    "scores": {k: (10 if v == 10 else 9.8)
                               for k, v in self.policy["threshold"].items()
                               if k in ("reference_fidelity", "visual_language")}
                    | {k: 9.8 for k in self.policy["required_dimensions"]
                       if k not in ("reference_fidelity", "visual_language")},
                    "defects": [],
                    "confidence": "high",
                    "observations": [
                        "Synthetic visual observation, not a genuine art review: " + str(n)
                        for n in range(3)],
                    "coverage": {
                        "material_ids": self.material_names[:],
                        "views": self.policy["evidence_profiles"]["static_3d"]["views"][:],
                        "reference_shas": [self.source["sha256"]]
                    }
                }]
            }
            raw = self.addfile("synthetic_" + critic + "_raw.json",
                               (json.dumps(payload) + "\n").encode())
            self.manifest["reviews"].append({
                "critic_id": critic,
                "independent_of_builder": True,
                "independent_run_id": 8100 + index,
                "provider": "synthetic-fixture-only",
                "model": "synthetic-not-a-vision-review",
                "reviewer_id": "test-only-" + critic,
                "raw_output": raw
            })

    def execute(self, mode="review", expected=None):
        return validate(self.manifest, self.root, mode=mode,
                        expected_paths=expected, policy=self.policy)

    def test_synthetic_contract_validates_with_complete_fixture(self):
        out = self.execute()
        self.assertTrue(out["passed"], out["errors"])
        self.assertFalse(out["user_approved"])
        self.assertEqual(["C1", "C2"], out["critic_ids_verified"])

    def test_original_source_is_byte_verified_not_extension_based(self):
        self.assertTrue(self.execute()["passed"])
        path = self.root / "18567.png"
        self.assertEqual(b"\xff\xd8", path.read_bytes()[:2])
        path.write_bytes(make_png(44))
        self.assertFalse(self.execute()["passed"])

    def test_score_9_49_on_metal_response_rejected(self):
        p = self.root / self.manifest["reviews"][0]["raw_output"]["path"]
        payload = json.loads(p.read_text())
        payload["assets"][0]["scores"]["roughness_metallic_and_normal_response"] = 9.49
        p.write_text(json.dumps(payload))
        self.manifest["reviews"][0]["raw_output"]["sha256"] = sha256(p)
        self.assertFalse(self.execute()["passed"])

    def test_reference_fidelity_9_9_rejected(self):
        p = self.root / self.manifest["reviews"][0]["raw_output"]["path"]
        payload = json.loads(p.read_text())
        payload["assets"][0]["scores"]["reference_fidelity"] = 9.9
        p.write_text(json.dumps(payload))
        self.manifest["reviews"][0]["raw_output"]["sha256"] = sha256(p)
        self.assertFalse(self.execute()["passed"])

    def test_no_score_averaging_allowed(self):
        p = self.root / self.manifest["reviews"][1]["raw_output"]["path"]
        payload = json.loads(p.read_text())
        payload["assets"][0]["scores"]["surface_color_and_pattern"] = 8.0
        p.write_text(json.dumps(payload))
        self.manifest["reviews"][1]["raw_output"]["sha256"] = sha256(p)
        self.assertFalse(self.execute()["passed"])

    def test_builder_self_review_rejected(self):
        self.manifest["reviews"][0]["independent_of_builder"] = False
        self.assertFalse(self.execute()["passed"])

    def test_same_review_job_or_builder_run_rejected(self):
        self.manifest["reviews"][1]["independent_run_id"] = 8100
        self.assertFalse(self.execute()["passed"])
        self.manifest["reviews"][1]["independent_run_id"] = 8003
        self.assertFalse(self.execute()["passed"])

    def test_no_second_reviewer_rejected(self):
        self.manifest["reviews"] = self.manifest["reviews"][:1]
        self.assertFalse(self.execute()["passed"])

    def test_missing_material_slot_rejected(self):
        self.manifest["assets"][0]["materials"][2]["visible_in_views"] = []
        self.assertFalse(self.execute()["passed"])

    def test_unreviewed_material_slot_rejected(self):
        p = self.root / self.manifest["reviews"][0]["raw_output"]["path"]
        payload = json.loads(p.read_text())
        payload["assets"][0]["coverage"]["material_ids"].pop()
        p.write_text(json.dumps(payload))
        self.manifest["reviews"][0]["raw_output"]["sha256"] = sha256(p)
        self.assertFalse(self.execute()["passed"])

    def test_changed_godot_pixel_bytes_rejected(self):
        (self.root / "godot_front.png").write_bytes(make_png(201))
        self.assertFalse(self.execute()["passed"])

    def test_godot_source_commit_mismatch_rejected(self):
        self.asset["captures"][0]["candidate_commit"] = "f" * 40
        self.assertFalse(self.execute()["passed"])

    def test_duplicate_or_missing_real_camera_view_rejected(self):
        self.asset["captures"].pop()
        self.assertFalse(self.execute()["passed"])

    def test_reference_camera_unmatched_is_blocked(self):
        self.asset["reference_camera"]["reference_visible_geometry_calibrated"] = False
        self.assertFalse(self.execute()["passed"])

    def test_visible_owner_rejection_blocks(self):
        self.asset["known_visible_reference_mismatches"] = ["Reference snow does not match"]
        self.assertFalse(self.execute()["passed"])

    def test_explicit_owner_rejection_blocks_even_perfect_critic_scores(self):
        self.asset["owner_visual_rejection_active"] = True
        out = self.execute()
        self.assertFalse(out["passed"])
        self.assertTrue(any("owner-rejected" in x for x in out["errors"]))

    def test_unresolved_critic_defect_blocks(self):
        p = self.root / self.manifest["reviews"][1]["raw_output"]["path"]
        payload = json.loads(p.read_text())
        payload["assets"][0]["defects"] = ["Material looks fake"]
        p.write_text(json.dumps(payload))
        self.manifest["reviews"][1]["raw_output"]["sha256"] = sha256(p)
        self.assertFalse(self.execute()["passed"])

    def test_path_traversal_or_symlink_rejected(self):
        self.asset["references"][0]["path"] = "../18567.png"
        self.assertFalse(self.execute()["passed"])

    def test_changed_visual_path_inventory_must_exactly_match(self):
        self.assertFalse(self.execute(expected=[self.assetpath, "HavenlineGodot/shaders/snow.gdshader"])["passed"])
        self.manifest["changed_visual_paths"] = []
        self.assertFalse(self.execute()["passed"])

    def test_candidate_evidence_mode_cannot_claim_independent_critic_pass(self):
        self.manifest["reviews"] = []
        result = self.execute("evidence")
        self.assertTrue(result["passed"], result["errors"])
        self.assertFalse(result["real_visual_review_completed"])
        self.assertEqual([], result["critic_ids_verified"])

    def test_release_rejects_isolated_godot_scenes(self):
        self.assertFalse(self.execute("release")["passed"])

    def test_full_release_census_and_real_scene_flag_still_separate_from_owner_signoff(self):
        self.manifest["full_shipped_material_census"] = True
        self.manifest["shipping_scenes_inspected"] = ["HavenlineGodot/scenes/main.tscn"]
        for shot in self.asset["captures"]:
            shot["shipping_scene_loaded"] = True
        result = self.execute("release")
        self.assertTrue(result["passed"], result["errors"])
        self.assertFalse(result["user_approved"])
        self.assertFalse(result["physical_android_verified"])

    def test_unapproved_dynamic_vfx_without_motion_rejected(self):
        vfx = copy.deepcopy(self.asset)
        vfx["profile"] = "dynamic_vfx"
        vfx["captures"] = [c for c in self.asset["captures"] if c["view"] in
                           self.policy["evidence_profiles"]["dynamic_vfx"]["views"]]
        self.manifest["assets"] = [vfx]
        self.assertFalse(self.execute("evidence")["passed"])

    def test_unverifiable_reference_path_rejected(self):
        self.asset["references"][0]["authority"] = "unsourced_ai_visual"
        self.assertFalse(self.execute()["passed"])

    def test_fixture_cannot_fool_source_scope_with_fake_paths(self):
        self.asset["asset_source"]["shipping_path"] = "Docs/Production/policy.json"
        self.assertFalse(self.execute()["passed"])

    def test_invalid_material_score_boolean_rejected(self):
        p = self.root / self.manifest["reviews"][0]["raw_output"]["path"]
        payload = json.loads(p.read_text())
        payload["assets"][0]["scores"]["texture_and_shader_fidelity"] = True
        p.write_text(json.dumps(payload))
        self.manifest["reviews"][0]["raw_output"]["sha256"] = sha256(p)
        self.assertFalse(self.execute()["passed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
