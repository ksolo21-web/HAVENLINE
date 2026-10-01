"""Exercise the hosted scope shell, including terminal validator failures."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[4]
WORKFLOW = ROOT / '.github/workflows/havenline-production-governance.yml'
INTEGRATION = 'codex/havenline-sequential-task-01'


class GovernanceScopeRoutingTests(unittest.TestCase):
    def run_scope(self, event, ref, fail=''):
        text = WORKFLOW.read_text()
        step = text.split('      - name: Validate complete V2 state and event-appropriate scope\n', 1)[1].split('      - name:', 1)[0]
        script = textwrap.dedent(step.split('        run: |\n', 1)[1])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            log = path / 'calls.jsonl'
            python = path / 'python3'
            python.write_text('#!' + os.sys.executable + '\n' + textwrap.dedent('''\
                import json, os, pathlib, sys
                args=sys.argv[1:]
                if args[0]=='-c':
                    print('codex/havenline-sequential-task-01')
                    raise SystemExit(0)
                with open(os.environ['CALL_LOG'],'a') as f:f.write(json.dumps(args)+'\\n')
                if os.environ.get('FAIL_VALIDATOR')==pathlib.Path(args[0]).name:
                    raise SystemExit(17)
                if '--output' in args:pathlib.Path(args[args.index('--output')+1]).write_text('{"passed":true}')
            '''))
            python.chmod(0o755)
            git = path / 'git'
            git.write_text('#!/bin/sh\nprintf "%s\\n" aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n')
            git.chmod(0o755)
            script = script.replace('/tmp/governance-scope.json', str(path / 'scope.json'))
            env = dict(os.environ, PATH=str(path)+os.pathsep+os.environ['PATH'],
                       SCOPE_EVENT=event, SCOPE_REF=ref, SCOPE_PR_BASE='b'*40,
                       CALL_LOG=str(log), FAIL_VALIDATOR=fail)
            result = subprocess.run(['bash','-c',script],env=env,capture_output=True,text=True)
            calls = [json.loads(line) for line in log.read_text().splitlines()]
            return result, calls

    def test_integration_push_uses_lifecycle_scope_with_exact_parent(self):
        result, calls = self.run_scope('push', INTEGRATION)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([Path(row[0]).name for row in calls],
                         ['validate_migration.py','validate_integration_scope.py'])
        self.assertEqual(calls[1][1:5], ['--base','a'*40,'--head','HEAD'])

    def test_governance_branches_keep_base_authoritative_migration_scope(self):
        for ref in ['havenline/governance-t09-closeout','havenline/QA-integration']:
            with self.subTest(ref=ref):
                result,calls=self.run_scope('push',ref)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertEqual(Path(calls[1][0]).name,'validate_migration_scope.py')

    def test_pull_request_cannot_enter_trusted_integration_push_lane(self):
        result,calls=self.run_scope('pull_request',INTEGRATION)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(Path(calls[1][0]).name,'validate_migration_scope.py')
        self.assertEqual(calls[1][1:5],['--base','b'*40,'--head','HEAD'])

    def test_scope_failure_is_terminal_in_both_lanes(self):
        for ref,validator in [(INTEGRATION,'validate_integration_scope.py'),
                              ('havenline/QA-integration','validate_migration_scope.py')]:
            with self.subTest(ref=ref):
                result,calls=self.run_scope('push',ref,validator)
                self.assertEqual(result.returncode,17)
                self.assertEqual(len(calls),2)
                self.assertNotIn('"passed":true',result.stdout)

    def test_full_migration_state_failure_cannot_be_routed_around(self):
        result,calls=self.run_scope('push',INTEGRATION,'validate_migration.py')
        self.assertEqual(result.returncode,17)
        self.assertEqual(len(calls),1)


if __name__=='__main__':
    unittest.main()
