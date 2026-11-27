from __future__ import annotations

import contextlib
import io
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import workstream


class WorkstreamStatusAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.docs = pathlib.Path(self.temp.name)
        self.registry = self.docs / "WORKSTREAM_REGISTRY.json"
        self.graph = self.docs / "DEPENDENCY_GRAPH.json"
        self.ownership = self.docs / "PATH_OWNERSHIP.json"
        self.registry.write_text(json.dumps({"workstreams": [{
            "task_id": "T12", "task_name": "test progression", "workstream_id": "T12-test",
            "status": "PREPARED", "owner": "test-builder", "branch": "havenline/test",
            "owned_paths": ["@reservation:T12"], "candidate_commit": None,
        }]}, indent=2) + "\n")
        self.graph.write_text(json.dumps({"tasks": {
            "T11": {"status": "APPROVED", "dependencies": []},
            "T12": {"name": "test progression", "status": "PREPARED", "dependencies": ["T11"], "critics": ["C3", "C5"]},
        }}, indent=2) + "\n")
        self.ownership.write_text(json.dumps({"aliases": {"@reservation:T12": ["test/T12/**"]}}, indent=2) + "\n")
        self.scope = patch.object(workstream, "DOCS", self.docs)
        self.scope.start()
        self.addCleanup(self.scope.stop)
        self.stdout = contextlib.redirect_stdout(io.StringIO())
        self.stdout.__enter__()
        self.addCleanup(self.stdout.__exit__, None, None, None)

    def snapshot(self):
        return {p.name: p.read_bytes() for p in (self.registry, self.graph, self.ownership)}

    def claim(self, status):
        workstream.claim("T12", "test-builder", "havenline/test", "a" * 40, "@reservation:T12", status)

    def test_approval_bearing_setter_and_claim_leave_all_bytes_unchanged(self):
        for status in ("APPROVED", "INTEGRATION_READY", "INTEGRATING"):
            for operation in (lambda value: workstream.set_status("T12", value), self.claim):
                with self.subTest(status=status, operation=operation):
                    before = self.snapshot()
                    error = io.StringIO()
                    with contextlib.redirect_stderr(error), self.assertRaises(SystemExit):
                        operation(status)
                    self.assertEqual(before, self.snapshot())
                    self.assertIn("current exact-candidate gates", error.getvalue())
                    self.assertIn("integration-owner evidence", error.getvalue())

    def test_ordinary_build_review_repair_progress_remains_possible(self):
        graph_before = self.graph.read_bytes()
        ownership_before = self.ownership.read_bytes()
        for status in ("PREPARED", "ASSIGNED", "BUILDING_ISOLATED", "BUILT_PENDING_DEPENDENCY", "UNDER_REVIEW", "FIX_REQUIRED", "BLOCKED"):
            with self.subTest(status=status):
                workstream.set_status("T12", status)
                row = json.loads(self.registry.read_text())["workstreams"][0]
                self.assertEqual(status, row["status"])
                self.assertEqual("test-builder", row["owner"])
                self.assertIsNone(row["candidate_commit"])
                self.assertIn("status_updated_at", row)
                self.assertEqual([], workstream.registry_errors())
        self.assertEqual(graph_before, self.graph.read_bytes())
        self.assertEqual(ownership_before, self.ownership.read_bytes())

    def test_prepared_and_assigned_claims_preserve_dependency_gate(self):
        self.claim("PREPARED")
        self.assertEqual("PREPARED", json.loads(self.registry.read_text())["workstreams"][0]["status"])
        self.claim("ASSIGNED")
        self.assertEqual("ASSIGNED", json.loads(self.registry.read_text())["workstreams"][0]["status"])
        graph = json.loads(self.graph.read_text())
        graph["tasks"]["T11"]["status"] = "LOCKED"
        self.graph.write_text(json.dumps(graph))
        before = self.snapshot()
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.claim("ASSIGNED")
        self.assertEqual(before, self.snapshot())
        self.claim("PREPARED")
        self.assertEqual("PREPARED", json.loads(self.registry.read_text())["workstreams"][0]["status"])

    def test_historical_approval_records_remain_readable_not_reapproved(self):
        data = json.loads(self.registry.read_text())
        data["workstreams"][0]["status"] = "APPROVED"
        self.registry.write_text(json.dumps(data))
        self.assertEqual([], workstream.registry_errors())
        before = self.snapshot()
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            workstream.set_status("T12", "APPROVED")
        self.assertEqual(before, self.snapshot())

    def test_unknown_status_is_rejected_without_writes(self):
        before = self.snapshot()
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            workstream.set_status("T12", "LOOKS_APPROVED")
        self.assertEqual(before, self.snapshot())


if __name__ == "__main__":
    unittest.main()
