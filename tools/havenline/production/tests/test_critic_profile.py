import copy
import json
import pathlib
import sys
import unittest

PRODUCTION = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PRODUCTION))
from critic_profile import resolve_critic, T10_C7_DIMENSIONS

ROOT = PRODUCTION.parents[2]


class CriticProfileTests(unittest.TestCase):
    def test_only_t10_c7_is_specialized_without_mutating_authorities(self):
        execution = json.loads((ROOT / 'Docs/Production/CRITIC_EXECUTION.json').read_text())
        matrix = json.loads((ROOT / 'Docs/Production/CRITIC_MATRIX.json').read_text())
        before = copy.deepcopy((execution, matrix))
        for number in range(10, 71):
            task = f'T{number:02d}'
            for critic in matrix['task_applicability'][task]:
                spec, checks = resolve_critic(task, critic, execution, matrix)
                if (task, critic) == ('T10', 'C7'):
                    self.assertEqual(T10_C7_DIMENSIONS, spec['dimensions'])
                    self.assertEqual(6, len(checks))
                    self.assertEqual(execution['critics'][critic]['execution_type'], spec['execution_type'])
                else:
                    self.assertEqual(execution['critics'][critic], spec)
                    self.assertEqual(matrix['critics'][critic]['checks'], checks)
        self.assertEqual(before, (execution, matrix))
        for task in (None, "", "T99"):
            with self.assertRaises(ValueError):
                resolve_critic(task, "C7", execution, matrix)
