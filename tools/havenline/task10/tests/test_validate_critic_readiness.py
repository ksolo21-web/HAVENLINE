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

class PackageBindingTests(unittest.TestCase):
    def test_missing_or_tampered_raw_package_rejects(self):
        import hashlib,json,sys,tempfile
        sys.path.insert(0,str(ROOT/'tools/havenline/task10'))
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);raw=root/'progression.json';raw.write_text('{}')
            index=dict(candidate='a'*40,files={'progression.json':hashlib.sha256(raw.read_bytes()).hexdigest()})
            (root/'evidence-index.json').write_text(json.dumps(index))
            raw.write_text('{"tampered":true}')
            errors=module.package_errors(root,'a'*40)
            self.assertTrue(any('indexed raw digest mismatch' in e for e in errors))
            raw.unlink()
            self.assertTrue(module.package_errors(root,'a'*40))
            self.assertTrue(module.package_errors(root,'b'*40))
