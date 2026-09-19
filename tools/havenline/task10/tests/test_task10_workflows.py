import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
WORKFLOWS = ROOT / '.github/workflows'
PINS = {'actions/checkout': 'fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09',
        'actions/cache/restore': 'caa296126883cff596d87d8935842f9db880ef25',
        'actions/cache/save': 'caa296126883cff596d87d8935842f9db880ef25',
        'actions/upload-artifact': 'b7c566a772e6b6bfb58ed0dc250532a479d7789f'}


def workflow_errors(source):
    errors = []
    if 'cancel-in-progress: false' not in source or 'cancel-in-progress: true' in source:
        errors.append('candidate cancellation')
    for action, version in re.findall(r'uses:\s*([^\s@]+)@([^\s]+)', source):
        if PINS.get(action) != version:
            errors.append('unpinned action')
    return errors


class WorkflowTests(unittest.TestCase):
    def test_all_task_actions_are_pinned_and_finish_sha(self):
        paths = list(WORKFLOWS.glob('havenline-task10-*.yml'))
        self.assertEqual(7, len(paths))
        for path in paths:
            self.assertEqual([], workflow_errors(path.read_text()), path.name)

    def test_canaries(self):
        self.assertTrue(workflow_errors('cancel-in-progress: true\nuses: actions/checkout@v4'))
        self.assertTrue(workflow_errors('cancel-in-progress: false\nuses: actions/checkout@v4'))

    def test_shared_regression_and_prerequisite_order(self):
        source = (WORKFLOWS / 'havenline-task10-world-transformation.yml').read_text()
        self.assertIn('production/regression_runner.py --base', source)
        self.assertIn('python3 -m pip install numpy==2.3.5', source)
        self.assertIn('Preserve regression logs on success or failure\n        if: always()', source)
        self.assertIn('--head "$GITHUB_SHA"', source)
        self.assertLess(source.index('bake_outpost_audio.py'), source.index('--import --quit'))
        self.assertLess(source.index('--import --quit'), source.index('production/regression_runner.py'))
        for suite in ('test_task09_harvesting', 'test_task09_integration', 'test_task10_world_transform', 'test_task10_integration'):
            self.assertIn(suite, source)

    def test_c0r_and_exact_builder_gate_are_direct_build_prerequisites(self):
        for name, build_job in (('world-transformation', 'first-builder-milestone'), ('isolated', 'built-pending-dependency')):
            source = (WORKFLOWS / ('havenline-task10-' + name + '.yml')).read_text()
            prebuild = source.split('  repair-sufficiency:', 1)[1].split('\n  ' + build_job + ':', 1)[0]
            build = source.split('\n  ' + build_job + ':', 1)[1]
            self.assertIn('repair_sufficiency_critic.py', prebuild)
            self.assertIn('builder_repair_gate.py', prebuild)
            self.assertIn('--base "$repair_base"', prebuild)
            self.assertIn('--head "$GITHUB_SHA"', prebuild)
            self.assertIn('INTEGRATION_BRANCH=codex/havenline-sequential-task-01', prebuild)
            self.assertIn('git fetch --no-tags origin "$INTEGRATION_BRANCH"', prebuild)
            self.assertIn('git rev-parse "origin/$INTEGRATION_BRANCH"', prebuild)
            self.assertNotIn("WORKSTREAM_REGISTRY.json'))['integration_branch']", prebuild)
            self.assertNotIn("REPAIR_PLAN.json'))['reconciled_integration_head']", prebuild)
            self.assertIn('needs: repair-sufficiency', build[:300])
            self.assertLess(prebuild.index('repair_sufficiency_critic.py'), prebuild.index('builder_repair_gate.py'))

    def test_bound_adapter_is_required(self):
        source = (WORKFLOWS / 'havenline-task10-adapter-preflight.yml').read_text()
        self.assertIn('--require-bound', source)
        self.assertIn("report['real_adapter_bound'] is True", source)
        source = (WORKFLOWS / 'havenline-task10-isolated.yml').read_text()
        self.assertIn("r.get('real_t09_adapter_bound') is True", source)
        self.assertIn("m.get('exact_debit_verified') is True", source)

    def test_historical_workflows_fail_closed_for_forward_use(self):
        for name in ('prebuild', 'preparation'):
            source = (WORKFLOWS / ('havenline-task10-' + name + '.yml')).read_text()
            self.assertIn('Reject activated forward use of historical preparation workflow', source)

class AdapterRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=(WORKFLOWS/'havenline-task10-adapter-preflight.yml').read_text()
        body=source.split("cat > /tmp/t10_adapter_scope.py <<'PY'\n",1)[1].split('          PY\n',1)[0]
        cls.namespace={'__name__':'workflow_fixture'}
        exec(compile('\n'.join(line[10:] for line in body.splitlines()),'adapter_scope','exec'),cls.namespace)
    def test_lifecycle_routing(self):
        from unittest.mock import patch
        for status,mode in [(None,'preactivation'),('LOCKED','preactivation'),('PREPARED','preactivation'),('ASSIGNED','registered'),('BLOCKED','registered'),('FIX_REQUIRED','registered')]:
            registry={'workstreams':[] if status is None else [dict(task_id='T10',status=status)]}
            with patch.dict(self.namespace,registry_errors=lambda r:[]):
                self.assertEqual(mode,self.namespace['select_mode'](registry)[0])
        for status in ('APPROVED','unknown'):
            with patch.dict(self.namespace,registry_errors=lambda r:[]),self.assertRaises(AssertionError):
                self.namespace['select_mode']({'workstreams':[dict(task_id='T10',status=status)]})
        with patch.dict(self.namespace,registry_errors=lambda r:['invalid registry']),self.assertRaises(AssertionError):
            self.namespace['select_mode']({'workstreams':[]})
    def test_registered_report_binding(self):
        check=self.namespace['validate_report'];base='a'*40;head='b'*40;integration='c'*40
        report=dict(passed=True,task_id='T10',base=base,head=head,integration_head=integration,errors=[])
        check(report,'registered',base,head,integration)
        for key,value in [('passed',False),('base','wrong'),('head','wrong'),('errors',['unauthorized'])]:
            with self.subTest(key=key),self.assertRaises(AssertionError):check(dict(report,**{key:value}),'registered',base,head,integration)
        with self.assertRaises(KeyError):check(dict(passed=True),'registered',base,head,integration)
    def test_failed_command_stops_and_no_scope_waiver(self):
        source=(WORKFLOWS/'havenline-task10-adapter-preflight.yml').read_text()
        self.assertIn('if result.returncode:',source)
        self.assertIn('raise SystemExit(result.stderr or result.stdout)',source)
        self.assertIn('check=True',source)
        self.assertNotIn('simulation.gd',source)
    def test_benchmark_uses_real_time_without_movie(self):
        source=(WORKFLOWS/'havenline-task10-isolated.yml').read_text()
        block=source.split('name: Measure warmed idle and committing performance',1)[1].split('      - name:',1)[0]
        self.assertIn('benchmark_supervisor.py',block)
        from benchmark_supervisor import command
        argv=command('a'*40,Path('/tmp/benchmark-fixture'))
        self.assertTrue(any(arg.endswith('benchmark_world_transform.gd') for arg in argv))
        self.assertNotIn('--fixed-fps',argv)
        self.assertNotIn('--write-movie',argv)

    def test_review_retention_and_bounded_control_timeout(self):
        source=(WORKFLOWS/'havenline-task10-isolated.yml').read_text()
        self.assertEqual(1,source.count('retention-days: 90'))
        self.assertIn('timeout-minutes: 40',source)
        from benchmark_supervisor import STALL_SECONDS, JOB_SECONDS
        self.assertEqual(1800,STALL_SECONDS)
        self.assertEqual(40*60,JOB_SECONDS)
        self.assertNotIn('timeout 1800 Godot',source)
        upload=source.split('name: Retain benchmark execution before further packaging',1)[1].split('name: Package source-bound specialist inputs',1)[0]
        self.assertIn('if: always()',upload)
        self.assertIn('timeout-minutes: 1',upload)

class ClosurePathTests(unittest.TestCase):
    common = {'HavenlineGodot/scripts/world_transform.gd', 'HavenlineGodot/scripts/world_transform_view.gd',
              'HavenlineGodot/data/world_transform_recipes.json', 'HavenlineGodot/assets/world_transform_v1/**',
              'Docs/Production/T10/**', 'tools/havenline/task10/**', '.github/workflows/havenline-task10-*.yml'}
    closure = {'ReviewExports/**', 'CriticRaw/**', 'independent-critic-review.json', 'defect-ledger.json',
               'verified-completion.json', 'Evidence/**', 'task-state.json'}

    @classmethod
    def check_paths(cls, source, name):
        block=source.split('  push:\n',1)[1].split('  pull_request:',1)[0]
        paths=re.findall(r"^      - '([^']+)'$",block,re.M)
        expected=cls.common | ({'HavenlineGodot/tests/test_task10_*.gd'} if name=='world-transformation' else {
            'HavenlineGodot/tests/test_task10_world_transform.gd', 'HavenlineGodot/tests/test_task10_integration.gd',
            'HavenlineGodot/tests/capture_task10_world_transform.gd'})
        assert {p for p in paths if not p.startswith('!')}==expected
        assert {p for p in paths if p.startswith('!')}=={'!Docs/Production/T10/'+p for p in cls.closure}
        return paths

    def test_only_closure_pushes_are_excluded(self):
        from fnmatch import fnmatchcase
        for name in ('isolated','world-transformation'):
            paths=self.check_paths((WORKFLOWS/('havenline-task10-'+name+'.yml')).read_text(),name)
            def triggered(file):
                result=False
                for pattern in paths:
                    if fnmatchcase(file,pattern.lstrip('!')):result=not pattern.startswith('!')
                return result
            for file in ('ReviewExports/C3-original-bundle.zip','CriticRaw/C3.json','independent-critic-review.json','defect-ledger.json','verified-completion.json','task-state.json'):
                self.assertFalse(triggered('Docs/Production/T10/'+file),file)
            for file in ('Docs/Production/T10/FROZEN_SCOPE.md','Docs/Production/T10/C0-new-finding.json','tools/havenline/task10/export_closure_records.py','HavenlineGodot/scripts/world_transform.gd','.github/workflows/havenline-task10-isolated.yml'):
                self.assertTrue(triggered(file),file)

    def test_missing_exclusion_and_broad_suppression_reject(self):
        for name in ('isolated','world-transformation'):
            source=(WORKFLOWS/('havenline-task10-'+name+'.yml')).read_text()
            for broken in (source.replace("      - '!Docs/Production/T10/CriticRaw/**'\n",'',1),
                           source.replace("!Docs/Production/T10/CriticRaw/**","!Docs/Production/T10/**",1),
                           source.replace("      - 'tools/havenline/task10/**'\n",'',1)):
                with self.assertRaises(AssertionError):self.check_paths(broken,name)

class FailureObservationTests(unittest.TestCase):
    def test_failed_lanes_invoke_c0_with_source_and_finish_running_sha(self):
        for name,required in [('world-transformation',['first-builder-milestone']),('isolated',['built-pending-dependency','review-c3','review-c4','review-c7'])]:
            source=(WORKFLOWS/('havenline-task10-'+name+'.yml')).read_text()
            job=source.split('  c0-diagnose:',1)[1]
            self.assertIn('always()',job)
            self.assertIn('uses: ./.github/workflows/havenline-c0-root-cause.yml',job)
            self.assertIn('failed_candidate: ${{ github.sha }}',job)
            self.assertIn('failed_run_id: ${{ github.run_id }}',job)
            self.assertIn('actions: read',source)
            for dependency in required:
                self.assertIn("needs."+dependency+".result == 'failure'",job)
            self.assertNotIn("== 'cancelled'",job)
