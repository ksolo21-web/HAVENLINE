import json
import tempfile
import unittest
from pathlib import Path

from evaluate_camera_reviews import DIMS, SOURCE_GROUPS, evaluate


SOURCE = "e" * 40


def row(role, group, passed=True, attempt="primary"):
    scores = {name: (10.0 if passed else 8.9) for name in DIMS[role]}
    return {
        "task": "T04", "source": SOURCE, "critic_id": role, "group": group,
        "attempt": attempt, "independent_execution": True, "error": None,
        "review": {"scores": scores, "observations": ["Observed."],
                   "defects": [] if passed else ["Camera defect."],
                   "coverage_complete": True, "confidence": "high"},
    }


def write_result(root: Path, role: str, attempt: str, rows: list[dict]):
    folder = root / f"{role}-{attempt}"
    folder.mkdir(parents=True)
    (folder / "review-result.json").write_text(json.dumps({
        "source": SOURCE, "critic_id": role, "attempt": attempt,
        "competency_passed": True, "error": None, "reviews": rows,
    }))


class VisualQuorumTests(unittest.TestCase):
    def primaries(self, root: Path, dissent=None):
        dissent = dissent or set()
        for role in DIMS:
            write_result(root, role, "primary", [row(role, group, (role, group) not in dissent) for group in SOURCE_GROUPS])

    def test_all_primary_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.primaries(root)
            report = evaluate(root, SOURCE, None)
            self.assertTrue(report["passed"]); self.assertEqual(report["status"], "PASS")

    def test_one_dissent_requires_then_passes_quorum(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); primary = root / "primary"; supplemental = root / "supplemental"
            self.primaries(primary, {("C1", "device-matrix")})
            self.assertEqual(evaluate(primary, SOURCE, None)["status"], "ADJUDICATION_REQUIRED")
            for attempt in ("supplement-1", "supplement-2"):
                write_result(supplemental, "C1", attempt, [row("C1", "device-matrix", True, attempt)])
            report = evaluate(primary, SOURCE, supplemental)
            self.assertTrue(report["passed"]); self.assertEqual(report["status"], "PASS_BY_QUORUM")

    def test_two_negative_votes_fail_without_averaging(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); primary = root / "primary"; supplemental = root / "supplemental"
            self.primaries(primary, {("C2", "tracking-and-target")})
            write_result(supplemental, "C2", "supplement-1", [row("C2", "tracking-and-target", False, "supplement-1")])
            write_result(supplemental, "C2", "supplement-2", [row("C2", "tracking-and-target", True, "supplement-2")])
            report = evaluate(primary, SOURCE, supplemental)
            self.assertFalse(report["passed"]); self.assertEqual(report["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
