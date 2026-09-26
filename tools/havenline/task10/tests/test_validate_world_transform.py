import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[4]
spec = importlib.util.spec_from_file_location('t10_contract', ROOT / 'tools/havenline/task10/validate_world_transform.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CaptureAuthorityTests(unittest.TestCase):
    def test_real_capture(self):
        self.assertEqual([], module.validate_capture_authority(module.CAPTURE.read_text()))

    def test_fabricated_receipt_rejected(self):
        source = module.CAPTURE.read_text() + '\nfunc simulation_ack(intent):\n    return intent\n'
        self.assertTrue(module.validate_capture_authority(source))

    def test_missing_debit_or_conservation_rejected(self):
        for marker in ('simulation.commit_world_transform_debit(intent)', 'simulation.inventory == carried_before'):
            self.assertTrue(module.validate_capture_authority(module.CAPTURE.read_text().replace(marker, 'fixture')))
