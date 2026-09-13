#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate_visual_quorum import DIMS, evaluate


SOURCE = "5df9726e0b1c33f0f8865385b1c49aca229fd461"
GROUPS = {"gate", "lane"}


def row(role: str, group: str, *, score: float = 10, coverage: bool = True, defects=None) -> dict:
    return {
        "task": "T03-boundary-v2",
        "source": SOURCE,
        "role": role,
        "group": group,
        "independent_execution": True,
        "error": None,
        "review": {
            "observations": ["One.", "Two."],
            "defects": [] if defects is None else defects,
            "coverage_complete": coverage,
            "confidence": "high",
            "scores": {name: score for name in DIMS},
        },
    }


class VisualQuorumTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write_base(self, overrides=None):
        overrides = overrides or {}
        for shard, role in enumerate(sorted(("reference-fidelity", "visual-integrity"))):
            rows = [overrides.get((role, group), row(role, group)) for group in sorted(GROUPS)]
            out = self.root / f"{role}-{shard}"
            out.mkdir()
            (out / "shard-review.json").write_text(json.dumps({
                "source": SOURCE,
                "role": role,
                "shard": shard,
                "competency_passed": True,
                "error": None,
                "reviews": rows,
            }))

    def test_all_clean_passes(self):
        self.write_base()
        self.assertEqual(evaluate(self.root, SOURCE, GROUPS, None)["status"], "PASS")

    def test_incomplete_is_retried_not_counted_as_vote(self):
        bad = row("reference-fidelity", "gate", coverage=False)
        self.write_base({("reference-fidelity", "gate"): bad})
        report = evaluate(self.root, SOURCE, GROUPS, None)
        self.assertEqual(report["status"], "RETRY_REQUIRED")
        self.assertEqual(report["dissent_judgments"], [])

    def test_one_dissent_requires_adjudication_then_two_of_three_passes(self):
        bad = row("visual-integrity", "gate", score=8, defects=["Visible defect."])
        self.write_base({("visual-integrity", "gate"): bad})
        report = evaluate(self.root, SOURCE, GROUPS, None)
        self.assertEqual(report["status"], "ADJUDICATION_REQUIRED")
        adjudication = self.root / "adjudication.json"
        adjudication.write_text(json.dumps(row("independent-adjudicator", "gate")))
        report = evaluate(self.root, SOURCE, GROUPS, adjudication)
        self.assertEqual(report["status"], "PASS_BY_QUORUM")
        self.assertEqual(report["quorums"][0]["clean_votes"], 2)

    def test_two_dissents_in_same_group_fail(self):
        overrides = {
            ("visual-integrity", "gate"): row("visual-integrity", "gate", score=8, defects=["A."]),
            ("reference-fidelity", "gate"): row("reference-fidelity", "gate", score=8, defects=["B."]),
        }
        self.write_base(overrides)
        self.assertEqual(evaluate(self.root, SOURCE, GROUPS, None)["status"], "FAIL")

    def test_separate_split_groups_each_get_a_quorum(self):
        overrides = {
            ("visual-integrity", "gate"): row("visual-integrity", "gate", score=8, defects=["A."]),
            ("reference-fidelity", "lane"): row("reference-fidelity", "lane", score=8, defects=["B."]),
        }
        self.write_base(overrides)
        self.assertEqual(evaluate(self.root, SOURCE, GROUPS, None)["status"], "ADJUDICATION_REQUIRED")
        adjudication = self.root / "adjudication.json"
        adjudication.write_text(json.dumps([
            row("independent-adjudicator", "gate"),
            row("independent-adjudicator", "lane"),
        ]))
        report = evaluate(self.root, SOURCE, GROUPS, adjudication)
        self.assertEqual(report["status"], "PASS_BY_QUORUM")
        self.assertEqual(len(report["quorums"]), 2)

    def test_adjudicator_corroboration_fails(self):
        bad = row("visual-integrity", "gate", score=8, defects=["Visible defect."])
        self.write_base({("visual-integrity", "gate"): bad})
        adjudication = self.root / "adjudication.json"
        adjudication.write_text(json.dumps(row("independent-adjudicator", "gate", score=8, defects=["Confirmed."])))
        self.assertEqual(evaluate(self.root, SOURCE, GROUPS, adjudication)["status"], "FAIL")

    def test_supplemental_retry_is_not_a_vote_and_can_clear_incomplete(self):
        incomplete = row("reference-fidelity", "gate", coverage=False)
        self.write_base({("reference-fidelity", "gate"): incomplete})
        supplemental = self.root / "supplemental.json"
        retry = row("reference-fidelity", "gate")
        retry["purpose"] = "retry"
        supplemental.write_text(json.dumps([retry]))
        self.assertEqual(evaluate(self.root, SOURCE, GROUPS, None, supplemental)["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
