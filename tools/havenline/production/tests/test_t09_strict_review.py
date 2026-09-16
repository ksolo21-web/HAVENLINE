from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
WORKFLOW = ROOT / ".github/workflows/havenline-task09-review.yml"
C2 = ROOT / "tools/havenline/production/t09_c2_visual_review.py"
C6 = ROOT / "tools/havenline/production/t09_c6_performance_review.py"
INPUT_BUILDER = ROOT / "tools/havenline/production/t09_build_specialist_input.py"
CLOSEOUT = ROOT / "tools/havenline/production/t09_closeout_preflight.py"
OWNERSHIP = ROOT / "Docs/Production/PATH_OWNERSHIP.json"
SOURCE = "da52ff403cb766308e8f5112f04a0e7d2c7dec16"
RUN_ID = "35134329102"


class T09StrictReviewGovernanceTests(unittest.TestCase):
    def test_workflow_is_exact_source_bound_and_complete(self) -> None:
        text = WORKFLOW.read_text()
        self.assertIn("EXPECTED_SOURCE: '" + SOURCE + "'", text)
        self.assertIn("PRIMARY_RUN_ID: '" + RUN_ID + "'", text)
        self.assertIn("havenline-task09-integrated-candidate-" + SOURCE, text)
        for job in ("c2:", "c3:", "c4:", "c5:", "c6:", "strict-review-gate:", "closeout-preflight:"):
            self.assertIn("\n  " + job, text)
        self.assertIn("['C2','C3','C4','C5','C6']", text)
        self.assertIn("all(float(score)>9.0", text)
        self.assertIn("row['defects']==[]", text)
        self.assertIn("task_approved':False", text)
        self.assertIn("source_run_id':os.environ['PRIMARY_RUN_ID']", text)
        self.assertIn("c5_full_cycle_groups", text)
        self.assertIn("len(cycle_groups)>=15", text)
        self.assertIn("t09_closeout_preflight.py", text)
        self.assertIn("approval_mutation_performed", text)
        self.assertIn("integration_mutation_performed", text)

    def test_review_workflow_is_qa_governance_owned(self) -> None:
        ownership = json.loads(OWNERSHIP.read_text())
        self.assertIn(
            ".github/workflows/havenline-task09-review.yml",
            ownership["aliases"]["@ownership:QA-GOV"],
        )
        self.assertIn("tools/havenline/production/**", ownership["aliases"]["@ownership:QA-GOV"])

    def test_c2_is_independent_and_uses_group_minima_not_averages(self) -> None:
        text = C2.read_text()
        self.assertIn('"independent_runtime": True', text)
        self.assertIn('min(float(j["scores"][dim])', text)
        self.assertNotIn("sum(final_scores", text)
        self.assertIn("all(score > 9.0", text)
        self.assertIn("not defects", text)
        self.assertIn("blind-vision-probe", text)
        self.assertIn("local-checksum-pinned-public-model", text)

    def test_c5_builder_uses_every_contiguous_frame_and_respects_group_limit(self) -> None:
        text = INPUT_BUILDER.read_text()
        self.assertIn('for resource in ("wood", "stone", "fuel")', text)
        self.assertIn('if len(frames) < 80', text)
        self.assertIn('if actual != expected', text)
        self.assertIn('for index, source in enumerate(frames)', text)
        self.assertIn('index // 18 + 1', text)
        self.assertIn('"c5_uses_every_captured_frame": True', text)
        self.assertIn('> 18', text)

    def test_closeout_preflight_is_read_only_and_strict(self) -> None:
        text = CLOSEOUT.read_text()
        self.assertIn('"approval_mutation_performed": False', text)
        self.assertIn('"integration_mutation_performed": False', text)
        self.assertIn('REQUIRED_CRITICS = ["C2", "C3", "C4", "C5", "C6"]', text)
        self.assertIn('float(value) <= 9.0', text)
        self.assertIn('candidate T09 defect ledger is not empty', text)
        self.assertIn('validate-candidate', text)
        self.assertNotIn('set-status', text)
        self.assertNotIn('"APPROVED"', text)

    def test_c6_accepts_exact_limits_and_rejects_regression(self) -> None:
        good = {
            "task": "T09",
            "candidate": SOURCE,
            "passed": True,
            "physical_4k60_verified": False,
            "thermal_certified": False,
            "exact_base": "7" * 40,
            "method": "exact-base",
            "delta": {
                "p95_ms": 9.9,
                "average_draw_calls": 12.0,
                "average_primitives": 5000.0,
                "process_static_memory_mb": 32.0,
                "materials_visible": 6,
                "unique_shader_resources": 0,
                "physics_active_bodies": 0,
                "animation_players": 0,
                "active_animations": 0,
            },
            "limits": {
                "p95_ms": 10.0,
                "draw_calls": 12.0,
                "primitives": 5000.0,
                "memory_mb": 32.0,
                "materials": 6,
                "shaders": 0,
                "physics_bodies": 0,
                "animation_players": 0,
            },
        }
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            record = root / "perf.json"
            out = root / "out.json"
            record.write_text(json.dumps(good))
            ok = subprocess.run(
                [sys.executable, str(C6), "--candidate", SOURCE, "--record", str(record), "--out", str(out)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(ok.returncode, 0, ok.stderr + ok.stdout)
            self.assertTrue(json.loads(out.read_text())["passed"])
            bad = json.loads(json.dumps(good))
            bad["delta"]["p95_ms"] = 10.01
            record.write_text(json.dumps(bad))
            failed = subprocess.run(
                [sys.executable, str(C6), "--candidate", SOURCE, "--record", str(record), "--out", str(out)],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(failed.returncode, 0)
            result = json.loads(out.read_text())
            self.assertFalse(result["passed"])
            self.assertTrue(any("p95_ms" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
