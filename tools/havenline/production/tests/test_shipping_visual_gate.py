"""Synthetic gate fixtures only: these files never constitute Havenline approval."""
import copy
import hashlib
import io
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image

PROD=pathlib.Path(__file__).resolve().parents[1]
ROOT=pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0,str(PROD))
import reference_acceptance
import reference_style_lock
import shipping_visual_gate as gate


class ShippingPolicyTests(unittest.TestCase):
    def test_policy_preserves_primitive_material_and_native_capture_requirements(self):
        p=gate.policy()
        for token in ("BoxMesh","PlaneMesh","SphereMesh","CylinderMesh","CapsuleMesh","PrismMesh","QuadMesh","PrimitiveMesh"):
            self.assertIn(token,p["forbidden_render_types"])
        for token in ("StandardMaterial3D","ORMMaterial3D"):
            self.assertIn(token,p["forbidden_material_types"])
        self.assertEqual([3840,2160],p["human_visual_gate"]["minimum_internal_resolution"])
        self.assertEqual(60,p["human_visual_gate"]["minimum_capture_fps"])
        self.assertTrue(p["human_visual_gate"]["explicit_user_visual_approval_required"])
        self.assertIn("HavenlineLevel1/",p["active_project_roots"])
        self.assertIn("HavenlineGodot/",p["preserved_project_roots"])

    def test_known_invalidations_remain_effective(self):
        active={r["task_id"] for r in gate.invalidations()["records"] if r.get("status")=="ACTIVE"}
        self.assertTrue({"T08","T09","T10","T11"}.issubset(active))
        for task in ("T08","T09","T10","T11"):
            result=gate.effective_approval(task)
            self.assertFalse(result["passed"],result)
            self.assertTrue(result["active_invalidation"])
            self.assertTrue(result["historical_approved"])

    def test_exact_visual_maps_reject_missing_low_boolean_and_nonfinite_scores(self):
        execution=gate.load(gate.DOCS/"CRITIC_EXECUTION.json")
        maps={cid:{dim:10 for dim in execution["critics"][cid]["dimensions"]} for cid in gate.policy()["visual_critic_ids"]}
        self.assertEqual([],gate._visual_critic_errors("T13",{"critic_scores":maps}))
        for value in (9.9,True,float("nan"),float("inf"),10.01):
            changed=copy.deepcopy(maps);changed["C1"]["reference_fidelity"]=value
            self.assertTrue(gate._visual_critic_errors("T13",{"critic_scores":changed}))
        changed=copy.deepcopy(maps);del changed["C1"]["cross_view_consistency"]
        self.assertTrue(gate._visual_critic_errors("T13",{"critic_scores":changed}))

    def test_current_motion_policy_adds_c5_for_all_five_named_tasks(self):
        execution=gate.load(gate.DOCS/"CRITIC_EXECUTION.json")
        maps={cid:{dim:10 for dim in execution["critics"][cid]["dimensions"]} for cid in gate.policy()["visual_critic_ids"] if cid!="C5"}
        for task in ("T09","T16","T19","T21","T23"):
            self.assertTrue(any("C5" in e for e in gate._visual_critic_errors(task,{"critic_scores":maps})),task)
        self.assertTrue(gate._visual_critic_errors("T71",{"critic_scores":maps}))


class ShippingArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.media=tempfile.TemporaryDirectory()
        cls.videos=[]
        for index in range(2):
            file=pathlib.Path(cls.media.name)/f"motion-{index}.mp4"
            subprocess.run(["ffmpeg","-v","error","-f","lavfi","-i",f"testsrc2=size=32x32:rate=4:duration=1,rotate={index}*PI/2", "-c:v","libx264","-pix_fmt","yuv420p","-y",str(file)],check=True,capture_output=True)
            cls.videos.append(file.read_bytes())

    @classmethod
    def tearDownClass(cls):
        cls.media.cleanup()

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=pathlib.Path(self.temp.name)
        self.cfg=copy.deepcopy(gate.policy())
        # Small actual media keeps the parser tests fast. Canonical 4K60 is
        # separately asserted above and is never rewritten by these fixtures.
        self.cfg["human_visual_gate"].update(minimum_internal_resolution=[32,32],minimum_capture_fps=4,minimum_motion_seconds=1)
        for owner,field,value in ((gate,"ROOT",self.root),(reference_style_lock,"ROOT",self.root)):
            p=patch.object(owner,field,value);p.start();self.addCleanup(p.stop)
        p=patch.object(gate,"policy",lambda:self.cfg);p.start();self.addCleanup(p.stop)
        self.git("init","-q")
        self.write("HavenlineLevel1/project.godot",b"config_version=5\n")
        self.write("HavenlineLevel1/main.gd",b"extends Node\n")
        self.write("HavenlineGodot/project.godot",b"config_version=5\n")
        self.write("HavenlineGodot/legacy.gd",b"var unused = BoxMesh.new()\n")
        self.sources=json.loads((ROOT/"Docs/Design/ReferenceVideoLock/reference-video-sources.json").read_text())
        self.write("Docs/Design/ReferenceVideoLock/reference-video-sources.json",json.dumps(self.sources).encode())
        self.candidate=self.commit()

    def git(self,*args):
        return subprocess.check_output(["git",*args],cwd=self.root,text=True,stderr=subprocess.PIPE).strip()

    def write(self,path,data):
        file=self.root/path;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(data)
        return {"path":path,"sha256":hashlib.sha256(data).hexdigest()}

    def commit(self):
        self.git("add",".")
        self.git("-c","user.name=Test","-c","user.email=test@example.invalid","commit","-qm","Synthetic gate fixture")
        return self.git("rev-parse","HEAD")

    def image(self,path,color):
        out=io.BytesIO();Image.new("RGB",(32,32),color).save(out,format="PNG")
        return self.write(path,out.getvalue())

    def scope(self):
        return {"candidate_commit":self.candidate,"project_root":"HavenlineLevel1/",
                "project_file_sha256":hashlib.sha256((self.root/"HavenlineLevel1/project.godot").read_bytes()).hexdigest(),"dependency_roots":[]}

    def record(self):
        rec={"schema_version":1,"task_id":"T13","candidate_sha":self.candidate,
             "reference_acceptance":reference_acceptance.acceptance_binding(),
             "primitive_audit":{"passed":True,"findings_count":0},
             "shipping_scope":self.scope(),"user_visual_approval":True,"user_visual_rejection":False}
        evidence={"candidate_commit":self.candidate,"source_bound":True,"workflow_run_id":123,"artifact_id":456,
                  "stills_count":4,"motion_video_seconds":2.0,"internal_resolution":[32,32],"capture_fps":4,"stills":[],"motion_videos":[]}
        for i in range(4):
            row=self.image(f"proof/still-{i}.png",(20+i*20,40,60));row.update(candidate_commit=self.candidate,scene="synthetic",state=f"state-{i}",camera=f"camera-{i}")
            evidence["stills"].append(row)
        for i,video in enumerate(self.videos):
            row=self.write(f"proof/motion-{i}.mp4",video);row.update(candidate_commit=self.candidate,scene="synthetic",state="cycle" if i==0 else "transition",camera=f"camera-{i}",category="motion_cycle" if i==0 else "motion_transition")
            evidence["motion_videos"].append(row)
        rec["visual_evidence"]=evidence
        build={**self.scope(),"source_bound":True,"passed":True,"dependency_census_complete":True,"workflow_run_id":123,"artifact_id":456}
        rec["shipping_scope"]["build_evidence"]=self.write("proof/build.json",json.dumps(build).encode())
        execution=gate.load(gate.DOCS/"CRITIC_EXECUTION.json")
        fidelity={"candidate_commit":self.candidate,"coverage_complete":True,"passed":True,"whole_frame_reviewed":True,
                  "side_by_side_reference_reviewed":True,"reference_pixels_reviewed":True,"failed_visible_classes":[],
                  "primary_reference_ids":["A","B"],"reference_frames":[],
                  "critic_scores":{cid:{dim:10 for dim in execution["critics"][cid]["dimensions"]} for cid in self.cfg["visual_critic_ids"]}}
        for i,source in enumerate(self.sources["sources"]):
            row=self.image(f"proof/reference-{source['id']}.png",(30,40+i*20,90))
            row.update(reference_id=source["id"],video_sha256=source["sha256"],sampled_timestamp_seconds=16)
            fidelity["reference_frames"].append(row)
        rec["reference_fidelity"]=fidelity
        independent={"independent_runtime":True,"candidate_commit":self.candidate,"provider":"agent-native",
                     "model":"synthetic-test-reviewer","request_or_run_id":"synthetic-test-only"}
        raw={**copy.deepcopy(fidelity),**independent,"task_id":"T13","reference_acceptance":rec["reference_acceptance"],
             "status":"PASS","defects":[],"visual_evidence":copy.deepcopy(evidence),"shipping_scope":copy.deepcopy(rec["shipping_scope"]),
             "reviewed_ranges":[{"path":row["path"],"sha256":row["sha256"],"start_seconds":0,"end_seconds":1,
                                  "checks":execution["critics"]["C5"]["dimensions"]} for row in evidence["motion_videos"]]}
        artifact=self.write("proof/reviewer.json",json.dumps(raw).encode())
        independent.update(raw_output_path=artifact["path"],raw_output_sha256=artifact["sha256"])
        fidelity["independent_review"]=independent
        return rec

    def validate(self,rec):
        self.write(gate.signoff_path("T13",self.candidate),json.dumps(rec).encode())
        return gate.validate_signoff("T13",self.candidate)

    def test_active_project_scan_does_not_treat_unused_preserved_project_as_shipped(self):
        result=gate.scan_task("T13",self.candidate,{"shipping_scope":self.scope()})
        self.assertTrue(result["passed"],result)
        self.assertIn("HavenlineLevel1/main.gd",result["scanned_files"])
        self.assertNotIn("HavenlineGodot/legacy.gd",result["scanned_files"])
        self.assertFalse(result["approval_allowed"])

    def test_new_active_files_are_scanned_even_outside_old_task_ownership(self):
        self.write("HavenlineLevel1/new_runtime/material_factory.cs",b"var m = new StandardMaterial3D();\n")
        self.candidate=self.commit()
        result=gate.scan_task("T13",self.candidate,{"shipping_scope":self.scope()})
        self.assertFalse(result["passed"])
        self.assertTrue(any(f.get("token")=="StandardMaterial3D" for f in result["findings"]))

    def test_missing_selection_and_unavailable_source_block(self):
        self.assertFalse(gate.scan_task("T13",self.candidate,{})["passed"])
        self.assertFalse(gate.scan_task("T13","0"*40,{"shipping_scope":self.scope()})["passed"])
        wrong=self.scope();wrong["project_root"]="HavenlineGodot/"
        self.assertFalse(gate.scan_task("T13",self.candidate,{"shipping_scope":wrong})["passed"])

    def test_unknown_project_cannot_be_silently_omitted(self):
        self.write("NewProject/project.godot",b"config_version=5\n")
        self.candidate=self.commit()
        result=gate.scan_task("T13",self.candidate,{"shipping_scope":self.scope()})
        self.assertFalse(result["passed"])
        self.assertIn("unregistered",str(result["findings"]))

    def test_registered_additional_active_project_must_be_included_and_scanned(self):
        self.write("NewProject/project.godot",b"config_version=5\n")
        self.write("NewProject/main.gd",b"var m = BoxMesh.new()\n")
        self.candidate=self.commit();self.cfg["active_project_roots"].append("NewProject/")
        scope=self.scope()
        self.assertFalse(gate.scan_task("T13",self.candidate,{"shipping_scope":scope})["passed"])
        scope["dependency_roots"]=["NewProject/"]
        result=gate.scan_task("T13",self.candidate,{"shipping_scope":scope})
        self.assertIn("NewProject/main.gd",result["scanned_files"])
        self.assertFalse(result["passed"])

    def test_external_runtime_dependency_requires_additive_selected_root(self):
        self.write("HavenlineLevel1/main.gd",b'var asset = "res://../SharedAssets/material.gd"\n')
        self.write("SharedAssets/material.gd",b"var m = BoxMesh.new()\n")
        self.candidate=self.commit();scope=self.scope()
        result=gate.scan_task("T13",self.candidate,{"shipping_scope":scope})
        self.assertTrue(any(f["category"]=="unselected_dependency" for f in result["findings"]))
        scope["dependency_roots"]=["SharedAssets/"]
        result=gate.scan_task("T13",self.candidate,{"shipping_scope":scope})
        self.assertIn("SharedAssets/material.gd",result["scanned_files"])
        self.assertFalse(result["passed"])

    def test_referenced_tool_fixture_cannot_hide_behind_directory_exclusion(self):
        self.write("HavenlineLevel1/main.gd",b'var asset = "res://tools/shipped.gd"\n')
        self.write("HavenlineLevel1/tools/shipped.gd",b"var m = BoxMesh.new()\n")
        self.candidate=self.commit()
        result=gate.scan_task("T13",self.candidate,{"shipping_scope":self.scope()})
        self.assertIn("HavenlineLevel1/tools/shipped.gd",result["scanned_files"])
        self.assertFalse(result["passed"])

    def test_real_media_decodes_and_source_bound_synthetic_record_passes(self):
        result=self.validate(self.record())
        self.assertTrue(result["passed"],result)

    def test_actual_artifacts_can_be_read_at_frozen_integration_commit(self):
        rec=self.record();self.validate(rec);integration=self.commit()
        self.write("proof/motion-0.mp4",b"later unrelated worktree bytes")
        result=gate.validate_signoff("T13",self.candidate,integration)
        self.assertTrue(result["passed"],result)
        self.assertFalse(gate.validate_signoff("T13",self.candidate)["passed"])

    def test_current_dependency_never_reuses_old_candidate_or_diagnostic_pass(self):
        with patch.object(gate,"graph",return_value={"tasks":{"T01":{"status":"APPROVED"}}}), \
             patch.object(gate,"active_invalidation",return_value=None), \
             patch.object(gate,"scan_task",return_value={"ref":self.candidate,"passed":True,"finding_count":0,"visual_task":True}), \
             patch.object(gate,"validate_signoff",return_value={"passed":False,"errors":["current proof missing"]}) as review:
            result=gate.effective_approval("T01",self.candidate)
        self.assertFalse(result["effective_approved"])
        self.assertFalse(result["approval_allowed"])
        review.assert_called_once_with("T01",self.candidate,None)

    def test_current_dependency_uses_bound_active_scan_and_reopens_after_source_change(self):
        rec=self.record();self.assertTrue(self.validate(rec)["passed"])
        original_load=gate.load
        def with_approved_task(path):
            result=original_load(path)
            if path.name=="task-gates.json": result={**result,"approved_tasks":[*result["approved_tasks"],"T13"]}
            return result
        current_graph=gate.graph();current_graph["tasks"]["T13"]["status"]="APPROVED"
        with patch.object(gate,"load",side_effect=with_approved_task), patch.object(gate,"graph",return_value=current_graph):
            result=gate.effective_approval("T13",self.candidate)
            self.assertTrue(result["passed"],result)
            self.assertNotIn("HavenlineGodot/legacy.gd",result["primitive_audit"]["scanned_files"])
            self.write("HavenlineLevel1/main.gd",b"extends Node\nvar changed = 1\n")
            changed=self.commit()
            result=gate.effective_approval("T13",changed)
            self.assertFalse(result["effective_approved"],result)
            self.assertEqual(changed,result["candidate_sha"])

    def test_claimed_pass_does_not_override_raw_independent_report_failure(self):
        rec=self.record();raw=json.loads((self.root/"proof/reviewer.json").read_text())
        raw["passed"]=False;raw["status"]="FAIL";raw["defects"]=["wrong reference framing"]
        artifact=self.write("proof/reviewer.json",json.dumps(raw).encode())
        rec["reference_fidelity"]["independent_review"]["raw_output_sha256"]=artifact["sha256"]
        result=self.validate(rec)
        self.assertFalse(result["passed"])
        self.assertTrue(any("independent raw report" in e for e in result["errors"]))

    def test_wrong_raw_candidate_or_artifact_identity_blocks(self):
        for field,value in (("candidate_commit","1"*40),("visual_evidence",{}),("reference_frames",[]),("critic_scores",{})):
            rec=self.record();raw=json.loads((self.root/"proof/reviewer.json").read_text());raw[field]=value
            artifact=self.write("proof/reviewer.json",json.dumps(raw).encode())
            rec["reference_fidelity"]["independent_review"]["raw_output_sha256"]=artifact["sha256"]
            with self.subTest(field=field): self.assertFalse(self.validate(rec)["passed"])

    def test_missing_owner_approval_interim_scope_and_active_invalidation_block(self):
        rec=self.record();rec["user_visual_approval"]=False
        self.assertFalse(self.validate(rec)["passed"])
        rec=self.record();rec["reference_acceptance"]=reference_acceptance.acceptance_binding("interim")
        self.assertFalse(self.validate(rec)["passed"])
        rec=self.record();rec["review_scope"]="historical"
        self.assertFalse(self.validate(rec)["passed"])
        with patch.object(gate,"active_invalidation",return_value={"family":"unresolved_visual_defect"}):
            self.assertFalse(self.validate(self.record())["passed"])

    def test_fake_reference_image_wrong_original_hash_missing_b_and_bad_timestamp_block(self):
        original=self.record()["reference_fidelity"]
        for change in ("fake_image","wrong_video","missing_b","bad_timestamp"):
            fidelity=copy.deepcopy(original)
            if change=="fake_image": fidelity["reference_frames"][0].update(self.write("proof/fake.png",b'{"not":"pixels"}'))
            elif change=="wrong_video": fidelity["reference_frames"][0]["video_sha256"]="0"*64
            elif change=="missing_b": fidelity["reference_frames"]=fidelity["reference_frames"][:1]
            else: fidelity["reference_frames"][0]["sampled_timestamp_seconds"]=1e6
            with self.subTest(change=change): self.assertTrue(gate._reference_frames_errors(fidelity,None))

    def test_corrupted_motion_or_misbound_build_proof_blocks(self):
        rec=self.record();video=rec["visual_evidence"]["motion_videos"][0]
        video.update(self.write(video["path"],b'{"not":"video"}'))
        self.assertFalse(self.validate(rec)["passed"])
        rec=self.record();build=json.loads((self.root/"proof/build.json").read_text());build["artifact_id"]=789
        rec["shipping_scope"]["build_evidence"]=self.write("proof/build.json",json.dumps(build).encode())
        self.assertFalse(self.validate(rec)["passed"])

    def test_duplicate_json_fields_and_path_escape_are_rejected(self):
        rec=self.record();path=gate.signoff_path("T13",self.candidate)
        body=json.dumps(rec);self.write(path,(body[:-1]+',"user_visual_approval":true}').encode())
        self.assertFalse(gate.validate_signoff("T13",self.candidate)["passed"])
        data,errors=gate._artifact_bytes({"path":"../outside.png","sha256":"0"*64},None)
        self.assertIsNone(data);self.assertTrue(errors)


if __name__=="__main__":
    unittest.main(verbosity=2)
