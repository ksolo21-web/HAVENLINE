import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
WORKFLOWS = ROOT / '.github/workflows'
PINS = {'actions/checkout': 'fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09',
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
        self.assertEqual(5, len(paths))
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
