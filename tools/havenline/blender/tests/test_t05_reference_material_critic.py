#!/usr/bin/env python3
"""Synthetic private-input critic regression checks; no owner artwork in CI."""
from __future__ import annotations

import copy
import hashlib
import io
import json
import pathlib
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import t05_reference_material_critic as c
from PIL import Image


def png(seed):
    im = Image.new("RGB", (32, 32))
    im.putdata([((x * 5 + seed) % 256, (y * 7 + seed) % 256,
                 (x * 13 + y * 17 + seed) % 256)
                for y in range(32) for x in range(32)])
    b = io.BytesIO()
    im.save(b, format="PNG")
    return b.getvalue()


def make_glb(names):
    src = png(27)
    doc = {
        "materials": [
            {"name": n, "pbrMetallicRoughness": {
                "baseColorTexture": {"index": i},
                "metallicFactor": 0.2, "roughnessFactor": 0.65}}
            for i, n in enumerate(names)
        ],
        "textures": [{"source": 0} for _ in names],
        "images": [{"bufferView": 0, "mimeType": "image/png"}],
        "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(src)}],
        "meshes": [{"primitives": [
            {"attributes": {"POSITION": 0, "TEXCOORD_0": 1}, "material": i}
            for i in range(len(names))]}]
    }
    js = json.dumps(doc).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    binary = src + b"\x00" * ((4 - len(src) % 4) % 4)
    chunks = struct.pack("<I4s", len(js), b"JSON") + js
    chunks += struct.pack("<I4s", len(binary), b"BIN\x00") + binary
    return struct.pack("<4sII", b"glTF", 2, 12 + len(chunks)) + chunks


class CookerCriticTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.policy = copy.deepcopy(c.load_policy())
        self.names = self.policy["required_material_names"]
        self.policy["reference"]["pixels"] = [32, 32]
        self.policy["required_godot_pixels"] = [32, 32]
        self.policy["reference"]["sha256"] = c.digest(png(10))
        self.source = png(10)
        self.glb = make_glb(self.names)
        self.glb_hash = c.digest(self.glb)
        self.root.joinpath("reference.png").write_bytes(self.source)
        self.root.joinpath("candidate.glb").write_bytes(self.glb)
        self.root.joinpath("review-board.png").write_bytes(png(40))
        hashes = {}
        for i, name in enumerate(self.policy["required_godot_views"]):
            raw = png(60 + i * 20)
            (self.root / ("godot-" + name + ".png")).write_bytes(raw)
            hashes[name] = c.digest(raw)
        native = {
            "candidate_glb_sha256": self.glb_hash,
            "source_reference_sha256": c.digest(self.source),
            "frames": [{"view": k, "sha256": v} for k, v in hashes.items()]
        }
        engine = {"godot_mesh_count": 9, "shipping_main_loaded": False,
                  "status": "ISOLATED_GODOT_IMPORT_ONLY_NOT_SHIPPING_QA"}
        native_path = self.root / "native-4k-byte-audit.json"
        engine_path = self.root / "isolated-godot-report.json"
        native_path.write_text(json.dumps(native))
        engine_path.write_text(json.dumps(engine))
        manifest = {
            "critic_id": self.policy["critic_id"],
            "owner_source_sha256": c.digest(self.source),
            "candidate_glb_sha256": self.glb_hash,
            "godot_resolution": [32, 32],
            "source_godot_run_id": "10002",
            "source_builder_commit": "b" * 40,
            "image_shas": hashes,
            "private_reference_sha256": c.digest(self.source),
            "review_board_sha256": c.filehash(self.root / "review-board.png"),
            "raw_godot_shas_verified_without_recompression": True,
            "native_audit_sha256": c.filehash(native_path),
            "engine_audit_sha256": c.filehash(engine_path),
            "material_inventory": c.glb_inventory(self.glb, self.names)
        }
        evidence_path = self.root / "evidence-manifest.json"
        evidence_path.write_text(json.dumps(manifest))
        self.review = {
            "critic_id": self.policy["critic_id"],
            "evidence_manifest_sha256": c.filehash(evidence_path),
            "candidate_glb_sha256": self.glb_hash,
            "reference_sha256": c.digest(self.source),
            "reviewer": {
                "id": "synthetic-independent-test-reviewer",
                "provider": "synthetic-fixture-not-real-critic",
                "model": "test-only",
                "separate_independent_run_id": "30004",
                "builder_independent": True,
                "raw_output_file": "synthetic-reviewer-raw.json"
            },
            "source_camera_alignment": {
                "verified": True,
                "evidence": "Synthetic controlled identical camera registration test"
            },
            "coverage": {
                "full_resolution_inspected": True,
                "five_godot_views_inspected": self.policy["required_godot_views"],
                "reference_regions_inspected": self.policy["required_reference_regions"],
                "material_names_inspected": self.names
            },
            "scores": {k: 10 if v == 10 else 9.8
                       for k, v in self.policy["scores_required"].items()},
            "defects": [],
            "observations": ["synthetic review observation " + str(x) for x in range(5)],
            "confidence": "high"
        }

    def verdict(self, change=None, mutate_raw=False):
        review = copy.deepcopy(self.review)
        if change:
            change(review)
        raw = {k: review[k] for k in ("scores", "defects", "observations", "confidence")}
        if mutate_raw:
            raw["scores"]["reference_fidelity"] = 8
        raw_file = self.root / "synthetic-reviewer-raw.json"
        raw_file.write_text(json.dumps(raw))
        review["reviewer"]["raw_output_sha256"] = c.filehash(raw_file)
        review_path = self.root / "review.json"
        review_path.write_text(json.dumps(review))
        args = type("Args", (), {"package": str(self.root), "review": str(review_path),
                                 "result": None})()
        with patch.object(c, "load_policy", return_value=self.policy):
            return c.validate(args)

    def test_synthetic_valid_complete_critic_record_can_pass(self):
        self.assertTrue(self.verdict()["passed"])

    def test_exact_10_reference_not_9_9(self):
        def f(r):
            r["scores"]["reference_fidelity"] = 9.9
        self.assertFalse(self.verdict(f)["passed"])

    def test_material_snow_9_49_rejected(self):
        def f(r):
            r["scores"]["snow_sculpture_and_contact"] = 9.49
        self.assertFalse(self.verdict(f)["passed"])

    def test_self_reviewer_rejected(self):
        def f(r):
            r["reviewer"]["builder_independent"] = False
        self.assertFalse(self.verdict(f)["passed"])

    def test_builder_job_cannot_masquerade_as_independent(self):
        def f(r):
            r["reviewer"]["separate_independent_run_id"] = "10002"
        self.assertFalse(self.verdict(f)["passed"])

    def test_missing_view_rejected(self):
        def f(r):
            r["coverage"]["five_godot_views_inspected"].pop()
        self.assertFalse(self.verdict(f)["passed"])

    def test_missing_reference_region_rejected(self):
        def f(r):
            r["coverage"]["reference_regions_inspected"].pop()
        self.assertFalse(self.verdict(f)["passed"])

    def test_missing_material_rejected(self):
        def f(r):
            r["coverage"]["material_names_inspected"].pop()
        self.assertFalse(self.verdict(f)["passed"])

    def test_missing_source_camera_registration_rejected(self):
        def f(r):
            r["source_camera_alignment"]["verified"] = False
        self.assertFalse(self.verdict(f)["passed"])

    def test_unresolved_defect_rejected(self):
        def f(r):
            r["defects"] = ["A visible gap at the blue stove roof"]
        self.assertFalse(self.verdict(f)["passed"])

    def test_high_mean_cannot_override_low_dimension(self):
        def f(r):
            r["scores"]["woodwork_and_steel_fittings"] = 8.0
        self.assertFalse(self.verdict(f)["passed"])

    def test_raw_critic_output_score_conflict_rejected(self):
        self.assertFalse(self.verdict(mutate_raw=True)["passed"])

    def test_real_reference_hash_required_not_just_manifest_claim(self):
        self.assertTrue(self.verdict()["passed"])
        (self.root / "reference.png").write_bytes(png(11))
        self.assertFalse(self.verdict()["passed"])

    def test_changed_native_frame_rejected(self):
        self.assertTrue(self.verdict()["passed"])
        (self.root / "godot-front.png").write_bytes(png(75))
        self.assertFalse(self.verdict()["passed"])

    def test_unbound_glb_texture_rejected(self):
        data = json.loads(self.root.joinpath("evidence-manifest.json").read_text())
        bad = make_glb(self.names[:-1])
        with self.assertRaises(ValueError):
            c.glb_inventory(bad, self.names)
        self.assertEqual(data["material_inventory"]["material_count"], 9)


if __name__ == "__main__":
    unittest.main()
