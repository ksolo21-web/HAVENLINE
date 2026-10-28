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


def synthetic_glb_for_materials(names):
    import struct
    doc={"asset":{"version":"2.0"},
         "materials":[{"name":name} for name in names],
         "meshes":[{"primitives":[{"attributes":{"POSITION":0},"material":i}
                                for i in range(len(names))]}]}
    payload=json.dumps(doc).encode()
    payload+=b" "*((-len(payload))%4)
    chunk=struct.pack("<I4s",len(payload),b"JSON")+payload
    return struct.pack("<4sII",b"glTF",2,12+len(chunk))+chunk


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
        original_materials = ["HL_snow", "HL_wood", "HL_metal"]
        self.glb = self.addfile("synthetic_mesh.glb", synthetic_glb_for_materials(original_materials))
        profile = self.policy["evidence_profiles"]["static_3d"]
        captures = []
        for i, view in enumerate(profile["views"]):
            p = self.addfile("godot_" + view + ".png", make_png(i * 24 + 10))
            captures.append({
                "view": view, **p, "engine": "Godot",
                "render_run_id": 8004, "candidate_commit": SRC,
                "shipping_scene_loaded": False})
        self.material_names = [str(i)+":"+name for i,name in enumerate(original_materials)]
        self.asset = {
            "asset_id": "test_tree",
            "profile": "static_3d",
            "asset_source": {**self.glb, "shipping_path": self.assetpath},
            "references": [{**self.source, "authority": "owner_original"}],
            "captures": captures,
            "materials": [{"material_id": m,
                           "reference_shas": [self.source["sha256"]],
                           "visible_in_views": list(profile["views"]),
                           "glTF_variant_names_reviewed": []}
                          for m in self.material_names],
            "reference_camera": {
                "reference_visible_geometry_calibrated": True,
                "justification": "Controlled synthetic camera perspective identical to generated comparison test geometry"},
            "known_visible_reference_mismatches": [],
            "unused_source_material_slots": [],
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
                        "inactive_source_material_slots_inspected": [],
                        "glTF_variant_names_inspected": {},
                        "views": self.policy["evidence_profiles"][self.asset["profile"]]["views"][:],
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

    def test_source_nine_materials_cannot_be_claimed_as_one_reviewed_surface(self):
        # The exact GLB primitive/material inventory must be used, not a
        # manifest reporting fewer surfaces than exist on the model.
        self.asset["materials"] = self.asset["materials"][:1]
        report=self.execute()
        self.assertFalse(report["passed"])
        self.assertTrue(any("omit, invent or merge actual GLB" in msg for msg in report["errors"]), report["errors"])

    def test_misnamed_source_glb_material_slot_is_blocked(self):
        self.asset["materials"][0]["material_id"] = "0:Imaginary"
        report=self.execute()
        self.assertFalse(report["passed"])
        self.assertTrue(any("actual GLB" in msg for msg in report["errors"]), report["errors"])

    def test_corrupted_glb_does_not_fallback_to_manifest_claims(self):
        p=self.root/"synthetic_mesh.glb"
        p.write_bytes(b"not-a-real-GLB")
        self.asset["asset_source"]["sha256"]=sha256(p)
        report=self.execute()
        self.assertFalse(report["passed"])
        self.assertTrue(any("actual authored GLB" in msg for msg in report["errors"]), report["errors"])

    def _activate_real_unused_slot_fixture(self):
        raw=synthetic_glb_for_materials(["HL_snow", "HL_wood", "HL_metal", "UNUSED_BAKED_PALETTE"])
        # Add a fourth source material which no primitive uses.
        import struct
        size=struct.unpack_from("<I",raw,12)[0]
        doc=json.loads(raw[20:20+size])
        doc["meshes"][0]["primitives"].pop()
        doc["meshes"][0]["primitives"].append({"attributes":{"POSITION":0},"material":2})
        payload=json.dumps(doc).encode()
        payload+=b" "*((-len(payload))%4)
        chunk=struct.pack("<I4s",len(payload),b"JSON")+payload
        glb=struct.pack("<4sII",b"glTF",2,len(chunk)+12)+chunk
        p=self.root/"synthetic_mesh.glb"
        p.write_bytes(glb)
        self.asset["asset_source"]["sha256"]=sha256(p)

    def test_source_unused_palette_cannot_be_silently_removed_from_inventory(self):
        self._activate_real_unused_slot_fixture()
        out=self.execute()
        self.assertFalse(out["passed"])
        self.assertTrue(any("inactive source material slot declaration" in x for x in out["errors"]),out["errors"])

    def test_unused_source_palette_needs_exact_both_critic_inactive_disposition(self):
        self._activate_real_unused_slot_fixture()
        self.asset["unused_source_material_slots"]=["3:UNUSED_BAKED_PALETTE"]
        self.asset["unused_material_disposition"]="REVIEWERS_CONFIRMED_NOT_RENDERED_IN_NATIVE_GODOT"
        for critic in self.manifest["reviews"]:
            p=self.root/critic["raw_output"]["path"]
            data=json.loads(p.read_text())
            data["assets"][0]["coverage"]["inactive_source_material_slots_inspected"]=["3:UNUSED_BAKED_PALETTE"]
            p.write_text(json.dumps(data))
            critic["raw_output"]["sha256"]=sha256(p)
        self.assertTrue(self.execute()["passed"])

    def test_one_critic_missing_inactive_material_proof_fails(self):
        self._activate_real_unused_slot_fixture()
        self.asset["unused_source_material_slots"]=["3:UNUSED_BAKED_PALETTE"]
        self.asset["unused_material_disposition"]="REVIEWERS_CONFIRMED_NOT_RENDERED_IN_NATIVE_GODOT"
        # C1 names the palette, C2 does not; reject rather than average.
        critic=self.manifest["reviews"][0]
        p=self.root/critic["raw_output"]["path"]
        data=json.loads(p.read_text())
        data["assets"][0]["coverage"]["inactive_source_material_slots_inspected"]=["3:UNUSED_BAKED_PALETTE"]
        p.write_text(json.dumps(data))
        critic["raw_output"]["sha256"]=sha256(p)
        result=self.execute()
        self.assertFalse(result["passed"])
        self.assertTrue(any("inactive GLB slots" in x for x in result["errors"]),result["errors"])

    def _configure_godot_runtime_vfx_obj(self):
        root=self.root
        obj="HavenlineGodot/assets/transfer_feedback_v2/transfer_arrow_sigil.obj"
        shader="HavenlineGodot/assets/transfer_feedback_v2/transfer_feedback_v2.gdshader"
        script="HavenlineGodot/scripts/transfer_feedback.gd"
        for path in (obj,shader,script):
            (root/path).parent.mkdir(parents=True,exist_ok=True)
        raw=b"v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n"
        geometry=self.addfile(obj,raw)
        code='''
const FEEDBACK_MESHES := {"arrow": "res://assets/transfer_feedback_v2/transfer_arrow_sigil.obj"}
const FEEDBACK_SHADER := "res://assets/transfer_feedback_v2/transfer_feedback_v2.gdshader"
func _make_feedback_instances(kind,color,capacity,role):
 var material := ShaderMaterial.new()
 material.shader = load(FEEDBACK_SHADER)
 var instances := MultiMesh.new()
 instances.mesh = mesh
 result.multimesh = instances
 result.material_override = material
func _make_arrows(color):
 return _make_feedback_instances("arrow", color, 42, 1.0)
func _ensure_trails():
 gather = _make_arrows(Color("5deaff"))
 destination = _make_arrows(Color("ffb548"))
'''
        script_entry=self.addfile(script,code.encode())
        shader_entry=self.addfile(shader,b"shader_type spatial;\nvoid fragment() { ALBEDO=vec3(1.0); }\n")
        self.asset["asset_source"]={**geometry,"shipping_path":obj}
        self.asset["profile"]="dynamic_vfx"
        self.asset["runtime_material_binding"]={
            "script":script_entry,"shader":shader_entry,
            "material_ids":["runtime:source_to_actor","runtime:actor_to_destination"]}
        views=self.policy["evidence_profiles"]["dynamic_vfx"]["views"]
        self.asset["captures"]=[]
        for i,view in enumerate(views):
            img=self.addfile("godot_dynamic_"+view+".png",make_png(i*25+88))
            self.asset["captures"].append({
                "view":view,**img,"engine":"Godot","render_run_id":8004,
                "candidate_commit":SRC,"shipping_scene_loaded":False})
        self.asset["motion"]={**self.addfile("godot_motion.bin",b"test-only native motion frames fixture bytes"),
                              "from_native_Godot":True}
        self.material_names=self.asset["runtime_material_binding"]["material_ids"][:]
        self.asset["materials"]=[
            {"material_id":ident,"reference_shas":[self.source["sha256"]],
             "visible_in_views":views[:],"glTF_variant_names_reviewed":[]}
            for ident in self.material_names]
        self.manifest["changed_visual_paths"]=[obj]
        self.make_reviews()
        return obj,script,shader

    def test_runtime_vfx_obj_real_script_shader_binding_proves_two_unapproved_materials(self):
        self._configure_godot_runtime_vfx_obj()
        out=self.execute("evidence")
        self.assertTrue(out["passed"],out["errors"])
        self.assertEqual(2,out["material_count"])
        self.assertFalse(out["real_visual_review_completed"])

    def test_runtime_obj_without_source_shader_cannot_pass(self):
        self._configure_godot_runtime_vfx_obj()
        (self.root/"HavenlineGodot/assets/transfer_feedback_v2/transfer_feedback_v2.gdshader").unlink()
        out=self.execute("evidence")
        self.assertFalse(out["passed"])
        self.assertTrue(any("runtime Godot shader" in x for x in out["errors"]),out["errors"])

    def test_runtime_obj_missing_second_direction_variant_fails(self):
        self._configure_godot_runtime_vfx_obj()
        self.asset["materials"].pop()
        out=self.execute("evidence")
        self.assertFalse(out["passed"])
        self.assertTrue(any("omit, invent or merge actual GLB/OBJ" in x for x in out["errors"]),out["errors"])

    def test_runtime_obj_cannot_masquerade_as_static_prop_without_motion(self):
        self._configure_godot_runtime_vfx_obj()
        self.asset["profile"]="static_3d"
        self.asset["motion"]={}
        out=self.execute("evidence")
        self.assertFalse(out["passed"])
        self.assertTrue(any("dynamic_vfx profile" in x for x in out["errors"]),out["errors"])

    def test_runtime_obj_source_code_shader_material_not_just_text_mentioned(self):
        self._configure_godot_runtime_vfx_obj()
        path=self.root/"HavenlineGodot/scripts/transfer_feedback.gd"
        path.write_text(path.read_text().replace("result.material_override = material","pass"))
        self.asset["runtime_material_binding"]["script"]["sha256"]=sha256(path)
        out=self.execute("evidence")
        self.assertFalse(out["passed"])
        self.assertTrue(any("source runtime shader override chain is unproven" in x for x in out["errors"]),out["errors"])

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
