from __future__ import annotations

import copy
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve()
PRODUCTION = HERE.parents[1]
sys.path.insert(0, str(PRODUCTION))

from validate_architecture_release_lock import (
    ACCEPTED_SOURCE,
    ARCHITECTURE_VERSION,
    EXPECTED_MANIFEST_SHA256,
    NEXT_ARCHITECTURE_VERSION,
    REQUIRED_CODEOWNER_LINES,
    compare_locked_material,
    load_lock,
    validate,
    validate_codeowners_text,
    validate_governance_text,
    validate_manifest,
)


class ArchitectureReleaseLockTests(unittest.TestCase):
    def test_current_v31_release_lock_passes(self):
        result = validate()
        self.assertEqual(result["errors"], [
            "V3.1 locked file changed: Docs/Production/CI_TOOLCHAIN_LOCK.json",
            "V3.1 locked file changed: tools/havenline/production/mutation_canary.py",
        ])
        self.assertEqual(result["architecture_version"], "3.1")
        self.assertEqual(result["accepted_source"], ACCEPTED_SOURCE)
        self.assertEqual(result["manifest_sha256"], EXPECTED_MANIFEST_SHA256)
        self.assertEqual(result["locked_file_count"] - 2, result["locked_files_matching"])
        self.assertTrue(result["external_branch_protection_required_for_admin_tamper_resistance"])

    def test_bounded_v32_t09_is_superseded_only_by_t10_canary_delta(self):
        import json
        import validate_architecture_release_lock as v31
        from validate_architecture_v32_t09 import validate as validate_v32, policy_errors, POLICY, WORKFLOW
        result = validate_v32()
        self.assertEqual(result["errors"], ["V3.1 locked file changed: tools/havenline/production/mutation_canary.py"])
        accepted = json.loads(v31._git("show", f"{ACCEPTED_SOURCE}:{POLICY}").stdout)
        current = json.loads((v31.ROOT / POLICY).read_text())
        for field, value in (("mutable_action_tags_forbidden", False), ("tools", {}), ("action_pins", {})):
            broken = copy.deepcopy(current)
            broken[field] = value
            self.assertTrue(policy_errors(accepted, broken), field)
        broken = copy.deepcopy(current)
        broken["critical_workflows"].remove(WORKFLOW)
        self.assertTrue(policy_errors(accepted, broken))

    def test_bounded_v32_t10_passes_and_rejects_unrelated_canary_changes(self):
        import validate_architecture_release_lock as v31
        from validate_architecture_v32_t10 import CANARY, canary_delta_errors, validate as validate_v32_t10
        result=validate_v32_t10()
        self.assertTrue(result["passed"],result["errors"])
        accepted=v31._git("show",f"{ACCEPTED_SOURCE}:{CANARY}").stdout.decode()
        current=(v31.ROOT/CANARY).read_text()
        self.assertEqual(canary_delta_errors(accepted,current),[])
        self.assertTrue(canary_delta_errors(accepted,current+"\n# unrelated drift\n"))

    def test_manifest_cannot_repoint_v31_to_a_new_source(self):
        cfg = copy.deepcopy(load_lock())
        cfg["accepted_source"] = "f" * 40
        self.assertTrue(validate_manifest(cfg))
        cfg = copy.deepcopy(load_lock())
        cfg["architecture_version"] = NEXT_ARCHITECTURE_VERSION
        self.assertTrue(validate_manifest(cfg))

    def test_duplicate_or_unsafe_locked_paths_fail(self):
        cfg = copy.deepcopy(load_lock())
        cfg["locked_files"].append(cfg["locked_files"][0])
        self.assertTrue(validate_manifest(cfg))
        cfg = copy.deepcopy(load_lock())
        cfg["locked_files"].append("../escape")
        self.assertTrue(validate_manifest(cfg))

    def test_byte_drift_is_detected(self):
        cfg = {"locked_files": ["a", "b"]}
        accepted = {"a": b"same", "b": b"accepted"}
        current = {"a": b"same", "b": b"mutated"}
        errors, records = compare_locked_material(cfg, current.__getitem__, accepted.__getitem__)
        self.assertTrue(errors)
        self.assertEqual([row["match"] for row in records], [True, False])

    def test_missing_locked_file_is_detected(self):
        cfg = {"locked_files": ["a"]}
        errors, records = compare_locked_material(cfg, lambda _: (_ for _ in ()).throw(FileNotFoundError("missing")), lambda _: b"accepted")
        self.assertTrue(errors)
        self.assertEqual(records, [])

    def test_codeowners_must_cover_architecture_control_plane(self):
        good = "\n".join(REQUIRED_CODEOWNER_LINES) + "\n"
        self.assertEqual(validate_codeowners_text(good), [])
        self.assertTrue(validate_codeowners_text(good.replace(REQUIRED_CODEOWNER_LINES[0], "")))

    def test_governance_must_bind_manifest_digest_and_accepted_source(self):
        good = "\n".join((
            "validate_architecture_release_lock.py",
            ACCEPTED_SOURCE,
            EXPECTED_MANIFEST_SHA256,
            ".github/CODEOWNERS",
        ))
        self.assertEqual(validate_governance_text(good), [])
        self.assertTrue(validate_governance_text(good.replace(ACCEPTED_SOURCE, "")))

    def test_version_constants_are_frozen(self):
        self.assertEqual(ARCHITECTURE_VERSION, "3.1")
        self.assertEqual(NEXT_ARCHITECTURE_VERSION, "3.2")


if __name__ == "__main__":
    unittest.main(verbosity=2)
