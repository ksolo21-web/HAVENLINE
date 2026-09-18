import copy
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from collect_failure_job_logs import collect

class FailureJobLogsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = pathlib.Path(self.temp.name) / 'failed.log'
        self.run = {'id': 12, 'repository': {'full_name': 'owner/repo'}, 'status': 'in_progress', 'conclusion': None}
        self.jobs = {'total_count': 2, 'jobs': [
            {'id': 4, 'run_id': 12, 'name': 'failed critic', 'status': 'completed', 'conclusion': 'failure'},
            {'id': 9, 'run_id': 12, 'name': 'C0', 'status': 'in_progress', 'conclusion': None}]}
    def invoke(self):
        return collect(self.run, self.jobs, 12, 'owner/repo', self.output)
    @patch('collect_failure_job_logs.subprocess.run')
    def test_active_parent_completed_job_and_deterministic_order(self, api):
        api.return_value = subprocess.CompletedProcess([], 0, b'actual failure\n', b'')
        self.jobs['jobs'].append({'id': 2, 'run_id': 12, 'name': 'timeout', 'status': 'completed', 'conclusion': 'timed_out'})
        self.jobs['total_count'] = 3
        result = self.invoke()
        self.assertEqual([2, 4], [row['job_id'] for row in result['jobs']])
        self.assertEqual(result, json.loads(self.output.read_text()))
        self.assertEqual(['gh', 'api', 'repos/owner/repo/actions/jobs/2/logs'], api.call_args_list[0].args[0])
        self.assertEqual('actual failure\n', result['jobs'][0]['raw_log'])
    @patch('collect_failure_job_logs.subprocess.run')
    def test_identity_and_inconsistent_states_fail_before_api(self, api):
        mutations = [lambda: self.run.update(id=13), lambda: self.run['repository'].update(full_name='other/repo'),
            lambda: self.jobs['jobs'][1].update(id=4), lambda: self.jobs['jobs'][0].update(run_id=13),
            lambda: self.jobs['jobs'][1].update(conclusion='failure'), lambda: self.jobs.update(total_count=100),
            lambda: self.run.update(conclusion='failure'), lambda: self.jobs['jobs'][0].update(conclusion='success'),
            lambda: self.jobs['jobs'][0].update(conclusion='cancelled'),
            lambda: self.jobs['jobs'][0].update(conclusion=None),
            lambda: self.jobs['jobs'][0].update(conclusion='unknown')]
        original_run, original_jobs = copy.deepcopy(self.run), copy.deepcopy(self.jobs)
        for change in mutations:
            self.run, self.jobs = copy.deepcopy(original_run), copy.deepcopy(original_jobs)
            change()
            with self.assertRaises(ValueError): self.invoke()
            self.assertFalse(self.output.exists())
        api.assert_not_called()
    @patch('collect_failure_job_logs.subprocess.run')
    def test_api_failure_empty_and_partial_are_atomic(self, api):
        self.jobs['jobs'][1].update(status='completed', conclusion='failure')
        for bad in [subprocess.CompletedProcess([], 1, b'', b'error'), subprocess.CompletedProcess([], 0, b'  ', b'')]:
            self.output.write_text('previous complete evidence')
            api.side_effect = [subprocess.CompletedProcess([], 0, b'first job', b''), bad]
            with self.assertRaises(ValueError): self.invoke()
            self.assertEqual('previous complete evidence', self.output.read_text())
            self.assertEqual([self.output], list(self.output.parent.iterdir()))
    @patch('collect_failure_job_logs.subprocess.run')
    def test_cancelled_and_startup_markers_are_not_fabricated_logs(self, api):
        self.jobs = {'total_count': 0, 'jobs': []}
        for conclusion, marker in [('cancelled', 'CANCELLED_NO_FAILED_JOB'), ('startup_failure', 'STARTUP_FAILURE_NO_JOB_LOG')]:
            self.run.update(status='completed', conclusion=conclusion)
            result = self.invoke()
            self.assertEqual(marker, result['diagnostic_marker'])
            self.assertTrue(result['non_product_diagnostic'])
            self.assertEqual([], result['jobs'])
        for conclusion in ['failure', 'timed_out', 'success', None]:
            self.run.update(status='completed', conclusion=conclusion)
            with self.assertRaises(ValueError): self.invoke()
        api.assert_not_called()
    @patch('collect_failure_job_logs.subprocess.run')
    def test_cancelled_jobs_only_collected_for_cancelled_parent(self, api):
        api.return_value = subprocess.CompletedProcess([], 0, b'cancelled log', b'')
        self.jobs['jobs'][1].update(status='completed', conclusion='cancelled')
        result = self.invoke()
        self.assertEqual([4], [row['job_id'] for row in result['jobs']])
        self.run.update(status='completed', conclusion='cancelled')
        result = self.invoke()
        self.assertEqual([4, 9], [row['job_id'] for row in result['jobs']])
        self.assertTrue(result['run_cancelled'])
        self.assertTrue(result['non_product_diagnostic'])
    @patch('collect_failure_job_logs.subprocess.run')
    def test_completed_failure_timeout_and_startup_with_real_logs(self, api):
        api.return_value = subprocess.CompletedProcess([], 0, b'failure log', b'')
        self.jobs['jobs'][1].update(status='completed', conclusion='skipped')
        for conclusion in ['failure', 'timed_out', 'startup_failure']:
            self.run.update(status='completed', conclusion=conclusion)
            self.assertEqual([4], [row['job_id'] for row in self.invoke()['jobs']])
