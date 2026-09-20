import copy
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw

MODULE_PATH = Path(__file__).parents[1] / "verify_rendered_clearance.py"
SPEC = importlib.util.spec_from_file_location("verify_rendered_clearance", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

SOURCE = "a" * 40
PRODUCT_SHA = "b" * 64
PROBE_SOURCE = "c" * 40
CAPTURE_SHA = "d" * 64
WORKFLOW_SHA = "e" * 64
RESOURCE_SHA = "f" * 64
VERIFIER_SHA = MODULE.sha256(MODULE_PATH)
LOGICAL_SIZE = [160, 100]
CAPTURE_SIZE = [320, 200]


class RenderedClearanceTests(unittest.TestCase):
    @staticmethod
    def transform(origin):
        return {
            "basis_x": [1.0, 0.0, 0.0],
            "basis_y": [0.0, 1.0, 0.0],
            "basis_z": [0.0, 0.0, 1.0],
            "origin": list(origin),
        }

    def test_diagnostic_workflow_is_one_shot_pinned_and_exact_baseline_bound(self):
        consumed_v1 = MODULE_PATH.parents[3] / ".github/workflows/havenline-rendered-clearance-t10-probe.yml"
        self.assertEqual(
            hashlib.sha256(consumed_v1.read_bytes()).hexdigest(),
            "607bb3ff328327c609a2735df7f46e5a60d9c174bb7e0d7770d769e3bccdbfe8",
        )
        workflow = MODULE_PATH.parents[3] / ".github/workflows/havenline-rendered-clearance-t10-probe-v2.yml"
        source = workflow.read_text()
        self.assertIn("branches: ['havenline/governance-T10-rendered-clearance-probe-v2']", source)
        self.assertIn("cancel-in-progress: false", source)
        self.assertIn("actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09", source)
        self.assertIn("actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f", source)
        self.assertIn("FAILED_SOURCE: 30a7e0cc40d44aea2b21229bc39f312da13865e0", source)
        self.assertIn("FAILED_VIEW_SHA256: 6d737567f224be8d221b18e4d0ace6c6ef10de0102d27901c9f9e8d37e6659ac", source)
        self.assertNotIn("havenline/T10-layout-solver-repair", source)
        self.assertNotIn("workflow_dispatch", source)
        self.assertIn("actions: read", source)
        self.assertIn("GITHUB_RUN_ATTEMPT", source)
        self.assertIn("T10-rendered-clearance-one-shot-v2.json", source)
        self.assertIn("T10_RENDERED_CLEARANCE_ONE_SHOT_V2", source)
        self.assertEqual(source.count("--check-only"), 4)
        self.assertEqual(source.count('timeout 30 "$engine" --headless'), 2)
        self.assertIn('test ! -e "$RUNNER_TEMP/t10-failed/HavenlineGodot/.godot"', source)
        self.assertIn('test ! -e "$GITHUB_WORKSPACE/HavenlineGodot/.godot"', source)
        self.assertIn("check-only-status.json", source)
        self.assertLess(source.index("--check-only"), source.index("- name: Render exact baseline"))
        self.assertIn("'run_id':35477329507", source)
        self.assertIn("d0fdd3252d330450f83acd14a15ca339fe9eb653cfd78008a09abe5e3c8c9116", source)
        self.assertIn("8b97ef6621bed10bcee713c9aa2021fdee2ebedfd5e2d0aa8d254c931fa1c32f", source)
        self.assertIn("one-shot diagnostic already attempted", source)
        self.assertIn("head_sha={head_sha}", source)
        self.assertIn("len(runs)==payload['total_count']", source)
        self.assertIn("len(current)==1", source)
        self.assertIn("workflow-runs-api.json", source)

    def test_one_shot_admission_rejects_missing_truncated_prior_and_wrong_attempt_history(self):
        workflow = MODULE_PATH.parents[3] / ".github/workflows/havenline-rendered-clearance-t10-probe-v2.yml"
        source = workflow.read_text()
        code = source.split("python3 - <<'PY'\n", 1)[1].split("\n          PY", 1)[0]
        code = "\n".join(line[10:] for line in code.splitlines())
        commit = "1" * 40
        tree = "2" * 40
        workflow_path = ".github/workflows/havenline-rendered-clearance-t10-probe-v2.yml"
        branch = "havenline/governance-T10-rendered-clearance-probe-v2"
        env = {
            "GITHUB_SHA": commit,
            "GITHUB_REF": f"refs/heads/{branch}",
            "GITHUB_EVENT_NAME": "push",
            "GITHUB_RUN_ATTEMPT": "1",
            "GITHUB_RUN_ID": "123",
            "GITHUB_API_URL": "https://api.github.test",
            "GITHUB_REPOSITORY": "owner/repo",
            "INTEGRATION_BRANCH": "codex/havenline-sequential-task-01",
            "AUTHORIZATION_PATH": "Docs/Production/ChangeRequests/T10-rendered-clearance-one-shot-v2.json",
            "FAILED_SOURCE": "3" * 40,
            "FAILED_VIEW_SHA256": "4" * 64,
            "GH_TOKEN": "fixture-token",
        }
        auth = {
            "task_id": "T10",
            "authorization_kind": "T10_RENDERED_CLEARANCE_ONE_SHOT_V2",
            "disposition": "AUTHORIZED_FOR_ONE_DIAGNOSTIC_EXECUTION",
            "diagnostic_execution_authorized": True,
            "max_runs": 1,
            "supersedes_failed_diagnostic": {
                "run_id": 35477329507,
                "run_attempt": 1,
                "conclusion": "failure",
                "source_commit": "f3ded9ba3d0c0d2182c9db4efbc9cc0a703dc347",
                "source_tree": "fca9a337b7b4fdf3b2ccbb1c38ce603876f927c0",
                "artifact_id": 10594507398,
                "artifact_zip_sha256": "d0fdd3252d330450f83acd14a15ca339fe9eb653cfd78008a09abe5e3c8c9116",
                "diagnosis_sha256": "8b97ef6621bed10bcee713c9aa2021fdee2ebedfd5e2d0aa8d254c931fa1c32f",
                "product_evidence": "NONE",
            },
            "probe": {
                "commit": commit, "tree": tree, "workflow_path": workflow_path,
                "workflow_sha256": hashlib.sha256(source.encode()).hexdigest(),
                "ref": env["GITHUB_REF"], "event": "push",
                "failed_source": env["FAILED_SOURCE"],
                "failed_view_sha256": env["FAILED_VIEW_SHA256"],
            },
        }
        current = {"id": 123, "path": workflow_path, "head_sha": commit,
                   "head_branch": branch, "event": "push", "run_attempt": 1}
        cases = {
            "missing_list": {},
            "missing_current": {"total_count": 0, "workflow_runs": []},
            "truncated": {"total_count": 101, "workflow_runs": [dict(current, id=i) for i in range(100)]},
            "prior": {"total_count": 2, "workflow_runs": [current, dict(current, id=122)]},
            "wrong_attempt": {"total_count": 1, "workflow_runs": [dict(current, run_attempt=2)]},
        }

        def mocked_git(args, **_kwargs):
            if args[1] == "rev-parse":
                return tree + "\n"
            return json.dumps(auth).encode()

        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / workflow_path
            target.parent.mkdir(parents=True)
            target.write_text(source)
            previous = os.getcwd()
            os.chdir(temporary)
            try:
                for name, payload in cases.items():
                    with self.subTest(name=name), patch.dict(os.environ, env), \
                            patch("subprocess.check_output", mocked_git), \
                            patch("urllib.request.urlopen", return_value=io.BytesIO(json.dumps(payload).encode())), \
                            contextlib.redirect_stdout(io.StringIO()), self.assertRaises(Exception):
                        exec(compile(code, "admission-fixture", "exec"), {})
                valid = {"total_count": 1, "workflow_runs": [current]}
                with patch.dict(os.environ, env), patch("subprocess.check_output", mocked_git), \
                        patch("urllib.request.urlopen", return_value=io.BytesIO(json.dumps(valid).encode())), \
                        contextlib.redirect_stdout(io.StringIO()):
                    exec(compile(code, "admission-fixture", "exec"), {})
                binding_mutations = {
                    "wrong_probe_commit": lambda row: row["probe"].update(commit="9" * 40),
                    "wrong_probe_tree": lambda row: row["probe"].update(tree="8" * 40),
                    "wrong_workflow_hash": lambda row: row["probe"].update(workflow_sha256="7" * 64),
                    "wrong_v1_artifact": lambda row: row["supersedes_failed_diagnostic"].update(
                        artifact_zip_sha256="6" * 64
                    ),
                    "false_v1_product_evidence": lambda row: row["supersedes_failed_diagnostic"].update(
                        product_evidence="PRESENT"
                    ),
                }
                for name, mutate in binding_mutations.items():
                    bad_auth = copy.deepcopy(auth)
                    mutate(bad_auth)

                    def bad_git(args, **_kwargs):
                        if args[1] == "rev-parse":
                            return tree + "\n"
                        return json.dumps(bad_auth).encode()

                    with self.subTest(name=name), patch.dict(os.environ, env), \
                            patch("subprocess.check_output", bad_git), \
                            patch("urllib.request.urlopen", return_value=io.BytesIO(json.dumps(valid).encode())), \
                            contextlib.redirect_stdout(io.StringIO()), self.assertRaises(Exception):
                        exec(compile(code, "admission-fixture", "exec"), {})
            finally:
                os.chdir(previous)

    def core(self, state: str, nonce: str):
        text = state.upper()
        lifecycle = "complete" if state == "replay" else state
        return {
            "case_nonce": nonce, "state": state, "angle": "gameplay",
            "viewport": LOGICAL_SIZE,
            "camera_transform": self.transform((5.2, 7.0, 8.7)),
            "camera_fov": 48.0, "camera_projection": 0, "camera_size": 1.0,
            "camera_near": 0.05, "camera_far": 4000.0, "camera_keep_aspect": 1,
            "visual_root_transform": self.transform((0.0, 0.0, 0.0)),
            "label_transform": self.transform((0.0, 2.8, 0.0)),
            "ring_transform": self.transform((0.0, 0.04, 0.0)),
            "ghost_transform": self.transform((0.0, 0.83, 0.0)),
            "lifecycle_descriptor": {"lifecycle": lifecycle, "readability_scale": 1.0,
                                     "feedback_text": text},
            "dynamic_phase_seconds": 0.25 / 1.4 if state == "committing" else 0.0,
            "label_text": text,
            "label_realization": {
                "offset": [-10.0, 20.0], "width": 960.0, "fixed_size": False,
                "pixel_size": 0.0057, "billboard": 1,
                "no_depth_test": True, "render_priority": 100, "outline_render_priority": 99,
            },
            "font_identity": {
                "class": "FontFile", "resource_path": "", "resource_name": "",
                "fallback_count": 1,
                "engine_version": {"major": 4, "minor": 7, "patch": 2},
                "font_size": 38, "outline_size": 9,
                "resource_symbols_path": "res://assets/world_transform_v1/resource_symbols.tres",
                "resource_symbols_sha256": RESOURCE_SHA,
            },
            "renderer": "mobile/test",
            "product_source": SOURCE, "product_view_sha256": PRODUCT_SHA,
            "probe_source": PROBE_SOURCE, "probe_capture_sha256": CAPTURE_SHA,
            "probe_verifier_sha256": VERIFIER_SHA, "probe_workflow_sha256": WORKFLOW_SHA,
        }

    def make_case(self, root: Path, state: str, response, label):
        size = tuple(CAPTURE_SIZE)
        background = Image.new("RGB", size, "#101820")
        response_only = background.copy()
        ImageDraw.Draw(response_only).rectangle(response, fill="#66b86a")
        label_id_background = Image.new("RGB", size, "black")
        label_id = label_id_background.copy()
        ImageDraw.Draw(label_id).rectangle(label, fill="white")
        normal = response_only.copy()
        ImageDraw.Draw(normal).rectangle(label, fill="white")
        images = {"normal": normal, "response_only": response_only, "background": background,
                  "label_id_background": label_id_background, "label_id": label_id}
        names = {name: MODULE.expected_layer_name(state, name) for name in images}
        nonce = hashlib.sha256(f"{SOURCE}:{PROBE_SOURCE}:{state}:gameplay".encode()).hexdigest()
        core = self.core(state, nonce)
        core_json = json.dumps(core, separators=(",", ":"), ensure_ascii=False)
        core_sha = hashlib.sha256(core_json.encode()).hexdigest()
        layer_records = {}
        for name, image in images.items():
            path = root / names[name]
            image.save(path)
            layer_records[name] = {
                "file": names[name], "sha256": MODULE.sha256(path),
                "core": copy.deepcopy(core), "core_json": core_json,
                "core_sha256": core_sha, "isolation": copy.deepcopy(MODULE.ISOLATION[name]),
            }
        clearance, frame = MODULE.expected_geometry(LOGICAL_SIZE)
        return {
            "state": state, "angle": "gameplay", "file": names["normal"], "size": CAPTURE_SIZE,
            "projected_readability": {"frame_rect": frame, "required_clearance_px": clearance},
            "rendered_clearance_layers": {
                "passed": True, "process_frozen": True, "case_nonce": nonce,
                "layer_records": layer_records,
            },
        }

    def manifest(self, records):
        return {
            "candidate": SOURCE, "logical_size": LOGICAL_SIZE,
            "capture_resolution": CAPTURE_SIZE, "native_scale_1": False,
            "renderer": "mobile/test", "rendered_clearance_probe": True,
            "rendered_clearance_identity": {
                "product_source": SOURCE, "product_view_sha256": PRODUCT_SHA,
                "probe_source": PROBE_SOURCE, "probe_capture_sha256": CAPTURE_SHA,
                "probe_verifier_sha256": VERIFIER_SHA, "probe_workflow_sha256": WORKFLOW_SHA,
            },
            "angles": ["gameplay"], "records": records,
        }

    def verify(self, root: Path, manifest: dict, variant="candidate"):
        path = root / "manifest.json"
        path.write_text(json.dumps(manifest))
        return MODULE.verify(root, path, root / "masks", SOURCE, PRODUCT_SHA, variant,
                             PROBE_SOURCE, CAPTURE_SHA, VERIFIER_SHA, WORKFLOW_SHA,
                             RESOURCE_SHA, tuple(CAPTURE_SIZE))

    def records(self, root: Path, failed_states=()):
        result = []
        for state in MODULE.STATES:
            response = (110, 100, 210, 170)
            label = (130, 40, 190, 60)
            if state in failed_states:
                label = (130, 86, 190, 116)
            result.append(self.make_case(root, state, response, label))
        return result

    def build(self, variant: str, failed_states=()):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        return tmp, self.verify(root, self.manifest(self.records(root, failed_states)), variant)

    def test_candidate_accepts_six_scale_two_cases(self):
        tmp, report = self.build("candidate")
        self.addCleanup(tmp.cleanup)
        self.assertTrue(report["passed"], report)
        self.assertEqual(MODULE.CONTRACT, report["contract"])
        self.assertFalse(report["domain_complete"])
        self.assertTrue(all(row["physical_scale_xy"] == [2.0, 2.0] for row in report["rows"]))
        self.assertTrue(all(row["required_clearance_radius_xy"] == [24, 24] for row in report["rows"]))

    def test_candidate_rejects_one_pixel_direct_and_low_alpha_overlap(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        records = self.records(root)
        layer = records[0]["rendered_clearance_layers"]["layer_records"]["label_id"]
        path = root / layer["file"]
        image = Image.open(path).convert("RGB")
        image.putpixel((150, 120), (8, 8, 8))
        image.save(path); layer["sha256"] = MODULE.sha256(path)
        report = self.verify(root, self.manifest(records))
        self.assertFalse(report["passed"])
        self.assertIn("ready", report["direct_failure_states"])
        self.assertEqual(1, next(row for row in report["rows"] if row["state"] == "ready")["difference_threshold"])

    def test_candidate_rejects_one_pixel_clearance_deficit_without_overlap(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        records = [self.make_case(root, state, (110, 100, 210, 170), (130, 70, 190, 76))
                   for state in MODULE.STATES]
        report = self.verify(root, self.manifest(records))
        self.assertFalse(report["passed"])
        self.assertEqual([], report["direct_failure_states"])
        self.assertEqual(list(MODULE.STATES), report["clearance_failure_states"])

    def test_baseline_requires_all_known_direct_failures(self):
        tmp, report = self.build("baseline", MODULE.KNOWN_FAILED_STATES)
        self.addCleanup(tmp.cleanup)
        self.assertTrue(report["passed"], report)
        self.assertEqual(list(MODULE.KNOWN_FAILED_STATES), report["direct_failure_states"])
        tmp2, incomplete = self.build("baseline", ("preview",)); self.addCleanup(tmp2.cleanup)
        self.assertFalse(incomplete["passed"])
        self.assertIn("baseline missed known direct failures", "\n".join(incomplete["errors"]))

    def test_safe_frame_and_clearance_are_independent_of_candidate_report(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        records = self.records(root)
        records[0]["projected_readability"]["required_clearance_px"] = 1.0
        with self.assertRaisesRegex(ValueError, "threshold/frame"):
            self.verify(root, self.manifest(records))

        root2 = Path(tempfile.mkdtemp()); self.addCleanup(lambda: __import__('shutil').rmtree(root2))
        records2 = [self.make_case(root2, state, (110, 100, 210, 170), (10, 40, 40, 60))
                    for state in MODULE.STATES]
        report = self.verify(root2, self.manifest(records2))
        self.assertFalse(report["passed"])
        self.assertEqual(list(MODULE.STATES), report["safe_frame_failure_states"])

    def test_contrast_safe_id_layer_survives_equal_rgb_normal(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        root = Path(tmp.name); records = self.records(root)
        normal = root / records[0]["file"]
        background = root / records[0]["rendered_clearance_layers"]["layer_records"]["background"]["file"]
        Image.open(background).save(normal)
        records[0]["rendered_clearance_layers"]["layer_records"]["normal"]["sha256"] = MODULE.sha256(normal)
        self.assertTrue(self.verify(root, self.manifest(records))["passed"])

    def test_serialized_core_hash_and_required_realization_fields_fail_closed(self):
        for mutation, message in (("hash", "serialized core"), ("missing", "camera transform")):
            with self.subTest(mutation=mutation):
                tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
                root = Path(tmp.name); records = self.records(root)
                layers = records[0]["rendered_clearance_layers"]["layer_records"]
                for layer in layers.values():
                    if mutation == "hash":
                        layer["core_sha256"] = "not-a-hash"
                    else:
                        layer["core"].pop("camera_transform")
                        layer["core_json"] = json.dumps(layer["core"], separators=(",", ":"))
                        layer["core_sha256"] = hashlib.sha256(layer["core_json"].encode()).hexdigest()
                with self.assertRaisesRegex(ValueError, message):
                    self.verify(root, self.manifest(records))

    def test_cross_case_reuse_traversal_absolute_symlink_and_wrong_size_fail_closed(self):
        cases = ("reuse", "traversal", "absolute", "symlink", "wrong_size")
        for mutation in cases:
            with self.subTest(mutation=mutation):
                tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
                root = Path(tmp.name); records = self.records(root)
                layer = records[1]["rendered_clearance_layers"]["layer_records"]["normal"]
                if mutation == "reuse":
                    layer["file"] = records[0]["file"]
                    layer["sha256"] = MODULE.sha256(root / layer["file"])
                elif mutation == "traversal":
                    layer["file"] = "../outside.png"
                elif mutation == "absolute":
                    layer["file"] = str((root / records[0]["file"]).resolve())
                elif mutation == "symlink":
                    path = root / layer["file"]
                    path.unlink()
                    path.symlink_to(root / records[0]["file"])
                    layer["sha256"] = MODULE.sha256(root / records[0]["file"])
                else:
                    records[1]["size"] = [160, 100]
                with self.assertRaises(ValueError):
                    self.verify(root, self.manifest(records))

    def test_source_manifest_native_claim_and_all_black_substitution_fail_closed(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        root = Path(tmp.name); records = self.records(root)
        manifest = self.manifest(records); manifest["candidate"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            self.verify(root, manifest)
        manifest = self.manifest(records); manifest["native_scale_1"] = True
        with self.assertRaisesRegex(ValueError, "native-scale"):
            self.verify(root, manifest)
        manifest = self.manifest(records)
        layer = records[0]["rendered_clearance_layers"]["layer_records"]["normal"]
        path = root / layer["file"]
        Image.new("RGB", tuple(CAPTURE_SIZE), "black").save(path); layer["sha256"] = MODULE.sha256(path)
        with self.assertRaisesRegex(ValueError, "all-black"):
            self.verify(root, manifest)


if __name__ == "__main__":
    unittest.main()
