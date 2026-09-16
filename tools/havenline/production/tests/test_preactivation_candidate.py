import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
MODULE_PATH = ROOT / "tools" / "havenline" / "production" / "preactivation_candidate.py"
spec = importlib.util.spec_from_file_location("preactivation_candidate", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PreActivationCandidateTests(unittest.TestCase):
    def test_t10_style_policy_is_explicitly_allowed(self):
        checklist = {
            "isolated_build_allowed_before_all_dependencies_approved": True,
            "built_pending_dependency_allowed": True,
            "integration_allowed_before_activation": False,
        }
        allowed, policy = module.explicit_build_pending_permission(checklist)
        self.assertTrue(allowed)
        self.assertEqual(policy, "generic_build_pending_policy")

    def test_t11_style_policy_is_explicitly_allowed(self):
        checklist = {
            "build_pending_policy": {
                "isolated_build_allowed_before_t10_approval": True,
                "maximum_state_before_t10_approval": "BUILT_PENDING_DEPENDENCY",
                "may_integrate": False,
                "may_claim_integration_ready": False,
            }
        }
        allowed, policy = module.explicit_build_pending_permission(checklist)
        self.assertTrue(allowed)
        self.assertEqual(policy, "task_specific_build_pending_policy")

    def test_missing_integration_block_fails_closed(self):
        checklist = {
            "isolated_build_allowed_before_all_dependencies_approved": True,
            "built_pending_dependency_allowed": True,
            "integration_allowed_before_activation": True,
        }
        allowed, _ = module.explicit_build_pending_permission(checklist)
        self.assertFalse(allowed)

    def test_path_patterns_cover_task_workflows_but_not_foreign_task(self):
        pattern = ".github/workflows/havenline-task10-*.yml"
        self.assertTrue(module.matches(".github/workflows/havenline-task10-adapter-preflight.yml", pattern))
        self.assertTrue(module.matches(".github/workflows/havenline-task10-world-transformation.yml", pattern))
        self.assertFalse(module.matches(".github/workflows/havenline-task09-harvesting.yml", pattern))

    def test_integration_only_path_does_not_match_task_reservation(self):
        planned = [
            "HavenlineGodot/scripts/world_transform.gd",
            "Docs/Production/T10/**",
            ".github/workflows/havenline-task10-*.yml",
        ]
        self.assertFalse(any(module.matches("HavenlineGodot/scripts/simulation.gd", p) for p in planned))


if __name__ == "__main__":
    unittest.main()
