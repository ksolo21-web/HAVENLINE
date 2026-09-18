import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[4]
spec = importlib.util.spec_from_file_location('readiness', ROOT / 'tools/havenline/task10/validate_critic_readiness.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AuthorityReadinessTests(unittest.TestCase):
    def records(self):
        return [
            {'candidate': 'a' * 40},
            {'candidate': 'a' * 40, 'fixture_simulation_only': False, 'real_t09_adapter_bound': True},
            *[{'candidate': 'a' * 40, 'real_t09_adapter_bound': True, 'exact_debit_verified': True, 'fixture_only': False} for _ in range(2)]
        ]

    def test_bound_source_passes(self):
        self.assertEqual([], module.authority_errors(*self.records(), 'a' * 40))

    def test_each_stale_source_rejects(self):
        for index in range(4):
            rows = self.records()
            rows[index]['candidate'] = 'b' * 40
            self.assertTrue(module.authority_errors(*rows, 'a' * 40))

    def test_fixture_or_missing_debit_rejects(self):
        for index, field in [(1, 'real_t09_adapter_bound'), (2, 'exact_debit_verified'), (3, 'real_t09_adapter_bound')]:
            rows = self.records()
            rows[index][field] = False
            self.assertTrue(module.authority_errors(*rows, 'a' * 40))
