import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import benchmark_supervisor as supervisor


def jobs(start=100):
    return {"total_count": 1, "jobs": [{"id": 7, "run_id": 3, "run_attempt": 1,
            "name": "built-pending-dependency", "status": "in_progress", "conclusion": None,
            "started_at": datetime.fromtimestamp(start, timezone.utc).isoformat(), "head_sha": "b" * 40}]}


class JobBudgetTests(unittest.TestCase):
    def bind(self, payload=None, **overrides):
        args = dict(run_id=3, attempt=1, job_name="built-pending-dependency", candidate="a" * 40,
                    wall=700, monotonic=50)
        args.update(overrides)
        return supervisor.job_binding(jobs() if payload is None else payload, **args)

    def test_actual_job_start_consumes_prior_steps_and_reserves_retention(self):
        binding = self.bind()
        self.assertEqual(40 * 60, binding["job_cap_seconds"])
        self.assertEqual(120, binding["retention_reserve_seconds"])
        self.assertEqual(1680, binding["benchmark_remaining_seconds"])
        self.assertEqual(1730, binding["benchmark_deadline_monotonic"])
        # A PR API head is not silently relabelled as its checkout merge source.
        self.assertEqual("b" * 40, binding["api_head_sha"])
        self.assertEqual("a" * 40, binding["candidate_commit"])
        late = self.bind(wall=2380)
        guard = supervisor.ProgressGuard(50, late["benchmark_deadline_monotonic"])
        with self.assertRaisesRegex(supervisor.EvidenceError, "JOB_BUDGET_EXHAUSTED"):
            guard.check(50)

    def test_stale_ambiguous_missing_and_future_metadata_fail(self):
        mutations = [lambda p: p.update(total_count=2), lambda p: p["jobs"].append(copy.deepcopy(p["jobs"][0])),
                     lambda p: p["jobs"][0].update(run_id=4), lambda p: p["jobs"][0].update(run_attempt=2),
                     lambda p: p["jobs"][0].update(status="completed"), lambda p: p["jobs"][0].update(conclusion="success"),
                     lambda p: p["jobs"][0].update(started_at=None), lambda p: p["jobs"][0].update(id=True)]
        for mutation in mutations:
            payload = jobs(); mutation(payload)
            with self.subTest(payload=payload), self.assertRaises(supervisor.EvidenceError):
                self.bind(payload)
        with self.assertRaisesRegex(supervisor.EvidenceError, "UNCHANGED_ATTEMPT"):
            self.bind(attempt=2)
        with self.assertRaisesRegex(supervisor.EvidenceError, "FUTURE"):
            self.bind(wall=99)
        with self.assertRaisesRegex(supervisor.EvidenceError, "INVALID_CLOCK"):
            self.bind(wall=float("nan"))


class PhaseLivenessTests(unittest.TestCase):
    def event(self, index):
        cycle, state = supervisor.EXPECTED[index]
        return json.dumps({"cycle": cycle, "completed_control": state})

    def test_healthy_progress_after_old_elapsed_cutoff_but_before_original_job_cap(self):
        guard = supervisor.ProgressGuard(0, 2200)
        times = [700, 840, 980, 1120, 1260, 1400, 1540, 1680, 1820]
        for index, now in enumerate(times):
            guard.line(self.event(index), now)
        guard.check(1850)
        self.assertEqual(9, len(guard.events))
        with self.assertRaisesRegex(supervisor.EvidenceError, "JOB_BUDGET_EXHAUSTED"):
            guard.check(2200)

    def test_duplicate_out_of_order_forged_and_extra_events_do_not_extend_time(self):
        for invalid in [self.event(0), self.event(2), '{"cycle":0,"completed_control":"frozen","passed":true}',
                        '{"cycle":false,"completed_control":"frozen"}', '{"completed_control":']:
            guard = supervisor.ProgressGuard(0, 4000)
            guard.line(self.event(0), 10)
            with self.subTest(invalid=invalid), self.assertRaises(supervisor.EvidenceError):
                guard.line(invalid, 1000)
            self.assertEqual(10, guard.last_progress)
        guard = supervisor.ProgressGuard(0, 4000)
        for index in range(9):
            guard.line(self.event(index), index + 1)
        with self.assertRaisesRegex(supervisor.EvidenceError, "INVALID_PROGRESS_SEQUENCE"):
            guard.line(self.event(8), 100)

    def test_log_noise_clock_regression_and_boundary_do_not_reset_deadline(self):
        guard = supervisor.ProgressGuard(0, 4000)
        guard.line("ordinary output", 1799)
        with self.assertRaisesRegex(supervisor.EvidenceError, "BENCHMARK_STALLED"):
            guard.line(self.event(0), 1800)
        guard = supervisor.ProgressGuard(20, 2200)
        with self.assertRaisesRegex(supervisor.EvidenceError, "CLOCK_REGRESSION"):
            guard.check(19)
        with self.assertRaisesRegex(supervisor.EvidenceError, "INVALID_CLOCK"):
            guard.check(float("nan"))

    def test_retained_observable_trace_is_replayable_from_clean_checkout(self):
        root = Path(__file__).resolve().parents[4]
        proof = json.loads((root / "Docs/Production/T10/Proofs/benchmark-supervisor-trace-proof.json").read_text())
        diagnostic = proof["completed_diagnostic"]
        guard = supervisor.ProgressGuard(0, diagnostic["counterfactual_stage_budget_seconds"])
        for row in diagnostic["observed_event_brackets"]:
            self.assertLessEqual(row["earliest_seconds"], row["latest_seconds"])
            guard.line(json.dumps(row["event"]), row["latest_seconds"])
        guard.check(diagnostic["latest_exit_observation_seconds"])
        self.assertEqual(9, len(guard.events))
        with self.assertRaisesRegex(supervisor.EvidenceError, "JOB_BUDGET_EXHAUSTED"):
            guard.check(diagnostic["counterfactual_stage_budget_seconds"])
        original = proof["original_failure"]
        events = guard.events[:original["completion_only_replay"]["event_count"]]
        errors = supervisor.completion_errors(124, events, None, original["candidate"])
        self.assertIn("BENCHMARK_PROCESS_FAILED", errors)
        self.assertIn("INCOMPLETE_PROGRESS_SEQUENCE", errors)
        self.assertIn("MISSING_BENCHMARK_MANIFEST", errors)
        self.assertIsNone(original["timestamps"])
        self.assertIsNone(proof["prior_success"]["timestamps"])
        self.assertFalse(proof["task_approved"])
        self.assertFalse(proof["approval_reuse"])
        # Full raw manifest replay is independently retained in the proof;
        # these embedded event brackets prove liveness only, never G8 approval.
        for row in proof["negative_contract_cases"].values():
            self.assertFalse(row["completion_contract_satisfied"])

    def test_later_phase_stall_does_not_borrow_prior_progress(self):
        guard = supervisor.ProgressGuard(0, 4000)
        guard.line(self.event(0), 100)
        guard.line("ordinary output", 1899)
        with self.assertRaisesRegex(supervisor.EvidenceError, "BENCHMARK_STALLED"):
            guard.check(1900)
        self.assertEqual(1, len(guard.events))
        self.assertEqual(100, guard.last_progress)

    def test_all_events_do_not_replace_process_exit_or_manifest_validation(self):
        events = [{"cycle": cycle, "completed_control": state} for cycle, state in supervisor.EXPECTED]
        with patch.object(supervisor, "benchmark_errors", return_value=[]):
            self.assertEqual([], supervisor.completion_errors(0, events, {"fixture": True}, "a" * 40))
            for returncode in (1, 124, -15):
                self.assertIn("BENCHMARK_PROCESS_FAILED", supervisor.completion_errors(returncode, events, {}, "a" * 40))
            self.assertIn("MISSING_BENCHMARK_MANIFEST", supervisor.completion_errors(0, events, None, "a" * 40))
            self.assertIn("INCOMPLETE_PROGRESS_SEQUENCE", supervisor.completion_errors(0, events[:-1], {}, "a" * 40))
        with patch.object(supervisor, "benchmark_errors", return_value=["source mismatch"]):
            self.assertIn("source mismatch", supervisor.completion_errors(0, events, {}, "a" * 40))


class SupervisorExecutionTests(unittest.TestCase):
    def test_late_admission_and_metadata_failure_never_launch_godot(self):
        import subprocess
        for wall, metadata, expected in [(2380, json.dumps(jobs()).encode(), "JOB_BUDGET_EXHAUSTED"),
                                         (700, subprocess.TimeoutExpired("gh api", 30), "timed out")]:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); script = root / "tools/havenline/task10/benchmark_world_transform.gd"
                script.parent.mkdir(parents=True); script.write_text("fixture only")
                context = {"GITHUB_RUN_ID": "3", "GITHUB_RUN_ATTEMPT": "1", "GITHUB_JOB": "built-pending-dependency", "GITHUB_REPOSITORY": "owner/repo"}
                with patch.object(supervisor, "ROOT", root), patch.object(supervisor.subprocess, "check_output", side_effect=["a" * 40, metadata]), \
                     patch.object(supervisor.subprocess, "run"), patch.object(supervisor.subprocess, "Popen") as spawn, \
                     patch.object(supervisor.time, "time", return_value=wall), patch.object(supervisor.time, "monotonic", return_value=50):
                    self.assertNotEqual(0, supervisor.run("a" * 40, root / "out", context))
                    spawn.assert_not_called()
                result = json.loads((root / "out/supervisor.json").read_text())
                self.assertFalse(result["benchmark_started"])
                self.assertIn(expected, " ".join(result["errors"]))

    def test_loop_clock_expiry_and_invalid_events_preserve_failure_evidence(self):
        scenarios = [(100, 1850, b"", "BENCHMARK_STALLED", 124),
                     (700, 1730, b"", "JOB_BUDGET_EXHAUSTED", 124),
                     (100, 50, b'{"cycle":0,"completed_control":"hidden"}\n' * 2, "INVALID_PROGRESS_SEQUENCE", 1)]
        for wall, loop_clock, log, expected, status in scenarios:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); script = root / "tools/havenline/task10/benchmark_world_transform.gd"
                script.parent.mkdir(parents=True); script.write_text("fixture only")
                class Child:
                    pid = 123
                    def __init__(self, argv, **kwargs):
                        kwargs["stdout"].write(log); kwargs["stdout"].flush()
                    def poll(self):
                        return None
                context = {"GITHUB_RUN_ID": "3", "GITHUB_RUN_ATTEMPT": "1", "GITHUB_JOB": "built-pending-dependency", "GITHUB_REPOSITORY": "owner/repo"}
                with patch.object(supervisor, "ROOT", root), patch.object(supervisor.subprocess, "check_output", side_effect=["a" * 40, json.dumps(jobs()).encode()]), \
                     patch.object(supervisor.subprocess, "run"), patch.object(supervisor.subprocess, "Popen", side_effect=Child), \
                     patch.object(supervisor, "terminate_group") as terminate, patch.object(supervisor.time, "time", return_value=wall), \
                     patch.object(supervisor.time, "monotonic", side_effect=[50, loop_clock, loop_clock]):
                    self.assertEqual(status, supervisor.run("a" * 40, root / "out", context))
                    terminate.assert_called_once()
                result = json.loads((root / "out/supervisor.json").read_text())
                self.assertIn(expected, result["errors"])
                self.assertEqual(status, result["supervisor_exit_code"])
                self.assertFalse(result["passed"])
                self.assertTrue((root / "out/benchmark.log").is_file())

    def test_existing_output_is_preserved_not_relabelled_as_another_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            original = '{"passed":false,"original_failure":"timeout"}'
            (output / "supervisor.json").write_text(original)
            with patch.object(supervisor.subprocess, "Popen") as spawn:
                self.assertEqual(1, supervisor.run("a" * 40, output, {}))
                spawn.assert_not_called()
            self.assertEqual(original, (output / "supervisor.json").read_text())
            self.assertFalse(json.loads((output / "supervisor-refused-existing-output.json").read_text())["passed"])

    def test_completed_child_is_drained_and_individual_lines_are_bounded(self):
        events = b"".join((json.dumps({"cycle": cycle, "completed_control": state}) + "\n").encode()
                          for cycle, state in supervisor.EXPECTED)
        noise = b"ordinary output\n" * 10000
        scenarios = [(events + noise, True, None),
                     (events + noise + events.splitlines()[0], False, "INVALID_PROGRESS_SEQUENCE"),
                     (events + noise + b'x' * 65537 + b'\n', False, "OVERSIZED_BENCHMARK_LOG_LINE"),
                     (events + noise + b'x' * 65537, False, "OVERSIZED_BENCHMARK_LOG_LINE")]
        for log, passed, error in scenarios:
            with self.subTest(error=error), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); script = root / "tools/havenline/task10/benchmark_world_transform.gd"
                script.parent.mkdir(parents=True); script.write_text("fixture only")
                output = root / "out"
                class Child:
                    pid = 123
                    def __init__(self, argv, **kwargs):
                        kwargs["stdout"].write(log); kwargs["stdout"].flush()
                        (output / "manifest.json").write_text('{"fixture":true}')
                    def poll(self):
                        return 0
                context = {"GITHUB_RUN_ID": "3", "GITHUB_RUN_ATTEMPT": "1", "GITHUB_JOB": "built-pending-dependency", "GITHUB_REPOSITORY": "owner/repo"}
                with patch.object(supervisor, "ROOT", root), patch.object(supervisor.subprocess, "check_output", side_effect=["a" * 40, json.dumps(jobs()).encode()]), \
                     patch.object(supervisor.subprocess, "run"), patch.object(supervisor.subprocess, "Popen", side_effect=Child), \
                     patch.object(supervisor.time, "time", return_value=700), patch.object(supervisor.time, "monotonic", return_value=50), \
                     patch.object(supervisor, "benchmark_errors", return_value=[]):
                    self.assertEqual(0 if passed else 1, supervisor.run("a" * 40, output, context))
                result = json.loads((output / "supervisor.json").read_text())
                self.assertEqual(passed, result["passed"])
                self.assertEqual(log, (output / "benchmark.log").read_bytes())
                if error:
                    self.assertIn(error, result["errors"])

    def test_real_supervision_loop_preserves_nonzero_signal_and_zero_outcomes(self):
        for child_exit, expected_exit in [(0, 0), (124, 124), (-15, 143)]:
            with self.subTest(child_exit=child_exit), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); script = root / "tools/havenline/task10/benchmark_world_transform.gd"
                script.parent.mkdir(parents=True); script.write_text("fixture only")
                output = root / "out"
                class Child:
                    pid = 123
                    def __init__(self, argv, **kwargs):
                        self.argv = argv
                        for cycle, state in supervisor.EXPECTED:
                            kwargs["stdout"].write((json.dumps({"cycle": cycle, "completed_control": state}) + "\n").encode())
                        kwargs["stdout"].flush()
                        (output / "manifest.json").write_text('{"fixture":true}')
                    def poll(self):
                        return child_exit
                context = {"GITHUB_RUN_ID": "3", "GITHUB_RUN_ATTEMPT": "1", "GITHUB_JOB": "built-pending-dependency",
                           "GITHUB_REPOSITORY": "owner/repo", "GH_TOKEN": "must-not-reach-child"}
                with patch.object(supervisor, "ROOT", root), patch.object(supervisor.subprocess, "check_output", side_effect=["a" * 40, json.dumps(jobs()).encode()]), \
                     patch.object(supervisor.subprocess, "run"), patch.object(supervisor.subprocess, "Popen", side_effect=Child) as spawn, \
                     patch.object(supervisor.time, "time", return_value=700), patch.object(supervisor.time, "monotonic", return_value=50), \
                     patch.object(supervisor, "benchmark_errors", return_value=[]):
                    self.assertEqual(expected_exit, supervisor.run("a" * 40, output, context))
                    self.assertNotIn("GH_TOKEN", spawn.call_args.kwargs["env"])
                result = json.loads((output / "supervisor.json").read_text())
                self.assertEqual(child_exit == 0, result["passed"])
                self.assertEqual(child_exit, result["exit_code"])
                self.assertEqual(9, len(result["progress"]))
                self.assertFalse(result["task_approved"])


if __name__ == "__main__":
    unittest.main()
