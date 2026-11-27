import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

PRODUCTION = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PRODUCTION))
import reference_style_lock as style

ROOT = PRODUCTION.parents[2]


class ReferenceStyleLockTests(unittest.TestCase):
    def test_policy_is_exact_ten_and_no_waiver(self):
        policy = json.loads(style.POLICY_PATH.read_text())
        acceptance = policy["acceptance"]
        self.assertEqual("MANDATORY_GLOBAL_VISUAL_CONTRACT", policy["status"])
        self.assertEqual(10.0, acceptance["required_style_fidelity"])
        self.assertEqual(["reference_fidelity", "visual_language"], acceptance["c1_exact_score_dimensions"])
        self.assertTrue(acceptance["no_exception_or_substitute"])
        self.assertFalse(acceptance["performance_or_schedule_waiver_allowed"])
        self.assertFalse(acceptance["placeholder_default_debug_material_allowed"])

    def test_visual_path_detection_is_additive_not_governance_noise(self):
        hits = style.visual_style_paths([
            "HavenlineGodot/shaders/outpost_snow.gdshader",
            "HavenlineLevel1/assets/tree.glb",
            "Docs/Production/REFERENCE_STYLE_LOCK.json",
        ])
        self.assertIn("HavenlineGodot/shaders/outpost_snow.gdshader", hits)
        self.assertIn("HavenlineLevel1/assets/tree.glb", hits)
        self.assertNotIn("Docs/Production/REFERENCE_STYLE_LOCK.json", hits)

    def test_t70_always_requires_full_style_lock(self):
        self.assertTrue(style.style_lock_required({"task_id": "T70"}))

    def test_missing_invalid_and_unavailable_source_diff_fail_closed(self):
        for base, candidate in [("", ""), ("HEAD", "main"), ("0" * 40, "1" * 40)]:
            with self.subTest(base=base):
                manifest = {"task_id": "T13", "base_commit": base, "candidate_commit": candidate,
                            "reference_style_lock": {"applicable": False}}
                self.assertTrue(style.style_lock_required(manifest))
                result = style.validate_manifest(manifest)
                self.assertTrue(result["required"])
                self.assertFalse(result["passed"])

    def test_old_candidate_sha_alone_never_bypasses_new_review(self):
        self.assertTrue(style.style_lock_required({
            "task_id": "T09", "base_commit": "7492074e40a0b061f31d8c32602b7a581b2610f3",
            "candidate_commit": "5415d85838ecf4bea8b3c71662072670e61797a0",
        }))

    def test_explicit_immutable_receipt_is_historical_only(self):
        result = style.validate_manifest({
            "review_scope": "historical", "task_id": "T09",
            "candidate_commit": "5415d85838ecf4bea8b3c71662072670e61797a0",
            "historical_receipt_path": "Docs/Production/T09/verified-completion.json",
        })
        self.assertTrue(result["passed"], result)
        self.assertTrue(result["historical_only"])
        self.assertFalse(result["approval_allowed"])
        self.assertEqual("HISTORICAL_RECEIPT_ONLY", result["validation_kind"])

    def test_missing_historical_receipt_is_not_preserved(self):
        result = style.validate_manifest({
            "review_scope": "historical", "task_id": "T09",
            "candidate_commit": "5415d85838ecf4bea8b3c71662072670e61797a0",
            "historical_receipt_path": "Docs/Production/does-not-exist.json",
        })
        self.assertFalse(result["passed"])
        self.assertFalse(result["approval_allowed"])

    def test_c1_contract_matches_policy_without_changing_dimensions(self):
        matrix = json.loads((ROOT / "Docs/Production/CRITIC_MATRIX.json").read_text())
        execution = json.loads((ROOT / "Docs/Production/CRITIC_EXECUTION.json").read_text())
        self.assertEqual(10.0, matrix["reference_style_lock"]["exact_score"])
        self.assertEqual(["reference_fidelity", "visual_language"], matrix["reference_style_lock"]["exact_c1_dimensions"])
        self.assertEqual(["reference_fidelity", "visual_language", "cross_view_consistency"], execution["critics"]["C1"]["dimensions"])
        self.assertEqual(10.0, execution["critics"]["C1"]["reference_style_lock"]["exact_required_score"])


class SourceDiffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.patch = patch.object(style, "ROOT", self.root)
        self.patch.start(); self.addCleanup(self.patch.stop)
        self.git("init", "-q")
        self.write("HavenlineLevel1/project.godot", "config_version=5\n")
        self.write("HavenlineLevel1/scripts/material.gd", "var material = StandardMaterial3D.new()\n")
        self.write("Generators/create.py", "material = 'StandardMaterial3D'\n")
        self.base = self.commit()

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, text=True, stderr=subprocess.PIPE).strip()

    def write(self, path, text):
        file = self.root / path; file.parent.mkdir(parents=True, exist_ok=True); file.write_text(text)

    def commit(self):
        self.git("add", ".")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "Synthetic gate fixture")
        return self.git("rev-parse", "HEAD")

    def test_deleted_and_renamed_material_sources_are_in_diff(self):
        self.git("mv", "HavenlineLevel1/scripts/material.gd", "HavenlineLevel1/scripts/renamed.gd")
        (self.root / "Generators/create.py").unlink()
        candidate = self.commit()
        files = style._changed(self.base, candidate)
        self.assertEqual({"HavenlineLevel1/scripts/material.gd", "HavenlineLevel1/scripts/renamed.gd", "Generators/create.py"}, set(files))
        self.assertEqual(set(files), set(style.visual_style_paths(files, (self.base, candidate))))

    def test_removing_codegen_material_token_still_requires_review(self):
        self.write("Generators/create.py", "material = None\n")
        candidate = self.commit()
        result = style.visual_style_paths(style._changed(self.base, candidate), (self.base, candidate))
        self.assertEqual(["Generators/create.py"], result)

    def test_new_project_and_declared_asset_root_are_detected(self):
        self.write("NewProject/project.godot", "config_version=5\n")
        self.write("NewProject/scripts/camera.gd", "extends Node\n")
        self.write("SharedAssets/catalog.txt", "new authored resource\n")
        candidate = self.commit()
        result = style.visual_style_paths(style._changed(self.base, candidate), (self.base, candidate), {"shipping_roots": ["SharedAssets/"]})
        self.assertEqual({"NewProject/project.godot", "NewProject/scripts/camera.gd", "SharedAssets/catalog.txt"}, set(result))

    def test_additive_root_cannot_escape_repository(self):
        with self.assertRaises(RuntimeError):
            style.visual_style_paths([], (self.base,), {"shipping_roots": ["../outside/"]})

    def test_malformed_style_proof_is_a_failure_not_a_waiver(self):
        manifest = {"task_id": "T13", "base_commit": self.base, "candidate_commit": self.base,
                    "reference_style_lock": {"applicable": True, "reference_hashes": [], "changed_visual_paths": [1, "x"], "evidence_path": [], "evidence_sha256": "invalid"}}
        result = style.validate_manifest(manifest, {"C1": []})
        self.assertFalse(result["passed"])
        self.assertTrue(result["required"])

    def test_nonvisual_resolvable_diff_can_remain_outside_style_scope(self):
        self.write("Docs/readme.md", "Governance only.\n")
        self.write("HavenlineLevel1/README.md", "Project instructions only.\n")
        self.write("HavenlineLevel1/LICENSE.txt", "License terms only.\n")
        candidate = self.commit()
        manifest = {"task_id": "T13", "base_commit": self.base, "candidate_commit": candidate}
        self.assertFalse(style.style_lock_required(manifest))
        self.assertTrue(style.validate_manifest(manifest)["passed"])

    def test_document_declared_as_runtime_visual_input_remains_additive(self):
        self.write("HavenlineLevel1/credits.md", "Visible in-game credits.\n")
        candidate = self.commit()
        manifest = {"task_id": "T13", "base_commit": self.base, "candidate_commit": candidate,
                    "reference_style_lock": {"changed_visual_paths": ["HavenlineLevel1/credits.md"]}}
        self.assertTrue(style.style_lock_required(manifest))
        self.assertEqual(["HavenlineLevel1/credits.md"], style.validate_manifest(manifest)["detected_visual_paths"])


if __name__ == "__main__":
    unittest.main()
