import copy
import importlib.util
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[4]
spec = importlib.util.spec_from_file_location('progression', ROOT / 'tools/havenline/task10/validate_progression.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ProgressionTests(unittest.TestCase):
    def test_missing_failed_duplicate_or_fixture_checks_reject(self):
        for suite, required in module.REQUIRED.items():
            report = {'passed': True, 'failures': [], 'checks': [{'name': name, 'passed': True} for name in sorted(required)], 'real_t09_adapter_bound': True, 'fixture_simulation_only': False}
            self.assertEqual([], module.validate_report(suite, report))
            missing = copy.deepcopy(report); missing['checks'].pop()
            self.assertTrue(module.validate_report(suite, missing))
            failed = copy.deepcopy(report); failed['checks'][0]['passed'] = False
            self.assertTrue(module.validate_report(suite, failed))
            duplicate = copy.deepcopy(report); duplicate['checks'].append(duplicate['checks'][0])
            self.assertTrue(module.validate_report(suite, duplicate))
            self.assertTrue(module.validate_report(suite, {'passed': True}))
        report['fixture_simulation_only'] = True
        self.assertTrue(module.validate_report('test_task10_integration', report))
