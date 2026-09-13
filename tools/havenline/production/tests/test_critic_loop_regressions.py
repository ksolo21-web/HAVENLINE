from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve()
PRODUCTION = HERE.parents[1]
ROOT = HERE.parents[4]
sys.path.insert(0, str(PRODUCTION))

from evaluate_visual_quorum import DIMS, evaluate


SOURCE = "a" * 40
GROUPS = {"gate"}


def review_row(role: str, *, score: float = 10.0, defects=None, observations=None) -> dict:
    return {
        "task": "regression-fixture",
        "source": SOURCE,
        "role": role,
        "group": "gate",
        "independent_execution": True,
        "error": None,
        "review": {
            "observations": ["fixture observation"] if observations is None else observations,
            "defects": [] if defects is None else defects,
            "coverage_complete": True,
            "confidence": "high",
            "scores": {name: score for name in DIMS},
        },
    }


class CriticLoopRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write_base(self, reference=None, integrity=None):
        rows = {
            "reference-fidelity": reference or review_row("reference-fidelity"),
            "visual-integrity": integrity or review_row("visual-integrity"),
        }
        for index, role in enumerate(sorted(rows)):
            out = self.root / f"{role}-{index}"
            out.mkdir()
            (out / "shard-review.json").write_text(json.dumps({
                "source": SOURCE,
                "role": role,
                "shard": index,
                "competency_passed": True,
                "error": None,
                "reviews": [rows[role]],
            }))

    def test_single_visual_dissent_routes_to_adjudication_not_product_failure(self):
        dissent = review_row("visual-integrity", score=8.0, defects=["visible fixture defect"])
        self.write_base(integrity=dissent)
        report = evaluate(self.root, SOURCE, GROUPS, None)
        self.assertEqual(report["status"], "ADJUDICATION_REQUIRED")
        self.assertFalse(report["passed"])

    def test_two_clean_votes_out_of_three_pass_without_score_averaging(self):
        dissent = review_row("visual-integrity", score=8.0, defects=["isolated fixture dissent"])
        self.write_base(integrity=dissent)
        adjudication = self.root / "adjudication.json"
        adjudication.write_text(json.dumps(review_row("independent-adjudicator")))
        report = evaluate(self.root, SOURCE, GROUPS, adjudication)
        self.assertEqual(report["status"], "PASS_BY_QUORUM")
        self.assertTrue(report["passed"])
        self.assertEqual(report["quorums"], [{
            "group": "gate",
            "original_pass_role": "reference-fidelity",
            "original_dissent_role": "visual-integrity",
            "adjudicator": "independent-adjudicator",
            "clean_votes": 2,
            "total_votes": 3,
        }])
        self.assertEqual(report["strict_rule"], ">9.0 unrounded; no score averaging")

    def test_two_correlated_visual_defect_votes_still_fail(self):
        reference = review_row("reference-fidelity", score=8.0, defects=["confirmed fixture defect"])
        integrity = review_row("visual-integrity", score=8.0, defects=["confirmed fixture defect"])
        self.write_base(reference=reference, integrity=integrity)
        report = evaluate(self.root, SOURCE, GROUPS, None)
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["passed"])

    def test_incomplete_reviewer_is_retry_not_a_negative_vote(self):
        incomplete = review_row("visual-integrity", observations=[])
        self.write_base(integrity=incomplete)
        report = evaluate(self.root, SOURCE, GROUPS, None)
        self.assertEqual(report["status"], "RETRY_REQUIRED")
        self.assertEqual(report["dissent_judgments"], [])

    def test_t03_closeout_uses_current_governance_with_frozen_candidate_evidence(self):
        workflow = (ROOT / ".github/workflows/havenline-task03-adjudicated-closeout.yml").read_text()
        self.assertIn("ACCEPTED_SOURCE:", workflow)
        self.assertIn("EXPECTED_SOURCE:", workflow)
        self.assertIn("actions/checkout@v4", workflow)
        self.assertNotIn("ref: ${{ env.ACCEPTED_SOURCE }}", workflow)
        self.assertNotIn("ref: '${{ env.ACCEPTED_SOURCE }}'", workflow)
        self.assertIn("--source \"$EXPECTED_SOURCE\"", workflow)
        self.assertIn("Enforce per-group two-of-three quorum", workflow)
        self.assertIn("clean_votes']==2 and q['total_votes']==3", workflow)

    def test_development_pr_does_not_require_final_game_release_certification(self):
        workflow = (ROOT / ".github/workflows/havenline-device-release-gate.yml").read_text()
        self.assertIn("ENFORCE_RELEASE_GATE:", workflow)
        self.assertIn("github.event_name == 'workflow_dispatch'", workflow)
        self.assertIn("github.ref == 'refs/heads/main'", workflow)
        self.assertIn("if: env.ENFORCE_RELEASE_GATE == 'true'", workflow)
        self.assertIn("python3 tools/havenline/release_gate.py", workflow)
        self.assertIn("validator regression tests remain mandatory", workflow)

    def test_governance_checkpoint_assertions_are_lifecycle_aware(self):
        governance = (ROOT / "tools/havenline/production/tests/test_governance.py").read_text()
        self.assertIn("registry_tasks", governance)
        self.assertIn('if node["status"]!="LOCKED"', governance)
        self.assertIn("unlocked before", governance)
        self.assertNotIn("range(4,71)", governance)

    def test_governance_only_changes_do_not_launch_full_native_review(self):
        workflow = (ROOT / ".github/workflows/havenline-godot-android.yml").read_text()
        self.assertEqual(workflow.count("!tools/havenline/production/**"), 2)
        self.assertIn("'HavenlineGodot/**'", workflow)
        self.assertIn("'tools/havenline/**'", workflow)
        self.assertIn("'.github/workflows/havenline-godot-android.yml'", workflow)

    def test_superseded_validation_runs_are_cancelled_per_branch(self):
        workflows = [
            ".github/workflows/havenline-production-governance.yml",
            ".github/workflows/havenline-critic-safeguards.yml",
            ".github/workflows/havenline-device-release-gate.yml",
        ]
        for rel in workflows:
            workflow = (ROOT / rel).read_text()
            self.assertIn("concurrency:", workflow, rel)
            self.assertIn("cancel-in-progress: true", workflow, rel)
            self.assertIn("github.event.pull_request.head.ref || github.ref_name", workflow, rel)

    def test_production_governance_is_not_frozen_to_t03_integration(self):
        workflow = (ROOT / ".github/workflows/havenline-production-governance.yml").read_text()
        self.assertIn("validate_integration_scope.py", workflow)
        self.assertIn("lifecycle-valid task integration impact", workflow)
        self.assertNotIn("CAUSALLY_GOVERNED_T03_REPAIR", workflow)
        self.assertNotIn("allowed=ownership['aliases']['@ownership:T03']", workflow)

    def test_repair_policy_blocks_evidence_only_loop_after_real_defect(self):
        policy = (PRODUCTION / "validate_repair_cycle.py").read_text()
        self.assertIn("two-strike rule blocks evidence-only rerun", policy)
        self.assertIn("no implicated production file changed", policy)
        self.assertIn("shipping gameplay scale not preserved", policy)


if __name__ == "__main__":
    unittest.main(verbosity=2)
