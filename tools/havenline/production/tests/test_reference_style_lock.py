import json
import pathlib
import sys
import unittest

PRODUCTION = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PRODUCTION))
from reference_style_lock import style_lock_required, visual_style_paths
from architecture_v32 import validate as validate_architecture_v32

ROOT = PRODUCTION.parents[2]


class ReferenceStyleLockTests(unittest.TestCase):
    def test_policy_is_exact_ten_and_no_waiver(self):
        policy = json.loads((ROOT / "Docs/Production/REFERENCE_STYLE_LOCK.json").read_text())
        acceptance = policy["acceptance"]
        self.assertEqual("MANDATORY_GLOBAL_VISUAL_CONTRACT", policy["status"])
        self.assertEqual(10.0, acceptance["required_style_fidelity"])
        self.assertEqual(["reference_fidelity", "visual_language"], acceptance["c1_exact_score_dimensions"])
        self.assertTrue(acceptance["no_exception_or_substitute"])
        self.assertFalse(acceptance["performance_or_schedule_waiver_allowed"])
        self.assertFalse(acceptance["placeholder_default_debug_material_allowed"])

    def test_visual_path_detection_is_additive_not_governance_noise(self):
        hits = visual_style_paths([
            "HavenlineGodot/shaders/outpost_snow.gdshader",
            "HavenlineGodot/assets/reference_forest/tree.glb",
            "Docs/Production/REFERENCE_STYLE_LOCK.json",
        ])
        self.assertIn("HavenlineGodot/shaders/outpost_snow.gdshader", hits)
        self.assertIn("HavenlineGodot/assets/reference_forest/tree.glb", hits)
        self.assertNotIn("Docs/Production/REFERENCE_STYLE_LOCK.json", hits)

    def test_t70_always_requires_full_style_lock(self):
        self.assertTrue(style_lock_required({"task_id": "T70", "base_commit": "", "candidate_commit": ""}))

    def test_declared_material_review_can_be_required_before_real_sha(self):
        self.assertTrue(style_lock_required({
            "task_id": "T13",
            "base_commit": "",
            "candidate_commit": "",
            "reference_style_lock": {"applicable": True},
        }))

    def test_exact_historical_source_is_preserved_without_task_waiver(self):
        self.assertFalse(style_lock_required({
            "task_id": "T09",
            "base_commit": "7492074e40a0b061f31d8c32602b7a581b2610f3",
            "candidate_commit": "5415d85838ecf4bea8b3c71662072670e61797a0",
        }))
        self.assertTrue(style_lock_required({
            "task_id": "T09",
            "base_commit": "0" * 40,
            "candidate_commit": "1" * 40,
        }))

    def test_unresolvable_exact_diff_fails_closed(self):
        manifest = {
            "task_id": "T13",
            "base_commit": "0" * 40,
            "candidate_commit": "1" * 40,
            "reference_style_lock": {"applicable": False},
        }
        self.assertTrue(style_lock_required(manifest))

    def test_v32_architecture_remains_green_with_style_lock(self):
        report = validate_architecture_v32()
        self.assertTrue(report["passed"], report["errors"])

    def test_c1_contract_matches_policy_without_changing_dimensions(self):
        matrix = json.loads((ROOT / "Docs/Production/CRITIC_MATRIX.json").read_text())
        execution = json.loads((ROOT / "Docs/Production/CRITIC_EXECUTION.json").read_text())
        self.assertEqual(10.0, matrix["reference_style_lock"]["exact_score"])
        self.assertEqual(["reference_fidelity", "visual_language"], matrix["reference_style_lock"]["exact_c1_dimensions"])
        self.assertEqual(
            ["reference_fidelity", "visual_language", "cross_view_consistency"],
            execution["critics"]["C1"]["dimensions"],
        )
        self.assertEqual(10.0, execution["critics"]["C1"]["reference_style_lock"]["exact_required_score"])


if __name__ == "__main__":
    unittest.main()
