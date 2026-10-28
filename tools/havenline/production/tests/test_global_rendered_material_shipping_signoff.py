#!/usr/bin/env python3
"""Synthetic receipt checks; these are NOT real review scores or shipping passes."""
import copy
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

PROD=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROD))
import shipping_visual_gate as g

COMMIT="a"*40
SHA="b"*64
REF="c"*64


class MaterialShippingReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=pathlib.Path(self.tmp.name)
        self.path=f"Docs/Production/MaterialCriticApprovals/T42/{COMMIT}.json"
        self.receipt={
            "mode":"release","status":"SOURCE_BOUND_MATERIAL_CRITIC_PASS_NOT_USER_APPROVAL",
            "passed":True,"task_id":"T42","candidate_commit":COMMIT,"asset_ids":["test_tree"],
            "source_paths_covered":["HavenlineGodot/assets/test/test_tree.glb"],
            "material_count":1,"critic_ids_verified":["C1","C2"],
            "real_visual_review_completed":True,"reference_fidelity_10_required":True,
            "other_dimensions_minimum_9_5":True,"errors":[],"user_approved":False,
            "shipping_scene_material_proof_verified":True,
            "full_shipped_material_census_verified":False,
            "policy_path":"Docs/Production/REFERENCE_STYLE_LOCK.json",
            "private_manifest_raw_sha256":SHA,
            "private_manifest_canonical_sha256":REF,
            "source_asset_hashes":{"test_tree":SHA},
            "reference_image_hashes":{"test_tree":[REF]},
            "native_godot_capture_hashes":{"test_tree":{"front":SHA,"in_game_use":REF}},
            "reviewed_material_ids":{"test_tree":["HL_wood"]},
            "profiles_by_asset":{"test_tree":"static_3d"},
            "verified_review_sources":[
                {"critic_id":"C1","independent_run_id":1010,"raw_sha256":SHA},
                {"critic_id":"C2","independent_run_id":1011,"raw_sha256":REF}]
        }

    def verify(self,change=None,block_change=None,task="T42"):
        report=copy.deepcopy(self.receipt)
        report["task_id"]=task
        if change:
            change(report)
        rel=f"Docs/Production/MaterialCriticApprovals/{task}/{COMMIT}.json"
        path=self.root/rel
        path.parent.mkdir(parents=True,exist_ok=True)
        data=(json.dumps(report,indent=2)+"\n").encode()
        path.write_bytes(data)
        block={"report_path":rel,"report_sha256":hashlib.sha256(data).hexdigest()}
        if block_change:
            block_change(block)
        with patch.object(g,"ROOT",self.root):
            return g.validate_material_critic_receipt(task,COMMIT,block)

    def test_synthetic_complete_provenance_receipt_shape_passes(self):
        self.assertEqual([],self.verify())

    def test_missing_receipt_blocks(self):
        self.assertIn("missing", " ".join(g.validate_material_critic_receipt("T42",COMMIT,None)))

    def test_report_hash_drift_blocks(self):
        errors=self.verify(block_change=lambda b:b.update(report_sha256=SHA))
        self.assertTrue(any("SHA mismatch" in e for e in errors),errors)

    def test_isolated_godot_not_accepted_for_shipping(self):
        errors=self.verify(change=lambda r:r.update(mode="review"))
        self.assertTrue(any("shipping-scene" in e for e in errors),errors)

    def test_missing_c2_blocks(self):
        errors=self.verify(change=lambda r:r.update(critic_ids_verified=["C1"]))
        self.assertTrue(any("C1 and C2" in e for e in errors),errors)

    def test_duplicated_critic_review_job_blocks(self):
        def mutate(r):r["verified_review_sources"][1]["independent_run_id"]=1010
        errors=self.verify(change=mutate)
        self.assertTrue(any("independent" in e for e in errors),errors)

    def test_fake_owner_approval_cannot_be_put_in_critic_receipt(self):
        errors=self.verify(change=lambda r:r.update(user_approved=True))
        self.assertTrue(any("owner" in e for e in errors),errors)

    def test_missing_material_inventory_blocks(self):
        errors=self.verify(change=lambda r:r.update(reviewed_material_ids={"test_tree":[]}))
        self.assertTrue(any("material" in e for e in errors),errors)

    def test_incomplete_asset_source_path_census_blocks(self):
        errors=self.verify(change=lambda r:r.update(source_paths_covered=[]))
        self.assertTrue(any("source paths" in e for e in errors),errors)

    def test_t70_full_game_census_is_mandatory(self):
        errors=self.verify(task="T70")
        self.assertTrue(any("T70 full" in e for e in errors),errors)

    def test_signoff_requires_material_critic_even_with_user_yes(self):
        record={
            "schema_version":1,"task_id":"T42","candidate_sha":COMMIT,
            "primitive_audit":{"passed":True,"findings_count":0},
            "visual_evidence":{"source_bound":True,"workflow_run_id":2000,
                "artifact_id":3000,"stills_count":7,"motion_video_seconds":5,
                "internal_resolution":[3840,2160],"capture_fps":60},
            "reference_fidelity":{"whole_frame_reviewed":True,
               "side_by_side_reference_reviewed":True,"passed":True,
               "failed_visible_classes":[]},
            "user_visual_approval":True
        }
        with patch.object(g,"_read_record",return_value=record):
            out=g.validate_signoff("T42",COMMIT)
        self.assertFalse(out["passed"],out)
        self.assertTrue(any("material" in x for x in out["errors"]),out)


if __name__=="__main__":
    unittest.main(verbosity=2)
