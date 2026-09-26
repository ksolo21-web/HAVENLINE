import copy
import pathlib
import sys
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pipeline_preflight import verify_probe, MARKER, PRODUCER

class PipelinePreflightTests(unittest.TestCase):
    def setUp(self):
        self.sha = 'a'*40
        self.run = dict(id=12, head_sha=self.sha, head_branch='havenline/T10-pipeline-preflight', repository=dict(full_name='owner/repo'))
        self.jobs = dict(jobs=[dict(id=1,name='cheap-boundary-checks',conclusion='success'),dict(id=2,name=PRODUCER,status='completed',conclusion='failure')])
        self.logs = dict(jobs=[dict(job_id=2,conclusion='failure',raw_log=f'2026-09-18 \x1b[31m{MARKER}:{self.sha}:12\x1b[0m\n')])
    def check(self):
        return verify_probe(self.run,self.jobs,self.logs,'owner/repo',12,self.sha)
    def test_real_marker_success_is_only_diagnostic(self):
        result=self.check()
        self.assertTrue(result['passed'])
        self.assertTrue(result['diagnostic_only'])
        self.assertFalse(result['task_approved'])
        self.assertFalse(result['reusable_for_approval'])
        self.assertEqual('failure', result['expected_workflow_conclusion'])
    def test_wrong_boundary_identity_job_and_echoed_marker_reject(self):
        original=copy.deepcopy((self.run,self.jobs,self.logs))
        changes=[lambda:self.run.update(head_sha='b'*40),lambda:self.run.update(id=13),
                 lambda:self.run.update(head_branch='havenline/T10-world-transformation'),
                 lambda:self.run['repository'].update(full_name='wrong/repo'),
                 lambda:self.jobs['jobs'][0].update(conclusion='failure'),
                 lambda:self.jobs['jobs'][1].update(conclusion='success'),
                 lambda:self.logs['jobs'][0].update(job_id=99),
                 lambda:self.logs['jobs'][0].update(raw_log=f"print('\\x1b[31m{MARKER}:{self.sha}:12\\x1b[0m')"),
                 lambda:self.logs['jobs'].append(copy.deepcopy(self.logs['jobs'][0]))]
        for change in changes:
            self.run,self.jobs,self.logs=copy.deepcopy(original)
            change()
            with self.assertRaises(ValueError): self.check()

    def test_workflow_is_bounded_pinned_diagnostic_only(self):
        root=pathlib.Path(__file__).resolve().parents[4]
        source=(root/'.github/workflows/havenline-task10-pipeline-preflight.yml').read_text()
        self.assertIn("branches: ['havenline/T10-pipeline-preflight']",source)
        self.assertNotIn('pull_request:',source)
        self.assertNotIn('paths:',source)
        self.assertIn('cancel-in-progress: false',source)
        self.assertIn('contents: read\n  actions: read',source)
        for required in ['unset GIT_LFS_SKIP_SMUDGE','prepare_activation.py','validate_world_transform.py --candidate', 'validate_migration.py','--require-bound','workstream.py validate-candidate T10','builder_repair_gate.py',"-s tools/havenline/production/tests","-s tools/havenline/task10/tests",'raise SystemExit(1)','needs: [cheap-boundary-checks, expected-diagnostic-failure]','pipeline_preflight.py --output pipeline-probe']:
            self.assertIn(required,source)
        for forbidden in ['continue-on-error', '|| true', 'cancel-in-progress: true', 'specialist_critic_runner', 'Godot', 'benchmark_world_transform', 'aggregate_critics', 'assemble_closeout.py --', 'contents: write', 'actions: write']:
            self.assertNotIn(forbidden,source)
