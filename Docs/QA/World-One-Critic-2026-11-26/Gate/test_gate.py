import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from verify_review import check

HERE = Path(__file__).resolve().parent
POLICY = json.loads((HERE / "policy.json").read_text())
COMMIT = "a" * 40


class Gate(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "proof.json").write_bytes(b"{}")
        proof = {"file": "proof.json", "sha256": hashlib.sha256(b"{}").hexdigest()}
        self.rows = {}
        for group, spec in POLICY["scopes"].items():
            for key in spec["dimensions"]:
                self.rows[f"{group}.{key}"] = dict(score=POLICY["style_minimums"].get(key, 9.5),
                    status="pass", source=COMMIT, authors=["builder"], reviewer="critic",
                    evidence=[proof], mandatory_defects=[], device_trace="physical")
        self.review = dict(source=COMMIT, scene=POLICY["scene"], dimensions=self.rows)

    def result(self):
        return check(POLICY, self.review, COMMIT, self.root)

    def test_inclusive_and_exact_style(self):
        self.assertEqual(self.result(), [])
        self.rows["field.visual_language"]["score"] = 9.99
        self.assertTrue(self.result())

    def test_no_rounding_or_unsampled_substitution(self):
        for value in [9.49999, None, True, "9.5", float("nan"), 10.01]:
            with self.subTest(score=value):
                self.rows["resources.five_second_return"]["score"] = value
                self.assertTrue(self.result())

    def test_hold_incomplete_or_artifact_mismatch(self):
        for field, value in [("status", "blocked"), ("mandatory_defects", ["clip"]), ("reviewer", "builder"),
                             ("source", "b"*40), ("evidence", []), ("authors", [])]:
            row = self.rows["world.traversal"]
            old, row[field] = row[field], value
            self.assertTrue(self.result())
            row[field] = old
        (self.root / "proof.json").write_bytes(b"changed")
        self.assertTrue(self.result())

    def test_physical_trace_and_complete_coverage(self):
        self.rows["ultra.device_frame_pacing"]["device_trace"] = "software"
        self.assertTrue(self.result())
        del self.rows["ultra.device_frame_pacing"]
        self.assertTrue(self.result())


if __name__ == "__main__":
    unittest.main()
